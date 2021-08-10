import pandas as pd

from apollo.src.service.aip_service import invest_week
from apollo.src.util.tools import is_trade_day, get_between_day


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)


def code_005827():

    code = '005827'
    start_interval = ('2021-02-23', '2021-03-04')
    end = '2021-08-09'
    amount = 100

    df = pd.DataFrame(columns=['定投开始日', '每周几', '收益率'])

    for start in get_between_day(start_interval[0], start_interval[1]):
        if not is_trade_day(start):
            continue
        res_in_week = invest_week(code, start, end, amount)

        for index, rate in enumerate(res_in_week):
            df = df.append({'定投开始日':start, 
                            '每周几':index+1, 
                            '收益率':rate}, 
                            ignore_index=True)

    print(df)




if __name__ == "__main__":
    code_005827()


