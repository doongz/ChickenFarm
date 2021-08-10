from apollo.src.service.tsp_service import transport
from apollo.src.config.buy_config import buy_list


def main():

    transport(buy_list)


if __name__ == "__main__":
    main()