from apollo.src.model_db.database import Database
from apollo.src.model_db.tbl_depository import DepositoryTable
from apollo.src.model_db.tbl_info import InfoTable
from apollo.src.model_db.tbl_total_for_field import TotalForField
from apollo.src.model_prof.fund_types import Filed
from apollo.src.util.log import get_logger


logger = get_logger()


def add_fund(code, buying, filed=None, comment=None):

    fund_info = InfoTable.get_by_code(code)
    if not fund_info:
        logger.error(f"Please upload {code} netvalue and info, firstly.")
        raise Exception(f"Not found {code} in tbl_info.")

    dpt_tbl = DepositoryTable()
    dpt_tbl.name = fund_info.name
    dpt_tbl.code = code
    dpt_tbl.filed = filed
    dpt_tbl.buying = buying
    dpt_tbl.position = buying
    dpt_tbl.comment = comment

    Database().add(dpt_tbl)
    logger.info(f"add {dpt_tbl.name}({dpt_tbl.code}) to tbl_depository successfully, "
                f"filed:{dpt_tbl.filed}, buying:{dpt_tbl.buying}, comment:{dpt_tbl.comment}.")


def update_fund(code, update_data):
    """
    :param update_data: dict {"name": name, "profit": profit,}
    """
    dpt_tbl = DepositoryTable.get_by_code(code)

    for attr in dpt_tbl.get_attrs():
        value = update_data.get(attr, None)
        if value:
            setattr(dpt_tbl, attr, value)
            # logger.debug(getattr(dpt_tbl, attr))

    Database().update()
    logger.info(f"update {dpt_tbl.name}({dpt_tbl.code}) data({update_data}).")


def delete_fund(code):

    dpt_tbl = DepositoryTable.get_by_code(code)
    Database().delete(dpt_tbl)
    
    logger.info(f"delete {dpt_tbl.name}({dpt_tbl.code}) from tbl_depository.")


def show_fund(code):

    dpt_tbl = DepositoryTable.get_by_code(code)
    for attr in dpt_tbl.get_attrs():
        value = getattr(dpt_tbl, attr)
        logger.info(f"{attr}: {value}")


def buy_fund():
    pass


def sell_fund():
    pass

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
        tot_field.profit_rate = round(tot_field.profit/tot_field.buying, 4)

        Database().update()
        logger.info(f"update total for {filed}, buying:{tot_field.buying}."
                    f"selling:{tot_field.selling}, position:{tot_field.position}, "
                    f"profit:{tot_field.profit}, profit_rate:{tot_field.profit_rate}")






# def add_fund(code, filed, buying, selling, position, status, comment=None):

#     fund_info = FundInfo(code)

#     dpt_tbl = DepositoryTable()
#     dpt_tbl.name = fund_info.name
#     dpt_tbl.code = code
#     dpt_tbl.filed = filed
#     dpt_tbl.buying = buying
#     dpt_tbl.selling = selling
#     dpt_tbl.position = position
#     dpt_tbl.status = status
#     dpt_tbl.comment = comment

#     dpt_tbl.profit = dpt_tbl.position + dpt_tbl.selling - dpt_tbl.buying
#     dpt_tbl.profit_rate = round(dpt_tbl.profit/dpt_tbl.buying, 4)

#     print(dpt_tbl.position, dpt_tbl.selling, dpt_tbl.buying)
#     print(dpt_tbl.profit)
#     print(dpt_tbl.profit_rate)

#     Database().add(dpt_tbl)
#     logger.info(f"add {dpt_tbl.name}({dpt_tbl.code}) to tbl_depository successfully, "
#                 f"filed:{dpt_tbl.filed}, buying:{dpt_tbl.buying}, comment:{dpt_tbl.comment}.")