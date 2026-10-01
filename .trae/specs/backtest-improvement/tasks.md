# 任务拆解 Tasks

> 建议实现顺序：第一批 → 第二批 → 第三批。每项均给出涉及文件与改动要点。

## 第一批：核心正确性（先调通基金固定金额通路）

- [x] **T1 长期持有盯市 + N 个完整周对齐（FR-1，基金固定金额）**
  - 文件：[algorithm.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/algorithm.py)、[stupid.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/stupid.py)、[backtest_mod.py](file:///Users/dodo/Desktop/ChickenFarm/src/module/backtest_mod.py)、[tools.py](file:///Users/dodo/Desktop/ChickenFarm/src/util/tools.py)
  - 改动：
    - 新增「识别完整交易周」工具：按 ISO 周分组，保留周一~周五均为交易日的周。
    - `prepare_data` 改为后视锚定：输入估值日 C 与 N，取 C 之前最近 N 个完整周；不再用自然日切片。
    - `sell_price` 语义改为 `mark_price = C 日 totvalue`，全程不产生卖出。
    - `invest_weekly` 对每个工作日分组取这 N 周中该工作日的 N 笔买入（每期固定 amount、份额=amount/price），按 FR-1 调和均值口径算盯市收益率；返回时附带每组笔数、N、窗口、C，供断言与统计。
    - `invest_daily` 改为在同样 N 个完整周内每个交易日买入（5N 笔）、C 日盯市；去除魔法数 `999`（改为异常或 None）。
    - 周期标签到 N 的映射：30→4、60→8、90→13、180→26、365→52、730→104。
    - 数据不足时按可用完整周缩减 N 并标注「样本不足」。

- [x] **T1A 标的类型识别（FR-1A）**
  - 文件：[tools.py](file:///Users/dodo/Desktop/ChickenFarm/src/util/tools.py) 或新增工具、`src/util/config.py`
  - 改动：按 6 位代码段判定 fund/etf（51/56/58、15/16 开头为 ETF）；支持配置 `backtest.fund_type_overrides` 覆盖；供算法选择下单模型。

### 第二批：ETF 固定手数通路（用户主要持仓，紧跟第一批，待 T1 验证后启动）

- [x] **T1B ETF 固定手数下单 + 盯市（FR-1B）**
  - 文件：[algorithm.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/algorithm.py)、[stupid.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/stupid.py)、[backtest_mod.py](file:///Users/dodo/Desktop/ChickenFarm/src/module/backtest_mod.py)
  - 改动：
    - ETF 每期固定买 L 手（1 手=100 份、整数手，默认 L=1 可配）；shares=L×100 固定，cash=L×100×price 浮动。
    - 周分组按 FR-1B 公式：`avg_cost=价格算术均值`、`profit_rate=price_C/avg_cost−1`；本金取实际累计花费（组间不同），不用 N×amount。
    - daily 在同样 N 完整周每交易日买（5N 次，每次 L 手）。
    - 复用 T1 的完整周/C 采样/数据不足逻辑；成交价本期默认 nav，预留 price_type。

### 第一批续：显著性与字段（与 T1 同批）

- [x] **T2 配对显著性检验（FR-2）**
  - 新增文件建议：`src/algorithm/significance.py`
  - 改动：
    - 组织「同一 start 情景 × 各工作日」的配对收益矩阵。
    - 实现 Wilcoxon（首选 `scipy.stats.wilcoxon`）+ Holm 多重比较校正；计算效应量（配对差中位数 / 秩二列相关 r 任选其一）。
    - 输出结构化结果（DataFrame：pair, median_diff, p, p_adj, effect_size）。

- [x] **T3 best day 标注规则改造（FR-2）**
  - 文件：[aip_plot.py](file:///Users/dodo/Desktop/ChickenFarm/src/plot/aip_plot.py)
  - 改动：重写 `get_best`：输入显著性结果，按 FR-2 规则决定是否标红；不满足则该子图不标红并加文字「无显著周几差异」。

- [x] **T4 收益字段扩容（FR-6）**
  - 文件：[db_backtest.py](file:///Users/dodo/Desktop/ChickenFarm/src/db/db_backtest.py)、`sql/DDL_db_backtest.sql`
  - 改动：`profit_rate` 改 `DECIMAL(7,4)`；DDL 同步；存量表给 ALTER 语句/说明。

## 第三批：样本与稳健性

- [x] **T5 估值日等间隔采样（FR-3）**
  - 文件：[backtest_mod.py](file:///Users/dodo/Desktop/ChickenFarm/src/module/backtest_mod.py)、[tools.py](file:///Users/dodo/Desktop/ChickenFarm/src/util/tools.py)
  - 改动：估值日 C 按交易日每 K（默认 5）个取一个，替代当前起始区间逐日扫描；每个 C 对应一个配对情景。

- [x] **T6 bootstrap 置信区间（FR-3）**
  - 新增：`src/algorithm/significance.py` 内增加函数。
  - 改动：对各工作日 / daily 中位数做 1000 次情景重采样，输出 95% CI，供图上误差信息与导出。

- [x] **T7 多估值日稳健性（FR-4）**
  - 文件：[backtest_mod.py](file:///Users/dodo/Desktop/ChickenFarm/src/module/backtest_mod.py)、[transport_mod.py](file:///Users/dodo/Desktop/ChickenFarm/src/module/transport_mod.py)、[aip_plot.py](file:///Users/dodo/Desktop/ChickenFarm/src/plot/aip_plot.py)
  - 改动：对每个估值日 C 各跑一遍盯市；聚合各 C 的 best day，多数一致才标注，否则「不稳定」。

## 第四批：成本与口径

- [x] **T8 费率 / 滑点参数化（FR-5 / FR-6）**
  - 文件：`src/util/config.py`、[algorithm.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/algorithm.py)、[stupid.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/stupid.py)
  - 改动：收益计算扣除可配置单边成本；可选从 `tbl_funds_for_backtest.buy_rate` 读取。

- [x] **T9 成交价类型预留 + 周期口径（FR-5 / FR-6）**
  - 文件：[algorithm.py](file:///Users/dodo/Desktop/ChickenFarm/src/algorithm/algorithm.py)、[aip_plot.py](file:///Users/dodo/Desktop/ChickenFarm/src/plot/aip_plot.py)
  - 改动：`price_type(nav/close)` 参数（本期仅 nav 生效，图题注明口径）；短周期子图加「样本少、噪声大」。

## 横切：统计导出与开关

- [ ] **T10 统计结果导出 + 配置开关**
  - 文件：`src/util/config.py`、[aip_plot.py](file:///Users/dodo/Desktop/ChickenFarm/src/plot/aip_plot.py) 或新增 `src/module/report_mod.py`
  - 改动：将 p 值 / 效应量 / CI / 稳健性导出到 `EXPORT_AIP_PLOT_PATH/stats/`（CSV/JSON）；新增配置 `backtest.align_window / significance_test / rolling_exit / bootstrap`，默认开启、可回退旧行为。

- [ ] **T11 全流程回归**
  - 对当前 17 只基金跑 `backtest_job`，确认净值→回测→绘图全部成功且排序、口径正确。
