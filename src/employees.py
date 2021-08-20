from chicken_farm.src.model_prof.fund_types import Filed

from chicken_farm.src.module.operate_mod import add_fund, delete_fund, update_fund, show_fund
from chicken_farm.src.module.operate_mod import buy_fund, sell_fund, update_position
from chicken_farm.src.module.statistics_mod import update_total_for_field, record_history
from chicken_farm.src.module.transport_mod import transport_netvalue, transport_backtest_data

from chicken_farm.src.plot.aip_mod import export_violin_plot
from chicken_farm.src.plot.statistics_plot import export_position_bar_chart, \
                                                  export_profit_bar_chart, \
                                                  export_position_profit_bar_chart, \
                                                  export_profit_rate_bar_chart, \
                                                  export_position_pie_chart

from chicken_farm.src.util.sheet_tools import read_buy_list, read_latest_position, export_tables


class Employee:

    def __init__(self, key):
        self.key = key


class Jober(Employee):

    def weekly_job(self):

        # 1、把基金的历史净值上传至 db_netvalue 数据库中
        transport_netvalue()

        # TODO: 2、更新本周的购买记录，需要适配支付宝和天天基金

        # TODO: 3、更新本周的售出记录，需要适配支付宝和天天基金

        # TODO: 4、更新本周所有基金的持仓，需要适配支付宝和天天基金

        # TODO: 5、统计并记录本周各个领域的投入、持仓、收益（已实现，待整合）

        # TODO: 6、导出个人数据统计图表（已实现，待整合）

        # TODO: 7、更新回测分析数据（已实现，待整合）

        # TODO: 8、导出回测分析图表（已实现，待整合）


class Operator(Employee):

    def add(self, code, amount, filed):
        # 新买入基金
        add_fund(code=code, 
                 amount=amount,
                 filed=filed,
                 key=self.key
                 )
        update_total_for_field()

    def delete(self, code):
        # 删除基金
        delete_fund(code=code, 
                    key=self.key
                    )
        update_total_for_field()


    def buy(self, code, amount):
        # 加仓基金
        buy_fund(code=code, 
                 amount=amount, 
                 key=self.key
                 )
        update_total_for_field()

    def sell(self, code, amount):
        # 卖出基金
        sell_fund(code=code, 
                  amount=amount, 
                  key=self.key
                  )
        update_total_for_field()

    def update_position(self, code, amount):
        # 更新基金的最新持仓
        update_position(code=code, 
                        amount=amount, 
                        key=self.key
                        )
        update_total_for_field()

    def update_position_list(self, code):
        # 读取 position.csv 中基金的最新持仓，并更新持仓
        latest_position = read_latest_position()
        for code, position in latest_position:
            update_position(code=code, 
                            amount=position,
                            key=self.key
                            )
        update_total_for_field()

    def show(self, code):
        # 展示基金
        show_fund(code='519674')

    def record_history(self)
        # 统计并记录各个领域以及总的投入、持仓、收益历史
        update_total_for_field()
        record_history()

    def export_tables(self):
        # 导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表
        export_tables()

    def draw_charts(self):
        # 绘制图表
        export_position_bar_chart()
        export_profit_bar_chart()
        export_position_profit_bar_chart()
        export_profit_rate_bar_chart()
        export_position_pie_chart()


class Analyst(Employee):

    def backtest(self):
        # 回测，并将回测数据上传
        transport_backtest_data()

    def draw_violin_plot(self):
        # 绘制各领域基金的小提琴图
        export_violin_plot()



if __name__ == "__main__":
    
    run()