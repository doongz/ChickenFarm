import pandas as pd
from sqlalchemy import text
from sqlalchemy import DateTime, DECIMAL, BIGINT

from src.db.connection import get_engine


class ETFMinute:

    def __init__(self, code):
        self.engine = get_engine()
        self.code = code
        self.tbl = f"minute_{self.code}"

        self.columns = {'datetime': DateTime,
                        'open': DECIMAL(10, 4),
                        'high': DECIMAL(10, 4),
                        'low': DECIMAL(10, 4),
                        'close': DECIMAL(10, 4),
                        'volume': BIGINT
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
        # 表尚不存在（首次采集）时安全返回带正确列名的空 DataFrame
        try:
            with self.engine.connect() as connection:
                sql = text(f"SELECT * FROM {self.tbl}")
                df = pd.read_sql(sql, con=connection)
        except Exception:
            df = pd.DataFrame({'datetime': pd.Series(dtype='datetime64[ns]'),
                               'open': pd.Series(dtype=float),
                               'high': pd.Series(dtype=float),
                               'low': pd.Series(dtype=float),
                               'close': pd.Series(dtype=float),
                               'volume': pd.Series(dtype='int64')
                               })
            return df
        # SQLite 无原生日期类型，读回为字符串，统一转回 datetime
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    def upsert(self, new_df):
        """
        增量去重写库：读已有数据与新数据拼接，按 datetime 去重保留最后一条
        （新数据优先），升序排序后整表写回。
        :return: 写入后的总行数
        """
        if new_df is None or new_df.empty:
            return len(self.read_sql())

        old_df = self.read_sql()
        # 拼接顺序为旧数据在前、新数据在后，keep='last' 保证新数据优先
        merged = pd.concat([old_df, new_df], ignore_index=True)
        merged = merged.drop_duplicates(subset='datetime', keep='last') \
            .sort_values('datetime').reset_index(drop=True)
        self.to_sql(merged, if_exists='replace')
        return len(merged)
