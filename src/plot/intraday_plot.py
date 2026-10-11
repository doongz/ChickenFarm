"""
ETF 日内择时绘图与 stats 导出（spec FR-8）。

按领域出图：每只库内 ETF 一行、每个分析窗口一列。子图横轴为盘中时刻，
纵轴为该时刻买入价相对当日 VWAP 的偏离（bps，负=便宜），画出跨日中位数
曲线与 bootstrap 95% 置信带，y=0 灰虚线为 VWAP 基准；显著且稳健的候选
最佳时刻红点标注（RECOMMENDED），显著但不稳定 / 无显著效应分别加注；
完整交易日不足 MIN_SESSIONS 的窗口画灰底占位子图。

本模块只读取 SQLite 分钟库并出图，不联网。中文字体初始化直接复用
aip_plot._setup_chinese_font，避免重复维护候选字体清单。
"""
import os
import multiprocessing

import numpy as np
import pandas as pd
# 先完成 matplotlib 中文字体/分辨率配置，再引入 pyplot
import matplotlib

from src.plot.aip_plot import _setup_chinese_font

_setup_chinese_font()
# 负号正常显示（_setup_chinese_font 已设置，这里显式声明口径）
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt

from src.algorithm.intraday_timing import analyze_etf_minute
from src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.util.industry_class import get_fileds_en
from src.util.tools import FundTypeTools
from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)

# 完整交易日不足该数量时子图灰底占位（与 intraday_timing.MIN_SESSIONS 同语义）
MIN_SESSIONS = 8


def _draw_insufficient(ax, window, n_days):
    """完整交易日不足的占位子图：灰底 + 居中提示，不画曲线。"""
    ax.set_facecolor('#f2f2f2')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.5, 'insufficient full-session days',
            transform=ax.transAxes, fontsize=11,
            horizontalalignment='center', verticalalignment='center',
            color='gray')
    ax.set_title(f'W{window} n={n_days}')


def _draw_window(ax, result, name, code, unadjusted):
    """
    画一个有效（非占位）窗口子图：median 曲线 + CI 带 + VWAP 基准线，
    并按 recommended / 显著不稳定 / 不显著给出结论标注。

    :return: (low, high)——该子图 median/ci 的全局范围，供同行统一纵轴
    """
    window = result['window']
    n_days = result['n_days']
    times = result['times']
    x = list(times.index)
    median = times['median'].astype(float)
    ci_low = times['ci_low'].astype(float)
    ci_high = times['ci_high'].astype(float)

    # bootstrap 中位数 95% 置信带（半透明蓝）
    ax.fill_between(np.arange(len(x)), ci_low.values, ci_high.values,
                    color='tab:blue', alpha=0.18, zorder=2)
    # 跨日中位数超额曲线
    ax.plot(np.arange(len(x)), median.values, color='tab:blue',
            linewidth=1.4, zorder=3)
    # y=0：当日 VWAP 基准
    ax.axhline(0, color='gray', linestyle='--', linewidth=1.0, zorder=1)

    # 横轴时刻很多，只稀疏显示刻度并旋转
    step = max(1, len(x) // 12)
    tick_pos = list(range(0, len(x), step))
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([x[i] for i in tick_pos], rotation=45,
                       ha='right', fontsize=8)

    p_value = result.get('p_value', np.nan)
    significant = bool(np.isfinite(p_value) and p_value < 0.05)
    recommended = bool(result.get('recommended', False))
    stable = bool(result.get('stable', False))

    title = f'{name}({code}) W{window} n={n_days}'
    if unadjusted:
        title += ' (unadjusted)'

    if recommended:
        # 推荐买入时刻：红点高亮 + 注释，标题加 RECOMMENDED
        best_time = result['best_time']
        best_median = result['best_median']
        best_idx = x.index(best_time)
        ax.scatter([best_idx], [best_median], color='red', s=40,
                   zorder=5)
        ax.annotate(f'{best_time}\n{best_median:.1f} bps',
                    xy=(best_idx, best_median),
                    xytext=(best_idx + len(x) * 0.03, best_median),
                    textcoords='data', fontsize=9, color='red',
                    verticalalignment='center',
                    arrowprops=dict(arrowstyle='->', color='red',
                                    lw=0.8))
        title += ' RECOMMENDED'
    elif significant and not stable:
        # 显著但分块不稳定：不给推荐，橙色提示
        ax.text(0.02, 0.98, 'significant but unstable',
                transform=ax.transAxes, fontsize=9,
                verticalalignment='top', color='darkorange')
    else:
        # 其余情况：无显著盘中择时效应
        ax.text(0.02, 0.98, 'no significant intraday timing effect',
                transform=ax.transAxes, fontsize=9,
                verticalalignment='top', color='gray')

    ax.set_title(title, fontsize=10)
    ax.set_ylabel('excess vs VWAP (bps)', fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)

    low = float(np.nanmin([ci_low.min(), median.min()]))
    high = float(np.nanmax([ci_high.max(), median.max()]))
    return low, high


def export_intraday_plot_by_filed(filed, show=False):
    '''
    导出指定领域的 ETF 日内买入时刻图（每只 ETF 一行 × 每个窗口一列），
    并在开启 export_stats 时汇总导出时刻级 stats CSV。

    无分钟数据的 ETF 直接跳过（不占图行、不进 stats）；领域内没有任何
    有数据的 ETF 时返回 False。

    :return: True 正常出图；False 该领域无可用数据/导出异常
    '''
    try:
        funds = FundsForBacktestTable.get_by_filed(filed)
        etfs = [fund for fund in funds
                if FundTypeTools.classify(fund.code) == 'etf']

        # 逐只分析，仅保留有分钟数据的结果
        analyzed = []
        for fund in etfs:
            result = analyze_etf_minute(fund.code)
            if result is None:
                logger.info('%s 无分钟数据，跳过日内择时出图', fund.code)
                continue
            analyzed.append((fund, result))

        if not analyzed:
            logger.info('领域 %s 没有任何有分钟数据的 ETF，跳过日内择时出图',
                        filed)
            return False

        # 窗口列取第一只有效标的的结果顺序（即配置的 INTRADAY_WINDOWS 升序）
        windows = [r['window'] for r in analyzed[0][1]['results']]
        ncols = len(windows)
        nrows = len(analyzed)

        fig, axs = plt.subplots(nrows=nrows, ncols=ncols,
                                figsize=(5.2 * ncols, 3.6 * nrows),
                                squeeze=False)

        # row_ranges[i] = (low, high)：该行所有非占位窗口的全局范围
        # placeholder[i][j] 标记灰底占位子图（不参与纵轴范围统一）
        row_ranges = []
        placeholder = [[False] * ncols for _ in range(nrows)]
        for i, (fund, data) in enumerate(analyzed):
            unadjusted = bool(data.get('unadjusted', False))
            results_by_window = {r['window']: r for r in data['results']}
            row_low, row_high = None, None

            for j, w in enumerate(windows):
                ax = axs[i][j]
                result = results_by_window.get(w)
                # 不足最小样本（算法层已标 insufficient，这里再按
                # MIN_SESSIONS 兜底，复用框架最小情景语义）
                if result is None or result.get('insufficient', False) or \
                        result.get('n_days', 0) < MIN_SESSIONS:
                    n_days = result.get('n_days', 0) if result else 0
                    _draw_insufficient(ax, w, n_days)
                    placeholder[i][j] = True
                    continue
                low, high = _draw_window(ax, result, fund.name, fund.code,
                                         unadjusted)
                row_low = low if row_low is None else min(row_low, low)
                row_high = high if row_high is None else max(row_high, high)

            row_ranges.append((row_low, row_high))

        # 同一行（同一 ETF）纵轴范围统一，留 8% margin；占位子图不处理
        for i, (row_low, row_high) in enumerate(row_ranges):
            if row_low is None:
                continue
            span = row_high - row_low
            if span <= 0:
                span = 1.0
            margin = span * 0.08
            y_min, y_max = row_low - margin, row_high + margin
            for j in range(ncols):
                if not placeholder[i][j]:
                    axs[i][j].set_ylim(y_min, y_max)

        fig.suptitle(f'{filed} ETF 日内买入时刻（相对当日 VWAP 偏离, bps）',
                     y=0.999, fontsize=14)
        plt.tight_layout()

        if show:
            plt.show()
        else:
            plot_path = os.path.join(Config().export_aip_plot_path,
                                     f'intraday_{filed}.png')
            plt.savefig(plot_path, dpi=matplotlib.rcParams['savefig.dpi'],
                        bbox_inches='tight')
            logger.info('Successfully exported %s intraday plot: %s',
                        filed, plot_path)
            plt.close(fig)

            if Config().backtest_config is None or \
                    Config().backtest_config.get('export_stats', True):
                _export_filed_stats(filed, analyzed)

        return True

    except Exception as error:
        logger.error('Export intraday plot by filed %s failed, error:%s.',
                     filed, error)
        return False


def _export_filed_stats(filed, analyzed):
    """
    汇总该领域所有 ETF × 所有【非占位】窗口的时刻级统计表并导出 CSV。
    每行一个时刻，前面拼接标的级（code/name/price_field/unadjusted）与
    窗口级（window/n_days/best_time/.../recommended）字段。
    """
    frames = []
    for fund, data in analyzed:
        for result in data['results']:
            # 与绘图一致：占位/不足最小样本的窗口不进 stats
            if result.get('insufficient', False) or \
                    result.get('n_days', 0) < MIN_SESSIONS:
                continue
            times = result['times'].reset_index(names='time')
            n = len(times)
            # times 内的 p_value/effect_size 仅 best_time 行有值，窗口级
            # 常量列（下方 meta）已携带同一结果，这里去掉避免同名列冲突
            times = times.drop(columns=['p_value', 'effect_size'])
            # 标的级/窗口级字段为常量列，用独立 DataFrame 横向拼接
            meta = pd.DataFrame({
                'code': [fund.code] * n,
                'name': [fund.name] * n,
                'window': [result['window']] * n,
                'price_field': [data.get('price_field')] * n,
                'unadjusted': [bool(data.get('unadjusted', False))] * n,
                'n_days': [result['n_days']] * n,
                'best_time': [result['best_time']] * n,
                'best_median': [result['best_median']] * n,
                'p_value': [result['p_value']] * n,
                'effect_size': [result['effect_size']] * n,
                'stable': [bool(result['stable'])] * n,
                'recommended': [bool(result['recommended'])] * n,
            })
            frames.append(pd.concat([meta, times], axis=1))

    if not frames:
        logger.info('领域 %s 无有效日内窗口，不导出 stats CSV', filed)
        return

    stats_path = os.path.join(Config().export_stats_path,
                              f'{filed}_intraday.csv')
    pd.concat(frames, ignore_index=True).to_csv(
        stats_path, index=False, encoding='utf-8-sig')
    logger.info('Export %s intraday stats to %s', filed, stats_path)


def export_intraday_plot_multiprocess(cpus=4):
    '''
    多进程导出所有领域的 ETF 日内择时图（只读取 SQLite + 画图，不联网）。
    与周定投小提琴图一致按领域分进程；worker 内异常被 get() 捕获记入
    fails，不中断整轮。

    :return: (successes, fails) 领域英文名列表
    '''
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fileds = get_fileds_en()
    for filed in fileds:
        res = pool.apply_async(export_intraday_plot_by_filed,
                               args=(filed,))
        results.append((filed, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for filed, res in results:
        try:
            if res.get():
                successes.append(filed)
            else:
                fails.append(filed)
        except Exception as error:
            logger.error('领域 %s 日内择时出图进程失败：%s', filed, error)
            fails.append(filed)

    logger.info('Export intraday plot:%s successful. fails:%s',
                len(successes), fails)
    return successes, fails
