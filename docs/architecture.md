# 架构设计

本文介绍 ChickenFarm 的目录结构、分层架构、核心角色及它们之间的协作关系。

## 总体结构

项目采用清晰的分层设计：入口层负责解析命令，核心角色层编排业务，业务模块层实现具体逻辑，底层由数据库访问、算法与工具支撑。

```
chick.py (CLI 入口)
      │  argparse 解析参数
      ▼
Farmer (src/farm.py)  ── 编排者，持有三个角色
      ├── Operator      数据采集与基金列表维护
      ├── Statistician  个人数据统计、表格与图表
      └── Analyst       净值传输、回测、回测绘图
                │
                ▼
   module/ (业务模块)
   ├── operate_mod.py     增删基金、抓取/更新资产与定投、记录历史
   ├── statistics_mod.py  按领域聚合持仓/收益/定投
   ├── backtest_mod.py    定投计划（AIP）抽象与实现
   └── transport_mod.py   多进程传输净值与回测数据
                │
        ┌───────┴────────┬──────────────┐
        ▼                ▼              ▼
   algorithm/        db/            plot/  +  util/
   定投算法          数据库/ORM       可视化    配置/日志/浏览器/日期
```

## 入口层

### [chick.py](../chick.py)

命令行入口，使用标准库 `argparse` 定义一组**互斥**参数（`-add`、`-update`、`-job` 等）。解析后将调用转发给 `Farmer` 及其下属角色。详见 [命令行手册](./cli.md)。

## 核心角色层（src/farm.py）

[src/farm.py](../src/farm.py) 是项目的中枢，采用“农场”隐喻组织职责：

| 角色 | 职责 | 关键方法 |
| :--- | :--- | :--- |
| `Farmer` | 总编排者，持有并调度其他三个角色；执行预置任务 | `job_run`、`base_job`、`backtest_job` |
| `Operator` | 维护回测基金列表；从天天基金采集持仓与定投 | `add`、`delete`、`update` |
| `Statistician` | 记录历史、导出表格、绘制个人图表 | `record_history`、`export_tables`、`draw_charts`、`show` |
| `Analyst` | 传输历史净值、执行回测、绘制小提琴图 | `transport_netvalue`、`backtest`、`draw_backtest_plots` |

`Farmer.__init__` 中一次性实例化三个角色，CLI 命令最终映射到对应角色的方法。

### 两个预置任务（流水线）

- **`base_job`**（个人数据）：`operator.update` → `statistician.record_history` → `statistician.export_tables` → `statistician.draw_charts`
- **`backtest_job`**（回测分析）：`analyst.transport_netvalue` → `analyst.backtest` → `analyst.draw_backtest_plots`

### `@confirm` 装饰器

`farm.py` 中的 `confirm` 装饰器会在执行删除或运行任务前提示 `[Y/N]` 二次确认，输入非 `y` 即中止，防止误操作。

## 业务模块层（src/module/）

| 文件 | 内容 |
| :--- | :--- |
| [operate_mod.py](../src/module/operate_mod.py) | `add_fund`/`delete_fund` 维护回测列表；`get_assets`/`update_assets` 处理持仓；`get_investments`/`update_investments` 处理定投；`record_history` 将当前持仓快照写入历史表 |
| [statistics_mod.py](../src/module/statistics_mod.py) | 按领域聚合数据：`get_fileds_position`、`get_fileds_profit`、`get_fileds_profit_rate`、`get_fileds_investment`；`get_filed_dataframe` 生成单领域基金明细 |
| [backtest_mod.py](../src/module/backtest_mod.py) | 定义抽象类 `AutomaticInvestmentPlan`（定投计划）与具体实现 `StupidPlan`；负责构造起始区间、处理发行日/数据缺失并调用算法 |
| [transport_mod.py](../src/module/transport_mod.py) | 使用 `multiprocessing.Pool` 多进程并发上传净值、更新基金信息、上传回测结果 |

## 算法层（src/algorithm/）

采用 **模板方法 + 抽象工厂** 风格：

- [algorithm.py](../src/algorithm/algorithm.py)：抽象基类 `Algorithm`。构造时加载基金名称与历史净值；`prepare_data(start, end)` 完成数据准备（校验交易日、截取买入区间、确定卖出净值）；声明抽象方法 `invest_weekly`。
- [stupid.py](../src/algorithm/stupid.py)：`StupidAlgorithm`，最朴素的定投策略 —— 每个交易日/每周固定一天投入固定金额（默认每期 1000）。实现 `invest_weekly`（返回周一至周五 5 个收益率）与 `invest_daily`（返回每日定投收益率）。

新增策略时，可继承 `Algorithm` 实现 `invest_weekly`，并在 `backtest_mod` 中新增对应的 `Plan`（工厂方法 `create_algo` 返回新算法）。详见 [回测与算法](./backtest.md)。

## 数据访问层（src/db/）

| 文件 | 内容 |
| :--- | :--- |
| [db_fund.py](../src/db/db_fund.py) | `Database` 类（**单例**），封装 SQLAlchemy engine/session，提供 `add`/`query`/`update`/`delete`/`to_df` 等通用操作，连接 `db_fund` |
| [db_netvalue.py](../src/db/db_netvalue.py) | `FundNetValue`，按基金代码映射到 `db_netvalue.tbl_<code>` 表，提供净值读写及发行日/最后日期属性 |
| [db_backtest.py](../src/db/db_backtest.py) | `FundBacktest`，按基金代码映射到 `db_backtest.tbl_<code>` 表，读写回测结果 |
| [tbl_assets.py](../src/db/tbl_assets.py) | `tbl_assets` 的 ORM 模型与查询方法 |
| [tbl_funds_for_backtest.py](../src/db/tbl_funds_for_backtest.py) | `tbl_funds_for_backtest` 的 ORM 模型与查询方法 |
| [tbl_investments.py](../src/db/tbl_investments.py) | `tbl_investments` 的 ORM 模型 |
| [tbl_history.py](../src/db/tbl_history.py) | `tbl_history` 的 ORM 模型 |

设计要点：

- `Database` 与 `Config` 都是单例，避免重复创建连接/读取配置。
- ORM 模型继承自 SQLAlchemy 的 declarative base，表结构与 [DDL_db_fund.sql](../sql/DDL_db_fund.sql) 对应。
- 净值库与回测库中每只基金一张表（`tbl_<6位代码>`），表在写入时通过 pandas `to_sql` 自动创建/替换。

## 可视化层（src/plot/）

| 文件 | 内容 |
| :--- | :--- |
| [statistics_plot.py](../src/plot/statistics_plot.py) | 个人数据图表：各领域持仓/收益/定投柱状图、持仓&收益对比图、持仓占比环形饼图等 |
| [aip_plot.py](../src/plot/aip_plot.py) | 回测可视化：核心为 `export_aip_violin_plot_by_filed` 按领域绘制小提琴图；另含若干箱型图/小提琴图比较函数 |

中文字体在 `farm.py` 顶部通过 `plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']` 配置。

## 工具层（src/util/）

| 文件 | 内容 |
| :--- | :--- |
| [config.py](../src/util/config.py) | `Config` 单例，读取 `config.yaml`（路径来自环境变量 `FARM_CONFIG_PATH`），以属性暴露配置项 |
| [log.py](../src/util/log.py) / [log.conf](../src/util/log.conf) | 基于 `logging.config.fileConfig` 的日志，输出到控制台与 `farm.log`（按大小轮转） |
| [chrome.py](../src/util/chrome.py) | `ChromeDriver`，用 Selenium 登录天天基金并抓取持仓、定投页面文本 |
| [tools.py](../src/util/tools.py) | `XAlphaTools`（基金信息）、`DateTools`（交易日/区间计算）、`SheetTools`（CSV 导出） |
| [industry_class.py](../src/util/industry_class.py) | 定义 8 个行业领域及其中英文名与配色 |
| [exceptions.py](../src/util/exceptions.py) | 自定义异常：`NonTradingError`、`FundNotFoundError` |

## 一次完整调用的数据流（以 backtest_job 为例）

```
chick.py -job backtest_job
  → Farmer.job_run("backtest_job")
    → Analyst.transport_netvalue
        → transport_mod.transport_netvalue_multiprocess（多进程）
            → XAlphaTools 取净值 → FundNetValue.to_sql（写 db_netvalue）
    → Analyst.backtest
        → transport_mod.transport_backtest_data_multiprocess
            → StupidPlan.analysis_realtime → StupidAlgorithm 计算
            → FundBacktest.to_sql（写 db_backtest）
    → Analyst.draw_backtest_plots
        → aip_plot.export_violin_plot_multiprocess
            → FundBacktest.read_sql → matplotlib 绘图并保存
```
