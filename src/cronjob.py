from chicken_farm.src.module.transport_mod import transport, transport_speed
from chicken_farm.src.util.sheet_tools import read_buy_list


def run(is_speed=True):

    # 把基金的历史净值上传至 db_netvalue 数据库中
    buy_list = read_buy_list()
    if is_speed:
        transport_speed(buy_list)
    else:
        transport(buy_list)


if __name__ == "__main__":

    run()