"""
ChickenFarm 定投回测 CLI。

在仓库根目录直接运行（无需配置 PYTHONPATH）：
    python chick.py -add -c 005827
    python chick.py -job backtest_job
    uv run chick.py -plots
"""
import sys
import argparse
from termcolor import colored
from argparse import RawTextHelpFormatter

from src.farm import Farmer


farmer = Farmer()


def main():
    parser = argparse.ArgumentParser(description=f"欢迎进入养鸡场（定投回测）(*^_^*)",
                                     formatter_class=RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-add',
                       action='store_true',
                       help='向「回测列表」中「添加」基金')
    group.add_argument('-delete',
                       action='store_true',
                       help='向「回测列表」中「删除」基金')
    group.add_argument('-fetch',
                       action='store_true',
                       help='采集行情：场外基金历史净值 + ETF 前复权日线，为回测提供数据')
    group.add_argument('-backtest',
                       action='store_true',
                       help='回测，并将回测数据上传')
    group.add_argument('-plots',
                       dest='plots',
                       action='store_true',
                       help='绘制各领域基金回测的小提琴图')
    group.add_argument('-job',
                       dest='job',
                       help="执行定制工作：backtest_job（采集 → 回测 → 绘图）")

    parser.add_argument('-c', '--code',
                        dest='code',
                        help="基金代码")

    args = parser.parse_args()

    if args.job:
        farmer.job_run(args.job)
        return 0

    if args.add or args.delete:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1

    if args.add:
        farmer.operator.add(args.code)
    elif args.delete:
        farmer.operator.delete(args.code)
    elif args.fetch:
        farmer.analyst.fetch()
    elif args.backtest:
        farmer.analyst.backtest()
    elif args.plots:
        farmer.analyst.draw_backtest_plots()

    return 0


if __name__ == '__main__':
    sys.exit(main())
