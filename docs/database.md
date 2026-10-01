# 数据库设计

ChickenFarm 使用三个相互独立的 MySQL 数据库，分别承载**个人统计数据**、**基金历史净值**与**回测结果**。

## 数据库总览

| 数据库 | 是否预建表 | 写入方式 | 内容 |
| :--- | :--- | :--- | :--- |
| `db_fund` | 是，执行 [DDL_db_fund.sql](../sql/DDL_db_fund.sql) | SQLAlchemy ORM | 个人持仓、定投计划、回测基金列表、历史快照 |
| `db_netvalue` | 否 | pandas `to_sql` 自动建表 | 每只基金一张净值表 |
| `db_backtest` | 否 | pandas `to_sql` 自动建表 | 每只基金一张回测结果表 |

库名通过 [config.yaml](../config.yaml) 的 `DB_FUND` / `DB_NETVALUE` / `DB_BACKTEST` 配置，不要求与本文示例同名。

## db_fund：个人统计数据库

该库包含 4 张表，对应 ORM 模型位于 [src/db/](../src/db/)。

### tbl_assets —— 基金最新数据

保存每只基金当前的持仓与收益，主键为基金代码。对应 [tbl_assets.py](../src/db/tbl_assets.py)。

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `name` | varchar(255) | 基金名称（非空、唯一） |
| `code` | char(6) | 基金代码（主键） |
| `filed` | varchar(255) | 所属领域 |
| `position` | decimal(10,2) | 当前持仓金额 |
| `netvalue` | decimal(10,4) | 最新单位净值 |
| `profit` | decimal(10,2) | 收益金额 |
| `profit_rate` | decimal(5,4) | 收益率 |
| `update_time` | datetime | 更新时间（自动更新） |
| `create_time` | datetime | 创建时间 |
| `comment` | varchar(255) | 备注 |
| `buy_rate` | decimal(5,4) | 买入费率 |
| `sell_rate_info` | varchar(255) | 卖出费率信息 |
| `url` | varchar(255) | 数据来源链接 |

### tbl_funds_for_backtest —— 回测基金列表

维护需要参与回测的基金清单。对应 [tbl_funds_for_backtest.py](../src/db/tbl_funds_for_backtest.py)。

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `name` | varchar(255) | 基金名称（非空、唯一） |
| `code` | char(6) | 基金代码（主键） |
| `filed` | varchar(255) | 所属领域 |
| `update_time` | datetime | 更新时间 |
| `create_time` | datetime | 创建时间 |
| `comment` | varchar(255) | 备注 |
| `buy_rate` | decimal(5,4) | 买入费率 |
| `sell_rate_info` | varchar(255) | 卖出费率信息 |
| `url` | varchar(255) | 数据来源链接 |

> 该表是回测流水线的“驱动表”：程序读取其中的全部代码，逐只抓取净值并回测。

### tbl_investments —— 定投计划

保存天天基金上的定投计划。对应 [tbl_investments.py](../src/db/tbl_investments.py)。

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `name` | varchar(255) | 基金名称（非空、唯一） |
| `code` | char(6) | 基金代码（主键） |
| `amount` | decimal(10,2) | 每期扣款金额 |
| `period` | varchar(255) | 扣款周期（如“每周”） |
| `data` | varchar(255) | 扣款日期（如“星期一”） |
| `state` | varchar(255) | 计划状态（如“正常”/“已暂停”） |
| `update_time` | datetime | 更新时间 |
| `create_time` | datetime | 创建时间 |

### tbl_history —— 历史快照

每次执行 `-record` 时追加一条各基金的持仓/净值/收益快照，用于历史回溯。对应 [tbl_history.py](../src/db/tbl_history.py)。

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `id` | bigint unsigned | 自增主键 |
| `code` | char(6) | 基金代码 |
| `position` | decimal(10,2) | 持仓金额 |
| `netvalue` | decimal(10,4) | 单位净值 |
| `profit` | decimal(10,2) | 收益金额 |
| `profit_rate` | decimal(5,4) | 收益率 |
| `record_time` | datetime | 记录时间 |

## db_netvalue：历史净值数据库

无需预建表。每只基金对应一张名为 `tbl_<code>` 的表（例如 `tbl_005827`），由
[FundNetValue.to_sql](../src/db/db_netvalue.py) 通过 pandas 写入（`if_exists='replace'`，即每次整表替换）。

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `date` | DateTime | 净值日期 |
| `netvalue` | DECIMAL(10,4) | 单位净值 |
| `totvalue` | DECIMAL(10,4) | 累计净值 |

`FundNetValue` 还提供两个便捷属性：

- `release_date`：表中第一条记录的日期（基金发行/数据起始日）。
- `last_date`：表中最后一条记录的日期（数据截止日）。

## db_backtest：回测结果数据库

无需预建表。每只基金对应一张 `tbl_<code>` 表，由
[FundBacktest.to_sql](../src/db/db_backtest.py) 写入。字段如下：

| 字段 | 类型 | 含义 |
| :--- | :--- | :--- |
| `start` | VARCHAR(64) | 本次回测的定投起始日 |
| `week` | INT | 定投的星期：1~5 表示周一至周五；`-1` 表示每日定投 |
| `algorithm` | VARCHAR(64) | 使用的算法名称（如 `stupid`） |
| `cycle` | INT | 投资周期（天数，如 180/365/730） |
| `profit_rate` | DECIMAL(5,4) | 回测收益率 |
| `test_date` | DateTime | 回测执行时间 |

回测数据如何生成、字段如何使用，见 [回测与算法](./backtest.md)。

## 表关系示意

```
db_fund
├── tbl_funds_for_backtest (回测清单, code)
│        │ 读取全部 code
│        ├──────────────► db_netvalue.tbl_<code>   (历史净值)
│        └──────────────► db_backtest.tbl_<code>   (回测结果)
├── tbl_assets            (最新持仓/收益, code)
│        │ -record 快照
│        └──────────────► tbl_history (按 code 关联, 追加历史)
└── tbl_investments       (定投计划, code)
```

## 连接与并发注意事项

- ORM 访问通过单例 [Database](../src/db/db_fund.py) 复用同一个 engine/session。
- 净值/回测写入采用多进程并发，每个进程创建独立连接，因此需要适当调高 MySQL
  `max_connections`（建议 500）。
- 回测写入使用 `if_exists='replace'` 整表替换；使用 `append` 在高频写入时容易导致连接数耗尽。
