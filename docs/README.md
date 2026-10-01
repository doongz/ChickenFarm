# ChickenFarm 文档

> 一家小小的养鸡场 —— 个人基金投资管理与定投回测工具

ChickenFarm 是一个用 Python 编写的个人基金（“养鸡”）管理工具。它能够自动采集天天基金的购买记录与最新持仓、爬取基金历史净值、统计个人各领域的投入/持仓/收益，并使用多种定投算法进行历史回测，最终生成投资策略与可视化图表。

> 注意：本项目及文档仅用于个人学习与研究，不构成任何投资建议。

## 功能一览

- **全自动数据采集**：通过 Selenium 登录天天基金，抓取最新持仓（资产）与定投计划。
- **净值爬取**：基于 `xalpha` 获取基金历史单位净值与累计净值，落库存储。
- **个人数据分析**：按行业领域统计持仓、收益、收益率，并导出 CSV 表格与图表。
- **定投回测分析**：在多个时间跨度（30/60/90/180/365/730 天）上回测周定投/日定投，绘制小提琴图辅助择时与选基。

## 文档索引

| 文档 | 内容 |
| :--- | :--- |
| [快速开始](./getting-started.md) | 环境准备、数据库初始化、配置与安装依赖、第一个任务 |
| [架构设计](./architecture.md) | 目录结构、分层架构、核心角色与调用关系 |
| [命令行手册](./cli.md) | `chick.py` 全部命令参数与预置任务说明 |
| [数据库设计](./database.md) | 三个数据库及各表结构、字段含义 |
| [回测与算法](./backtest.md) | 定投算法原理、回测流程、小提琴图解读 |

## 技术栈

- **语言**：Python 3.12（兼容 3.10+）
- **数据处理**：pandas、numpy
- **数据源**：xalpha、akshare
- **数据采集**：Selenium + ChromeDriver
- **数据库**：MySQL（PyMySQL 驱动 + SQLAlchemy ORM）
- **可视化**：matplotlib
- **交易日历**：chinesecalendar
- **配置**：PyYAML（`config.yaml`）

## 项目布局

```
ChickenFarm/
├── chick.py               # CLI 入口
├── config.yaml            # 配置文件（数据库、账号、导出路径）
├── requirements.txt       # 依赖清单
├── sql/
│   └── DDL_db_fund.sql    # db_fund 建表脚本
├── docs/                  # 项目文档（本目录）
└── src/
    ├── farm.py            # 核心角色（Farmer/Operator/Statistician/Analyst）
    ├── algorithm/         # 定投算法
    ├── db/                # 数据库连接与表模型
    ├── module/            # 业务模块（操作/统计/回测/传输）
    ├── plot/              # 绘图（个人统计、回测小提琴图）
    └── util/              # 工具（配置、日志、浏览器、日期等）
```

下一步请阅读 [快速开始](./getting-started.md)。
