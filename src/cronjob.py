from apollo.src.config.buy_config import buy_list
from apollo.src.service.tsp_service import transport


def main():

    transport(buy_list)


if __name__ == "__main__":
    main()