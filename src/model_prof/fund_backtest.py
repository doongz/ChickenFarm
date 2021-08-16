import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import DateTime, DECIMAL, INT, VARCHAR

from apollo.src.config.mysql import USER, PWD, ADDRESS, PORT, DB_BACKTEST


class FundBacktest():

    def __init__(self, code):

        self.engine = create_engine(f"mysql+pymysql://{USER}:{PWD}@{ADDRESS}:{PORT}/{DB_BACKTEST}")
        self.code = code
        self.tbl = f"tbl_{self.code}"

        self.columns = {'start': VARCHAR(64),
                        'week': INT,
                        'algorithm': VARCHAR(64),
                        'before_days': INT,
                        'profit_rate': DECIMAL(5, 4),
                        'test_date': DateTime
                        }

    def to_sql(self, df):

        df.to_sql(name=self.tbl, 
                  con=self.engine, 
                  if_exists="replace",
                  index=False,
                  dtype=self.columns)
        return self.tbl

    def read_sql(self):
        return pd.read_sql(self.tbl, self.engine)

    def query_sql(self, sql):
        sql = f"select * from {self.tbl};"
        return pd.read_sql_query(sql, self.engine)

