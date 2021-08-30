from chicken_farm.src.model_prof.fund_types import Filed, OperateType 

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

    def record_op_auto(self):
        # 从天天基金获取交易记录，自动将买入、卖出添加至数据库中
        df = get_trade_record()
        for index, row in df.iterrows():
            if row['operate_type'] == OperateType.BUY:
                buy_fund(code=row['code'], 
                         amount=row['amount'],
                         operate_time=row['operate_time'],
                         key=self.key
                         )
            if row['operate_type'] == OperateType.SELL:
                sell_fund(code=code, 
                          amount=amount, 
                          operate_time=row['operate_time'],
                          key=self.key
                          )
        update_total_for_field()
        return df

    def update_position(self, code, amount):
        # 更新基金的最新持仓
        update_position(code=code, 
                        amount=amount, 
                        key=self.key
                        )
        update_total_for_field()

    def update_position_list(self):
        # 读取 position.csv 中基金的最新持仓，并更新持仓
        latest_position = SheetTools.read_latest_position()
        for code, position in latest_position:
            update_position(code=code, 
                            amount=position,
                            key=self.key
                            )
        update_total_for_field()
        return latest_position

    def update_position_auto(self):
        # 从天天基金获取持仓数据，更新至数据库中
        # todo: 等支付宝里面的都卖完了，这里简化
        df = get_position()
        from decimal import Decimal
        code_list = df['code'].tolist()
        latest_position = SheetTools.read_latest_position()
        for code, position in latest_position:
            if code in code_list:
                p = df.loc[df['code'] == code]['position'].values[0] + Decimal(position).quantize(Decimal('0.00'))
                df.at[df.loc[df['code'] == code].index, 'position'] = p
            else:
                df = df.append({'code': code,
                                'position': Decimal(position).quantize(Decimal('0.00'))
                                }, ignore_index=True)
                
        for index, row in df.iterrows():
            update_position(code=row['code'], 
                            amount=row['position'],
                            key=self.key
                            )
        update_total_for_field()

        return df


    def get_dpt(self, code):
        # 用于展示基金
        return fund_dpt(code=code)


class Statistician(Employee):

    def transport_netvalue(self):
        # 把基金的历史净值上传至 db_netvalue 数据库中
        return transport_netvalue()

    def record_history(self):
        # 统计并记录各个领域以及总的投入、持仓、收益历史
        update_total_for_field()
        record_history()

    def export_tables(self):
        # 导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表
        SheetTools.export_tables()

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

    def draw_backtest_plot(self):
        # 绘制各领域基金回测的小提琴图
        export_violin_plot()


class Jober(Operator, Statistician, Analyst):

    def weekly_job(self):
        """
        todo: 未验证，如果其中一步失败了怎么办: 备忘录模式
        1、把基金的历史净值上传至 db_netvalue 数据库中
        2、更新本周的操作记录，需要适配支付宝和天天基金
        3、更新本周所有基金的持仓，需要适配支付宝和天天基金
        4、统计并记录本周各个领域的投入、持仓、收益
        5、导出个人数据统计表
        6、导出个人数据统计图
        7、更新回测分析数据
        8、导出回测分析图表
        """
        super().transport_netvalue()
        super().record_op_auto()
        super().update_position_auto()
        super().record_history()
        super().export_tables() 
        super().draw_charts()
        super().transport_backtest_data()
        super().draw_backtest_plot()








