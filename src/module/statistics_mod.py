from collections import defaultdict

from src.util.types import get_fileds_en
from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


def get_fileds_position():

    df = Database().to_df('tbl_assets')
    data_map = defaultdict(int)
    for _, row in df.iterrows():
        data_map[row['filed']] += row["position"]
        data_map[row['filed']] = round(data_map[row['filed']], 2)

    data = []
    keys = get_fileds_en()
    for en in keys:
        data.append(data_map[en])
    return data


def get_fileds_profit():
    df = Database().to_df('tbl_assets')
    data_map = defaultdict(int)
    for _, row in df.iterrows():
        data_map[row['filed']] += row["profit"]
        data_map[row['filed']] = round(data_map[row['filed']], 2)

    data = []
    keys = get_fileds_en()
    for en in keys:
        data.append(data_map[en])
    return data


def get_fileds_profit_rate():
    df = Database().to_df('tbl_assets')
    data_map = defaultdict(int)
    for _, row in df.iterrows():
        data_map[row['filed']] += row["profit_rate"]
        data_map[row['filed']] = round(data_map[row['filed']], 2)

    data = []
    keys = get_fileds_en()
    for en in keys:
        data.append(data_map[en])
    return data
