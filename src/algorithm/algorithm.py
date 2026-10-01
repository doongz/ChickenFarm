import pandas as pd
from abc import ABC, abstractmethod

from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from ChickenFarm.src.db.db_netvalue import FundNetValue
from ChickenFarm.src.db.db_etf import ETFDaily
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

        self._amount = 1000

        # 标的类型决定下单模型：fund 固定金额，etf 固定手数
        self.fund_type = FundTypeTools.classify(code)
        bt_cfg = Config().backtest_config or {}
        # ETF 每期买入手数 L，1 手 = 100 份
        self.lots = int(bt_cfg.get('etf_lots', 1))
        self.lot_size = 100

        # 交易成本参数（T8），均可配置，给出贴合实盘的默认值
        # 尾盘买入：用相对价差近似（买入价相对收盘价的上浮比例）
        self.spread = float(bt_cfg.get('spread', 0.0005))
        # 佣金（账户免5，默认 0）；滑点默认 0
        self.commission = float(bt_cfg.get('commission', 0.0))
        self.slippage = float(bt_cfg.get('slippage', 0.0))
        # 场外申购费率折扣（一折常见，0.1）；实际申购费 = buy_rate × discount
        self.fund_fee_discount = float(
            bt_cfg.get('fund_fee_discount', 0.1))

        if self.fund_type == 'etf':
            # ETF：用 db_etf 前复权收盘价 adj_close 成交与盯市（T9）
            raw = ETFDaily(code).read_sql()
            self._value_df = raw[['date', 'adj_close']] \
                .rename(columns={'adj_close': 'totvalue'})
        else:
            # 场外基金：用累计净值 totvalue
            self._value_df = FundNetValue(code).read_sql()[['date', 'totvalue']]

    def effective_buy_price(self, close_price):
        """
        买入实际成交价：收盘价 + 价差 + 滑点（尾盘买入近似）。
        """
        return close_price * (1 + self.spread + self.slippage)

    def fund_subscription_fee(self):
        """
        场外基金实际申购费率：已采集 buy_rate × 折扣；无数据时为 0。
        """
        record = FundsForBacktestTable.get_by_code(self.code)
        raw_rate = float(record.buy_rate) if record and record.buy_rate else 0.0
        return raw_rate * self.fund_fee_discount

    def place_order(self, close_price):
        """
        一笔下单：按标的类型返回 (买入份额, 实际花费本金，含交易成本)。
        买入成交价在收盘价基础上加价差/滑点；
        - fund：固定金额 _amount，份额 = amount/成交价，
                花费 = amount + 申购费(amount×打折费率)
        - etf ：固定手数 lots，份额 = lots*100，
                花费 = 份额×成交价 × (1+佣金率)
        """
        buy_price = self.effective_buy_price(close_price)

        if self.fund_type == 'etf':
            shares = self.lots * self.lot_size
            cost = shares * buy_price * (1 + self.commission)
            return shares, cost

        shares = self._amount / buy_price
        cost = self._amount * (1 + self.fund_subscription_fee())
        return shares, cost

    def execution_price(self, row):
        """
        取该笔成交价：场外基金为累计净值 totvalue，ETF 为前复权收盘价 adj_close。
        统一映射到 totvalue 列。
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

        


