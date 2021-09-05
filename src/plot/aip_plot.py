import os
import math
import pandas as pd
import matplotlib.pyplot as plt
import multiprocessing

from chicken_farm.src.module.aip_mod import AutomaticInvestmentPlan
from chicken_farm.src.db.tbl_depository import DepositoryTable
from chicken_farm.src.db.db_backtest import FundBacktest
from chicken_farm.src.db.types import Filed
from chicken_farm.src.util.tools import DateTools
from chicken_farm.src.util.config import Config
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS'] # 显示中文
plt.rcParams['figure.dpi'] = 300  # 显示分辨率
plt.rcParams['savefig.dpi'] = 300  # 保存图片分辨率
 

def export_violin_plot(cpus=8):
    '''
    导出所有领域的周定投-小提琴图
    '''

    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fileds = Filed().get_fileds()
    for filed in fileds:
        if filed == Filed.MILITARY:
            continue
        res = pool.apply_async(export_aip_violin_plot_by_filed, args=(filed, ))
        results.append((filed, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res:
            successes.append(code)
        else:
            fails.append(code)

    logger.info(f"Export violin plot:{len(successes)} successful. fails:{fails}")


def export_aip_violin_plot_by_filed(filed, show=False):
    '''
    导出指定领域的周定投-小提琴图
    '''
    try:
        fund_list = DepositoryTable.get_holding_by_filed(filed)
        df_dict = {}

        for fund in fund_list:
            for cycle in AutomaticInvestmentPlan.InvestmentCycles:
                df = FundBacktest(fund.code).read_sql()
                df_dict[f'{fund.name}-{cycle}天'] = df.loc[df['cycle'] == cycle]
                logger.debug(f"Loaded {fund.name}-{cycle} to df_dict.")

        df_cnt = len(df_dict)
        rows = math.ceil(df_cnt/3)
        cols = 3
        
        fig, axs = plt.subplots(nrows=rows, 
                                ncols=cols, 
                                figsize=(10, 5*rows),# Width, height
                                ) 
        plt.subplots_adjust(wspace=0.3, hspace=0.3)
        fig.suptitle(f"{filed} {DateTools.today()}",
                     fontsize=30)
        
        i = 0
        for fund, fund_df in df_dict.items():
            # 这里 *100 变为百分比
            bodies = [fund_df.loc[fund_df['week'] == day]['profit_rate']*100 for day in range(1, 6)]
            
            violin_plot = axs[math.floor(i/cols)][i%cols].violinplot(bodies,
                                                showmeans=False, # 均值
                                                showmedians=True, # 中位数
                                                showextrema=True,  # 极值
                                               ) 
            axs[math.floor(i/cols)][i%cols].set_title(fund)
            i += 1
            
        # adding horizontal grid lines
        for r in range(rows):
            for c in range(cols):
                axs[r][c].yaxis.grid(True)
                axs[r][c].set_xticks([i+1 for i in range(5)])
                if c == 0:
                    axs[r][c].set_ylabel('Profit Rate / %')
                

        # add x-tick labels
        labels = [f"week {day}" for day in range(1, 6)]
        plt.setp(axs, xticks=[i+1 for i in range(5)],
                 xticklabels=labels)
        
        if show:
            plt.show()
        else:
            plt.savefig(os.path.join(Config().export_aip_plot_path, f'{filed}.png'))
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
        boxes = [fund_df.loc[fund_df['week'] == day]['profit_rate'] for day in range(1, 6)]
        
        box_plot = ax_list[i].boxplot(boxes,
                                      notch=notch,  # notch shape
                                      vert=vert,  # vertical box alignment
                                      patch_artist=True,  # fill with color
                                      labels=labels)  # will be used to label x-ticks
        ax_list[i].set_title(fund)
        plot_list.append(box_plot)
        i += 1
        
    # fill with colors
    colors = ['lightsalmon', 'lightyellow', 'lightgreen', 'lightblue', 'lightpink']
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
        boxes_list.extend([fund_df.loc[fund_df['week'] == day]['profit_rate'] for day in range(1, 6)])
    
    box_plot = ax.boxplot(boxes_list,
                          notch=notch,  # notch shape
                          vert=vert,  # vertical box alignment
                          patch_artist=True,  # fill with color
                          labels=labels)  # will be used to label x-ticks
    
    ax.set_title("Automatic Investment Plan")
    
    
    # box 上色，每个基金一种颜色
    colors = ['lightsalmon', 'lightyellow', 'lightgreen', 'lightblue', 'lightpink']
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
        bodies = [fund_df.loc[fund_df['week'] == day]['profit_rate'] for day in range(1, 6)]
        
        violin_plot = ax_list[i].violinplot(bodies,
                                            showmeans=False, # 均值
                                            showmedians=True, # 中位数
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







