'''
操作模块，负责添加、删除、更新、购买、卖出、更新持仓等功能
'''
from apollo.src.model_db.database import Database
from apollo.src.model_db.tbl_depository import DepositoryTable, get_fund_dic_from_dpt
from apollo.src.model_db.tbl_info import InfoTable
from apollo.src.model_prof.fund_types import OperateType
from apollo.src.util.tools import auth, record_operation
from apollo.src.util.log import get_logger


logger = get_logger(__file__)


@auth
@record_operation(OperateType.BUY)
def add_fund(code, amount, filed=None, comment=None, *args, **kwargs):
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


@auth
@record_operation(OperateType.UPDATE)
def update_fund(code, update_data, *args, **kwargs):
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


@auth
@record_operation(OperateType.DELETE)
def delete_fund(code, *args, **kwargs):
    '''
    删除 tbl_depository 表中一条基金记录
    '''
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        return

    Database().delete(fund_dpt)
    logger.info(f"Delete {fund_dpt.name}({fund_dpt.code}) from tbl_depository.")


@auth
@record_operation(OperateType.BUY)
def buy_fund(code, amount, *args, **kwargs):
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


@auth
@record_operation(OperateType.SELL)
def sell_fund(code, amount, *args, **kwargs):
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


@auth
@record_operation(OperateType.UPDATE)
def update_position(code, amount, *args, **kwargs):
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


def show_fund(code):
    '''
    展示 tbl_depository 表中一条基金记录
    '''
    fund_dpt_dic = get_fund_dic_from_dpt(code)
    for key, value in fund_dpt_dic.items():
        logger.info(f"{key}: {value}")

