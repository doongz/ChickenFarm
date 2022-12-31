import os
import numpy as np
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters

from ChickenFarm.src.module.statistics_mod import get_fileds_position, get_fileds_profit
from src.util.types import get_fileds_color, get_fileds_en, get_fileds_cn
from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.util.tools import DateTools
from ChickenFarm.src.util.config import Config
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)
config = Config()
register_matplotlib_converters()


FIGSIZE = (10, 5)
COLORS = ['limegreen', 'dodgerblue', 'mediumorchid', 'lightskyblue',
          'silver', 'gold', 'coral', 'orange', 'royalblue', 'slategray']


def export_position_bar_chart(show=False):
    # 导出当前每个领域持仓的柱状图

    data = get_fileds_position()
    lables = get_fileds_cn()
    color = get_fileds_color()

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=FIGSIZE)
    bar_plot = ax.bar(x=lables,
                      height=data,
                      width=0.5,
                      color=color)

    ax.set_title(f"各领域最新持仓 {DateTools.today()}")
    ax.set_ylabel('数额')
    ax.yaxis.grid(True)

    # 显示在图形上的值
    for a, b in zip(lables, data):
        plt.text(a, b+100, b, ha='center', va='bottom')

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(
            config.export_chart_path, 'position_bar_chart.png'))
        logger.info(f"Successfully exported position bar chart.")


def export_profit_bar_chart(show=False):
    # 导出当前每个领域收益的柱状图
    labels = get_fileds_cn()
    data = get_fileds_profit()
    colors = get_fileds_color()

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=FIGSIZE)
    bar_plot = ax.barh(y=labels,
                       width=data,
                       height=0.7,
                       color=colors)
    ax.set_title(f"各领域最新收益 {DateTools.today()}")
    ax.xaxis.grid(True)

    for a, b in zip(labels, data):
        plt.text(b, a, b, ha='center', va='center')

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(
            config.export_chart_path, 'profit_bar_chart.png'))
        logger.info(f"Successfully exported profit bar chart.")


def export_position_profit_bar_chart(show=False):
    # 导出当前每个领域持仓和收益的柱状图
    position_data = get_fileds_position()
    profit_data = get_fileds_profit()
    label = get_fileds_cn()

    x = np.arange(len(label))
    total_width, n = 0.8, 2    # 有多少个类型，只需更改n即可
    width = total_width / n
    x = x - (total_width - width) / 2

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=FIGSIZE)
    ax.bar(x - width/2, position_data, width, label='持仓', color='skyblue')
    ax.bar(x + width/2, profit_data, width, label='收益', color='gold')

    for a, b in zip(x - width/2, position_data):
        plt.text(a, b+50, b, ha='center', va='bottom', fontsize=7)
    for a, b in zip(x + width/2, profit_data):
        plt.text(a, b+50, b, ha='center', va='bottom', fontsize=7)

    ax.set_ylabel('数额')
    ax.set_title(f"各领域最新持仓 & 收益 {DateTools.today()}")
    ax.set_xticks(x)
    ax.set_xticklabels(label)
    ax.legend(fontsize=10)
    ax.yaxis.grid(True)

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(config.export_chart_path,
                    'position&profit_bar_chart.png'))
        logger.info(f"Successfully exported profit & bar chart.")


def export_position_pie_chart(show=False):
    # 导出持仓占比的饼状图
    position_data = get_fileds_position()
    label = get_fileds_cn()
    position_data = get_fileds_position()
    p_sum = sum(position_data)

    fig, ax = plt.subplots(figsize=FIGSIZE, subplot_kw=dict(aspect="equal"))
    wedges, texts = ax.pie(position_data, wedgeprops=dict(
        width=0.35), startangle=-40, colors=COLORS)

    bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    kw = dict(arrowprops=dict(arrowstyle="-"),
              bbox=bbox_props, zorder=0, va="center")

    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        percent = str(round(position_data[i]*100/p_sum, 2)) + '%'
        ax.annotate(label[i]+' '+percent, xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                    horizontalalignment=horizontalalignment, **kw)

    ax.set_title(f"各领域持仓占比 {DateTools.today()}")

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(
            config.export_chart_path, 'position_pie_chart.png'))
        logger.info(f"Successfully exported position pie chart.")


def export_history_position_line_chart(show=False):
    # TODO:
    df = Database().to_df('tbl_history_position')
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
    fileds = get_fileds_en()
    x = df['date'].tolist()

    for i, filed in enumerate(fileds):
        y = df[filed].tolist()
        ax.plot(x, y, label=filed,
                color=COLORS[i], linestyle='-', marker='.', linewidth=1.5)

        # 在最后一个数据点加标注
        for _x, _y in zip(x[-1:], y[-1:]):
            ax.text(_x, _y, _y, ha='center', va='bottom')

    ax.set_title(f"各领域持仓历史 {DateTools.today()}")
    ax.set_xticks(x)
    ax.set_xticklabels(list(map(lambda t: t.strftime('%Y-%m-%d'), x)))
    ax.yaxis.grid(True, linestyle='--')
    ax.set_ylabel('数额 ¥')
    ax.legend(loc='upper left')  # 图例

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(config.export_chart_path,
                    'history_position_line_chart.png'))
        logger.info(f"Successfully exported history position line chart.")


def export_history_profit_line_chart(show=False):
    # TODO:
    df = Database().to_df('tbl_history_profit')
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
    fileds = get_fileds_en()
    x = df['date'].tolist()

    for i, filed in enumerate(fileds):
        y = df[filed].tolist()
        ax.plot(x, y, label=filed,
                color=COLORS[i], linestyle='-', marker='.', linewidth=1.5)

        # 在最后一个数据点加标注
        for _x, _y in zip(x[-1:], y[-1:]):
            ax.text(_x, _y, _y, ha='center', va='bottom')

    ax.set_title(f"各领域收益历史 {DateTools.today()}")
    ax.set_xticks(x)
    ax.set_xticklabels(list(map(lambda t: t.strftime('%Y-%m-%d'), x)))
    ax.yaxis.grid(True, linestyle='--')
    ax.set_ylabel('数额 ¥')
    ax.legend(loc='upper left')  # 图例

    if show:
        plt.show()
    else:
        plt.savefig(os.path.join(config.export_chart_path,
                    'history_profit_line_chart.png'))
        logger.info(f"Successfully exported history profit line chart.")
