from apollo.src.config.buy_config import buy_list
from apollo.src.service.tsp_service import transport, transport_speed


def main(is_speed=True):

    # 把基金的历史净值上传至 db_netvalue 数据库中
    if is_speed:
        transport_speed(buy_list)
    else:
        transport(buy_list)


if __name__ == "__main__":

    main()