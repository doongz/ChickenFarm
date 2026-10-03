import pandas as pd
from sqlalchemy import text
from sqlalchemy import DateTime, DECIMAL

from src.db.connection import get_engine


class FundNetValue():

    def __init__(self, code):
        self.engine = get_engine()
        self.code = code
        self.tbl = f"tbl_{self.code}"

        self.columns = {'date': DateTime,
                        'netvalue': DECIMAL(10, 4),
                        'totvalue': DECIMAL(10, 4)
                        }

    def to_sql(self, price_df):

        price_df.to_sql(name=self.tbl,
                        con=self.engine,
                        if_exists="replace",  # append 重复的行数据也会追加
                        index=False,
                        dtype=self.columns)
        return self.tbl

    def read_sql(self):
        with self.engine.connect() as connection:
            sql = text(f"SELECT * FROM {self.tbl}")
            df = pd.read_sql(sql, con=connection)
        # SQLite 无原生日期类型，读回为字符串，统一转回 datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df

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
