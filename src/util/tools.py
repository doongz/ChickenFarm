import os
import pandas as pd
import xalpha as xa
from chinese_calendar import is_workday
from datetime import datetime, timedelta


from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.util.config import Config
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


class SheetTools:

    @staticmethod
    def read_buy_list():
        # 从 position.csv 中读取已购买基金的代码列表
        df = pd.read_csv(Config().position_csv_path, dtype={"code": str})
        return df['code'].tolist()

    @staticmethod
    def read_latest_position():
        # 从 position.csv 中读取已购买基金的最新持仓
        latest_position = []
        df = pd.read_csv(Config().position_csv_path, dtype={"code": str})

        for index, row in df.iterrows():
            latest_position.append((row['code'], row['position']))

        return latest_position

    @staticmethod
    def export_tables():
        # 从 db_fund 数据库中导出csv文件
        table_names = ['tbl_assets',
                       'tbl_funds_for_backtest', 'tbl_history']

        for tbl in table_names:
            df = Database().to_df(tbl)
            tbl_path = os.path.join(Config().export_table_path, tbl+'.csv')
            df.to_csv(tbl_path)

            logger.info(f"Export table:{tbl} to {tbl_path} success.")


class XAlphaTools:

    @staticmethod
    def get_fundinfo_from_xalpha(code):
        fundinfo = xa.fundinfo(code)
        return fundinfo


class DateTools:

    @staticmethod
    def today():
        return datetime.today().strftime('%Y-%m-%d')

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
