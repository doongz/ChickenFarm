import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy import DateTime, DECIMAL, INT, VARCHAR

from src.util.config import Config


config = Config()


class FundBacktest():

    def __init__(self, code):

        self.engine = create_engine(
            f"mysql+pymysql://{config.db_username}:{config.db_password}@{config.db_address}:{config.db_port}/{config.db_backtest}"
        )
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
        # 注意使用 append 会导致数据库连接数爆掉，整表 replace
        with self.engine.connect() as conn:
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
        return df
