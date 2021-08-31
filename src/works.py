from chicken_farm.src.employees import Operator
from chicken_farm.src.employees import Statistician
from chicken_farm.src.employees import Analyst


class Work:

    def __init__(self, Operator, Statistician, Analyst):
        
        self.operator = Operator(key)
        self.statistician = Statistician(key)
        self.analyst = Analyst(key)

    def weekly(self):
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
        self.statistician.transport_netvalue()
        self.operator.record_op_auto()
        self.operator.update_position_auto()
        self.statistician.record_history()
        self.statistician.export_tables() 
        self.statistician.draw_charts()
        self.analyst.transport_backtest_data()
        self.analyst.draw_backtest_plot()