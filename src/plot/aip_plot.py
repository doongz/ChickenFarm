import os
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import multiprocessing

from src.module.backtest_mod import AutomaticInvestmentPlan
from ChickenFarm.src.algorithm.significance import build_paired_matrix, \
    bootstrap_median_ci, stability_verdict
from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from ChickenFarm.src.db.db_backtest import FundBacktest
from ChickenFarm.src.util.industry_class import get_fileds_en
from ChickenFarm.src.util.tools import DateTools
from ChickenFarm.src.util.config import Config
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


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


def get_best(fund_df):
    """
    判定 best day（FR-2）并叠加多估值日稳健性（FR-4）：
    将情景按时间分 4 块逐块检验，仅当同一工作日在 ≥60% 块中都显著最优才标红。
    :return: best day 在 bodies 中的下标（0~4），不显著或不稳健时返回 None
    """
    matrix = build_paired_matrix(fund_df)
    if matrix.shape[0] < 8 or matrix.shape[1] < 5:
        return None
    stable_day, block_days = stability_verdict(matrix)
    return stable_day - 1 if stable_day is not None else None


def get_ci(fund_df):
    """
    对 6 个分组的中位数做 bootstrap 95% 置信区间（FR-3），返回按 bodies 顺序的数组。
    :return: (median[6], ci_low[6], ci_high[6])，数据不足时返回 None
    """
    matrix = build_full_matrix(fund_df)
    if matrix.shape[0] < 8:
        return None
    ci = bootstrap_median_ci(matrix)
    # group 列按工作日 1..5 与 -1 排序；重排为 bodies 顺序（1..5, -1）
    order = [1, 2, 3, 4, 5, -1]
    ci = ci.set_index('group').reindex(order)
    return (ci['median'].values * 100,
            ci['ci_low'].values * 100,
            ci['ci_high'].values * 100)

def export_aip_violin_plot_by_filed(filed, show=False):
    '''
    导出指定领域的周定投-小提琴图，「主要是用这个函数绘图」
    '''
    try:
        fund_list = FundsForBacktestTable.get_by_filed(filed)
        df_dict = [] # [[code, name, fund_df], ]

        if len(fund_list) == 0:
            logger.info(f"filed: {filed} dont have any fund.")
            return True

        for fund in fund_list:
            for cycle in AutomaticInvestmentPlan.InvestmentCycles:
                df = FundBacktest(fund.code).read_sql()
                df_dict.append([f'{fund.code}', f'定投{cycle}天', df.loc[df['cycle'] == cycle]])
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
        plt.subplots_adjust(wspace=0.3, hspace=0.3)
        fig.suptitle(f"{filed} {DateTools.today()}",
                     fontsize=30)

        i = 0
        low_high = [[(0,0) for _ in range(cols) ] for _ in range(rows)]
        for _, name, fund_df in df_dict:
            # 这里 *100 变为百分比
            bodies = [fund_df.loc[fund_df['week'] == day]
                      ['profit_rate']*100 for day in range(1, 6)] # 5天
            bodies.append(fund_df.loc[fund_df['week'] == -1]['profit_rate']*100) # 每天，-1是特殊标记

            best_day_idx = get_best(fund_df)

            low = float("inf")
            high = float("-inf")
            for i_i in range(6): # 5天+每天
                low = min(low, bodies[i_i].min())
                high = max(high, bodies[i_i].max())
            low_high[i//cols][i%cols] = (low, high)
            
            ax = axs[math.floor(i/cols)][i % cols]
            violin_plot = ax.violinplot(bodies,
                                        showmeans=False,  # 均值
                                        showmedians=True,  # 中位数
                                        showextrema=True,  # 是否显示极值线（小提琴顶部 / 底部的短刻度，对应数据的最大值 / 最小值）
                                        quantiles=[[0.25, 0.75] for _ in range(5+1)] # 显示 25%/75% 分位
                                        )

            # 设置每天定投的颜色
            violin_plot['bodies'][5].set_facecolor('gold')      # 填充色
            violin_plot['bodies'][5].set_edgecolor('orange')    # 边框色

            # 设置best day的颜色；不显著或不稳健则不标红并加注
            if best_day_idx is not None:
                violin_plot['bodies'][best_day_idx].set_facecolor('red')    # 填充色
                violin_plot['bodies'][best_day_idx].set_edgecolor('orange') # 边框色
            else:
                ax.text(0.02, 0.98, 'no significant\nweekday effect',
                        transform=ax.transAxes, fontsize=9,
                        verticalalignment='top', color='gray')

            # bootstrap 中位数 95% CI 误差线（黑色，覆盖 6 个分组）
            ci_result = get_ci(fund_df)
            if ci_result is not None:
                medians, ci_low, ci_high = ci_result
                x_pos = np.arange(1, 7)
                ax.errorbar(x_pos, medians,
                            yerr=[medians - ci_low, ci_high - medians],
                            fmt='none', ecolor='black', capsize=3,
                            elinewidth=1.2, zorder=5)

            ax.set_xlabel(name)
            i += 1

        # 为每个子图添加y坐标最大最小值和间隔
        interval = 2
        for r in range(rows):
            max_range = 0 # 找到每一行的最大跨度
            for c in range(cols):
                low = low_high[r][c][0]
                high = low_high[r][c][1]
                max_range = max(max_range, high-low)
            for c in range(cols):
                low = low_high[r][c][0]
                high = low_high[r][c][1]
                d = (max_range - (high - low)) / 2
                ytick_low = low - d
                ytick_high = high + d
                axs[r][c].set_yticks(np.arange(ytick_low, ytick_high + 1, interval))

        # 为每个子图添加水平线
        idx = 0
        for r in range(rows):
            for c in range(cols):
                axs[r][c].yaxis.grid(True)
                axs[r][c].set_xticks([i+1 for i in range(5)])
                if c == 0:
                    axs[r][c].set_title(f"{fund_list[idx].name}")
                    axs[r][c].set_ylabel(f"Profit Rate / %")
                if c == 1:
                    axs[r][c].set_title(f"{fund_list[idx].code}")
                    idx += 1

        # add x-tick labels
        labels = [f"{day}" for day in range(1, 6)]
        labels.append("daily")
        plt.setp(axs, xticks=[i+1 for i in range(6)],
                 xticklabels=labels)

        if show:
            plt.show()
        else:
            plt.savefig(os.path.join(
                Config().export_aip_plot_path, f'{filed}.png'))
            logger.info(f"Successfully exported {filed} aip violin plot.")
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
