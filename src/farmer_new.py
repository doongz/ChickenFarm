from termcolor import colored

from chicken_farm.src.employees import Operator
from chicken_farm.src.employees import Statistician
from chicken_farm.src.employees import Analyst
from chicken_farm.src.util.config import Config
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


class Slave():
    """
    1、更新本周的操作记录，需要适配支付宝和天天基金
    2、更新本周所有基金的持仓，需要适配支付宝和天天基金
    3、统计并记录本周各个领域的投入、持仓、收益
    4、导出个人数据统计表
    5、导出个人数据统计图
    6、把基金的历史净值上传至 db_netvalue 数据库中
    7、更新回测分析数据
    8、导出回测分析图表
    """

    def __init__(self, key):
        self.operator = Operator(key)
        self.statistician = Statistician(key)
        self.analyst = Analyst(key)
        self.reset()

    def reset(self):
        self._job = Job()

    @property
    def job(self):
        job = self._job
        self.reset()
        return job

    def record_op_auto(self):
        self._job.add(self.operator.record_op_auto)

    def update_position_auto(self):
        self._job.add(self.operator.update_position_auto)

    def record_history(self):
        self._job.add(self.statistician.record_history)

    def export_tables(self):
        self._job.add(self.statistician.export_tables)

    def draw_charts(self):
        self._job.add(self.statistician.draw_charts)

    def transport_netvalue(self):
        self._job.add(self.statistician.transport_netvalue)

    def backtest(self):
        self._job.add(self.analyst.backtest)

    def draw_backtest_plot(self):
        self._job.add(self.analyst.draw_backtest_plot)


class Job():

    def __init__(self):
        self.parts = []

    def add(self, part):
        self.parts.append(part)
        
    def run(self):
        logger.info(f"Job parts: {[p.__name__ for p in self.parts]}")
        for f in self.parts:
            f()
            print(colored(f"Run {f.__name__} success.", "green"))


class Farmer:

    def __init__(self):
        self._slave = None

    @property
    def slave(self):
        return self._slave

    @slave.setter
    def slave(self, slave):
        self._slave = slave

    def base_job(self):
        """
        todo: 对数据库的连接前5个任务一直在主进程，transport_netvalue 进入分进程，
              backtest 进入分进程，draw_backtest_plot又进入分进程
              这种情况下数据库的连接会有问题
        https://www.cnblogs.com/flowell/p/multiprocessing_flask_sqlalchemy.html
        """
        self.slave.record_op_auto()
        self.slave.update_position_auto()
        self.slave.record_history()
        self.slave.export_tables() 
        self.slave.draw_charts()
        self.slave.transport_netvalue()
        self.slave.backtest()
        self.slave.draw_backtest_plot()

    def backtest_job(self):
        self.slave.backtest()
        self.slave.draw_backtest_plot()


if __name__ == "__main__":

    farmer = Farmer()
    slave = Slave(Config().operation_key)
    farmer.slave = slave

    print("Base job: ")
    farmer.base_job()
    slave.job.run()

#     print("Backtest job: ")
#     farmer.backtest_job()
#     slave.job.run()

#     # Remember, the Builder pattern can be used without a Director class.
#     print("Custom product: ")
#     slave.record_op_auto()
#     slave.update_position_auto()
#     slave.job.run()