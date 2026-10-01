# 命令行手册

ChickenFarm 通过项目根目录的 [chick.py](../chick.py) 提供命令行界面（CLI）。

## 基本用法

```shell
python3 chick.py [命令] [-c 基金代码] [-a 数额]
```

> 所有主命令位于同一个**互斥参数组**中，一次只能执行其中一个。
> 使用 uv 时可写为 `uv run chick.py ...`。

查看帮助：

```shell
python3 chick.py -h
```

## 通用参数

| 参数 | 说明 |
| :--- | :--- |
| `-c`, `--code` | 基金代码（6 位），配合 `-add` / `-delete` 使用 |
| `-a`, `--amount` | 数额（预留参数） |

## 命令一览

### 基金与操作

| 命令 | 说明 |
| :--- | :--- |
| `-add -c <code>` | 向「回测基金列表」添加基金；运行后按提示选择所属领域 |
| `-delete -c <code>` | 从「回测基金列表」删除基金（执行前需 `Y` 确认） |
| `-update` | 从天天基金抓取最新资产（持仓）与定投数据，更新至数据库 |

### 个人数据分析

| 命令 | 说明 |
| :--- | :--- |
| `-record` | 记录当前各基金的持仓、净值、收益、收益率到历史表 |
| `-tables` | 导出最新数据总表、回测基金表、历史记录表为 CSV |
| `-charts` | 绘制个人数据图表并保存 |
| `-show` | 在终端打印各领域持仓基金明细并展示图表 |

### 回测分析

| 命令 | 说明 |
| :--- | :--- |
| `-netvalue` | 更新基金历史净值（写入 `db_netvalue`），为回测提供数据 |
| `-backtest` | 运行回测并将结果写入 `db_backtest` |
| `-plots` | 绘制各领域基金回测的小提琴图并保存 |

### 预置任务

| 命令 | 说明 |
| :--- | :--- |
| `-job base_job` | 一键执行个人数据分析流水线（执行前需 `Y` 确认） |
| `-job backtest_job` | 一键执行回测分析流水线（执行前需 `Y` 确认） |

## 使用示例

添加一只基金到回测列表（选择领域，`0` 表示 None）：

```shell
python3 chick.py -add -c 005827
```

删除回测列表中的基金：

```shell
python3 chick.py -delete -c 005827
```

仅更新历史净值：

```shell
python3 chick.py -netvalue
```

仅运行回测（依赖已上传的净值数据）：

```shell
python3 chick.py -backtest
```

仅绘制回测小提琴图：

```shell
python3 chick.py -plots
```

一键回测流水线（净值 → 回测 → 绘图）：

```shell
python3 chick.py -job backtest_job
```

一键个人数据流水线（采集 → 记录 → 表格 → 图表）：

```shell
python3 chick.py -job base_job
```

## 典型执行顺序

**首次回测一只新基金：**

```shell
python3 chick.py -add -c 005827     # 只需添加一次
python3 chick.py -job backtest_job  # 后续可反复运行，更新数据与图表
```

**每周个人数据复盘：**

```shell
python3 chick.py -job base_job
```

## 退出码

- `0`：正常执行完成。
- `-1`：缺少必要参数（如 `-add` / `-delete` 未提供 `-c` 基金代码）。
