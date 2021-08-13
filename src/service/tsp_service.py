"""Transport
将xalpha的数据搬运到自建数据库
只有函数 get_fundinfo_from_xalpha() 读取xalpha数据，其他脚本一律读取数据库中数据
"""
import xalpha as xa

from apollo.src.model_db.database import Database
from apollo.src.model_db.tbl_info import InfoTable
from apollo.src.model_prof.fund_netvalue import FundNetValue
from apollo.src.util.log import get_logger


logger = get_logger(__file__)


def get_fundinfo_from_xalpha(code):
    fundinfo = xa.fundinfo(code)
    return fundinfo


def transport(codes):
    """
    :params codes 基金代码 list
    todo:可以改成多进程加速
    """
    for code in codes:
        upload_netvalue_and_info(code)
    logger.info(f"Transport {len(codes)} data successful.")


def upload_netvalue_and_info(code):
    '''
    把基金的历史净值上传至 db_netvalue 数据库中
    并更新 db_fund.tbl_info 中的信息
    '''
    fundinfo = get_fundinfo_from_xalpha(code)

    fund_val = FundNetValue(code)
    fund_val.to_sql(fundinfo.price)

    info = InfoTable.get_by_code(code)
    if not info:
        info = InfoTable()
        info.name = fundinfo.name
        info.code = fundinfo.code
        info.rate = fundinfo.rate / 100
        info.feeinfo = str(fundinfo.feeinfo)
        info.url = fundinfo._url
        Database().add(info)
        logger.info(f"Add the data({info.name}) to the table({fund_val.tbl}, {info.__tablename__}).")
        return

    info.name = fundinfo.name
    info.code = fundinfo.code
    info.rate = fundinfo.rate / 100
    info.feeinfo = str(fundinfo.feeinfo)
    info.url = fundinfo._url
    Database().update()
    logger.info(f"Update the data({info.name}) to the table({fund_val.tbl}, {info.__tablename__}).")






