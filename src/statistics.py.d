from chicken_farm.src.module.statistics_mod import update_total_for_field
from chicken_farm.src.module.statistics_mod import record_history


def run():
    '''
    1、更新 tbl_total_for_field 表
    2、统计并记录各个领域以及总的投入、持仓、收益历史
    '''
    update_total_for_field()
    record_history()


if __name__ == "__main__":

    run()