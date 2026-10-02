import pandas as pd
import xalpha as xa
from chinese_calendar import is_workday
from datetime import datetime, timedelta

from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)


class XAlphaTools:

    @staticmethod
    def get_fundinfo_from_xalpha(code):
        fundinfo = xa.fundinfo(code)
        return fundinfo


class FundTypeTools:
    # 识别场内 ETF 的代码前两位（沪 51/56/58，深 15/16）
    ETF_PREFIXES = ('51', '56', '58', '15', '16')

    @staticmethod
    def classify(code):
        '''
        按 6 位代码段判定标的类型
        :return 'fund'（场外基金，固定金额下单）/ 'etf'（场内，固定手数下单）
        '''
        overrides = Config().backtest_config.get('fund_type_overrides', {}) \
            if Config().backtest_config else {}
        code = str(code)
        if code in overrides:
            return overrides[code]
        return 'etf' if code[:2] in FundTypeTools.ETF_PREFIXES else 'fund'


class DateTools:

    @staticmethod
    def today():
        return datetime.today().strftime('%Y-%m-%d')

    @staticmethod
    def complete_trade_weeks(value_df):
        '''
        识别净值 df 中的「完整交易周」：周一至周五 5 个工作日全部为交易日
        节假日导致任一工作日休市的整周剔除
        :param value_df: 含 date 列的净值 DataFrame
        :return: list[week_df]，按时间先后，每个 week_df 恰含周一~周五 5 行
        '''
        df = value_df.copy()
        df['weekday'] = df['date'].dt.weekday
        iso = df['date'].dt.isocalendar()
        df['iso_year'] = iso['year']
        df['iso_week'] = iso['week']

        weeks = []
        for _, grp in df.groupby(['iso_year', 'iso_week']):
            weekdays = set(grp['weekday'].tolist())
            if len(grp) == 5 and weekdays == {0, 1, 2, 3, 4}:
                weeks.append(
                    grp.drop(columns=['weekday', 'iso_year', 'iso_week'])
                       .sort_values('date')
                       .reset_index(drop=True)
                )
        weeks.sort(key=lambda week: week['date'].iloc[0])
        return weeks

    @staticmethod
    def is_trade_day(date):
        '''
        判断指定日期是否为股票交易日
        :param date  string/datetime '2021-08-13'
        '''
        if isinstance(date, str):
            # 如果输入的是str, 转为datetime
            date = datetime.strptime(date, '%Y-%m-%d')
        if is_workday(date):
            if date.isoweekday() < 6:
                return True
        return False

    @staticmethod
    def get_recent_trading_day(date):
        '''
        得到最近的交易日，往前找
        :param  date     string/datetime  '2021-08-15'
        :return date     datetime         datetime.datetime(2021, 8, 13, 0, 0)
        '''
        if isinstance(date, str):
            # 如果输入的是str, 转为datetime
            date = datetime.strptime(date, '%Y-%m-%d')

        while not DateTools.is_trade_day(date):
            date = date - timedelta(days=1)

        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_between_data(begin_date, end_date):
        '''
        得到两个日期之间连续日期列表
        :param  begin_date  datetime
        :param  end_date    datetime
        :return date_list   list   [datetime, datetime, ...]
        '''
        date_list = []
        while begin_date <= end_date:
            date_list.append(begin_date)
            begin_date += timedelta(days=1)
        return date_list

    @staticmethod
    def get_before_date(days):
        '''
        得到指定天数前的那一天，近半年，近一年，近三年
        :param  days  int       180
        :return data  datetime  datetime.datetime(2021, 8, 13, 0, 0)
        '''
        today_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        data = today_date - timedelta(days=days)
        return data

    @staticmethod
    def get_before_date_interval(days, size=30):
        '''
        得到指定天数前的日期区间，近半年，近一年，近三年
        :param  days  int   180
        :param  size  int   区间大小，30
        :return       (datetime, datetime)
        '''
        nearly_date = DateTools.get_before_date(days)
        begin_date = nearly_date
        end_date = nearly_date + timedelta(days=size)

        return (begin_date, end_date)
