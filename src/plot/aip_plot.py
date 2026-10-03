import os
import math
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import multiprocessing


def _setup_chinese_font():
    # 选择系统可用中文字体，避免中文与负号显示为方框
    candidates = ['Arial Unicode MS', 'STHeiti', 'Hiragino Sans GB',
                  'Songti SC', 'PingFang SC']
    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((name for name in candidates if name in available), None)
    if chosen:
        matplotlib.rcParams['font.sans-serif'] = [chosen]
    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['figure.dpi'] = 100   # 显示分辨率
    matplotlib.rcParams['savefig.dpi'] = 200  # 保存图片分辨率


_setup_chinese_font()

from src.module.backtest_mod import AutomaticInvestmentPlan
from src.algorithm.significance import build_paired_matrix, \
    build_excess_matrix, bootstrap_median_ci, stability_verdict
from src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.db.db_backtest import FundBacktest
from src.util.industry_class import get_fileds_en
from src.util.tools import DateTools
from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)

# 满 N 情景少于该数量时不出小提琴/不做检验/不导出 stats
MIN_SCENARIOS = 8


def eligible_scenarios(df):
    """
    只保留满 N 个完整周的估值日情景（sample_insufficient==0）。
    不足 N 周的情景买入笔数少、噪声大，且与满 N 情景口径不一致，
    按 spec FR-1 不得混入分布、检验与 CI；旧 schema（无该列）视为全部可用。
    """
    if df is None or df.empty or 'sample_insufficient' not in df.columns:
        return df
    return df[df['sample_insufficient'] == 0]


def get_recent_years():
    """
    估值日 C 的近期窗口（年）：只保留「库内最后一个 C 往前 recent_years 年」
    内的情景，使收益预期与当下市场环境贴合。
    默认 1；设为 0（或负数）表示使用全部历史 C。
    """
    cfg = Config().backtest_config or {}
    return float(cfg.get('recent_years', 1))


def recent_scenarios(df):
    """
    按 recent_years 近期窗口过滤估值日情景：以该 df 内最后一个 mark_day
    为锚点，只保留窗口内的 C（按自然年偏移）。未配置窗口、无数据或
    旧 schema（无 mark_day 列）时原样返回。
    """
    if df is None or df.empty or 'mark_day' not in df.columns:
        return df
    years = get_recent_years()
    if years <= 0:
        return df
    # SQLite 读回的日期列为字符串，统一转 Timestamp 再比较
    mark_days = pd.to_datetime(df['mark_day'])
    last_c = mark_days.max()
    cutoff = last_c - pd.DateOffset(years=int(years))
    return df[mark_days > cutoff]


def analysis_scenarios(df):
    """绘图/统计的统一读取口径：近期窗口 → 满 N 完整周过滤。"""
    return eligible_scenarios(recent_scenarios(df))


def window_desc():
    """图标题用的估值日窗口说明。"""
    years = get_recent_years()
    return f'mark days within recent {years:g}y' if years > 0 \
        else 'all historical mark days'


def get_plot_metric():
    """
    小提琴口径：
    - excess（默认）：同一估值日 C 下「工作日收益 − daily 收益」配对超额，
      抵消市场 β，只呈现周几效应；
    - absolute：原始盯市收益率（跨牛熊，分布宽，含市场 β）。
    """
    cfg = Config().backtest_config or {}
    metric = cfg.get('plot_metric', 'excess')
    if metric not in ('excess', 'absolute'):
        logger.warning(f"Unknown plot_metric:{metric}, fallback to 'excess'.")
        metric = 'excess'
    return metric


def export_violin_plot_multiprocess(cpus=8):
    '''
    多进程导出所有领域的周定投-小提琴图
    '''
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fileds = get_fileds_en()
    for filed in fileds: # ["Bond"]
        res = pool.apply_async(export_aip_violin_plot_by_filed, args=(filed, ))
        results.append((filed, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res.get():
            successes.append(code)
        else:
            fails.append(code)

    logger.info(
        f"Export violin plot:{len(successes)} successful. fails:{fails}")

def build_full_matrix(fund_df):
    """
    在工作日配对矩阵基础上并入 daily(week=-1) 列，供 bootstrap CI 覆盖 6 个分组。
    """
    matrix = build_paired_matrix(fund_df)
    daily = fund_df[fund_df['week'] == -1] \
        .pivot_table(index='mark_day', values='profit_rate', aggfunc='first')
    if not daily.empty:
        matrix[-1] = daily
    return matrix.dropna()


def get_best(fund_df, bodies=None):
    """
    判定 best day：默认按配对显著性 + 多估值日稳健性（FR-2/FR-4）。
    配置 significance_test=False 时回退到旧的裸中位数最大值。
    :return: best day 在 bodies 中的下标（0~4；仅工作日组）
    """
    cfg = Config().backtest_config or {}

    if not cfg.get('significance_test', True):
        # 旧行为：周一~周五中位数最大者
        medians = [b.median() for b in bodies[:5]]
        return int(np.argmax(medians))

    matrix = build_paired_matrix(fund_df)
    if matrix.shape[0] < MIN_SCENARIOS or matrix.shape[1] < 5:
        return None
    stable_day, block_days = stability_verdict(matrix)
    return stable_day - 1 if stable_day is not None else None


def bootstrap_ci_table(fund_df, cycle):
    """
    满 N 情景的中位数 bootstrap 95% CI（长表，供绘图与 stats CSV 共用）。

    移动分块 bootstrap，块长 L = min(周期完整周数 N, max(1, n//4))：
    相邻估值日的买入窗口高度重叠（长周期 ≈99%），按时间块重采样才能
    诚实反映有效样本量；L=1 时退化为旧的 i.i.d. bootstrap。
    - excess 口径：5 个工作日超额组，另补一行 daily(group=-1) 恒为 0
      以保持 CSV schema 稳定；
    - absolute 口径：周一~周五 + daily 共 6 组。

    :return: DataFrame[group, median, ci_low, ci_high, metric]；
             样本不足或 bootstrap=False 时返回 None
    """
    cfg = Config().backtest_config or {}
    if not cfg.get('bootstrap', True):
        return None

    metric = get_plot_metric()
    matrix = (build_excess_matrix(fund_df) if metric == 'excess'
              else build_full_matrix(fund_df))
    if matrix.shape[0] < MIN_SCENARIOS:
        return None

    n_weeks = AutomaticInvestmentPlan.WeeksPerCycle[cycle]
    block_len = min(n_weeks, max(1, matrix.shape[0] // 4))
    ci = bootstrap_median_ci(matrix, block_len=block_len)

    if metric == 'excess':
        ci = pd.concat([ci, pd.DataFrame([{
            'group': -1, 'median': 0.0, 'ci_low': 0.0,
            'ci_high': 0.0}])], ignore_index=True)
    ci['metric'] = metric
    return ci


def get_ci(fund_df, cycle):
    """
    绘图用 bootstrap 95% CI（百分制）。
    :return: (groups, medians, ci_low, ci_high)，groups 形如 [1..5,-1]；
             excess 口径下调用方只取前 5 个（daily 恒为 0，画为基准线）；
             数据不足或关闭时返回 None
    """
    ci = bootstrap_ci_table(fund_df, cycle)
    if ci is None:
        return None
    order = [1, 2, 3, 4, 5, -1]
    ci = ci.set_index('group').reindex(order).dropna()
    groups = [int(g) for g in ci.index]
    return (groups, ci['median'].values * 100,
            ci['ci_low'].values * 100,
            ci['ci_high'].values * 100)


def export_filed_stats(filed, fund_list):
    """
    汇总该领域所有基金×周期（仅满 N 情景）的统计结果并导出 CSV：
    - pairwise：工作日配对 Wilcoxon（median_diff/p/p_adj/effect_size）
    - ci：中位数分块 bootstrap 95% CI（含 metric 列；bootstrap=False 时不导出）
    - stability：分时间块的 best day 与稳健结论
    满 N 情景 < MIN_SCENARIOS 的单元一律跳过。
    """
    from src.algorithm.significance import (
        pairwise_wilcoxon, best_day_by_block)

    pairwise_rows, ci_rows, stability_rows = [], [], []

    for fund in fund_list:
        fund_df_all = FundBacktest(fund.code).read_sql()
        # 与绘图一致：整只基金层面先近期窗口、再满 N 过滤
        fund_df_win = eligible_scenarios(recent_scenarios(fund_df_all))
        for cycle in AutomaticInvestmentPlan.InvestmentCycles:
            fund_df = fund_df_win[fund_df_win['cycle'] == cycle]
            matrix = build_paired_matrix(fund_df)
            if (matrix.shape[0] < MIN_SCENARIOS
                    or matrix.shape[1] < 5):
                continue

            # 配对检验（逐行减 daily 不改变工作日两两差值）
            pairs = pairwise_wilcoxon(matrix)
            pairs.insert(0, 'code', fund.code)
            pairs.insert(1, 'cycle', cycle)
            pairwise_rows.append(pairs)

            # 分块 bootstrap CI（excess 5 组 + daily 零行 / absolute 6 组）
            ci = bootstrap_ci_table(fund_df, cycle)
            if ci is not None:
                ci.insert(0, 'code', fund.code)
                ci.insert(1, 'cycle', cycle)
                ci_rows.append(ci)

            # 稳健性：分块 best day
            block_days = [day for _, day in
                          best_day_by_block(matrix)]
            stable_day, _ = stability_verdict(matrix)
            stability_rows.append(pd.DataFrame({
                'code': [fund.code], 'cycle': [cycle],
                'block_best_days': [str(block_days)],
                'stable_best_day': [stable_day],
            }))

    if pairwise_rows:
        pd.concat(pairwise_rows, ignore_index=True) \
            .to_csv(os.path.join(Config().export_stats_path,
                                 f'{filed}_pairwise.csv'), index=False)
        if ci_rows:
            pd.concat(ci_rows, ignore_index=True) \
                .to_csv(os.path.join(Config().export_stats_path,
                                     f'{filed}_ci.csv'), index=False)
        pd.concat(stability_rows, ignore_index=True) \
            .to_csv(os.path.join(Config().export_stats_path,
                                 f'{filed}_stability.csv'), index=False)
        logger.info(f"Export {filed} stats to {Config().export_stats_path}.")


def _draw_placeholder(ax, name, n_groups):
    """满 N 情景不足的子图：灰底占位 + 文字标注，不画小提琴。"""
    ax.set_facecolor('#f2f2f2')
    ax.set_xlim(0.5, n_groups + 0.5)
    ax.set_xticks(range(1, n_groups + 1))
    labels = [str(day) for day in range(1, 6)]
    if n_groups == 6:
        labels.append('daily')
    ax.set_xticklabels(labels)
    ax.text(0.5, 0.5, 'insufficient\nfull-window scenarios',
            transform=ax.transAxes, fontsize=11,
            horizontalalignment='center', verticalalignment='center',
            color='gray')
    ax.set_xlabel(name)
    # 占位轴无数值口径，隐藏纵轴刻度，避免与同行正常子图混淆
    ax.set_yticks([])
    ax.yaxis.grid(False)


def export_aip_violin_plot_by_filed(filed, show=False):
    '''
    导出指定领域的周定投-小提琴图，「主要是用这个函数绘图」。
    默认 excess 口径：每把小提琴是「同一估值日 C 下该工作日收益 − daily 收益」
    的配对超额分布，y=0 灰虚线即 daily 基准；absolute 口径为原始盯市收益率。
    满 N 完整周情景 < MIN_SCENARIOS 的子图灰显占位。
    '''
    try:
        fund_list = FundsForBacktestTable.get_by_filed(filed)
        df_dict = [] # [[code, name, fund_df, cycle], ]

        if len(fund_list) == 0:
            logger.info(f"filed: {filed} dont have any fund.")
            return True

        metric = get_plot_metric()
        is_excess = metric == 'excess'
        n_groups = 5 if is_excess else 6
        xticklabels = [str(day) for day in range(1, 6)]
        if not is_excess:
            xticklabels.append('daily')
        y_label = ('Excess vs daily / %' if is_excess
                   else 'Profit Rate / %')

        for fund in fund_list:
            fund_df_all = FundBacktest(fund.code).read_sql()
            # 近期窗口在整只基金层面过滤，保证各周期共用同一批估值日与锚点
            fund_df_win = eligible_scenarios(recent_scenarios(fund_df_all))
            for cycle in AutomaticInvestmentPlan.InvestmentCycles:
                fund_df = fund_df_win.loc[fund_df_win['cycle'] == cycle]
                df_dict.append([f'{fund.code}', f'定投{cycle}天',
                                fund_df, cycle])
                logger.debug(f"Loaded {fund.name}-{cycle} to df_dict.")

        df_cnt = len(df_dict)
        cols = len(AutomaticInvestmentPlan.InvestmentCycles)
        rows = math.ceil(df_cnt/cols)

        # 当 rows != 1 时，axs 为二维数组[rows][cols]
        # 但 rows == 1 时，axs 为一维数组[cols]
        # 因此当只有一个基金的时候，会导致 axs 不一致，故扩充一行
        nrows = rows if rows != 1 else 2
        ncols = cols
        fig, axs = plt.subplots(nrows=nrows,
                                ncols=ncols,
                                figsize=(20, 5*rows),  # Width, height
                                )
        plt.subplots_adjust(wspace=0.3, hspace=0.35, top=0.93)
        metric_desc = ('excess vs daily (weekday − daily)' if is_excess
                       else 'absolute mark-to-market profit rate')
        fig.suptitle(f"{filed} {DateTools.today()}  "
                     f"[{metric_desc}; {window_desc()}; full-N-week scenarios; "
                     f"fund: totvalue nav / etf: adjusted close]",
                     fontsize=20)

        i = 0
        # None 表示占位子图，不参与同行纵坐标范围统一
        low_high = [[None for _ in range(cols)] for _ in range(rows)]
        for _, name, fund_df, cycle in df_dict:
            ax = axs[i // cols][i % cols]
            # 短周期（30/60 天）每组仅 4~8 笔扣款，噪声大，加注提示
            short_cycle = cycle in (30, 60)

            # 满 N 配对情景不足：灰显占位并跳过所有统计元素
            if build_paired_matrix(fund_df).shape[0] < MIN_SCENARIOS:
                _draw_placeholder(ax, name, n_groups)
                i += 1
                continue

            # 这里 *100 变为百分比
            if is_excess:
                excess = build_excess_matrix(fund_df)
                bodies = [excess[day] * 100 for day in range(1, 6)]
            else:
                bodies = [fund_df.loc[fund_df['week'] == day]
                          ['profit_rate'] * 100 for day in range(1, 6)]
                # 每天，-1是特殊标记
                bodies.append(
                    fund_df.loc[fund_df['week'] == -1]
                    ['profit_rate'] * 100)

            best_day_idx = get_best(fund_df, bodies)

            low = min(float(s.min()) for s in bodies)
            high = max(float(s.max()) for s in bodies)
            low_high[i // cols][i % cols] = (low, high)

            violin_plot = ax.violinplot(
                bodies,
                showmeans=False,  # 均值
                showmedians=True,  # 中位数
                showextrema=True,  # 极值线（最大值/最小值处短刻度）
                # 显示 25%/75% 分位
                quantiles=[[0.25, 0.75] for _ in range(n_groups)]
                )

            if not is_excess:
                # absolute 口径：每天定投的小提琴染金色
                violin_plot['bodies'][5].set_facecolor('gold')
                violin_plot['bodies'][5].set_edgecolor('orange')
            else:
                # excess 口径：y=0 灰虚线即 daily 基准
                ax.axhline(0, color='gray', linestyle='--',
                           linewidth=1.0, zorder=1)

            # 设置best day的颜色；不显著或不稳健则不标红并加注
            if best_day_idx is not None:
                violin_plot['bodies'][best_day_idx].set_facecolor('red')
                violin_plot['bodies'][best_day_idx].set_edgecolor('orange')
            else:
                ax.text(0.02, 0.98, 'no significant\nweekday effect',
                        transform=ax.transAxes, fontsize=9,
                        verticalalignment='top', color='gray')

            # 短周期噪声提示（右下角）
            if short_cycle:
                ax.text(0.98, 0.02, 'few buys\nhigh noise',
                        transform=ax.transAxes, fontsize=9,
                        verticalalignment='bottom',
                        horizontalalignment='right',
                        color='darkorange')

            # 分块 bootstrap 中位数 95% CI 误差线（黑色）；
            # excess 口径仅 5 个工作日（daily 恒为 0，以基准线表示）
            ci_result = get_ci(fund_df, cycle)
            if ci_result is not None:
                groups, medians, ci_low, ci_high = ci_result
                ci_n = min(n_groups, len(groups))
                medians, ci_low, ci_high = (medians[:ci_n],
                                            ci_low[:ci_n],
                                            ci_high[:ci_n])
                x_pos = np.arange(1, ci_n + 1)
                ax.errorbar(x_pos, medians,
                            yerr=[medians - ci_low, ci_high - medians],
                            fmt='none', ecolor='black', capsize=3,
                            elinewidth=1.2, zorder=5)

            ax.set_xlabel(name)
            i += 1

        # 同一行（同一 ETF 的不同周期）统一绝对纵坐标范围，便于横向对比；
        # 刻度间隔按范围动态选择（支持 0.1~100 的档位），每图约 8~12 个刻度；
        # 占位子图不参与范围计算
        nice_steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100]
        for r in range(rows):
            valid = [low_high[r][c] for c in range(cols)
                     if low_high[r][c] is not None]
            if not valid:
                continue
            row_low = min(v[0] for v in valid)
            row_high = max(v[1] for v in valid)

            span = row_high - row_low
            target_ticks = 10
            interval = next((s for s in nice_steps
                             if span / s <= target_ticks), nice_steps[-1])

            # 用整间隔对齐边界，使同一行各子图刻度完全一致
            y_min = math.floor(row_low / interval) * interval
            y_max = math.ceil(row_high / interval) * interval

            ticks = np.arange(y_min, y_max + interval / 2, interval)
            for c in range(cols):
                if low_high[r][c] is not None:
                    axs[r][c].set_yticks(ticks)
                    axs[r][c].set_ylim(y_min, y_max)

        # 网格、标题与统一 x 轴刻度（行 r 即第 r 只基金）
        for r in range(rows):
            for c in range(cols):
                ax = axs[r][c]
                ax.yaxis.grid(True)
                ax.set_xticks(range(1, n_groups + 1))
                ax.set_xticklabels(xticklabels)
                if c == 0:
                    ax.set_title(f"{fund_list[r].name}")
                    ax.set_ylabel(y_label)
                if c == 1:
                    ax.set_title(f"{fund_list[r].code}")

        if show:
            plt.show()
        else:
            plt.savefig(os.path.join(
                Config().export_aip_plot_path, f'{filed}.png'))
            logger.info(f"Successfully exported {filed} aip violin plot.")
            if Config().backtest_config is None or \
                    Config().backtest_config.get('export_stats', True):
                export_filed_stats(filed, fund_list)
        return True

    except Exception as error:
        logger.error(f"Export aip violin plot by filed failed, error:{error}.")
        return False


def show_diff_box_plot(df_dict, figsize=(20, 7), notch=True, vert=True):
    '''
    一次可以看多个基金的周定投-箱型图，适合不同领域基金之间比较

    :param df_dict: 基金字典    dict  {'LanChou':df_005827, 'GuoTaiChe':df_001790, 'ZhongOuYiliao':df_003095}
    :param figsize: 画布大小    tuple (20, 7)
    :param notch:   是否为凹口型 bool  True
    :param vert:    是否垂直放置 bool  True
    '''

    funds_cnt = len(df_dict)
    ax_list = [None for _ in range(funds_cnt)]
    plot_list = []
    labels = [f"week {day}" for day in range(1, 6)]

    fig, ax_list = plt.subplots(nrows=1, ncols=funds_cnt, figsize=figsize)

    i = 0
    for fund, fund_df in df_dict.items():
        # 每周一个box
        boxes = [fund_df.loc[fund_df['week'] == day]['profit_rate']
                 for day in range(1, 6)]

        box_plot = ax_list[i].boxplot(boxes,
                                      notch=notch,  # notch shape
                                      vert=vert,  # vertical box alignment
                                      patch_artist=True,  # fill with color
                                      labels=labels)  # will be used to label x-ticks
        ax_list[i].set_title(fund)
        plot_list.append(box_plot)
        i += 1

    # fill with colors
    colors = ['lightsalmon', 'lightyellow',
              'lightgreen', 'lightblue', 'lightpink']
    for box_plot in plot_list:
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)

    # adding horizontal grid lines
    for ax in ax_list:
        ax.yaxis.grid(True)
        ax.set_ylabel('Profit Rate / %')

    plt.show()


def show_one_box_plot(df_dict, figsize=(20, 10), notch=True, vert=True):
    '''
    适合同一领域基金放在一起比较,最多支持5个基金比较

    :param df_dict: 基金字典    dict  {'ZhaoShang':df_161725, 'HuaPeng':df_160632}
    :param figsize: 画布大小    tuple (20, 10)
    :param notch:   是否为凹口型 bool  True
    :param vert:    是否垂直放置 bool  True
    '''

    funds_cnt = len(df_dict)
    boxes_list = []
    labels = ['' for _ in range(5 * funds_cnt)]
    i = 1
    for key in df_dict:
        labels[i*5-3] = key
        i += 1

    # 因为要画水平线，就只能用子图
    fig, (ax) = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    for fund, fund_df in df_dict.items():
        boxes_list.extend([fund_df.loc[fund_df['week'] == day]
                          ['profit_rate'] for day in range(1, 6)])

    box_plot = ax.boxplot(boxes_list,
                          notch=notch,  # notch shape
                          vert=vert,  # vertical box alignment
                          patch_artist=True,  # fill with color
                          labels=labels)  # will be used to label x-ticks

    ax.set_title("Automatic Investment Plan")

    # box 上色，每个基金一种颜色
    colors = ['lightsalmon', 'lightyellow',
              'lightgreen', 'lightblue', 'lightpink']
    for i in range(funds_cnt):
        for patch, color in zip(box_plot['boxes'][i*5:i*5+5], [colors[i]]*5):
            patch.set_facecolor(color)

    # adding horizontal grid lines
    ax.yaxis.grid(True)
    ax.set_ylabel('Profit Rate / %')

    plt.show()


def show_diff_violin_plot(df_dict, figsize=(20, 7)):
    '''
    一次可以看多个基金的周定投-小提琴图

    :param df_dict: 基金字典    dict  {'LanChou':df_005827, 'GuoTaiChe':df_001790, 'ZhongOuYiliao':df_003095}
    :param figsize: 画布大小    tuple (20, 7)
    '''

    funds_cnt = len(df_dict)
    ax_list = [None for _ in range(funds_cnt)]
    plot_list = []
    labels = [f"week {day}" for day in range(1, 6)]

    fig, ax_list = plt.subplots(nrows=1, ncols=funds_cnt, figsize=figsize)

    i = 0
    for fund, fund_df in df_dict.items():
        # 每周一个box
        bodies = [fund_df.loc[fund_df['week'] == day]['profit_rate']
                  for day in range(1, 6)]

        violin_plot = ax_list[i].violinplot(bodies,
                                            showmeans=False,  # 均值
                                            showmedians=True,  # 中位数
                                            showextrema=True,  # 极值
                                            )
        ax_list[i].set_title(fund)
        plot_list.append(violin_plot)
        i += 1

    # adding horizontal grid lines
    for i, ax in enumerate(ax_list):
        ax.yaxis.grid(True)
        ax.set_xticks([i+1 for i in range(5)])
        ax.set_ylabel('Profit Rate / %')

    # add x-tick labels
    plt.setp(ax_list, xticks=[i+1 for i in range(5)],
             xticklabels=labels)

    plt.show()
