import pandas as pd
from datetime import datetime
from abc import ABC, abstractmethod

from chicken_farm.src.db.tbl_info import InfoTable
from chicken_farm.src.model_prof.fund_netvalue import FundNetValue
from chicken_farm.src.util.tools import DateTools
from chicken_farm.src.util.exceptions import NonTradingError
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


class Algorithm(ABC):

    def __init__(self, code):
        """
        :param code:    基金代码         str     '005827'
        :param start:   定投开始日       str     '2020-08-04'
        :param end:     定投结束日       str     '2021-08-03'
        :param amount:  每次投资的金额    int     100
        """

        self.code = code
        self.name = InfoTable.get_by_code(code).name

        self._value_df = FundNetValue(code).read_sql()
        self._amount = 1000

    def prepare_data(self, start, end):
        # 第一步
        self.start = self.__check_start(start) 
        self.end = self.__check_end(end)
        self.buy_df = self.__cut_buy_df()         # 待买df
        self.sell_price = self.__find_sell_price()     # 要卖那天的累计净值

    @abstractmethod
    def invest_weekly(self):
        # 第二步
        pass

    def __check_start(self, start):
        # 确保输入的 start 为交易日
        if not DateTools.is_trade_day(start):
            raise NonTradingError(f"Start date:{start} is not trading day.")
        return start
        
    def __check_end(self, end):
        # 确保输入的 end 为交易日
        if not DateTools.is_trade_day(end):
            raise NonTradingError(f"End date:{end} is not trading day.")
        return end

    def __cut_buy_df(self):
        # 从所有的净值 df 截取出 start~end 间的 df
        # 如果没找到 start_index 或 end_index 返回空的 df

        buy_df = pd.DataFrame()
        try:
            start_index = self._value_df.loc[self._value_df['date'] == self.start].index[0]
        except Exception as error:
            logger.warning(f"Not found start:{self.start} in value_df, error:{error}.")
            return buy_df
        try:
            end_index = self._value_df.loc[self._value_df['date'] == self.end].index[0]
        except Exception as error:
            logger.warning(f"Not found end:{self.end} in value_df, error:{error}.")
            return buy_df

        buy_df = self._value_df.iloc[start_index : end_index] 
        return buy_df


    def __find_sell_price(self):
        # 查找卖出价格
        sell_price = self._value_df.loc[self._value_df['date'] == self.end]['totvalue']
        return float(sell_price)

        


