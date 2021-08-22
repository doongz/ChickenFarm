import os
import sys
import logging
import requests
import argparse
import threading
import getpass
import time
from termcolor import colored
from argparse import RawTextHelpFormatter

from chicken_farm.src.employees import Jober
from chicken_farm.src.employees import Operator
from chicken_farm.src.employees import Statistician
from chicken_farm.src.employees import Analyst

key = os.getenv('OPERATION_KEY', None)
jober = Jober(key)
operator = Operator(key)
statistician = Statistician(key)
analyst = Analyst(key)

# def progbar(curr, total, full_progbar):
#     frac = float(curr) / float(total)
#     filled_progbar = int(round(frac * full_progbar))
#     if curr != total:
#         print('|',
#             '#' * filled_progbar + '-' * (full_progbar - filled_progbar),
#             end='\r', file=sys.stderr)
#     else:
#         print(' ', ' ' * full_progbar, end='\r', file=sys.stderr)
#     sys.stderr.flush()


# progbar_event = threading.Event()

# def progbar_thread():
#     for i in range(0, 59):
#         if progbar_event.is_set():
#             progbar(60, 60, 60)
#             break
#         progbar(i, 60, 60)
#         time.sleep(0.5)

def confirm(func):

    def wrapper(*args, **kwargs):
        answer = input("Are you sure you want to perform this operation [Y/N]?\n: ").lower()
        if answer != 'y':
            print(colored("Aborted", "red"))
            sys.exit(0)
        func(*args, **kwargs)

    return wrapper


def netvalue():
    successes, fails = statistician.transport_netvalue()
    print(colored(f"上传基金历史净值成功 {len(successes)} 条。", "green"))
    if len(fails) != 0:
        print(colored(f"上传基金历史净值失败 {len(fails)} 条。", "red"))


@confirm
def buy(code, amount):
    operator.buy(code, amount)
    print(colored(f"{code} 买入 {amount} ¥。", "green"))


@confirm
def sell(code, amount):
    operator.sell(code, amount)
    print(colored(f"{code} 卖出 {amount} ¥。", "green"))


@confirm
def position(code, amount):
    operator.update_position(code, amount)
    print(colored(f"{code} 更新持仓为 {amount} ¥。", "green"))


@confirm
def position_list():
    latest_position = operator.update_position_list()
    for code, position in latest_position:
        print(colored(f"{code} 更新持仓为 {position} ¥。", "green"))


def show(code):
    fund_dpt = operator.get_dpt(code)
    for key, value in fund_dpt.items():
        print(colored(f"{key}: {value}", "green"))


def record_history():
    statistician.record_history()


def export_tables():
    statistician.export_tables()

def draw_charts():
    statistician.draw_charts()

def backtest():
    analyst.backtest()

def draw_backtest_plot():
    analyst.draw_backtest_plot()


def main():
    parser = argparse.ArgumentParser(description=f"",
        formatter_class=RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', '--netvalue', 
                       action='store_true',  
                       help='更新基金历史净值数据')
    group.add_argument('-b', '--buy', 
                       action='store_true',  
                       help='买入基金')
    group.add_argument('-s', '--sell', 
                       action='store_true',  
                       help='卖出基金')
    group.add_argument('-p', '--position', 
                       action='store_true',  
                       help='更新持仓 单个基金')
    group.add_argument('-pl', '--position-list', 
                       dest='position_list', 
                       action='store_true',  
                       help='读取 position.csv 中基金的最新持仓，并更新持仓')
    group.add_argument('-show', '--show', 
                       action='store_true',  
                       help='展示基金存储')
    group.add_argument('-record', '--record-history', 
                       dest='record_history', 
                       action='store_true',  
                       help='统计并记录各个领域以及总的投入、持仓、收益历史')
    group.add_argument('-tables', '--export-tables', 
                       dest='export_tables', 
                       action='store_true',  
                       help='导出基金最新数据总表、每个领域合计表、历史购买表、历史仓位表、历史收益表')
    group.add_argument('-charts', '--draw-charts', 
                       dest='draw_charts', 
                       action='store_true',  
                       help='绘制图表')
    group.add_argument('-bt', '--backtest', 
                       dest='backtest', 
                       action='store_true',  
                       help='回测，并将回测数据上传')
    group.add_argument('-draw', '--draw-plot', 
                       dest='draw_backtest_plot', 
                       action='store_true',  
                       help='绘制各领域基金回测的小提琴图')


    parser.add_argument('-c', '--code',
                        dest='code',
                        help="基金代码")
    parser.add_argument('-a', '--amount',
                        dest='amount',
                        help="数额")

    args = parser.parse_args()


    if args.buy or args.sell or args.position:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1
        if not args.amount:
            print(colored(f"请输入数额 -a", "red"))
            return -1
    if args.show:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1

    if args.netvalue:
        netvalue()
    elif args.buy:
        buy(args.code, args.amount)
    elif args.sell:
        sell(args.code, args.amount)
    elif args.position:
        position(args.code, args.amount)
    elif args.position_list:
        position_list()
    elif args.show:
        show(args.code)
    elif args.record_history:
        record_history()
    elif args.export_tables:
        export_tables()
    elif args.draw_charts:
        draw_charts()
    elif args.backtest:
        backtest()
    elif args.draw_backtest_plot:
        draw_backtest_plot()

    return 0


if __name__ == '__main__':
    sys.exit(main())

