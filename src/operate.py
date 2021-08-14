from apollo.src.module.operate_mod import add_fund, delete_fund, update_fund, show_fund
from apollo.src.module.operate_mod import buy_fund, sell_fund, update_position
from apollo.src.module.statistics_mod import update_total_for_field
from apollo.src.model_prof.fund_types import Filed
from apollo.src.util.sheet import read_latest_position, export_tables
from apollo.src.util.log import get_logger

logger = get_logger(__file__)


def run():

    # 新买入基金
    # add_fund(code='519674', 
    #          amount=50,
    #          filed=Filed.SEMI,
    #          key='AK06@w33D')
    # update_total_for_field()

    # 删除基金
    # delete_fund(code='519674', key='AK06@w33D')
    # update_total_for_field()

    # 加仓基金
    # buy_fund(code='167301', amount=50, key='AK06@w33D')
    # update_total_for_field()

    # 卖出基金
    # sell_fund(code='519674', amount=200, key='AK06@w33D')
    # update_total_for_field()

    # 一条一条更新基金的最新持仓
    # update_position(code='320007', amount=1292.62, key='AK06@w33D')
    # update_total_for_field()

    # 读取 position.csv 中基金的最新持仓
    # latest_position = read_latest_position()
    # for code, position in latest_position:
    #     update_position(code=code, amount=position, key='AK06@w33D')
    # update_total_for_field()

    # 展示基金
    # show_fund(code='519674')

    # 导出数据库中的table
    export_tables()

    pass


if __name__ == "__main__":
    
    run()