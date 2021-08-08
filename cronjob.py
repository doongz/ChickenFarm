from service.tsp_service import transport
from db_model.tbl_info import InfoTable
from db_model.database import Database
from config.buy_config import buy_list

def main():

    transport(buy_list)


if __name__ == "__main__":
    main()