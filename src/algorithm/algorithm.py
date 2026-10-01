import pandas as pd
from abc import ABC, abstractmethod

from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from ChickenFarm.src.db.db_netvalue import FundNetValue
from ChickenFarm.src.util.tools import DateTools, FundTypeTools
from ChickenFarm.src.util.config import Config
from ChickenFarm.src.util.exceptions import NonTradingError
from ChickenFarm.src.util.log import get_logger


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
        self.name = FundsForBacktestTable.get_by_code(code).name

        self._value_df = FundNetValue(code).read_sql()
        self._amount = 1000

        # 标的类型决定下单模型：fund 固定金额，etf 固定手数
        self.fund_type = FundTypeTools.classify(code)
        bt_cfg = Config().backtest_config or {}
        # ETF 每期买入手数 L，1 手 = 100 份
        self.lots = int(bt_cfg.get('etf_lots', 1))
        self.lot_size = 100
        # 成交价类型：nav（累计净值）/ close（日线，本期预留，未接入数据源）
        self.price_type = bt_cfg.get('price_type', 'nav')

    def place_order(self, price):
        """
        一笔下单：按标的类型返回 (买入份额, 实际花费本金)。
        - fund：固定金额 _amount，份额 = amount/price（可小数），花费 = amount
        - etf ：固定手数 lots，份额 = lots*100（整数），花费 = lots*100*price
        """
        if self.fund_type == 'etf':
            shares = self.lots * self.lot_size
            cost = shares * price
            return shares, cost
        return self._amount / price, self._amount

    def execution_price(self, row):
        """
        取该笔成交价。本期统一使用累计净值 totvalue；
        price_type=close 需 ETF 日线数据源，未接入时回退到 totvalue。
        """
        return float(row['totvalue'])

    def prepare_data(self, mark_day, n_weeks):
        """
        后视锚定：以统一估值日 C(mark_day) 结束，取 C 之前最近 n_weeks 个完整交易周。
        全程不卖出，C 日净值仅用于对持仓盯市。

        :param mark_day: 估值日 C，str/datetime
        :param n_weeks:  买入窗口的完整交易周数 N
        """
        self.end = self.__check_end(mark_day)
        self.mark_price = self.__find_mark_price()

        weeks = DateTools.complete_trade_weeks(
            self._value_df[self._value_df['date'] < self.end])
        self.sample_insufficient = len(weeks) < n_weeks
        self.n_weeks = min(len(weeks), n_weeks)
        self.weeks = weeks[-self.n_weeks:] if self.n_weeks > 0 else []

        if self.weeks:
            self.start = self.weeks[0]['date'].iloc[0]
            self.buy_df = pd.concat(self.weeks).reset_index(drop=True)
        else:
            self.start = None
            self.buy_df = pd.DataFrame()

    @abstractmethod
    def invest_weekly(self):
        # 第二步
        pass

    def __check_end(self, end):
        # 确保输入的估值日为交易日
        if not DateTools.is_trade_day(end):
            raise NonTradingError(f"Mark day:{end} is not trading day.")
        if isinstance(end, str):
            end = pd.Timestamp(end)
        return end

    def __find_mark_price(self):
        # 估值日 C 的累计净值（盯市价格，不产生卖出）
        mark_price = self._value_df.loc[self._value_df['date'] == self.end]['totvalue']
        return float(mark_price)

        


