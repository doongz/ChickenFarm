"""
ETF 日线行情采集
主源：新浪财经 K 线接口（原始不复权），失败按指数退避重试 4 次；
兜底：akshare 东方财富 fund_etf_hist_em（原始不复权）。
"""
import json
import time

import pandas as pd
import requests

from src.util.log import get_logger


logger = get_logger(__file__)

SINA_URL = ('https://money.finance.sina.com.cn/quotes_service/api/'
            'json_v2.php/CN_MarketData.getKLineData')
SINA_DATALEN = 4000   # 约 16 年日线
MAX_RETRIES = 4


def market_symbol(code):
    # 沪市 ETF（51/56/58）前缀 sh；深市 ETF（15/16）前缀 sz
    prefix = 'sh' if code[:2] in ('51', '56', '58') else 'sz'
    return prefix + code


def fetch_from_sina(code):
    """
    新浪日线行情，最多重试 MAX_RETRIES 次，退避 1/2/4/8 秒。
    :return: DataFrame[date, open, high, low, close, volume]，失败抛异常
    """
    params = {'symbol': market_symbol(code),
              'scale': 240,
              'ma': 'no',
              'datalen': SINA_DATALEN}

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(SINA_URL, params=params, timeout=15)
            resp.raise_for_status()
            try:
                data = json.loads(resp.text)
            except json.JSONDecodeError:
                # 高并发限流时新浪可能返回非 JSON（警告页/空串），按可重试错误处理
                raise ValueError(f'non-json response: {resp.text[:80]!r}')
            if not data:
                raise ValueError('empty kline data')

            df = pd.DataFrame(data)
            df = df.rename(columns={'day': 'date'})
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            df['volume'] = df['volume'].astype('int64')
            logger.info(f"Sina ETF kline success:{code}, rows:{len(df)}.")
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as error:
            last_error = error
            wait = 2 ** attempt
            logger.warning(f"Sina ETF kline failed:{code}, attempt:"
                           f"{attempt+1}/{MAX_RETRIES}, wait:{wait}s, "
                           f"error:{error}.")
            time.sleep(wait)

    raise ConnectionError(f"Sina kline failed after {MAX_RETRIES} retries: "
                          f"{last_error}")


def fetch_from_akshare(code):
    """
    兜底：akshare 东财 ETF 日线（原始不复权），请求窗口 1970~2050。
    :return: DataFrame[date, open, high, low, close, volume]
    """
    import akshare as ak

    df = ak.fund_etf_hist_em(symbol=code,
                             period='daily',
                             start_date='19700101',
                             end_date='20500101',
                             adjust='')
    df = df.rename(columns={'日期': 'date',
                            '开盘': 'open',
                            '收盘': 'close',
                            '最高': 'high',
                            '最低': 'low',
                            '成交量': 'volume'})
    df['date'] = pd.to_datetime(df['date'])
    for col in ['open', 'high', 'low', 'close']:
        df[col] = df[col].astype(float)
    df['volume'] = df['volume'].astype('int64')
    logger.info(f"AkShare ETF kline success:{code}, rows:{len(df)}.")
    return df[['date', 'open', 'high', 'low', 'close', 'volume']]


def fetch_etf_daily(code):
    """
    采集 ETF 原始不复权日线：新浪优先，全部重试失败后切 AkShare。
    """
    try:
        return fetch_from_sina(code)
    except Exception as sina_error:
        logger.warning(f"Switch to AkShare for {code}, sina error:{sina_error}.")
        return fetch_from_akshare(code)
