from chinese_calendar import is_workday
from datetime import datetime, timedelta


# 得到当前日期是否为股票交易日
def is_trade_day(date):
    '''
    :param date  string '2021-08-13'
    '''
    date = datetime.strptime(date, '%Y-%m-%d')
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False


# 两个日期之间连续日期列表
def get_between_day(begin_date,end_date):
    date_list = []
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)
    return date_list
 