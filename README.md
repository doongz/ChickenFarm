<h1 align="center">
  <br>
  <a href="https://github.com/WalleDong/ChickenFarm"><img src="https://github.com/WalleDong/ChickenFarm/raw/main/docs/images/logo.png" alt="Chicken Farm"></a>
</h1>
<h4 align="center">一家小小的养鸡场
    <a >
      <img alt="Chat" src="https://img.shields.io/badge/Chat%20on-Wechat-green?logo=wechat&style=social" />
    </a>
</h4>


<p align="center">
    <a>
      <img alt="env" src="https://img.shields.io/badge/macOS-passing-green?logo=apple" />
    </a>
    <a>
      <img alt="Python" src="https://img.shields.io/badge/Python-3.7-blue?logo=python&logoColor=white" />
    </a>
    <a href="https://github.com/WalleDong/ChickenFarm/graphs/commit-activity">
      <img alt="commit-activity" src="https://img.shields.io/github/last-commit/WalleDong/ChickenFarm.svg?logo=github&logoColor=white" />
    </a>
    <a href="https://github.com/WalleDong/ChickenFarm/issues">
      <img alt="Issues" src="https://img.shields.io/github/issues/WalleDong/ChickenFarm?style=flat&color=%23FFA24E&label=Issues&logo=github" />
    </a>
  </p>


<p align="center">
  <a href="#Features">Features</a> •
  <a href="#Installation">Installation</a> •
  <a href="#Usage">Usage</a> •
  <a href="#TODO">TODO</a> •
  <a href="#Contribute">Contribute</a> •
  <a href="#License">License</a>
</p>


  在养鸡场里面，农场主指挥着工人们记录各项操作记录、统计农场里的各项数据、利用各种算法进行回测分析


# Features

- [x] 个人数据统计
- [x] 回测分析
- [ ] 详细设计

# Installation

零、请自备数据库

一、初次使用需要添加环境变量
echo "export PYTHONPATH=$PYTHONPATH:/Users/zhangdong/Desktop" >> ~/.bash_profile
echo "export FARM_CONFIG_PATH=" >> ~/.bash_profile
source ~/.bash_profile

# Usage

二、新买一个基金需要将基金的历史数据上传至数据库中
1、将基金代码写入 position.csv 中
2、执行                    python cronjob.py 


三、每周末需要做

1、手动处理支付宝里卖的
2、填写支付宝里的持仓，填写csv
3、一键更新


1、更新净值数据库(一键)                         python cli/farm.py -n                   
2、将本周的交易记录下来   
  0) 先把支付宝里卖的手动处理，填写csv后                
  1) 自动记录本周交易操作                       python cli/farmer.py -roa
  2) 自动记录最新持仓                           python cli/farmer.py -pa
被选:

    1）处理加仓，一条一条基金执行                   python cli/farmer.py -b -c <code> -a <amount>
    2）处理卖出，一条一条基金执行                   python cli/farmer.py -s -c <code> -a <amount>
    3）更新持仓，现将基金的最新持仓维护至 position.csv 中，然后运行  python cli/farmer.py -pl              
3、统计并记录本周各个领域的投入、持仓、收益(一键)    python cli/farmer.py -record
4、导出个人数据统计表(一键)                       python cli/farmer.py -tables
5、导出个人数据统计图(一键)                       python cli/farmer.py -charts                 
6、更新回测分析数据(一键)                        python cli/farmer.py -bt
7、导出回测分析图表(一键)                        python cli/farmer.py -draw


# TODO
3、掌握目标止盈等投资算法后，全部使用人肉定投
4、readme

# Contribute

Contributions are always welcome!
Please read the [contribution guidelines](https://github.com/WalleDong/ChickenFarm/blob/main/docs/contribution.md).:relaxed:

# License

[![License](https://img.shields.io/github/license/WalleDong/ChickenFarm?color=blue&label=License)](https://github.com/WalleDong/ChickenFarm/blob/main/LICENSE)

Copyright @ [Walle Dong](https://github.com/WalleDong)