"""
Automatic Investment Plan
周定投
月定投
"""
import pandas as pd
import multiprocessing
from datetime import datetime, timedelta

from apollo.src.model_prof.fund_netvalue import FundNetValue
from apollo.src.model_prof.fund_backtest import FundBacktest
from apollo.src.model_db.tbl_info import InfoTable
from apollo.src.util.date_tools import is_trade_day, get_between_data, get_before_date_interval
from apollo.src.util.date_tools import get_recent_trading_day
from apollo.src.util.log import get_logger


logger = get_logger(__file__)


class InvestmentCycle:

    CYCLES = [180, 365, 1095]
    HALF_YEAR = 180
    ONE_YEAR = 365
    THREE_YEAR = 1095



def upload_backtest_data(code):
    '''
    向 db_backtest 数据库上传基金的，半年、一年、三年回测数据
    todo: 将半年、一年、三年固定
    '''
    try:
        backtest_df = pd.DataFrame()
        for days in InvestmentCycle.CYCLES:
            df = invest_weekly_nearly_day(code=code, before_days=days)
            backtest_df = pd.concat([backtest_df, df])

        btest = FundBacktest(code)
        btest.to_sql(backtest_df)
        logger.info(f"Upload backtest data({code}) success.")
        return True

    except Exception as error:
        logger.error(f"Upload backtest data occur error:{error}.")
        return False


def invest_weekly_nearly_day(code, before_days, size=60):
    '''
    距离今天指定时间前（半年、一年、三年）的定投分析

    :param code:             基金代码         str     '005827'
    :param before_days:      多少天前开始      int     180, 365, 365*3
    :param size:             起始区间大小      int     30
    :param amount:           每次投资的金额    int     100
    :return df                               dataframe
    '''
    fund_value = FundNetValue(code)

    # 处理起始区间，如果起始点在发行日之前，就调整为发行日那天
    start_interval = get_before_date_interval(before_days, size)
    start = datetime.strptime(start_interval[0], "%Y-%m-%d")
    if start < fund_value.release_date:
        start_interval = (fund_value.release_date.strftime("%Y-%m-%d"),
                          (fund_value.release_date + timedelta(days=size)).strftime("%Y-%m-%d")
                          )
        logger.warning(f"基金:{code}, 起始日:{start} 超过首发日:{fund_value.release_date}, "
                       f"start_interval修复为{start_interval}.")

    # 处理结束的那天，如果结束的那天在数据库里还没上传，就调整为数据库中最后的日子
    end = get_recent_trading_day(datetime.today())
    if datetime.strptime(end, "%Y-%m-%d") > fund_value.last_date:
        end = fund_value.last_date.strftime("%Y-%m-%d")
        logger.warning(f"基金:{code}, 结束日在数据库中不存在, 修复为{end}.")

    logger.info(f"开始统计，{code} 前{before_days}天每周定投，区间大小:{size}"
                f" 起始区间:{start_interval}, 结束日:{end}.")

    df = invest_weekly_with_start_interval(code, start_interval, end, before_days)
    return df


def invest_weekly_with_start_interval(code, start_interval, end, before_days, amount=100):
    """
    每周定投 起始日为一个区间
    须确保end为交易日，起始区间内的非交易日会被自动剔除 

    :param code:             基金代码         str     '005827'
    :param start_interval:   定投开始日       tuple    ('2021-01-08', '2021-02-23')
    :param end:              定投结束日       str     '2021-08-09'
    :param amount:           每次投资的金额    int     100
    :return df                               dataframe
    """
    if not is_trade_day(end):
        logger.error(f"End date:{end} is not trading day.")
        return

    df = pd.DataFrame(columns=['start', 'week', 'algorithm', 'before_days', 'profit_rate', 'test_date'])

    for start in get_between_data(start_interval[0], start_interval[1]):
        if not is_trade_day(start):
            continue
        res_in_week = invest_weekly(code, start, end, amount)

        for index, rate in enumerate(res_in_week):
            df = df.append({'start':start, 
                            'week':index+1,
                            'algorithm':'stupid',
                            'before_days':before_days,
                            'profit_rate':rate,
                            'test_date':datetime.now()}, 
                            ignore_index=True)
    logger.info(f"统计完成，{code} 每周定投{amount}，起始日区间为{start_interval}, 结束日为{end}.")
    return df


def invest_weekly(code, start, end, amount=100):
    """
    每周定投，须确保输入的 start, end 为交易日
    todo: ut 

    :param code:    基金代码        str      '005827'
    :param start:   定投开始日       str     '2020-08-04'
    :param end:     定投结束日       str     '2021-08-03'
    :param amount:  每次投资的金额    int     100
    :return res:    list
    """
    if not is_trade_day(start):
        logger.error(f"Start date:{start} is not trading day.")
        return
    if not is_trade_day(end):
        logger.error(f"End date:{end} is not trading day.")
        return

    fund_val = FundNetValue(code)
    price_df = fund_val.read_sql()
    logger.debug(f"Invest week, {InfoTable.get_by_code(code).name} "
                f"{code} start:{start} end:{end}.")
    
    start = datetime.strptime(start, '%Y-%m-%d')
    end = datetime.strptime(end, '%Y-%m-%d')
    try:
        start_index = price_df.loc[price_df['date'] == start].index[0]
    except Exception as error:
        logger.warning(f"Not found start:{start} in price_df, error:{error}.")
        return []
    try:
        end_index = price_df.loc[price_df['date'] == end].index[0]
    except Exception as error:
        logger.warning(f"Not found end:{end} in price_df, error:{error}.")
        return []
    
    buy_df = price_df.iloc[start_index : end_index] # 待买df
    sell_price = float(price_df.loc[price_df['date'] == end]['totvalue']) # 要卖那天的累计净值
    
    total = [0] * 5  # 存放对应星期合计买的份数
    count = [0] * 5  # 存放对应星期的成本

    for index, row in buy_df.iterrows():
        weekday = int(row['date'].weekday())
        # amount金额除以当日累计净值得到购买基金份额，并计算累计份额
        total[weekday] = total[weekday] + amount/float(row['totvalue']) 
        count[weekday] += amount

    res = []
    for index, unit in enumerate(total):
        profit_rate = round((sell_price*unit-count[index])/count[index], 4)
        res.append(profit_rate)
        logger.debug(f"每周 {index+1} 定投，累计投入 {count[index]} 单位金额，"
                    f"最终卖出 {round(sell_price*unit,2)} 单位金额，"
                    f"收益率 {100*profit_rate}% ;")
    return res



def invest_month(code, start, end, amount=100, day_list=['05', '10', '15', '20', '25']):

    fund_val = FundNetValue(code)
    price_df = fund_val.read_sql()
    logger.info(InfoTable.get_by_code(code).name)
    
    start_index = price_df.loc[price_df['date'] == start].index[0]
    end_index = price_df.loc[price_df['date'] == end].index[0]
    buy_df = price_df.iloc[start_index : end_index] # 待买df
    sell_price = float(price_df.loc[price_df['date'] == end]['totvalue']) # 要卖那天的累计净值
    
    
    buy_df['year-month'] = buy_df['date'].map(lambda x: x.strftime("%Y-%m"))
    month_array = buy_df['year-month'].unique()

    shares_dict = {}  # 存放对应星期合计买的份数
    cost_dict = {}  # 存放对应星期的成本

    for month in month_array:
        for day in day_list:
            buy_day = datetime.strptime(f"{month}-{day} 0:0:0", "%Y-%m-%d %H:%M:%S")
            while buy_day not in buy_df['date'].to_list():
                # 如果那一天不交易就取前一个交易日
                buy_day = buy_day + timedelta(days = -1)

            shares_dict[day] = shares_dict.get(day, 0) + amount/float(buy_df.loc[buy_df['date'] == buy_day]['totvalue'])
            cost_dict[day] = cost_dict.get(day, 0) + amount
    
    for day in day_list:
        logger.info(f"每月 {day} 日定投，累计投入 {cost_dict[day]} 单位金额，"
                    f"最终卖出 {round(sell_price*shares_dict[day], 2)} 单位金额，"
                    f"收益率 {round(100*(sell_price*shares_dict[day] - cost_dict[day])/cost_dict[day],2)}% ;")
