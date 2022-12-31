<h1 align="center">
  <br>
  <a href="https://github.com/WalleDong/ChickenFarm"><img src="./docs/images/logo.png" alt="Chicken Farm"></a>
</h1>
<h4 align="center">一家小小的养鸡场 </h4>

<p align="center">
    <a>
      <img alt="env" src="https://img.shields.io/badge/macOS-passing-green?logo=apple" />
    </a>
    <a>
      <img alt="Python" src="https://img.shields.io/badge/Python-3.9-blue?logo=python&logoColor=white" />
    </a>
    <a href="https://github.com/dowalle/ChickenFarm/graphs/commit-activity">
      <img alt="commit-activity" src="https://img.shields.io/github/last-commit/dowalle/ChickenFarm.svg?logo=github&logoColor=white" />
    </a>
    <a href="https://github.com/dowalle/ChickenFarm/issues">
      <img alt="Issues" src="https://img.shields.io/github/issues/dowalle/ChickenFarm?style=flat&color=6A5EF6&label=Issues&logo=github" />
    </a>
    <a href="https://github.com/dowalle/ChickenFarm/pulls">
      <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/dowalle/ChickenFarm?color=0088ff&logo=github" />
    </a>
    <a>
      <img alt="stars" src="https://img.shields.io/github/stars/dowalle/ChickenFarm?color=E3BA3E&logo=github" />
    </a>
    <a>
      <img alt="forks" src="https://img.shields.io/github/forks/dowalle/ChickenFarm?color=5EEDF6&logo=github" />
    </a>
  </p>
<p align="center">
  <a href="#Features">Features</a> •
  <a href="#Installation">Installation</a> •
  <a href="#Usage">Usage</a> •
  <a href="#Todo">Todo</a> •
  <a href="#Contribute">Contribute</a> •
  <a href="#Community">Community</a> •
  <a href="#License">License</a>
</p>

非专业养鸡场:hatching_chick::hatched_chick::baby_chick:，统计购买和卖出操作，分析持仓和收益，爬取基金净值，使用各种定投算法回测分析，生成投资策略 :chart_with_upwards_trend::chart_with_upwards_trend::chart_with_upwards_trend:

## Todo

计划进行重构，特性：

- 定投导致成本和收益计算错误
- 定投回测分析参考 xalpha 内置的 backtest
- 完善全量系统测试 python chick.py -job base_job && python chick.py -job backtest_job

tbl_assets 存储最新信息，里面的基金由页面上的自动采集（采集后需要手动配置领域，才能展示）
tbl_fund_history 存储每个基金的历史信息
tbl_operation_record 记录的一些操作


tbl_funds_for_backtest 专门为回测使用，需要手动往里面添加


## Features
- 全自动数据采集（天天基金购买记录、最新持仓采集）
- 爬取最新基金净值
- [个人数据分析](#个人数据统计图)
- [定投回测分析](#定投分析图)

## Installation

> 本项目，想要部署、调通是有一定难度的。

### 0、准备 Mysql 数据库
- 推荐 [阿里云](https://cn.aliyun.com/product/rds/mysql)，一年19.9，阿里云打:moneybag:
- 数据库 **db_fund** 使用[sql文件](./sql/DDL_db_fund.sql)整库建表
- 数据库 **db_netvalue** 库名保持一致，无需建表
- 数据库 **db_backtest** 库名保持一致，无需建表

### 1、填写配置表
将 [配置表(farmConfig.json)](./farmConfig.json) 移动到项目目录外，按照注释填写配置表。**该表涉及账号密码，请勿提交此表！！！**

### 2、配置环境变量
```shell
echo "export PYTHONPATH=$PYTHONPATH:<项目所在的父目录>" >> ~/.bash_profile
echo "export FARM_CONFIG_PATH=<配置表(farmConfig.json)路径>" >> ~/.bash_profile
source ~/.bash_profile
```

### 3、安装依赖包
```shell
python3 -m pip install -r requirements.txt
```
## Usage

### 回测

1. 添加基金

```shell
python3 chick.py -add -c <code>
```

2. 执行回测分析任务

```shell
python3 chick.py -job backtest_job
```

### 个人数据分析

```shell
python3 chick.py -job base_job
```


### 二、CLI

```shell
python3 chick.py
```

#### 1、操作

| command                         | help                                           |
| :------------------------------ | :--------------------------------------------- |
| -add -c `code`                  | 添加基金                                       |
| -delete -c `code`               | 删除基金                                       |
| -show                           | 展示指定领域基金数据                           |
| -show -c `code`                 | 展示指定基金数据                               |
| -assets            | 从天天基金获取最新资产数据，更新至数据库中         |

#### 2、个人数据分析

| command         | help                                                         |
| :-------------- | :----------------------------------------------------------- |
| -record | 统计并记录各个领域以及总的投入、持仓、收益历史               |
| -tables         | 导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表 |
| -charts         | 绘制个人数据图表                                             |

#### 3、回测分析

| command         | help                         |
| :-------------- | :--------------------------- |
| -netvalue       | 更新基金历史净值数据         |
| -backtest       | 回测，并将回测数据上传       |
| -backtest-plots | 绘制各领域基金回测的小提琴图 |

#### 4、执行任务

```shell
python chick.py -job base_job
```

1. 更新本周的操作记录，
2. 更新本周所有基金的持仓
3. 统计并记录本周各个领域的投入、持仓、收益
4. 导出个人数据统计表
5. 导出个人数据统计图

```shell
python chick.py -job backtest_job
```

1. 把基金的历史净值上传至 db_netvalue 数据库中
2. 更新回测分析数据
3. 导出回测分析图表

### 三、个人数据统计

- 各领域最新持仓图
- 各领域持仓占比图
- 各领域最新收益图
- 各领域最新收益率图
- 各领域最新持仓 & 收益图

![personal_data_statistics](./docs/images/1.png)

### 四、定投分析

> 下面实现的定投方法，仅为一种「最简单的思路」，抛砖引玉
>

选择一周中的固定一天（周一至周五），每周以固定的资金进行买入，在近半年、近一年、近三年的时间跨度进行定投回测，回测结果绘制出小提琴图。

- 每一行，为一个基金的180天、365天、1095天区间的回测分析
- 每一列，为一类基金的相同天数回测分析，**可判断不同基金的定投收益**
- 子图为一周五天的小提琴图，中间横线为中位数，上、下端横线为极值，**可分析选择周内的哪一天定投收益高**
- 小提琴图中宽的地方为概率密度大的地方，也就是多数样本分布的地方，也就是**最有可能获得的收益率**

注：定投的起点，也就是开始定投的日子对最终的收益有很大的影响。所以，并没有直接用距今天180天前的那一天开始算单一结果，而是取距今天180天前那一天的「附近区间的多个起点」，统计出多个样本来绘制「Violin Plot」。

例：白酒和半导体的一些基金回测分析

![aip_backtest](./docs/images/2.png)

![aip_backtest](./docs/images/3.png)

按照策略进行的实际定投情况，大多数买在了相对较低的点上

<img src="./docs/images/实际定投.png" alt="实际定投" style="zoom:60%;" />

## Todo

计划进行重构，特性：

- 极简使用，甚至无需本地算力；
- 无需申请数据库，使用本地 splite；
- 支持回测分析，不在兼容个人数据统计；

## Contribute

Contributions are always welcome!
Please read the [contribution guidelines](https://github.com/WalleDong/ChickenFarm/blob/main/docs/contribution.md).:relaxed:

## Community

[![Chat](https://img.shields.io/badge/Chat%20on-Wechat-green?logo=wechat&style=social)](./docs/images/wechat.JPG)

## License

[![License](https://img.shields.io/github/license/WalleDong/ChickenFarm?color=blue&label=license)](https://github.com/WalleDong/ChickenFarm/blob/main/LICENSE)

Copyright © 2022 [Do Walle](https://github.com/dowalle). All rights reserved.
