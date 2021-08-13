import argparse

from apollo.src.service.data_service import add_fund, delete_fund, update_fund, show_fund
from apollo.src.service.data_service import buy_fund, sell_fund, update_position
from apollo.src.service.data_service import update_total_for_field
from apollo.src.model_prof.fund_types import Filed, Status





def main():

    # 新买入基金
    # add_fund(code='519674', 
    #          amount=50,
    #          filed=Filed.SEMI)
    # update_total_for_field()

    # 删除基金
    # delete_fund(code='519674')
    # update_total_for_field()

    # 加仓基金
    # buy_fund(code='519674', amount=100)
    # update_total_for_field()

    # 卖出基金
    # sell_fund(code='519674', amount=100)
    # update_total_for_field()

    # 更新基金的最新持仓
    # update_position(code='519674', amount=500)
    # update_total_for_field()
    pass


if __name__ == "__main__":
    main()