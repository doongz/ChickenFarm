import sys
import pandas as pd
import matplotlib.pyplot as plt
from termcolor import colored

import ChickenFarm.src.plot.aip_plot as aip_plot
import ChickenFarm.src.plot.statistics_plot as st_plot
from ChickenFarm.src.module.operate_mod import add_fund, delete_fund
from ChickenFarm.src.module.operate_mod import get_assets, update_assets, get_investments, update_investments, record_history
from ChickenFarm.src.module.statistics_mod import get_filed_dataframe
from ChickenFarm.src.module.transport_mod import transport_netvalue_multiprocess, transport_backtest_data_multiprocess
from ChickenFarm.src.util.industry_class import get_fileds_en, get_fileds_cn
from ChickenFarm.src.util.tools import SheetTools
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180)  # 设置打印宽度(**重要**)

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 显示中文
plt.rcParams['figure.dpi'] = 100  # 显示分辨率
plt.rcParams['savefig.dpi'] = 200  # 保存图片分辨率


def confirm(func):

    def wrapper(*args, **kwargs):
        answer = input("Are you sure you want to " +
                       colored(f"{func.__name__} {args}", "blue") +
                       " [Y/N]?\n: ").lower()
        if answer != 'y':
            print(colored("Aborted", "red"))
            sys.exit(0)
        func(*args, **kwargs)

    return wrapper


class Operator():

    @confirm
    def add(self, code):
        # 「回测列表」中「添加」基金
        fileds = get_fileds_en()
        options = "Choose filed:\n" + "0 - None\n"
        for i, filed in enumerate(fileds):
            options += f"{i+1} - {filed}\n"
        choose = int(input(options + ": "))
        filed = None if choose == 0 else fileds[choose-1]

        add_fund(code=code,
                 filed=filed,
                 )
        print(colored(f"添加基金: {code}, 所属领域: {filed}", "green"))

    @confirm
    def delete(self, code):
        # 「回测列表」中「删除」基金
        delete_fund(code=code)
        print(colored(f"删除基金: {code}", "green"))

    def update(self):
        # 从天天基金获取持仓数据，更新至数据库中
        df_asts = get_assets()
        for _, row in df_asts.iterrows():
            update_assets(row)
        print(colored(df_asts, "green"))
        print(colored(f"自动更新持仓数据完成。", "green"))

        df_invs = get_investments()
        for _, row in df_invs.iterrows():
            update_investments(row)
        print(colored(df_invs, "green"))
        print(colored(f"自动更新定投数据完成。", "green"))


class Statistician():

    def record_history(self):
        # 记录各个基金的持仓、净值、收益、收益率
        record_history()
        print(colored(f"记录各个基金的持仓、净值、收益、收益率。", "green"))

    def export_tables(self):
        # 导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表
        SheetTools.export_tables()
        print(colored(f"导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表完成。", "green"))

    def draw_charts(self, is_show=False):
        # 绘制图表
        st_plot.export_position_bar_chart(is_show)
        st_plot.export_profit_bar_chart(is_show)
        st_plot.export_position_profit_bar_chart(is_show)
        st_plot.export_position_pie_chart(is_show)
        st_plot.export_investment_bar_chart(is_show)
        # st_plot.export_history_position_line_chart(is_show)
        # st_plot.export_history_profit_line_chart(is_show)
        print(colored(f"绘制图表完成。", "green"))

    def show(self):
        print(colored(f"展示所有持仓的基金", "green"))
        fileds_en = get_fileds_en()
        fileds_cn = get_fileds_cn()
        for i, en in enumerate(fileds_en):
            print(colored(f"{fileds_cn[i]} 领域的基金", "blue"))
            print(get_filed_dataframe(en))

        self.draw_charts(is_show=True)
        input("confirm is done: ")
        return


class Analyst():

    def transport_netvalue(self):
        # 把基金的历史净值上传至 db_netvalue 数据库中
        successes, fails = transport_netvalue_multiprocess()

        print(colored(f"上传基金历史净值成功 {len(successes)} 条。", "green"))
        if len(fails) != 0:
            print(colored(f"上传基金历史净值失败 {len(fails)} 条。", "red"))

    def backtest(self):
        # 回测，并将回测数据上传
        transport_backtest_data_multiprocess()
        print(colored(f"回测完成，已将回测数据上传。", "green"))

    def draw_backtest_plots(self):
        # 绘制各领域基金回测的小提琴图
        aip_plot.export_violin_plot_multiprocess()
        print(colored(f"绘制各领域基金回测的小提琴图完成。", "green"))


class Farmer:

    def __init__(self):
        self.operator = Operator()
        self.statistician = Statistician()
        self.analyst = Analyst()

    @confirm
    def job_run(self, job):
        if job == "base_job":
            self.base_job()
        elif job == "backtest_job":
            self.backtest_job()
        else:
            print(colored(f"输入的任务 {job} 无效", "red"))
            return

    def base_job(self):
        """
        1. 更新本周的操作记录，
        2. 更新本周所有基金的持仓
        3. 统计并记录本周各个领域的投入、持仓、收益
        4. 导出个人数据统计表
        5. 导出个人数据统计图
        """
        self.operator.update()
        self.statistician.record_history()
        self.statistician.export_tables()
        self.statistician.draw_charts()

    def backtest_job(self):
        """
        1. 把基金的历史净值上传至 db_netvalue 数据库中
        2. 更新回测分析数据
        3. 导出回测分析图表
        """
        self.analyst.transport_netvalue()
        self.analyst.backtest()
        self.analyst.draw_backtest_plots()
