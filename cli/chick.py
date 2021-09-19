import os
import sys
import argparse
import pandas as pd
from termcolor import colored
from argparse import RawTextHelpFormatter

from ChickenFarm.src.farm import Farmer, Slave

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)

key = os.getenv('OPERATION_KEY', None)
farmer = Farmer()
slave = Slave(key)
farmer.slave = slave


def confirm(func):

    def wrapper(*args, **kwargs):
        answer = input("Are you sure you want to perform this operation [Y/N]?\n: ").lower()
        if answer != 'y':
            print(colored("Aborted", "red"))
            sys.exit(0)
        func(*args, **kwargs)

    return wrapper


@confirm
def add(code):
    slave.add(code)
    

@confirm
def delete(code):
    slave.delete(code)
    

@confirm
def buy(code, amount):
    slave.buy(code, amount)


@confirm
def sell(code, amount):
    slave.sell(code, amount)


@confirm
def position(code, amount):
    slave.update_position(code, amount)
    

def show(code):
    slave.show(code)


@confirm
def record_op():
    slave.record_op()
    slave.job.run()


@confirm
def position_auto():
    slave.update_position_auto()
    slave.job.run()


def record_history():
    slave.record_history()
    slave.job.run()


def tables():
    slave.export_tables()
    slave.job.run()


def charts():
    slave.draw_charts()
    slave.job.run()


@confirm
def netvalue():
    slave.transport_netvalue()
    slave.job.run()


@confirm
def backtest():
    slave.backtest()
    slave.job.run()


@confirm
def backtest_plot():
    slave.draw_backtest_plot()
    slave.job.run()


@confirm
def job_run(job):
    if job == "base_job":
        farmer.base_job()
    elif job == "backtest_job":
        farmer.backtest_job()
    else:
        print(colored(f"输入的任务 {job} 无效", "red"))
        return
    slave.job.run()


def main():
    parser = argparse.ArgumentParser(description=f"欢迎进入养鸡场 (*^_^*)",
        formatter_class=RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-add',
                       action='store_true',  
                       help='添加基金')
    group.add_argument('-delete',
                       action='store_true',  
                       help='删除基金')
    group.add_argument('-buy',
                       action='store_true',  
                       help='买入基金')
    group.add_argument('-sell',
                       action='store_true',  
                       help='卖出基金')
    group.add_argument('-position', 
                       action='store_true',  
                       help='更新单个基金的持仓')
    group.add_argument('-show', 
                       action='store_true',  
                       help='展示基金数据')
    group.add_argument('-record-op',
                       dest='record_op', 
                       action='store_true',  
                       help='从天天基金获取数据，自动将买入、卖出添加至数据库中')
    group.add_argument('-position-auto',
                       dest='position_auto', 
                       action='store_true',  
                       help='从天天基金获取持仓数据，更新至数据库中')

    group.add_argument('-record-history',
                       dest='record_history', 
                       action='store_true',  
                       help='统计并记录各个领域以及总的投入、持仓、收益历史')
    group.add_argument('-tables',
                       action='store_true',  
                       help='导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表')
    group.add_argument('-charts',
                       action='store_true',  
                       help='绘制个人数据图表')

    group.add_argument('-netvalue',
                       action='store_true',  
                       help='更新基金历史净值数据')
    group.add_argument('-backtest',
                       action='store_true',  
                       help='回测，并将回测数据上传')
    group.add_argument('-backtest-plot',
                       dest='backtest_plot', 
                       action='store_true',  
                       help='绘制各领域基金回测的小提琴图')

    group.add_argument('-job',
                       dest='job',
                       help="执行定制工作")

    parser.add_argument('-c', '--code',
                        dest='code',
                        help="基金代码")
    parser.add_argument('-a', '--amount',
                        dest='amount',
                        help="数额")

    args = parser.parse_args()


    if args.job:
        job_run(args.job)
        return 0

    if args.buy or args.sell or args.position:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1
        if not args.amount:
            print(colored(f"请输入数额 -a", "red"))
            return -1
    if args.add or args.delete or args.show:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1

    if args.add:
        add()
    elif args.delete:
        delete()
    elif args.buy:
        buy(args.code, args.amount)
    elif args.sell:
        sell(args.code, args.amount)
    elif args.position:
        position(args.code, args.amount)
    elif args.show:
        show(args.code)
    elif args.record_op:
        record_op()
    elif args.position_auto:
        position_auto()

    elif args.record_history:
        record_history()
    elif args.tables:
        tables()
    elif args.charts:
        charts()

    elif args.netvalue:
        netvalue()
    elif args.backtest:
        backtest()
    elif args.backtest_plot:
        backtest_plot()

    return 0


if __name__ == '__main__':
    sys.exit(main())

