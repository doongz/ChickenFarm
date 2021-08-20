"""Transport
将xalpha的数据搬运到自建数据库
只有函数 get_fundinfo_from_xalpha() 读取xalpha数据，其他脚本一律读取数据库中数据
"""
import multiprocessing
import xalpha as xa

from chicken_farm.src.model_db.database import Database
from chicken_farm.src.model_db.tbl_info import InfoTable
from chicken_farm.src.model_prof.fund_netvalue import FundNetValue
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


def get_fundinfo_from_xalpha(code):
    fundinfo = xa.fundinfo(code)
    return fundinfo


def transport(codes):
    """
    :params codes 基金代码 list
    """
    for code in codes:
        _upload_netvalue_and_info(code)

    logger.info(f"Transport {len(codes)} data successful.")


def transport_speed(codes, cpus=8):
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    for code in codes:
        ret = pool.apply_async(_upload_netvalue_and_info, args=(code, ))
        results.append((code, ret))
    pool.close()
    pool.join()

    logger.info(f"Transport-Speed {len(codes)} data successful.")


def _upload_netvalue_and_info(code):
    '''
    把基金的历史净值上传至 db_netvalue 数据库中
    并更新 db_fund.tbl_info 中的信息
    '''
    try:
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
            return True

        info.name = fundinfo.name
        info.code = fundinfo.code
        info.rate = fundinfo.rate / 100
        info.feeinfo = str(fundinfo.feeinfo)
        info.url = fundinfo._url
        Database().update()
        logger.info(f"Update the data({info.name}) to the table({fund_val.tbl}, {info.__tablename__}).")
        return True

    except Exception as error:
        logger.error(f"Upload netvalue and info occurre an error: {error}.")
        return False






