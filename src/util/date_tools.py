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
    :param  date     string/datetime  '2021-08-13'
    :return date     string           '2021-08-13'
    '''
    if isinstance(date, str):
        # 如果输入的是str, 转为datetime
        date = datetime.strptime(date, '%Y-%m-%d')

    while not is_trade_day(date):
        date = date - timedelta(days=1)

    return date.strftime("%Y-%m-%d")



def get_between_data(begin_date, end_date):
    '''
    得到两个日期之间连续日期列表
    :param  begin_date  string '2021-07-13'
    :param  end_date    string '2021-08-13'
    :return date_list   list   ['2021-07-13',' 2021-07-14'...]
    '''
    date_list = []
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)
    return date_list


def get_before_date(days):
    '''
    得到指定天数前的那一天，近半年，近一年，近三年
    :param  days  int       180
    :return data  datetime  
    '''
    data = datetime.today() - timedelta(days=days)
    return data


def get_before_date_interval(days, size=30):
    '''
    得到指定天数前的日期区间，近半年，近一年，近三年
    :param  days  int   180
    :param  size  int   区间大小，30
    :return date_list   tuple, ('2021-02-01', '2021-03-03')
    '''
    nearly_date = get_before_date(days)
    begin_date = nearly_date
    end_date = nearly_date + timedelta(days=size)

    return (begin_date.strftime("%Y-%m-%d"), 
            end_date.strftime("%Y-%m-%d"))










