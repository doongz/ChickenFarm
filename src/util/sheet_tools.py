import os
import pandas as pd

from chicken_farm.src.model_db.database import Database
from chicken_farm.src.config.path import POSITION_CSV_PATH, EXPORT_TABLE_PATH
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


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


# 从数据库中导出csv文件
def export_tables():
    table_names = ['tbl_depository', 'tbl_total_for_field', 'tbl_history_buying', 
                   'tbl_history_position', 'tbl_history_profit']

    for tbl in table_names:
        df = Database().to_df(tbl)
        tbl_path = os.path.join(EXPORT_TABLE_PATH, tbl+'.csv')
        df.to_csv(tbl_path)

        logger.info(f"Export table:{tbl} to {tbl_path} success.")









