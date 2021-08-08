"""
Automatic Investment Plan
周定投
月定投
"""
from apollo.src.prof_model.fund_netvalue import FundNetValue
from apollo.src.db_model.tbl_info import InfoTable


def invest_week(code, start, end, amount):
    """
    每周定投

    :param code:    基金代码        str      '005827'
    :param start:   定投开始日       str     '2020-08-04'
    :param end:     定投结束日       str     '2021-08-03'
    :param amount:  每次投资的金额    int     400
    :return: 
    """
    fund_val = FundNetValue(code)
    price_df = fund_val.read_sql()
    print(InfoTable.get_by_code(code).name)
    
    start_index = price_df.loc[price_df['date'] == start].index[0]
    end_index = price_df.loc[price_df['date'] == end].index[0]
    buy_df = price_df.iloc[start_index : end_index] # 待买df
    sell_price = float(price_df.loc[price_df['date'] == end]['totvalue']) # 要卖那天的累计净值
    
    total = [0] * 5  # 存放对应星期合计买的份数
    count = [0] * 5  # 存放对应星期的成本

    for index, row in buy_df.iterrows():
        weekday = int(row['date'].weekday())
        # amount金额除以当日累计净值得到购买基金份额，并计算累计份额
        total[weekday] = total[weekday] + amount/float(row['totvalue']) 
        count[weekday] += amount

    for index, unit in enumerate(total):
        print(f"每周 {index+1} 定投，累计投入 {count[index]} 单位金额，",
              f"最终卖出 {round(sell_price*unit,2)} 单位金额，",
              f"收益率 {round(100*(sell_price*unit-count[index])/count[index],2)}% ;")


def invest_month(code, start, end, amount, day_list=['05', '10', '15', '20', '25']):
    fund = xa.fundinfo(code)
    price_df = fund.price
    print(fund.info())
    
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
        print(f"每月 {day} 日定投，累计投入 {cost_dict[day]} 单位金额，",
              f"最终卖出 {round(sell_price*shares_dict[day], 2)} 单位金额，",
              f"收益率 {round(100*(sell_price*shares_dict[day] - cost_dict[day])/cost_dict[day],2)}% ;")