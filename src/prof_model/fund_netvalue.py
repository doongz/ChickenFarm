import pandas as pd
from sqlalchemy import create_engine

from apollo.src.config.mysql import USER, PWD, ADDRESS, PORT, DB_NETVALUE


class FundNetValue():

    def __init__(self, code):
        self.code = code
        self.tbl = f"tbl_{self.code}"
        self.engine = create_engine(f"mysql+pymysql://{USER}:{PWD}@{ADDRESS}:{PORT}/{DB_NETVALUE}")

    def to_sql(self, price_df):
        price_df.to_sql(self.tbl, self.engine, if_exists="append", index=True)
        return self.tbl

    def read_sql(self):
        return pd.read_sql(self.tbl, self.engine)

    def query_sql(self, sql):
        sql = f"select * from {self.tbl};"
        return pd.read_sql_query(sql, self.engine)