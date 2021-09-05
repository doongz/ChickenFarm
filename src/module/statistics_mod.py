'''
更新每个领域的统计情况
每周去统计各个领域和基金的投入、持仓、收益历史
'''
from chicken_farm.src.db.db_fund import Database
from chicken_farm.src.db.tbl_depository import DepositoryTable
from chicken_farm.src.db.tbl_history_buying import HistroyBuyingTable
from chicken_farm.src.db.tbl_history_position import HistroyPositionTable
from chicken_farm.src.db.tbl_history_profit import HistroyProfitTable
from chicken_farm.src.db.tbl_total_for_field import TotalForField
from chicken_farm.src.db.types import Filed
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


def update_total_for_field():
    '''
    从 tbl_depository 表中获取每个领域基金的数据
    合计每个领域的投入、赎回、持仓、收益，计算收益率
    上传到 tbl_total_for_field 表
    '''
    fileds = Filed().get_fileds()
    for filed in fileds:
        funds = DepositoryTable.get_by_filed(filed)
        tot_field = TotalForField.get_by_filed(filed)

        tot_field.buying = sum([fund.buying for fund in funds])
        tot_field.selling = sum([fund.selling for fund in funds])
        tot_field.position = sum([fund.position for fund in funds])
        tot_field.profit = sum([fund.profit for fund in funds])
        if tot_field.buying == 0:
            # 这个领域的基金还没买过
            tot_field.profit_rate = round(0, 4)
        else:
            tot_field.profit_rate = round(tot_field.profit/tot_field.buying, 4)

        Database().update()
        logger.debug(f"update total for {filed}, buying:{tot_field.buying}."
                     f"selling:{tot_field.selling}, position:{tot_field.position}, "
                     f"profit:{tot_field.profit}, profit_rate:{tot_field.profit_rate}")

    logger.info(f"Update tbl_total_for_field completed.")


def record_history():
    # 统计并记录各个领域以及总的投入、持仓、收益历史
    try:
        _record_history_buying()
    except Exception as error:
        logger.error(f"Record history buying error:{error}.")

    try:
        _record_history_position()
    except Exception as error:
        logger.error(f"Record history position error:{error}.")

    try:
        _record_history_profit()
    except Exception as error:
        logger.error(f"Record history profit error:{error}.")


def _record_history_buying():
    '''
    向 tbl_history_buying 记录购买历史
    '''
    fileds_buying = {}
    fileds = Filed().get_fileds()
    for filed in fileds:
        tot_field = TotalForField.get_by_filed(filed)
        fileds_buying[filed] = tot_field.buying

    ht_buy = HistroyBuyingTable()
    ht_buy.total = sum(fileds_buying.values())
    ht_buy.ENERGY = fileds_buying[Filed.ENERGY]
    ht_buy.SEMI = fileds_buying[Filed.SEMI]
    ht_buy.METALS = fileds_buying[Filed.METALS]
    ht_buy.MEDICAL = fileds_buying[Filed.MEDICAL]
    ht_buy.SPIRIT = fileds_buying[Filed.SPIRIT]
    ht_buy.HK = fileds_buying[Filed.HK]
    ht_buy.US = fileds_buying[Filed.US]
    ht_buy.BLUE = fileds_buying[Filed.BLUE]
    ht_buy.FINANCE = fileds_buying[Filed.FINANCE]
    ht_buy.MILITARY = fileds_buying[Filed.MILITARY]

    Database().add(ht_buy)
    logger.info(f"Record history buying to tbl_history_buying successfully.")


def _record_history_position():
    '''
    向 tbl_history_position 记录购买历史
    '''
    fileds_position = {}
    fileds = Filed().get_fileds()
    for filed in fileds:
        tot_field = TotalForField.get_by_filed(filed)
        fileds_position[filed] = tot_field.position

    ht_buy = HistroyPositionTable()
    ht_buy.total = sum(fileds_position.values())
    ht_buy.ENERGY = fileds_position[Filed.ENERGY]
    ht_buy.SEMI = fileds_position[Filed.SEMI]
    ht_buy.METALS = fileds_position[Filed.METALS]
    ht_buy.MEDICAL = fileds_position[Filed.MEDICAL]
    ht_buy.SPIRIT = fileds_position[Filed.SPIRIT]
    ht_buy.HK = fileds_position[Filed.HK]
    ht_buy.US = fileds_position[Filed.US]
    ht_buy.BLUE = fileds_position[Filed.BLUE]
    ht_buy.FINANCE = fileds_position[Filed.FINANCE]
    ht_buy.MILITARY = fileds_position[Filed.MILITARY]

    Database().add(ht_buy)
    logger.info(f"Record history position to tbl_history_position successfully.")


def _record_history_profit():
    '''
    向 tbl_history_profit 记录购买历史
    '''
    fileds_profit = {}
    fileds = Filed().get_fileds()
    for filed in fileds:
        tot_field = TotalForField.get_by_filed(filed)
        fileds_profit[filed] = tot_field.profit

    ht_buy = HistroyProfitTable()
    ht_buy.total = sum(fileds_profit.values())
    ht_buy.ENERGY = fileds_profit[Filed.ENERGY]
    ht_buy.SEMI = fileds_profit[Filed.SEMI]
    ht_buy.METALS = fileds_profit[Filed.METALS]
    ht_buy.MEDICAL = fileds_profit[Filed.MEDICAL]
    ht_buy.SPIRIT = fileds_profit[Filed.SPIRIT]
    ht_buy.HK = fileds_profit[Filed.HK]
    ht_buy.US = fileds_profit[Filed.US]
    ht_buy.BLUE = fileds_profit[Filed.BLUE]
    ht_buy.FINANCE = fileds_profit[Filed.FINANCE]
    ht_buy.MILITARY = fileds_profit[Filed.MILITARY]

    Database().add(ht_buy)
    logger.info(f"Record history profit to tbl_history_profit successfully.")
