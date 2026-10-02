"""
周定投配对显著性检验
对「同一估值日 C 情景」下的周一~周五收益做配对 Wilcoxon 符号秩检验，
并对所有配对的 p 值做 Holm 多重比较校正。
"""
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from src.util.log import get_logger


logger = get_logger(__file__)

WEEKDAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']


def build_paired_matrix(df):
    """
    将单基金、单周期的回测 df 组织成「估值日情景 × 工作日」配对收益矩阵。
    配对键为估值日 C(mark_day)，而非买入窗口起始日（不同 C 可共享同一 start）。

    :param df: 含 mark_day(估值日)、week(1..5)、profit_rate 的 DataFrame
    :return: DataFrame，index=mark_day，columns=工作日 1..5
    """
    weekday_df = df[df['week'].isin(range(1, 6))]
    matrix = weekday_df.pivot_table(
        index='mark_day', columns='week', values='profit_rate', aggfunc='first')
    matrix = matrix.dropna()
    return matrix


def _holm_correct(pairs):
    """
    Holm 法对 (pair, p) 列表做多重比较校正
    :return: 与输入同序的 p_adj 列表
    """
    m = len(pairs)
    order = sorted(range(m), key=lambda i: pairs[i][1])
    p_adj = [None] * m
    running = 0.0
    for rank, idx in enumerate(order):
        adjusted = (m - rank) * pairs[idx][1]
        running = max(running, adjusted)
        p_adj[idx] = min(running, 1.0)
    return p_adj


def pairwise_wilcoxon(matrix):
    """
    对 5 个工作日的所有配对做配对 Wilcoxon 符号秩检验 + Holm 校正。

    :param matrix: build_paired_matrix 的结果
    :return: DataFrame[pair, day_a, day_b, median_diff, p, p_adj, effect_size]
    """
    days = list(matrix.columns)
    pairs = []
    for a, b in combinations(days, 2):
        diff = (matrix[a] - matrix[b]).astype(float)
        median_diff = float(diff.median())

        # 差值全为 0（完全无差异）时 Wilcoxon 无定义
        if np.allclose(diff, 0):
            p = 1.0
        else:
            try:
                p = float(stats.wilcoxon(matrix[a], matrix[b]).pvalue)
            except ValueError:
                p = 1.0

        # 效应量：配对符号秩 r = z / sqrt(n)，符号取差值中位数方向
        n = len(diff)
        try:
            result = stats.wilcoxon(matrix[a], matrix[b], method='approx')
            z = result.zstatistic
            effect_size = float(z / np.sqrt(n)) if n else 0.0
            if median_diff < 0:
                effect_size = -abs(effect_size)
            else:
                effect_size = abs(effect_size)
        except Exception:
            effect_size = 0.0

        pairs.append({
            'pair': f'{WEEKDAY_NAMES[a-1]}-{WEEKDAY_NAMES[b-1]}',
            'day_a': a, 'day_b': b,
            'median_diff': round(median_diff, 4),
            'p': p,
            'effect_size': round(effect_size, 4),
        })

    p_adj = _holm_correct([(p['pair'], p['p']) for p in pairs])
    for item, adjusted in zip(pairs, p_adj):
        item['p_adj'] = round(float(adjusted), 4)

    return pd.DataFrame(pairs)[
        ['pair', 'day_a', 'day_b', 'median_diff', 'p', 'p_adj', 'effect_size']]


def bootstrap_median_ci(matrix, n_boot=1000, alpha=0.05, seed=42):
    """
    对「估值日情景」整体做非参数 bootstrap：每次重采同样数量的情景行
    （保留 5 个工作日配对关系），计算各组中位数，取分位数得置信区间。

    :param matrix: index=情景、columns=分组（工作日 1..5，可含其他列）
    :return: DataFrame[group, median, ci_low, ci_high]
    """
    rng = np.random.RandomState(seed)
    data = matrix.astype(float)
    n = data.shape[0]
    boot_medians = []
    for _ in range(n_boot):
        sample = data.iloc[rng.randint(0, n, size=n)]
        boot_medians.append(sample.median().values)
    boot_medians = np.array(boot_medians)

    lo_q, hi_q = 100 * alpha / 2, 100 * (1 - alpha / 2)
    rows = []
    for j, group in enumerate(data.columns):
        rows.append({
            'group': group,
            'median': round(float(data.iloc[:, j].median()), 4),
            'ci_low': round(float(np.percentile(boot_medians[:, j], lo_q)), 4),
            'ci_high': round(float(np.percentile(boot_medians[:, j], hi_q)), 4),
        })
    return pd.DataFrame(rows)


def best_day_by_block(matrix, n_blocks=4, min_scenarios=8):
    """
    将估值日情景按时间先后切为 n_blocks 个连续块，逐块做显著性检验并判定 best day，
    用于检验结论是否跨市场环境稳定（FR-4）。

    :return: list[(block_start, best_day)]，块内样本不足或无显著日时 best_day=None
    """
    n = matrix.shape[0]
    block_size = max(1, n // n_blocks)
    results = []
    for k in range(n_blocks):
        chunk = matrix.iloc[k*block_size:(k+1)*block_size]
        if chunk.shape[0] < min_scenarios:
            results.append((chunk.index[0], None))
            continue
        stats_df = pairwise_wilcoxon(chunk)
        results.append((chunk.index[0], find_best_day(chunk, stats_df)))
    return results


def stability_verdict(matrix, n_blocks=4, agree_ratio=0.6):
    """
    汇总各时间块的 best day：若同一工作日在 agree_ratio 以上的块中都为 best，
    判为稳定；否则不稳定（None）。

    :return: (stable_day 或 None, block_best_days list)
    """
    block_results = best_day_by_block(matrix, n_blocks=n_blocks)
    block_days = [day for _, day in block_results]

    for day in matrix.columns:
        if block_days.count(day) / len(block_days) >= agree_ratio:
            return day, block_days
    return None, block_days


def find_best_day(matrix, stats_df, alpha=0.05):
    """
    按 FR-2 规则判定 best day：
    某工作日相对其余工作日中至少 3 个，差异方向一致（该日收益更高）
    且校正后 p < alpha，才标为 best day。

    :return: best day(1..5) 或 None（无显著周几差异）
    """
    medians = matrix.median()
    for day in matrix.columns:
        related = stats_df[
            (stats_df['day_a'] == day) | (stats_df['day_b'] == day)]

        better_cnt = 0
        for _, row in related.iterrows():
            other = row['day_b'] if row['day_a'] == day else row['day_a']
            # 该日是否显著高于 other：差值方向（day-other）> 0 且显著
            if row['day_a'] == day:
                is_better = row['median_diff'] > 0
            else:
                is_better = row['median_diff'] < 0
            if is_better and row['p_adj'] < alpha \
                    and medians[day] > medians[other]:
                better_cnt += 1

        if better_cnt >= 3:
            return day
    return None
