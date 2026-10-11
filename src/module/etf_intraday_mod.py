"""
ETF 日内分钟行情采集
数据源：akshare 新浪分时接口 stock_zh_a_minute，仅取 1 分钟（period='1'）
原始不复权数据（复权统一在分析层处理，与日线采集存原始价的口径一致）。

新浪分钟接口每日仅约 10 次配额，采集方必须【串行】调用，严禁多进程；
单只失败按指数退避（1/2/4/8 秒）重试，重试耗尽后向上抛出，
由 transport 层记入 fails 并继续下一只。
"""
import time

import pandas as pd

from src.util.log import get_logger


logger = get_logger(__file__)

DEFAULT_RETRIES = 4


def market_symbol(code):
    # 沪市 ETF（51/56/58）前缀 sh；深市 ETF（15/16）前缀 sz
    prefix = 'sh' if code[:2] in ('51', '56', '58') else 'sz'
    return prefix + code


def fetch_etf_minute(code, retries=DEFAULT_RETRIES):
    """
    采集单只 ETF 的 1 分钟原始不复权行情，最多重试 retries 次，退避 1/2/4/8 秒。
    :param code: 6 位 ETF 代码
    :param retries: 重试次数
    :return: DataFrame[datetime, open, high, low, close, volume]，
             按 datetime 升序、同一 datetime 去重保留最后一条；失败抛异常
    """
    import akshare as ak

    last_error = None
    for attempt in range(retries):
        try:
            # 只请求 1 分钟周期，绝不请求 5/15 分钟（接口日配额极低）
            df = ak.stock_zh_a_minute(symbol=market_symbol(code),
                                      period='1',
                                      adjust='')
            if df is None or df.empty:
                raise ValueError('empty minute data')

            # 原始列名 day/open/high/low/close/volume，day 为字符串时间
            df = df.rename(columns={'day': 'datetime'})
            df['datetime'] = pd.to_datetime(df['datetime'])
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            # volume 原始可能是字符串/浮点，先强制数值再转 int，空值填 0
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce') \
                .fillna(0).astype('int64')

            # 按分钟时刻去重保留最后一条，再升序排序
            df = df.drop_duplicates(subset='datetime', keep='last') \
                .sort_values('datetime').reset_index(drop=True)

            logger.info(f"Sina ETF minute success:{code}, rows:{len(df)}.")
            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as error:
            last_error = error
            wait = 2 ** attempt
            logger.warning(f"Sina ETF minute failed:{code}, attempt:"
                           f"{attempt+1}/{retries}, wait:{wait}s, "
                           f"error:{error}.")
            time.sleep(wait)

    raise ConnectionError(f"Sina minute failed after {retries} retries: "
                          f"{last_error}")
