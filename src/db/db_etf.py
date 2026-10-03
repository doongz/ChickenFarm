import pandas as pd
from sqlalchemy import text
from sqlalchemy import DateTime, DECIMAL, BIGINT

from src.db.connection import get_engine


class ETFDaily:

    def __init__(self, code):
        self.engine = get_engine()
        self.code = code
        self.tbl = f"etf_{self.code}"

        self.columns = {'date': DateTime,
                        'open': DECIMAL(10, 4),
                        'high': DECIMAL(10, 4),
                        'low': DECIMAL(10, 4),
                        'close': DECIMAL(10, 4),
                        'volume': BIGINT,
                        'adj_close': DECIMAL(10, 4)
                        }

    def to_sql(self, price_df, if_exists='replace'):

        with self.engine.begin() as conn:
            price_df.to_sql(name=self.tbl,
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
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df
