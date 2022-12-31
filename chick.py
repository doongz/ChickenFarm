import sys
import argparse
from termcolor import colored
from argparse import RawTextHelpFormatter

from ChickenFarm.src.farm import Farmer


farmer = Farmer()


def main():
    parser = argparse.ArgumentParser(description=f"欢迎进入养鸡场 (*^_^*)",
                                     formatter_class=RawTextHelpFormatter)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-add',
                       action='store_true',
                       help='向「回测列表」中「添加」基金')
    group.add_argument('-delete',
                       action='store_true',
                       help='向「回测列表」中「删除」基金')
    group.add_argument('-netvalue',
                       action='store_true',
                       help='更新基金「历史净值」，为回测提供数据')
    group.add_argument('-backtest',
                       action='store_true',
                       help='回测，并将回测数据上传')
    group.add_argument('-plots',
                       dest='plots',
                       action='store_true',
                       help='绘制各领域基金回测的小提琴图')

    group.add_argument('-assets',
                       dest='assets',
                       action='store_true',
                       help='从天天基金获取最新资产数据，更新至数据库中')
    group.add_argument('-record',
                       dest='record',
                       action='store_true',
                       help='记录各个基金的持仓、净值、收益、收益率')
    group.add_argument('-tables',
                       action='store_true',
                       help='导出基金最新数据总表、回测基金表，历史记录表')
    group.add_argument('-charts',
                       action='store_true',
                       help='绘制个人数据图表')

    group.add_argument('-job',
                       dest='job',
                       help="执行定制工作")
    group.add_argument('-show',
                       action='store_true',
                       help='展示基金数据')

    parser.add_argument('-c', '--code',
                        dest='code',
                        help="基金代码")
    parser.add_argument('-a', '--amount',
                        dest='amount',
                        help="数额")

    args = parser.parse_args()

    if args.job:
        farmer.job_run(args.job)
        return 0
    elif args.show:
        farmer.statistician.show()
        return 0

    if args.add or args.delete:
        if not args.code:
            print(colored(f"请输入基金代码 -c", "red"))
            return -1

    if args.add:
        farmer.operator.add(args.code)
    elif args.delete:
        farmer.operator.delete(args.code)
    elif args.netvalue:
        farmer.analyst.transport_netvalue()
    elif args.backtest:
        farmer.analyst.backtest()
    elif args.plots:
        farmer.analyst.draw_backtest_plots()

    elif args.assets:
        farmer.operator.update_assets()
    elif args.record:
        farmer.statistician.record_history()
    elif args.tables:
        farmer.statistician.export_tables()
    elif args.charts:
        farmer.statistician.draw_charts()

    return 0


if __name__ == '__main__':
    sys.exit(main())
