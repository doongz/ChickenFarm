from chinese_calendar import is_workday
from datetime import datetime


# 得到当前日期是否为股票交易日
def is_trade_day(date):
    '''
    date = '2021-08-13'
    date = datetime.strptime(date, '%Y-%m-%d')
    '''
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False
 