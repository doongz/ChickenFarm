import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy import DateTime, DECIMAL, BIGINT

from ChickenFarm.src.util.config import Config


config = Config()


class ETFDaily:

    def __init__(self, code):

        self.engine = create_engine(
            f"mysql+pymysql://{config.db_username}:{config.db_password}@{config.db_address}:{config.db_port}/{config.db_etf}"
        )
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

        with self.engine.connect() as conn:
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
        return df
