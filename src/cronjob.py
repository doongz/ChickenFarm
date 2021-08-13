from apollo.src.config.buy_config import buy_list
from apollo.src.service.tsp_service import transport


def main():

    # 把基金的历史净值上传至 db_netvalue 数据库中
    transport(buy_list)


if __name__ == "__main__":
    main()