import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import DateTime, DECIMAL

from chicken_farm.src.util.config import Config


config = Config()


class FundNetValue():

    def __init__(self, code):

        self.engine = create_engine(
            f"mysql+pymysql://{config.db_username}:{config.db_password}@{config.db_address}:{config.db_port}/{config.db_netvalue}"
            )
        self.code = code
        self.tbl = f"tbl_{self.code}"

        self.columns = {'date': DateTime, 
                        'netvalue': DECIMAL(10,4), 
                        'totvalue': DECIMAL(10,4)
                        }
        

    def to_sql(self, price_df):

        price_df.to_sql(name=self.tbl, 
                        con=self.engine, 
                        if_exists="replace", # append 重复的行数据也会追加
                        index=False,
                        dtype=self.columns)
        return self.tbl

    def read_sql(self):
        return pd.read_sql(self.tbl, self.engine)

    def query_sql(self, sql):
        sql = f"select * from {self.tbl};"
        return pd.read_sql_query(sql, self.engine)

    @property
    def release_date(self):
        # 为数据库中第一条
        pd = self.read_sql()
        return pd.iloc[0]['date']

    @property
    def last_date(self):
        # 为数据库中最后一条
        pd = self.read_sql()
        return pd.iloc[-1]['date']

    