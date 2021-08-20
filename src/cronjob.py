from chicken_farm.src.module.transport_mod import transport, transport_speed
from chicken_farm.src.util.sheet_tools import read_buy_list


def weekly_job():

    # 1、把基金的历史净值上传至 db_netvalue 数据库中
    buy_list = read_buy_list()
    transport_speed(buy_list)

    # TODO: 2、更新本周的购买记录，需要适配支付宝和天天基金

    # TODO: 3、更新本周的售出记录，需要适配支付宝和天天基金

    # TODO: 4、更新本周所有基金的持仓，需要适配支付宝和天天基金

    # TODO: 5、统计并记录本周各个领域的投入、持仓、收益（已实现，待整合）

    # TODO: 6、导出个人数据统计图表（已实现，待整合）

    # TODO: 7、更新回测分析数据（已实现，待整合）

    # TODO: 8、导出回测分析图表（已实现，待整合）


if __name__ == "__main__":

    weekly_job()