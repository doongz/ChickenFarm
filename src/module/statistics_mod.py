from collections import defaultdict
import pandas as pd


from ChickenFarm.src.db.tbl_assets import AssetsTable
from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.util.industry_class import get_fileds_en, get_fileds_cn
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


def get_fileds_investment():
    df = Database().to_df('tbl_assets')
    code_to_filed = defaultdict(int)
    for _, row in df.iterrows():
        code_to_filed[row['code']] = row["filed"]

    df = Database().to_df('tbl_investments')
    filed_to_amount = defaultdict(int)
    for _, row in df.iterrows():
        filed_to_amount[code_to_filed[row['code']]] += row["amount"]

    data = []
    keys = get_fileds_en()
    for en in keys:
        data.append(filed_to_amount[en])
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


def get_filed_dataframe(en):

    funds = AssetsTable.get_holding_by_filed(en)
    df = pd.DataFrame(columns=['name', 'code', 'position',
                               'profit', 'profit_rate', 'netvalue'])
    for f in funds:
        tmp_pd = pd.DataFrame({'name': [f.name],
                               'code': [f.code],
                               'position': [f.position],
                               'profit': [f.profit],
                               'profit_rate': [f.profit_rate],
                               'netvalue': [f.netvalue]
                               })
        df = pd.concat([df, tmp_pd], ignore_index=True)
    # reset_index 重置索引
    return df.sort_values(by='position', ascending=False).reset_index(drop=True)
