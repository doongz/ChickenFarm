<h1 align="center">
  <br>
  <a href="https://github.com/WalleDong/ChickenFarm"><img src="https://github.com/WalleDong/ChickenFarm/raw/main/docs/images/logo.png" alt="Chicken Farm"></a>
</h1>
<h4 align="center">养鸡，我们是专业的</h4>

<p align="center">
    <a href="https://github.com/ArmynC/ArminC-AutoExec/commits/master">
    <img src="https://img.shields.io/github/last-commit/ArmynC/ArminC-AutoExec.svg?style=flat-square&logo=github&logoColor=white"
         alt="GitHub last commit">
    <a href="https://github.com/ArmynC/ArminC-AutoExec/issues">
    <img src="https://img.shields.io/github/issues-raw/ArmynC/ArminC-AutoExec.svg?style=flat-square&logo=github&logoColor=white"
         alt="GitHub issues">
    <a href="https://github.com/ArmynC/ArminC-AutoExec/pulls">
    <img src="https://img.shields.io/github/issues-pr-raw/ArmynC/ArminC-AutoExec.svg?style=flat-square&logo=github&logoColor=white"
         alt="GitHub pull requests">
    <a href="https://twitter.com/intent/tweet?text=Try this CS:GO AutoExec:&url=https%3A%2F%2Fgithub.com%2FArmynC%2FArminC-AutoExec">
    <img src="https://img.shields.io/twitter/url/https/github.com/ArmynC/ArminC-AutoExec.svg?style=flat-square&logo=twitter"
         alt="GitHub tweet">
</p>

<p align="center">
  <a href="#about">About</a> •
  <a href="#installation">Installation</a> •
  <a href="#updating">Updating</a> •
  <a href="#features">Features</a> •
  <a href="#binds">Binds</a> •
  <a href="#wiki">Wiki</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#credits">Credits</a> •
  <a href="#support">Support</a> •
  <a href="#license">License</a>
</p>

---



零、请自备数据库

一、初次使用需要添加环境变量
echo "export PYTHONPATH=$PYTHONPATH:/Users/zhangdong/Desktop" >> ~/.bash_profile
echo "export FARM_CONFIG_PATH=" >> ~/.bash_profile
source ~/.bash_profile


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


TODO:
3、掌握目标止盈等投资算法后，全部使用人肉定投
4、readme



