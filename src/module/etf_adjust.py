"""
ETF 前复权价合成
基于东财分红表 fund_fh_em（现金分红）与可选拆分因子，从最新交易日向后
递推前复权因子：除息日及更早的价格减去每份分红；拆分日及更早价格按
拆分比率折算。最新价保持不变。
"""
import pandas as pd

from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)


def fetch_cash_dividends(code):
    """
    取该 ETF 的现金分红记录：除息日 -> 累计每份分红额（同日多笔相加）。
    :return: dict{ex_date(Timestamp): dividend_per_share}
    """
    import akshare as ak

    df = ak.fund_fh_em()
    df = df[df['基金代码'] == code]
    dividends = {}
    for _, row in df.iterrows():
        ex_date = pd.Timestamp(row['除息日期'])
        amount = float(row['分红'])
        dividends[ex_date] = dividends.get(ex_date, 0.0) + amount
    return dividends


def _split_ratios(code):
    """
    可选拆分比率：配置 backtest.split_factors: {code: {YYYY-MM-DD: ratio}}
    ratio = 拆分后份额/拆分前份额（如 1 拆 2 -> 2.0）。当前数据源无拆分表，默认空。
    """
    cfg = Config().backtest_config or {}
    raw = (cfg.get('split_factors') or {}).get(code, {})
    return {pd.Timestamp(d): float(r) for d, r in raw.items()}


def apply_forward_adjust(df, code):
    """
    对原始日线 df 增加 adj_close 列（前复权收盘价）。

    从最新日向后递推：
        若下一复权日为除息日：factor_t = factor_next - dividend/c_next
        若下一复权日为拆分日：factor_t = factor_next / ratio
    adj_close_t = factor_t * c_t；最新日 factor=1（adj_close=close）。

    :param df: fetch_etf_daily 的结果（含 date、close）
    :return: 带 adj_close 的 df
    """
    dividends = fetch_cash_dividends(code)
    splits = _split_ratios(code)

    data = df.sort_values('date').reset_index(drop=True)
    closes = data['close'].astype(float).tolist()
    dates = data['date'].tolist()
    n = len(data)

    factor = 1.0
    factors = [0.0] * n
    factors[n - 1] = factor

    # 从倒数第二天向后走；用「次日 t+1 是否为复权事件日」决定因子变化
    for t in range(n - 2, -1, -1):
        next_day = dates[t + 1]
        c_next = closes[t + 1]
        if next_day in splits:
            factor = factor / splits[next_day]
        if next_day in dividends:
            factor = factor - dividends[next_day] / c_next
        factors[t] = factor

    data['adj_close'] = [round(f * c, 4)
                         for f, c in zip(factors, closes)]
    return data
