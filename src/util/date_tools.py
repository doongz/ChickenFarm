import decimal
from chinese_calendar import is_workday
from datetime import datetime, timedelta


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


def get_recent_trading_day(date):
    '''
    得到最近的交易日，往前找
    :param  date     string/datetime  '2021-08-15'
    :return date     datetime         datetime.datetime(2021, 8, 13, 0, 0)
    '''
    if isinstance(date, str):
        # 如果输入的是str, 转为datetime
        date = datetime.strptime(date, '%Y-%m-%d')

    while not is_trade_day(date):
        date = date - timedelta(days=1)

    return date.replace(hour=0, minute=0, second=0, microsecond=0)



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


def get_before_date(days):
    '''
    得到指定天数前的那一天，近半年，近一年，近三年
    :param  days  int       180
    :return data  datetime  datetime.datetime(2021, 8, 13, 0, 0)
    '''
    today_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    data = today_date - timedelta(days=days)
    return data


def get_before_date_interval(days, size=30):
    '''
    得到指定天数前的日期区间，近半年，近一年，近三年
    :param  days  int   180
    :param  size  int   区间大小，30
    :return       (datetime, datetime) 
    '''
    nearly_date = get_before_date(days)
    begin_date = nearly_date
    end_date = nearly_date + timedelta(days=size)

    return (begin_date, end_date)










