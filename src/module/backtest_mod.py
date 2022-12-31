import pandas as pd
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from ChickenFarm.src.algorithm.stupid import StupidAlgorithm
from ChickenFarm.src.db.db_netvalue import FundNetValue
from ChickenFarm.src.util.tools import DateTools
from ChickenFarm.src.util.exceptions import NonTradingError
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


class AutomaticInvestmentPlan(ABC):

    InvestmentCycles = [90, 180, 365, 730, 1095]

    @abstractmethod
    def create_algo(self):
        # factory method
        pass

    def invest_with_start_interval(self, code, start_interval, end, cycle=None):
        """
        每周定投 起始日为一个区间
        须确保end为交易日，起始区间内的非交易日会被自动剔除 

        :param code:             基金代码            str       '005827'
        :param start_interval:   定投开始日          (datetime, datetime)     ('2021-01-08', '2021-02-23')
        :param end:              定投结束日          str       '2021-08-09'
        :param cycle:            投资周期，仅作为标记  int        180 365 365*3
        :return df                                  dataframe
        """

        df = pd.DataFrame(
            columns=['start', 'week', 'algorithm', 'cycle', 'profit_rate', 'test_date'])

        stupid = self.create_algo(code)

        for start in DateTools.get_between_data(start_interval[0], start_interval[1]):
            try:
                stupid.prepare_data(start, end)
            except NonTradingError as error:
                logger.debug(f"Start:{start} is non-trading day, continue.")
                continue

            res = stupid.invest_weekly()
            for index, rate in enumerate(res):
                tmp_pd = pd.DataFrame({'start': [start],
                                'week': [index+1],
                                'algorithm': ['stupid'],
                                'cycle': [cycle],
                                'profit_rate': [rate],
                                'test_date': [datetime.now()]
                                })
                df = pd.concat([df, tmp_pd])

        logger.info(f"统计完成:{code}, 起始日区间为{start_interval}, 结束日为{end}.")
        return df

    def analysis_realtime(self, code, cycle, size=60):
        '''
        距离今天指定时间前（半年、一年、三年）的定投分析

        :param code:             基金代码         str     '005827'
        :param cycle:            投资周期         int     180
        :param size:             起始区间大小      int     60
        :return df                               dataframe
        '''
        fund_value = FundNetValue(code)

        # 处理起始区间，如果起始点在发行日之前，就调整为发行日那天
        start_interval = DateTools.get_before_date_interval(cycle, size)
        start = start_interval[0]
        if start < fund_value.release_date:
            start_interval = (fund_value.release_date,
                              fund_value.release_date + timedelta(days=size)
                              )
            logger.warning(f"基金:{code}, 起始日:{start} 超过首发日:{fund_value.release_date}, "
                           f"start_interval修复为{start_interval}.")

        # 处理结束的那天，如果结束的那天在数据库里还没上传，就调整为数据库中最后的日子
        end = DateTools.get_recent_trading_day(datetime.today())
        if end > fund_value.last_date:
            end = fund_value.last_date
            logger.debug(f"基金:{code}, 结束日在数据库中不存在, 修复为{end}.")

        logger.info(f"开始统计，{code} 前{cycle}天每周定投，区间大小:{size}"
                    f" 起始区间:{start_interval}, 结束日:{end}.")

        df = self.invest_with_start_interval(code, start_interval, end, cycle)
        return df


class StupidPlan(AutomaticInvestmentPlan):

    def create_algo(self, code):
        return StupidAlgorithm(code)
