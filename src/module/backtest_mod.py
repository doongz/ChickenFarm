import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod

from src.algorithm.stupid import StupidAlgorithm
from src.util.log import get_logger


logger = get_logger(__file__)


class AutomaticInvestmentPlan(ABC):

    InvestmentCycles = [30, 60, 90, 180, 365, 730]  # 展示标签（天）
    # 周期标签 -> 买入窗口完整周数 N（N = round(cycle/7)）
    WeeksPerCycle = {30: 4, 60: 8, 90: 13, 180: 26, 365: 52, 730: 104}
    # 估值日采样步长：每 K 个交易日取一个估值日 C
    MarkDayInterval = 5

    @abstractmethod
    def create_algo(self):
        # factory method
        pass

    def analysis_realtime(self, code, cycle, size=None):
        '''
        长期持有盯市回测：在历史交易日上等间隔采样估值日 C（默认每 5 个一个），
        每个 C 之前取最近 N=WeeksPerCycle[cycle] 个完整交易周买入，C 日盯市。

        :param code:   基金代码         str   '005827'
        :param cycle:  周期展示标签      int   30/60/.../730
        :param size:   已废弃（兼容旧签名），忽略
        :return df                      dataframe
        '''
        n_weeks = self.WeeksPerCycle[cycle]
        stupid = self.create_algo(code)

        # 在库内全部交易日上等间隔采样估值日 C
        trading_days = (stupid._value_df.sort_values('date')['date']
                        .tolist())
        mark_days = trading_days[::self.MarkDayInterval]

        df = pd.DataFrame(
            columns=['start', 'mark_day', 'week', 'algorithm', 'cycle',
                     'profit_rate', 'sample_insufficient', 'test_date'])

        for mark_day in mark_days:
            stupid.prepare_data(mark_day, n_weeks)
            if stupid.buy_df.empty:
                continue

            insufficient = 1 if stupid.sample_insufficient else 0
            mark_ts = pd.Timestamp(mark_day)

            res = stupid.invest_weekly()
            for index, rate in enumerate(res):
                tmp_pd = pd.DataFrame({'start': [stupid.start],
                                'mark_day': [mark_ts],
                                'week': [index+1],
                                'algorithm': ['stupid'],
                                'cycle': [cycle],
                                'profit_rate': [rate],
                                'sample_insufficient': [insufficient],
                                'test_date': [datetime.now()]
                                })
                df = pd.concat([df, tmp_pd])

            profit_rate = stupid.invest_daily()
            if profit_rate is not None:
                tmp_pd = pd.DataFrame({'start': [stupid.start],
                                'mark_day': [mark_ts],
                                'week': [-1],
                                'algorithm': ['stupid'],
                                'cycle': [cycle],
                                'profit_rate': [profit_rate],
                                'sample_insufficient': [insufficient],
                                'test_date': [datetime.now()]
                                })
                df = pd.concat([df, tmp_pd])

        logger.info(f"统计完成:{code}, 周期:{cycle}天 N:{n_weeks}, "
                    f"估值日数:{len(mark_days)}.")
        return df


class StupidPlan(AutomaticInvestmentPlan):

    def create_algo(self, code):
        return StupidAlgorithm(code)
