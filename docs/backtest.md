# 回测与算法

本文介绍 ChickenFarm 的定投（AIP, Automatic Investment Plan）回测方法、内置算法原理，以及如何解读输出的小提琴图。

> 这里实现的定投方法仅为一种“最简单的思路”，抛砖引玉，不构成投资建议。历史回测不代表未来收益。

## 核心思想

定投的最终收益对**买入区间与结束时点**非常敏感，只取单一日期算一个结果具有很强的偶然性。因此 ChickenFarm：

1. 在历史交易日上**等间隔采样估值日 C**（默认每 5 个交易日取一个），每个 C 是一个独立情景，避免样本高度重叠；
2. 每个情景取 C 之前最近 **N 个完整交易周**作为买入窗口；
3. 分别模拟「每周固定一天买入」（周一~周五 5 组）与「每日买入」，全程不卖出，在 C 日用当日价格对持仓**盯市**；
4. 收集所有情景的收益率样本，用**小提琴图（Violin Plot）**展示分布，并做配对显著性检验与 bootstrap 置信区间。

## 回测流程

入口为 [src/module/backtest_mod.py](../src/module/backtest_mod.py) 的 `AutomaticInvestmentPlan.analysis_realtime`，对每只基金、每个周期执行：

1. 由周期标签确定买入窗口完整周数 N（见下表）；
2. 从库内全部交易日中按步长 5 等间隔采样估值日 C；
3. 对每个 C，`Algorithm.prepare_data` 取 C 之前最近 N 个完整交易周（不足时标记 `sample_insufficient=1`）；
4. `StupidAlgorithm.invest_weekly` / `invest_daily` 计算 5 个工作日分组与每日买入分组在 C 日的盯市收益率；
5. 结果写入 `db_backtest.tbl_<code>`，随后由绘图模块读取。

## 周期与窗口

周期标签与买入窗口完整周数 N（N = round(cycle/7)）在 [backtest_mod.py](../src/module/backtest_mod.py) 中定义：

```python
InvestmentCycles = [30, 60, 90, 180, 365, 730]          # 展示标签（天）
WeeksPerCycle   = {30: 4, 60: 8, 90: 13, 180: 26,
                   365: 52, 730: 104}                   # 各周期完整交易周数
MarkDayInterval = 5                                     # 估值日采样步长（交易日）
```

「完整交易周」指周一至周五 5 个工作日全部为交易日（节假日导致任一工作日休市的整周剔除），保证周一~周五 5 组在同一组周内都有买入、笔数严格相等。30/60 天短周期每组仅 4~8 笔扣款，噪声较大，图上会标注 `few buys high noise`。

## 标的类型与下单口径

`FundTypeTools`（[src/util/tools.py](../src/util/tools.py)）按 6 位代码前缀区分类型（沪市 51/56/58、深市 15/16 为 ETF，其余为场外基金），也可用配置 `BACKTEST.fund_type_overrides` 强制指定。两类标的的下单模型在 [src/algorithm/algorithm.py](../src/algorithm/algorithm.py) 中分流：

| 口径 | 场外基金 fund | 场内 ETF etf |
| :-- | :-- | :-- |
| 每期买入 | 固定金额（默认 1000 元） | 固定手数（默认 1 手 = 100 份，`etf_lots` 可配） |
| 成交价格 | 累计净值 `totvalue` | 前复权收盘价 `adj_close` |
| 买入份额 | 金额 / 买入价 | 手数 × 100 |
| 成本 | 金额 ×（1 + 申购费率 × 折扣） | 份额 × 买入价 ×（1 + 佣金率） |

- 买入价 = 收盘价 ×（1 + `spread` + `slippage`），默认尾盘价差万 5、佣金 0、滑点 0；
- 场外申购费率取清单中采集的 `buy_rate` × `fund_fee_discount`（默认一折 0.1）；
- ETF 日线由 [src/module/etf_mod.py](../src/module/etf_mod.py) 采集（新浪主源、akshare 兜底，指数退避重试），再由 [src/module/etf_adjust.py](../src/module/etf_adjust.py) 基于现金分红与可选拆分因子递推前复权价。

收益率统一为：

```
profit_rate = (C 日盯市价格 × 累计份额 − 累计投入本金) / 累计投入本金
```

## 显著性检验与稳健性

仅比较中位数大小会把噪声误判为「最佳定投日」。[src/algorithm/significance.py](../src/algorithm/significance.py) 因此做了三层统计：

1. **配对 Wilcoxon 符号秩检验**：以估值日 C 为配对键，对周一~周五全部 10 个配对做检验，并报告效应量 r；p 值经 **Holm 多重比较校正**；
2. **bootstrap 中位数 95% 置信区间**：对情景整体做 1000 次非参数重采（保留 5 个工作日的配对关系），图上以黑色误差线呈现，覆盖周一~周五与 daily 共 6 组；
3. **分时间块稳健性**：将情景按时间先后切 4 块逐块判定 best day，同一工作日在 ≥60% 的块中占优才判为稳健。

判定规则：某工作日相对其余 4 个工作日中至少 3 个，收益方向一致更高且 Holm 校正后 p < 0.05，并通过稳健性判定，才在图上标红；否则标注 `no significant weekday effect`。配置 `significance_test: false` 可回退为旧的「裸中位数最大」逻辑，`bootstrap: false` / `export_stats: false` 可分别关闭误差线与 stats 导出。

## 如何扩展新算法

1. 在 [src/algorithm/](../src/algorithm/) 中新增类，继承 `Algorithm`，实现 `invest_weekly`（可复用 `prepare_data`、`place_order`）；
2. 在 [backtest_mod.py](../src/module/backtest_mod.py) 中新增 Plan 类，工厂方法 `create_algo` 返回新算法；
3. 在 [transport_mod.py](../src/module/transport_mod.py) 的 `_upload_backtest_data` 中把新 Plan 加入 `aip_plans` 列表即可参与回测。

## 小提琴图解读

绘图核心为 [src/plot/aip_plot.py](../src/plot/aip_plot.py) 的 `export_aip_violin_plot_by_filed`，按**领域**分别出图：

- **每一行**：一只基金在各周期（30/60/90/180/365/730 天）的回测分析，同一行各子图纵坐标刻度完全一致，便于横向比较；
- **每一列**：同一周期下不同基金的结果，可横向比较**不同基金的定投收益**；
- **每个子图**：周一至周五（标记 1~5）以及「daily」（每日定投）共 6 把小提琴；
- **中间横线**：中位数；顶端/底端短横线为**极值**；小提琴内标出 25%/75% 分位线；黑色误差线为中位数 95% CI；
- **小提琴宽窄**：概率密度 —— 越宽说明越多样本落在该收益率附近，即**最有可能获得的收益率**。

配色约定：

- `daily`（每日定投）小提琴为**金色**；
- 显著且稳健占优的「最佳定投日」标为**红色**；
- 短周期（30/60 天）右下角橙色提示 `few buys high noise`；
- 无显著周几效应时，左上角灰色标注 `no significant weekday effect`。

图表保存到 `EXPORT_AIP_PLOT_PATH/<日期>/<领域>.png`；每领域另有 3 份统计 CSV 输出到同级 `stats/` 目录：`<领域>_pairwise.csv`（配对检验）、`<领域>_ci.csv`（置信区间）、`<领域>_stability.csv`（分块稳健性）。

## 局限与注意事项

- 回测基于历史净值/行情，**历史表现不代表未来收益**；
- 结果对周期、完整周数量与数据完整性敏感，基金成立时间较短时可用情景会减少；
- 模型对成交价、费用与复权做了简化近似（尾盘价差、固定费率、现金分红递推），未模拟申赎确认与到账延迟；
- 多进程采集/回测对数据库连接数有要求，建议将 MySQL `max_connections` 调到 500 左右；
- ETF 日线采集多进程并发默认限制为 4，避免触发数据源限流。
