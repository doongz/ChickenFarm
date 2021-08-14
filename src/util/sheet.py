import os
import pandas as pd

if os.getenv('POSITION_CSV_PATH', None):
    POSITION_CSV_PATH = os.getenv('POSITION_CSV_PATH')
else:
    POSITION_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config/position.csv")


# 从 position.csv 中读取已购买基金的代码列表
def read_buy_list():
    df = pd.read_csv(POSITION_CSV_PATH, dtype={"code": str})
    return df['code'].tolist()


# 从 position.csv 中读取已购买基金的最新持仓
def read_latest_position():
    latest_position = []
    df = pd.read_csv(POSITION_CSV_PATH, dtype={"code": str})

    for index, row in df.iterrows():
        latest_position.append((row['code'], row['position']))

    return latest_position