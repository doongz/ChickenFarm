from apollo.src.model_db.database import Database
from apollo.src.model_db.tbl_depository import DepositoryTable
from apollo.src.model_db.tbl_info import InfoTable
from apollo.src.model_db.tbl_total_for_field import TotalForField
from apollo.src.model_prof.fund_types import Filed
from apollo.src.util.log import get_logger


logger = get_logger()


def add_fund(code, amount, filed=None, comment=None):
    '''
    向 tbl_depository 添加第一次购买的基金
    '''
    fund_info = InfoTable.get_by_code(code)
    if not fund_info:
        logger.error(f"Please upload {code} netvalue and info, firstly.")
        raise Exception(f"Not found {code} in tbl_info.")

    fund_dpt = DepositoryTable.get_by_code(code)
    if fund_dpt:
        logger.error(f"{fund_dpt.code}({fund_dpt.name}) has been in tbl_depository.")
        return

    fund_dpt = DepositoryTable()
    fund_dpt.name = fund_info.name
    fund_dpt.code = code
    fund_dpt.filed = filed
    fund_dpt.buying = amount
    fund_dpt.position = amount
    fund_dpt.comment = comment

    Database().add(fund_dpt)
    logger.info(f"Add {fund_dpt.name}({fund_dpt.code}) to tbl_depository successfully, "
                f"filed:{fund_dpt.filed}, buying:{fund_dpt.buying}, comment:{fund_dpt.comment}.")


def update_fund(code, update_data):
    """
    更新 tbl_depository 表中基金的数据，直接指定数据
    :param update_data: dict {"name": name, "profit": profit,}
    """
    fund_dpt = DepositoryTable.get_by_code(code)

    for attr in fund_dpt.get_attrs():
        value = update_data.get(attr, None)
        if value:
            setattr(fund_dpt, attr, value)
            # logger.debug(getattr(fund_dpt, attr))

    Database().update()
    logger.info(f"Update {fund_dpt.name}({fund_dpt.code}) data({update_data}).")


def delete_fund(code):
    '''
    删除 tbl_depository 表中一条基金记录
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        return

    Database().delete(fund_dpt)
    logger.info(f"Delete {fund_dpt.name}({fund_dpt.code}) from tbl_depository.")


def show_fund(code):
    '''
    展示 tbl_depository 表中一条基金记录
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    for attr in fund_dpt.get_attrs():
        value = getattr(fund_dpt, attr)
        logger.info(f"{attr}: {value}")


def buy_fund(code, amount):
    '''
    加仓基金，更新 tbl_depository 表中该基金的 buying position profit_rate 数据
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        return

    fund_dpt.buying += amount
    fund_dpt.position += amount
    fund_dpt.profit_rate = round(fund_dpt.profit/fund_dpt.buying, 4)

    Database().update()
    logger.info(f"Buy fund {fund_dpt.name}({fund_dpt.code}), amount({amount}), buying({fund_dpt.buying}), "
                f"position({fund_dpt.position}), profit_rate({fund_dpt.profit_rate}).")


def sell_fund(code, amount):
    '''
    卖出基金，更新 tbl_depository 表中该基金的 selling position 数据
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        return

    fund_dpt.selling += amount
    fund_dpt.position -= amount

    Database().update()
    logger.info(f"Sell fund {fund_dpt.name}({fund_dpt.code}), amount({amount}), "
                f"selling({fund_dpt.selling}), position({fund_dpt.position}).")


def update_position(code, amount):
    '''
    上传基金最新持仓，更新 tbl_depository 表中该基金的 position profit profit_rate 数据
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        return

    fund_dpt.position = amount
    fund_dpt.profit = fund_dpt.position + fund_dpt.selling - fund_dpt.buying
    fund_dpt.profit_rate = round(fund_dpt.profit/fund_dpt.buying, 4)

    Database().update()
    logger.info(f"Update position {fund_dpt.name}({fund_dpt.code}), amount({amount}), "
                f"position({fund_dpt.position}), profit({fund_dpt.profit}), "
                f"profit_rate({fund_dpt.profit_rate}).")


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