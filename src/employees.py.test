from chicken_farm.src.db.types import Filed, OperateType 

from chicken_farm.src.module.operate_mod import add_fund, delete_fund, update_fund, fund_dpt
from chicken_farm.src.module.operate_mod import buy_fund, sell_fund, update_position
from chicken_farm.src.module.statistics_mod import update_total_for_field, record_history
from chicken_farm.src.module.transport_mod import transport_netvalue, transport_backtest_data
from chicken_farm.src.module.chrome_mod import get_trade_record, get_position

from chicken_farm.src.plot.aip_plot import export_violin_plot
from chicken_farm.src.plot.statistics_plot import export_position_bar_chart, \
                                                  export_profit_bar_chart, \
                                                  export_position_profit_bar_chart, \
                                                  export_profit_rate_bar_chart, \
                                                  export_position_pie_chart
from chicken_farm.src.util.tools import SheetTools


class Employee:

    def __init__(self, key=None):
        self.key = key


class Operator(Employee):

    def add(self, code, amount, filed):
        print("add")

    def delete(self, code):
        print("delete")

    def buy(self, code, amount):
        print("buy")

    def sell(self, code, amount):
        print("sell")

    def record_op_auto(self):
        print("record_op_auto")

    def update_position_auto(self):
        print("update_position_auto")

    def update_position(self, code, amount):
        print("update_position")

    def update_position_list(self):
        print("update_position_list")

    def get_dpt(self, code):
        print("get_dpt")



class Statistician(Employee):

    def transport_netvalue(self):
        print("transport_netvalue")

    def record_history(self):
        print("record_history")

    def export_tables(self):
        print("export_tables")

    def draw_charts(self):
        print("draw_charts")


class Analyst(Employee):

    def backtest(self):
        print("backtest")

    def draw_backtest_plot(self):
        print("draw_backtest_plot")










