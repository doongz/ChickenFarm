import pandas as pd
from datetime import datetime
from decimal import Decimal

from chicken_farm.src.model_prof.fund_types import OperateType 
from chicken_farm.src.util.chrome import ChromeDriver
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)


def get_trade_record():

    records = ChromeDriver().query_trade_records()

    df = pd.DataFrame(columns=['operate_time', 'name', 'code', 'operate_type', 'amount'])
    for r in records:
        r = r.replace(' ', '\n').split('\n')
        if '入' in r[4]:
            operate_type = OperateType.BUY
        elif '出' in r[4]:
            operate_type = OperateType.SELL
        else:
            continue

        df = df.append({'operate_time': datetime.strptime(r[0]+' '+r[1], '%Y-%m-%d %H:%M:%S'), 
                        'name': r[2],
                        'code': r[3],
                        'operate_type': operate_type,
                        'amount': Decimal(r[5][:-1]).quantize(Decimal('0.00'))
                        }, ignore_index=True)
    
    df = df.iloc[::-1]
    return df


def get_position():

    positions = ChromeDriver().query_position()

    df = pd.DataFrame(columns=['name', 'code', 'position'])
    for p in positions:
        if len(p) == 0: continue
        if '010718' in p: continue  # 010718这个基金不纳入持仓统计
        p = p.replace(' ', '\n').split('\n')

        df = df.append({'name': p[0][:-8], 
                        'code': p[0][-7:-1],
                        'position': Decimal(p[2]).quantize(Decimal('0.00'))
                        }, ignore_index=True)

    return df

if __name__ == "__main__":
    df = get_position()
    print(df)


