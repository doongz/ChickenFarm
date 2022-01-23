import pandas as pd
from termcolor import colored

from ChickenFarm.src.module.operate_mod import add_fund, delete_fund
from ChickenFarm.src.module.operate_mod import buy_fund, sell_fund, update_position
from ChickenFarm.src.module.statistics_mod import update_total_for_field, record_history
from ChickenFarm.src.module.transport_mod import transport_netvalue, transport_netvalue_speed, transport_backtest_data
from ChickenFarm.src.module.chrome_mod import get_trade_record, get_position
from ChickenFarm.src.db.tbl_depository import get_fund_dic_from_dpt, get_filed_pd_from_dpt, get_all_pd_from_dpt
from ChickenFarm.src.db.types import OperateType
import ChickenFarm.src.plot.aip_plot as aip_plot
import ChickenFarm.src.plot.statistics_plot as st_plot
from ChickenFarm.src.util.tools import SheetTools
from ChickenFarm.src.util.exceptions import FundNotFoundError, OpHasBeenRecordedError
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180)  # 设置打印宽度(**重要**)


class SlaveBase:

    def __init__(self, key=None):
        self.key = key


class Operator(SlaveBase):

    def add(self, code, filed):
        # 新买入基金
        add_fund(code=code,
                 filed=filed,
                 key=self.key,
                 )
        update_total_for_field()
        print(colored(f"添加基金: {code}, 所属领域: {filed}", "green"))

    def delete(self, code):
        # 删除基金
        delete_fund(code=code,
                    key=self.key)
        update_total_for_field()
        print(colored(f"删除基金: {code}", "green"))

    def buy(self, code, amount):
        # 加仓基金
        buy_fund(code=code,
                 amount=amount,
                 key=self.key)
        update_total_for_field()
        print(colored(f"{code} 买入 {amount} ¥。", "green"))

    def sell(self, code, amount):
        # 卖出基金
        sell_fund(code=code,
                  amount=amount,
                  key=self.key)
        update_total_for_field()
        print(colored(f"{code} 卖出 {amount} ¥。", "green"))

    def update_position(self, code, amount):
        # 更新基金的最新持仓
        update_position(code=code,
                        amount=amount,
                        key=self.key
                        )
        update_total_for_field()
        print(colored(f"{code} 更新持仓为 {amount} ¥。", "green"))

    def show(self, code=None, filed=None):
        # 展示基金数据
        if code != None:
            fund_dict = get_fund_dic_from_dpt(code)
            for key, value in fund_dict.items():
                print(colored(f"{key}: {value}", "green"))
            return

        if filed != None:
            filed_pd = get_filed_pd_from_dpt(filed)
            print(colored(f"展示 {filed} 领域的基金", "green"))
            print(filed_pd)
            return

        funds_dp = get_all_pd_from_dpt()
        print(colored(f"展示所有持仓的基金", "green"))
        print(funds_dp)
        return

    def record_op(self):
        # 从天天基金获取交易记录，自动将买入、卖出添加至数据库中
        df = get_trade_record()
        for index, row in df.iterrows():
            if row['operate_type'] == OperateType.BUY:
                try:
                    buy_fund(code=row['code'],
                             amount=row['amount'],
                             operate_time=row['operate_time'],
                             key=self.key)
                except OpHasBeenRecordedError as error:
                    logger.warning(f"{error}")
                    continue
                except FundNotFoundError as error:
                    logger.warning(f"{error}")
                    add_fund(code=row['code'],
                             key=self.key)
                    buy_fund(code=row['code'],
                             amount=row['amount'],
                             operate_time=row['operate_time'],
                             key=self.key
                             )

            if row['operate_type'] == OperateType.SELL:
                sell_fund(code=row['code'],
                          amount=row['amount'],
                          operate_time=row['operate_time'],
                          key=self.key
                          )
        update_total_for_field()

        print(colored(df, "green"))
        print(colored(f"自动记录买入、卖出操作完成。", "green"))

    def update_position_auto(self):
        # 从天天基金获取持仓数据，更新至数据库中
        # todo: 等支付宝里面的都卖完了，这里简化
        df = get_position()
        from decimal import Decimal
        code_list = df['code'].tolist()
        latest_position = SheetTools.read_latest_position()
        for code, position in latest_position:
            if code in code_list:
                p = df.loc[df['code'] == code]['position'].values[0] + \
                    Decimal(position).quantize(Decimal('0.00'))
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

        print(colored(df, "green"))
        print(colored(f"自动更新持仓数据完成。", "green"))


class Statistician(SlaveBase):

    def record_history(self):
        # 统计并记录各个领域以及总的投入、持仓、收益历史
        update_total_for_field()
        record_history()
        print(colored(f"统计并记录各个领域以及总的投入、持仓、收益历史完成。", "green"))

    def export_tables(self):
        # 导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表
        SheetTools.export_tables()
        print(colored(f"导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表完成。", "green"))

    def draw_charts(self):
        # 绘制图表
        st_plot.export_position_bar_chart()
        st_plot.export_profit_bar_chart()
        st_plot.export_position_profit_bar_chart()
        st_plot.export_profit_rate_bar_chart()
        st_plot.export_position_pie_chart()
        st_plot.export_history_position_line_chart()
        st_plot.export_history_profit_line_chart()
        st_plot.export_history_buying_line_chart()
        print(colored(f"绘制图表完成。", "green"))


class Analyst(SlaveBase):

    def transport_netvalue(self):
        # 把基金的历史净值上传至 db_netvalue 数据库中
        successes, fails = transport_netvalue()

        print(colored(f"上传基金历史净值成功 {len(successes)} 条。", "green"))
        if len(fails) != 0:
            print(colored(f"上传基金历史净值失败 {len(fails)} 条。", "red"))

    def transport_netvalue_speed(self):
        # 加速上传
        successes, fails = transport_netvalue_speed()

        print(colored(f"上传基金历史净值成功 {len(successes)} 条。", "green"))
        if len(fails) != 0:
            print(colored(f"上传基金历史净值失败 {len(fails)} 条。", "red"))

    def backtest(self):
        # 回测，并将回测数据上传
        transport_backtest_data()
        print(colored(f"回测完成，并将回测数据上传。", "green"))

    def draw_backtest_plots(self):
        # 绘制各领域基金回测的小提琴图
        aip_plot.export_violin_plot()
        print(colored(f"绘制各领域基金回测的小提琴图完成。", "green"))


class Slave(Operator, Statistician, Analyst):

    def __init__(self, key):
        super().__init__(key)
        self.reset()

    def reset(self):
        self._job = Job()

    @property
    def job(self):
        job = self._job
        self.reset()
        return job

    """
    不可进行编排任务，直接使用
    """

    def add(self, code, filed):
        super().add(code, filed)

    def delete(self, code):
        super().delete(code)

    def buy(self, code, amount):
        super().buy(code, amount)

    def sell(self, code, amount):
        super().sell(code, amount)

    def update_position(self, code, amount):
        super().update_position(code, amount)

    def show(self, code, filed):
        super().show(code, filed)

    def transport_netvalue_speed(self):
        super().transport_netvalue_speed()

    """
    可进行编排任务，需要 slave.job.run() 启动
    """

    def record_op(self):
        self._job.add(super().record_op)

    def update_position_auto(self):
        self._job.add(super().update_position_auto)

    def record_history(self):
        self._job.add(super().record_history)

    def export_tables(self):
        self._job.add(super().export_tables)

    def draw_charts(self):
        self._job.add(super().draw_charts)

    def transport_netvalue(self):
        self._job.add(super().transport_netvalue)

    def backtest(self):
        self._job.add(super().backtest)

    def draw_backtest_plots(self):
        self._job.add(super().draw_backtest_plots)


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
        1、更新本周的操作记录，
        2、更新本周所有基金的持仓
        3、统计并记录本周各个领域的投入、持仓、收益
        4、导出个人数据统计表
        5、导出个人数据统计图
        6、把基金的历史净值上传至 db_netvalue 数据库中

        todo: 对数据库的连接前5个任务一直在主进程，transport_netvalue 进入分进程，
              backtest 进入分进程，draw_backtest_plot又进入分进程
              这种情况下数据库的连接会有问题
        https://www.cnblogs.com/flowell/p/multiprocessing_flask_sqlalchemy.html
        """
        self.slave.record_op()
        self.slave.update_position_auto()
        self.slave.record_history()
        self.slave.export_tables()
        self.slave.draw_charts()
        self.slave.transport_netvalue()

    def backtest_job(self):
        """
        1、更新回测分析数据
        2、导出回测分析图表
        """
        self.slave.backtest()
        self.slave.draw_backtest_plots()
