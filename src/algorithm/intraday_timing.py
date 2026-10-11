"""
ETF 日内最佳买入时刻分析核心（spec FR-3 / FR-4）。

分析思路：把「选周几」的配对分析范式平移到「选盘中时刻」——
在同一组对齐的最近 W 个完整交易日上构造配对矩阵 M[日期, 时刻]，
值为该日该时刻的复权买入价；以当日 VWAP 为基准计算每时刻的
偏离（bps），再做中位数超额、bootstrap CI、配对 Wilcoxon 显著性
检验与分块稳定性判定，最后结合单边交易成本决定是否推荐。

本模块为纯计算模块：除读取分钟/日线 SQLite 表与配置外不联网；
唯一可能缺失的外部输入是日线复权因子，取不到时整体回退原始价
（unadjusted=True），绝不因复权不可用而中断分析。
"""
import math

import numpy as np
import pandas as pd
from scipy import stats

from src.db.db_etf import ETFDaily
from src.db.db_etf_intraday import ETFMinute
from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)

# 默认分析窗口（最近完整交易日数，升序）
DEFAULT_WINDOWS = [5, 10, 20, 60]
# 判定完整交易日的当日分钟 bar 数下限（09:31~15:00 共 240 根）
DEFAULT_MIN_BARS = 230
# 稳定性判定中「块内最便宜前 K 名」的默认 K
DEFAULT_TOP_K = 5
# 默认买入成交价使用的分钟字段
DEFAULT_PRICE_FIELD = 'open'
# 推荐结论所需的最小完整交易日数（复用框架 MIN_SCENARIOS=8 语义）
MIN_SESSIONS = 8

# 合法价格字段；vwap 用每根 bar 的典型价 (high+low+close)/3 近似
_VALID_PRICE_FIELDS = ('open', 'close', 'vwap')

# bootstrap 参数（样本是日期，数量通常几十天，用 block_len=1 的 i.i.d. 重采样）
_N_BOOT = 1000
_BOOT_SEED = 42

# 稳定性分块参数
_N_BLOCKS = 4
_STABLE_RATIO = 0.6


def get_intraday_config():
    """
    读取 INTRADAY_ 前缀配置，做健壮的类型/取值处理后返回。

    任何配置缺失、类型异常或取值非法都回退默认值并记录日志，
    绝不抛异常中断分析。

    :return: dict，键 windows/min_bars_per_day/price_field/top_k
    """
    windows = list(DEFAULT_WINDOWS)
    min_bars = DEFAULT_MIN_BARS
    price_field = DEFAULT_PRICE_FIELD
    top_k = DEFAULT_TOP_K
    try:
        raw_cfg = Config().intraday_config or {}

        raw_windows = raw_cfg.get('windows')
        if isinstance(raw_windows, (list, tuple)) and len(raw_windows) > 0:
            try:
                # 元素转 int、去重、升序；丢弃无法转换/非正的元素
                parsed = sorted({int(w) for w in raw_windows if int(w) > 0})
                if parsed:
                    windows = parsed
            except (TypeError, ValueError):
                logger.warning('INTRADAY_WINDOWS 配置无法解析，回退默认 %s',
                               DEFAULT_WINDOWS)

        if 'min_bars_per_day' in raw_cfg:
            try:
                min_bars = int(raw_cfg['min_bars_per_day'])
            except (TypeError, ValueError):
                logger.warning('INTRADAY_MIN_BARS_PER_DAY 配置无法解析，'
                               '回退默认 %s', DEFAULT_MIN_BARS)

        if 'top_k' in raw_cfg:
            try:
                top_k = int(raw_cfg['top_k'])
            except (TypeError, ValueError):
                logger.warning('INTRADAY_TOP_K 配置无法解析，回退默认 %s',
                               DEFAULT_TOP_K)

        raw_field = raw_cfg.get('price_field')
        if raw_field is not None:
            price_field = str(raw_field).strip().lower()
            if price_field not in _VALID_PRICE_FIELDS:
                logger.warning("INTRADAY_PRICE_FIELD 取值 '%s' 非法"
                               "（仅支持 open/close/vwap），回退 '%s'",
                               raw_field, DEFAULT_PRICE_FIELD)
                price_field = DEFAULT_PRICE_FIELD
    except Exception as e:
        # 配置文件不存在等情况下也不能中断分析，整体回退默认
        logger.warning('读取日内择时配置失败，全部使用默认值：%s', e)

    return {
        'windows': windows,
        'min_bars_per_day': min_bars,
        'price_field': price_field,
        'top_k': top_k,
    }


def build_sessions(minute_df, min_bars=DEFAULT_MIN_BARS):
    """
    从分钟数据识别完整交易日并按日切分。

    按自然日分组，仅保留「当日分钟 bar 数达到该标的典型时段长度」的交易日，
    替代旧脚本「粗暴剔除第一天」的脆弱做法；时刻集合完全由实际数据决定，
    不硬编码时间网格。

    完整日阈值按标的【自适应】：取该标的 bar 数众数（最常见的当日 bar 数）
    作为典型交易时段长度 typical，阈值 = min(min_bars, 0.9×typical)。
    这样常规全天 ETF（typical≈238）阈值≈214，残缺半日（如 67/130 根）被剔除；
    而正常交易时段本身较短的标的（如部分跨境 ETF 每日仅 ~178 根）不会被
    230 的绝对阈值误删——跨时刻配对本来就只在该标的自身日期的时刻交集内进行。

    :param minute_df: ETFMinute.read_sql() 的结果，
                      列 datetime/open/high/low/close/volume
    :param min_bars: bar 数上限阈值（全天标的据此收紧到典型长度的 90%）
    :return: list[(date, day_df)]，按日期升序；day_df 含原始列并已按
             datetime 升序。空输入返回 []
    """
    if minute_df is None or minute_df.empty:
        return []

    df = minute_df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df['_date'] = df['datetime'].dt.date

    counts = df.groupby('_date').size()
    typical = int(counts.mode().iloc[0]) if len(counts) else 0
    # 自适应阈值：全天标的≈214（剔半日）；短时段标的按其典型长度的 90%
    threshold = min(int(min_bars), max(1, int(0.9 * typical)))

    sessions = []
    for date, day_df in df.groupby('_date', sort=True):
        if len(day_df) >= threshold:
            sessions.append((date, day_df.drop(columns=['_date']).reset_index(
                drop=True)))
    return sessions


def minute_adjusted(day_df, factor):
    """
    给单日分钟 OHLC 乘以前复权因子，volume 保持不变。

    :param day_df: 单日分钟 DataFrame
    :param factor: 日复权因子（float）
    :return: 复权后的新 DataFrame（不修改入参）
    """
    adjusted = day_df.copy()
    factor = float(factor)
    for col in ('open', 'high', 'low', 'close'):
        if col in adjusted.columns:
            adjusted[col] = adjusted[col].astype(float) * factor
    return adjusted


def day_adjust_factors(code):
    """
    计算「交易日 -> 前复权因子」映射，使分钟价口径与日线 adj_close 一致。

    日线 adj_close 已由采集链路算好，故这里只做 adj_close/close，
    不调用 etf_adjust.fetch_cash_dividends（联网且可能失败）。

    :return: dict{datetime.date: float}；日线为空、缺列或任何异常时
             返回 {}（表示无因子，调用方按原始价 1.0 处理）
    """
    try:
        daily = ETFDaily(code).read_sql()
        if daily is None or daily.empty:
            return {}
        if 'adj_close' not in daily.columns or 'close' not in daily.columns:
            return {}

        factors = {}
        for _, row in daily.iterrows():
            close = float(row['close'])
            adj_close = row['adj_close']
            if pd.isna(adj_close) or not close:
                continue
            factors[pd.Timestamp(row['date']).date()] = float(adj_close) / close
        return factors
    except Exception as e:
        logger.warning('%s 日线复权因子不可用，日内分析回退原始价：%s',
                       code, e)
        return {}


def _typical_price(day_df):
    # 每根 bar 的典型价 (high+low+close)/3，vwap 字段时使用
    return (day_df['high'].astype(float)
            + day_df['low'].astype(float)
            + day_df['close'].astype(float)) / 3.0


def vwap(day_df, price_field):
    """
    当日基准 VWAP：sum(price*volume)/sum(volume)。

    price_field='vwap' 时 price 取每根 bar 的典型价；volume 全为
    0/缺失时退化为当日 price 列的算术平均。

    :return: float
    """
    if price_field == 'vwap':
        price = _typical_price(day_df)
    else:
        price = day_df[price_field].astype(float)

    volume = day_df['volume'].astype(float) if 'volume' in day_df.columns \
        else pd.Series(0.0, index=day_df.index)
    total_volume = float(volume.sum())
    if np.isfinite(total_volume) and total_volume > 0:
        return float((price * volume).sum() / total_volume)
    return float(price.mean())


def session_price(day_df, price_field):
    """
    返回单日用于「时刻买入价」的 Series。

    :return: Series，index 为 HH:MM:SS 字符串，值为买入价
    """
    times = pd.to_datetime(day_df['datetime']).dt.strftime('%H:%M:%S')
    if price_field == 'vwap':
        values = _typical_price(day_df)
    else:
        values = day_df[price_field].astype(float)
    return pd.Series(values.values, index=times)


def build_paired_matrix(sessions, factors, price_field):
    """
    把多个完整交易日组装成严格按日期对齐的宽表（缺失保留 NaN）。

    每个交易日先按日复权因子复权，再取时刻买入价；当日基准 VWAP
    也用同一份复权后数据计算，保证口径一致。因子缺失日按 1.0
    （原始价）处理。

    :param sessions: build_sessions 的结果
    :param factors: day_adjust_factors 的结果
    :param price_field: open/close/vwap
    :return: (prices, vwaps)
             prices: DataFrame，index=date，columns=HH:MM:SS
             vwaps: Series，index=date
    """
    price_rows = {}
    vwap_map = {}
    for date, day_df in sessions:
        factor = factors.get(date, 1.0)
        adjusted = minute_adjusted(day_df, factor)
        price_rows[date] = session_price(adjusted, price_field)
        vwap_map[date] = vwap(adjusted, price_field)

    if not price_rows:
        return pd.DataFrame(), pd.Series(dtype=float)

    prices = pd.DataFrame.from_dict(price_rows, orient='index')
    prices.index.name = 'date'
    # 列按盘中时间先后排序（HH:MM:SS 字符串排序与真实时刻顺序一致）
    prices = prices.reindex(sorted(prices.columns), axis=1)
    prices = prices.sort_index()

    vwaps = pd.Series(vwap_map).reindex(prices.index)
    vwaps.index.name = 'date'
    return prices, vwaps


def align_window(prices, vwaps, w):
    """
    取最近 w 个日期并构造严格配对矩阵。

    先删任一日期缺失的时刻列，再删在剩余时刻上仍有缺失的日期行，
    从而保证所有时刻共用同一组日期（修复旧脚本各时刻日期集合
    不一致的错配缺陷）。

    :return: (prices_aligned, vwaps_aligned)，无数据时为 (空表, 空序列)
    """
    if prices is None or prices.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    window = prices.sort_index().tail(int(w))
    if window.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    aligned = window.dropna(axis=1, how='any').dropna(axis=0, how='any')
    if aligned.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    aligned_vwaps = vwaps.reindex(aligned.index)
    return aligned, aligned_vwaps


def _wilcoxon_best(dev_best):
    """
    对最佳时刻一列 dev（相对 0=VWAP）做单样本双侧 Wilcoxon 符号秩检验。

    :return: (p_value, effect_size, n)；样本不足或无法检验时
             p/r 为 np.nan
    """
    x = pd.Series(dev_best).astype(float).dropna()
    nonzero = x[~np.isclose(x.values, 0.0)]
    n = int(len(nonzero))
    if n < 6:
        return np.nan, np.nan, len(x)

    try:
        res = stats.wilcoxon(x, zero_method='wilcox',
                             alternative='two-sided')
    except ValueError:
        # 全为 0 或样本不足导致检验无定义
        return np.nan, np.nan, len(x)

    p_value = float(res.pvalue)
    # 正态近似换算效应量 r=|z|/sqrt(n)：
    # W 的均值与方差按符号秩零假设计算（不做 tie/连续性校正，保持简单稳健）
    mu = n * (n + 1) / 4.0
    var = n * (n + 1) * (2 * n + 1) / 24.0
    if var > 0:
        z = (float(res.statistic) - mu) / math.sqrt(var)
        effect_r = abs(z) / math.sqrt(n)
    else:
        effect_r = np.nan
    return p_value, effect_r, len(x)


def _bootstrap_median_ci(dev):
    """
    对 dev 矩阵按【日期行】做 i.i.d. bootstrap，numpy 向量化一次生成
    全部 (n_boot, n) 索引，计算各时刻中位数的 95% CI。

    :return: (ci_low Series, ci_high Series)，index 与 dev 列一致
    """
    values = dev.astype(float).values
    n = values.shape[0]
    rng = np.random.RandomState(_BOOT_SEED)
    # 一次性生成所有 bootstrap 行索引：(n_boot, n)
    idx = rng.randint(0, n, size=(_N_BOOT, n))
    boot_medians = np.median(values[idx], axis=1)
    ci_low = pd.Series(np.nanpercentile(boot_medians, 2.5, axis=0),
                       index=dev.columns)
    ci_high = pd.Series(np.nanpercentile(boot_medians, 97.5, axis=0),
                        index=dev.columns)
    return ci_low, ci_high


def _is_stable(dev, best_time, top_k):
    """
    分块稳定性：日期按时间先后切 4 块，best_time 在 >=60% 的有效块中
    进入「块内中位数最便宜前 K 名」则判稳。块内天数不足 2 的块跳过不计。

    :return: bool
    """
    n = dev.shape[0]
    block_size = max(1, n // _N_BLOCKS)
    hit = 0
    valid_blocks = 0
    for k in range(_N_BLOCKS):
        chunk = dev.iloc[k * block_size:(k + 1) * block_size]
        if chunk.shape[0] < 2:
            continue
        valid_blocks += 1
        cheapest = chunk.median(axis=0).nsmallest(int(top_k)).index
        if best_time in set(cheapest):
            hit += 1

    if valid_blocks == 0:
        return False
    need = math.ceil(_STABLE_RATIO * valid_blocks)
    return hit >= need


def analyze_window(prices_aligned, vwaps_aligned, top_k=DEFAULT_TOP_K,
                   cost_bps=0.0):
    """
    在严格对齐的窗口矩阵上计算每时刻统计量、显著性、CI 与稳定性。

    :param prices_aligned: align_window 结果，index=date、columns=时刻
    :param vwaps_aligned: 与 prices_aligned 同行索引的当日 VWAP
    :param top_k: 稳定性判定的块内前 K 名
    :param cost_bps: 单边交易成本（bps），节省中位数需大于它才可能推荐
    :return: dict，含 n_days/times/best_time/best_median/p_value/
             effect_size/stable/recommended
    """
    # dev[d,t] = (price / vwap - 1) * 10000，按日（行）对齐基准
    dev = prices_aligned.astype(float).div(vwaps_aligned, axis=0).sub(
        1.0, axis=0) * 10000.0

    n_days = int(dev.shape[0])
    medians = dev.median(axis=0)
    means = dev.mean(axis=0)
    # 样本标准差：样本数 <=1 时无定义，记 0
    stds = dev.std(axis=0, ddof=1) if n_days > 1 else pd.Series(
        0.0, index=dev.columns)
    cheap_ratio = (dev < 0).mean(axis=0)

    ci_low, ci_high = _bootstrap_median_ci(dev)

    # 中位数最小（最便宜）的时刻为候选最佳
    best_time = str(medians.idxmin())
    best_median = float(medians[best_time])
    p_value, effect_size, _ = _wilcoxon_best(dev[best_time])
    stable = _is_stable(dev, best_time, top_k)

    times = pd.DataFrame({
        'median': medians,
        'mean': means,
        'std': stds,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'cheap_ratio': cheap_ratio,
        'p_value': np.nan,
        'effect_size': np.nan,
    })
    # 显著性只对候选最佳时刻报告（避免对 ~240 个时刻做海量两两检验）
    times.loc[best_time, 'p_value'] = p_value
    times.loc[best_time, 'effect_size'] = effect_size
    times = times.sort_index()

    significant = bool(np.isfinite(p_value) and p_value < 0.05)
    recommended = (n_days >= MIN_SESSIONS and significant and stable
                   and best_median < -float(cost_bps))

    return {
        'n_days': n_days,
        'times': times,
        'best_time': best_time,
        'best_median': best_median,
        'p_value': p_value,
        'effect_size': effect_size,
        'stable': bool(stable),
        'recommended': bool(recommended),
    }


def _get_cost_bps():
    """
    从 BACKTEST_ 配置读单边交易成本率并换算为 bps。
    单边成本率 = spread + slippage + commission，仅用于判断节省是否
    覆盖成本，不参与时刻排序。
    """
    try:
        cfg = Config().backtest_config or {}
        spread = float(cfg.get('spread', 0.0005))
        commission = float(cfg.get('commission', 0.0))
        slippage = float(cfg.get('slippage', 0.0))
        return (spread + slippage + commission) * 10000.0
    except Exception as e:
        logger.warning('读取回测成本配置失败，成本按 0 处理：%s', e)
        return 0.0


def analyze_etf_minute(code, windows=None, min_bars=None, price_field=None,
                       top_k=None):
    """
    单只 ETF 的日内择时分析顶层函数（供绘图/入口调用）。

    读取分钟库表 -> 识别完整交易日 -> 日级复权（失败回退原始价）
    -> 构造配对矩阵 -> 逐窗口对齐并分析。任何单只 ETF 级异常都
    容错记录 error 并返回 None，调用方循环多只标的时不被打断。

    :return: {'code', 'unadjusted', 'price_field', 'results':[每窗口 dict]}
             或 None（无数据/分析异常）
    """
    try:
        cfg = get_intraday_config()
        if windows is None:
            windows = cfg['windows']
        windows = sorted({int(w) for w in windows if int(w) > 0})
        if min_bars is None:
            min_bars = cfg['min_bars_per_day']
        if price_field is None:
            price_field = cfg['price_field']
        if top_k is None:
            top_k = cfg['top_k']

        minute_df = ETFMinute(code).read_sql()
        if minute_df is None or minute_df.empty:
            logger.info('%s 分钟库表无数据，跳过日内择时分析', code)
            return None

        sessions = build_sessions(minute_df, min_bars=min_bars)
        if not sessions:
            logger.info('%s 无满足 %s 根 bar 阈值的完整交易日，跳过分析',
                        code, min_bars)
            return None

        factors = day_adjust_factors(code)
        unadjusted = len(factors) == 0
        if unadjusted:
            logger.info('%s 复权因子不可用，按原始价分析（unadjusted）',
                        code)

        prices, vwaps = build_paired_matrix(sessions, factors, price_field)
        cost_bps = _get_cost_bps()

        results = []
        for w in windows:
            aligned_prices, aligned_vwaps = align_window(prices, vwaps, w)
            if aligned_prices.empty:
                results.append({'window': w, 'n_days': 0,
                                'insufficient': True})
                continue
            try:
                result = analyze_window(aligned_prices, aligned_vwaps,
                                        top_k=top_k, cost_bps=cost_bps)
            except Exception as e:
                logger.error('%s 窗口 %s 日内分析失败：%s', code, w, e)
                results.append({'window': w, 'n_days': 0,
                                'insufficient': True})
                continue
            result['window'] = w
            result['insufficient'] = result['n_days'] < MIN_SESSIONS
            results.append(result)

        return {
            'code': code,
            'unadjusted': unadjusted,
            'price_field': price_field,
            'results': results,
        }
    except Exception as e:
        logger.error('%s 日内择时分析异常：%s', code, e)
        return None
