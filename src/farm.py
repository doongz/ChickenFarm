import sys
from termcolor import colored

import src.plot.aip_plot as aip_plot
from src.module.operate_mod import add_fund, delete_fund
from src.module.transport_mod import (
    update_market_data_multiprocess,
    transport_backtest_data_multiprocess,
    transport_etf_minute_serial,
)
from src.util.config import Config
from src.util.industry_class import get_fileds_en
from src.util.log import get_logger


logger = get_logger(__file__)


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


class Analyst():

    def fetch(self):
        # 采集回测所需行情：场外基金累计净值（xalpha）+ ETF 前复权日线
        results = update_market_data_multiprocess()
        for fund_type, (successes, fails) in results.items():
            print(colored(f"{fund_type} 行情采集成功 {len(successes)} 条: {successes}",
                          "green"))
            if fails:
                print(colored(f"{fund_type} 行情采集失败 {len(fails)} 条: {fails}",
                              "red"))

    def intraday_fetch(self):
        # 串行采集清单中全部 etf 的 1 分钟分时数据并增量入库（接口限频，禁止并发）
        if not Config().intraday_config.get('enabled', True):
            print(colored("日内择时已禁用（INTRADAY_ENABLED=false）", "yellow"))
            return
        successes, fails = transport_etf_minute_serial()
        print(colored(f"分钟行情采集成功 {len(successes)} 条: {successes}",
                      "green"))
        if fails:
            print(colored(f"分钟行情采集失败 {len(fails)} 条: {fails}",
                          "red"))

    def backtest(self):
        # 回测，并将回测数据上传
        successes, fails = transport_backtest_data_multiprocess()
        print(colored(f"回测完成，成功 {len(successes)} 条。", "green"))
        if fails:
            print(colored(f"回测失败 {len(fails)} 条: {fails}", "red"))

    def draw_backtest_plots(self):
        # 绘制各领域基金回测的小提琴图
        aip_plot.export_violin_plot_multiprocess()
        print(colored(f"绘制各领域基金回测的小提琴图完成。", "green"))

    def intraday_analysis(self):
        # 基于库内 ETF 分钟数据按领域导出日内买入时刻图与 stats（不联网采集）
        if not Config().intraday_config.get('enabled', True):
            print(colored("日内择时已禁用（INTRADAY_ENABLED=false）", "yellow"))
            return
        from src.plot.intraday_plot import export_intraday_plot_multiprocess
        successes, fails = export_intraday_plot_multiprocess()
        print(colored(f"日内择时图导出成功领域: {successes}", "green"))
        if fails:
            print(colored(f"日内择时图导出失败/无数据领域: {fails}", "red"))


class Farmer:

    def __init__(self):
        self.operator = Operator()
        self.analyst = Analyst()

    @confirm
    def job_run(self, job):
        if job == "backtest_job":
            self.backtest_job()
        elif job == "intraday_job":
            self.intraday_job()
        else:
            print(colored(f"输入的任务 {job} 无效，可选：backtest_job、intraday_job", "red"))
            sys.exit(-1)

    def backtest_job(self):
        """
        1. 采集行情（场外基金净值 + ETF 前复权日线）
        2. 更新回测分析数据
        3. 导出回测分析图表
        """
        self.analyst.fetch()
        self.analyst.backtest()
        self.analyst.draw_backtest_plots()

    def intraday_job(self):
        """
        ETF 日内择时串行任务：
        1. 串行采集分钟分时数据入库（接口限频，禁止并发）
        2. 日内分析并按领域出图、导出 stats
        """
        self.analyst.intraday_fetch()
        self.analyst.intraday_analysis()
