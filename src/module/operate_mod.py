'''
操作模块，负责添加、删除、更新、购买、卖出、更新持仓等功能
'''
from decimal import Decimal

from chicken_farm.src.db.database import Database
from chicken_farm.src.db.tbl_depository import DepositoryTable, get_fund_dic_from_dpt
from chicken_farm.src.model_prof.fund_types import OperateType
from chicken_farm.src.util.tools import XAlphaTools
from chicken_farm.src.util.tools import auth, record_operation
from chicken_farm.src.util.exceptions import FundNotFoundError
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


@auth
@record_operation(OperateType.ADD)
def add_fund(code, filed=None, comment=None, *args, **kwargs):
    '''
    向 tbl_depository 添加第一次购买的基金
    '''
    fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)
    fund_dpt = DepositoryTable.get_by_code(code)

    if fund_dpt:
        logger.error(f"{fund_dpt.code}({fund_dpt.name}) has been in tbl_depository.")
        raise Exception(f"{fund_dpt.code}({fund_dpt.name}) has been in tbl_depository.")

    fund_dpt = DepositoryTable()
    fund_dpt.name = fundinfo.name
    fund_dpt.code = code
    fund_dpt.filed = filed
    fund_dpt.comment = comment
    fund_dpt.buy_rate = fundinfo.rate / 100
    fund_dpt.sell_rate_info = str(fundinfo.feeinfo)
    fund_dpt.url = fundinfo._url

    Database().add(fund_dpt)
    logger.info(f"Add {fund_dpt.name}({fund_dpt.code}) to tbl_depository successfully, "
                f"filed:{fund_dpt.filed}, comment:{fund_dpt.comment}.")


@auth
@record_operation(OperateType.UPDATE)
def update_fund(code, update_data, *args, **kwargs):
    """
    更新 tbl_depository 表中基金的数据，直接指定数据
    :param update_data: dict {"name": name, "profit": profit,}
    """
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        raise Exception(f"Not found {code} in tbl_depository.")

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
        raise FundNotFoundError(f"Not found {code} in tbl_depository.")

    Database().delete(fund_dpt)
    logger.info(f"Delete {fund_dpt.name}({fund_dpt.code}) from tbl_depository.")


@auth
@record_operation(OperateType.BUY)
def buy_fund(code, amount, *args, **kwargs):
    '''
    加仓基金，更新 tbl_depository 表中该基金的 buying position profit_rate 数据
    '''
    amount = Decimal(amount).quantize(Decimal('0.00'))
    
    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        raise FundNotFoundError(f"Not found {code} in tbl_depository.")

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
    amount = Decimal(amount).quantize(Decimal('0.00'))

    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        raise Exception(f"Not found {code} in tbl_depository.")

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
    amount = Decimal(amount).quantize(Decimal('0.00'))

    fund_dpt = DepositoryTable.get_by_code(code)
    if not fund_dpt:
        logger.error(f"Not found {code} in tbl_depository.")
        raise Exception(f"Not found {code} in tbl_depository.")

    fund_dpt.position = amount
    fund_dpt.profit = fund_dpt.position + fund_dpt.selling - fund_dpt.buying
    fund_dpt.profit_rate = round(fund_dpt.profit/fund_dpt.buying, 4)

    Database().update()
    logger.info(f"Update position {fund_dpt.name}({fund_dpt.code}), amount({amount}), "
                f"position({fund_dpt.position}), profit({fund_dpt.profit}), "
                f"profit_rate({fund_dpt.profit_rate}).")


def fund_dpt(code):
    '''
    获取 tbl_depository 表中一条基金记录
    '''
    fund_dpt = get_fund_dic_from_dpt(code)
    return fund_dpt


