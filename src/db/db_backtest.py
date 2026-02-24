import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy import DateTime, DECIMAL, INT, VARCHAR

from ChickenFarm.src.util.config import Config


config = Config()


class FundBacktest():

    def __init__(self, code):

        # self.engine = create_engine(
        #     f"mysql+pymysql://{config.db_username}:{config.db_password}@{config.db_address}:{config.db_port}/{config.db_backtest}"
        # )
        self.engine = create_engine(
            f"mysql+pymysql://{config.db_username}@{config.db_address}:{config.db_port}/{config.db_backtest}"
        )
        self.code = code
        self.tbl = f"tbl_{self.code}"

        self.columns = {'start': VARCHAR(64),
                        'week': INT,
                        'algorithm': VARCHAR(64),
                        'cycle': INT,
                        'profit_rate': DECIMAL(5, 4),
                        'test_date': DateTime
                        }

    def to_sql(self, df, if_exists='replace'):
        # if_exists: replace append
        # 注意使用 append 会导致数据库连接数爆掉
        # # 查看当前最大连接数
        # show variables like 'max_connections';
        # # 查看当前活跃连接数
        # show status like 'Threads_connected';
        # # 临时调高最大连接数（重启MySQL后失效）
        # set global max_connections = 1000;

        # df.to_sql(name=self.tbl,
        #           con=self.engine,
        #           if_exists="replace",
        #           index=False,
        #           dtype=self.columns)
        
        with self.engine.connect() as conn:
            df.to_sql(name=self.tbl,
                      con=conn,
                      if_exists=if_exists,
                      index=False,
                      dtype=self.columns
                      )
            
            conn.commit()
        return self.tbl

    def read_sql(self):
        # return pd.read_sql(self.tbl, self.engine)
        with self.engine.connect() as connection:
            sql = text(f"SELECT * FROM {self.tbl}")
            df = pd.read_sql(sql, con=connection)
        return df
