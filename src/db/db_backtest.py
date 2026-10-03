import pandas as pd
from sqlalchemy import text
from sqlalchemy import DateTime, DECIMAL, INT, VARCHAR

from src.db.connection import get_engine


class FundBacktest():

    def __init__(self, code):
        self.engine = get_engine()
        self.code = code
        self.tbl = f"tbl_{self.code}"

        self.columns = {'start': VARCHAR(64),
                        'mark_day': DateTime,
                        'week': INT,
                        'algorithm': VARCHAR(64),
                        'cycle': INT,
                        'profit_rate': DECIMAL(7, 4),
                        'sample_insufficient': INT,
                        'test_date': DateTime
                        }

    def to_sql(self, df, if_exists='replace'):
        # 由主进程统一串行写入；整表 replace
        with self.engine.begin() as conn:
            df.to_sql(name=self.tbl,
                      con=conn,
                      if_exists=if_exists,
                      index=False,
                      dtype=self.columns
                      )
        return self.tbl

    def read_sql(self):
        with self.engine.connect() as connection:
            sql = text(f"SELECT * FROM {self.tbl}")
            df = pd.read_sql(sql, con=connection)
        # SQLite 无原生日期类型，读回为字符串，统一转回 datetime
        for col in ('mark_day', 'test_date'):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        return df
