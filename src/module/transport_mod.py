"""Transport
1、将xalpha的数据传输到自建数据库
2、将回测的数据传输到自建数据库
"""
import pandas as pd
import multiprocessing

from chicken_farm.src.db.database import Database
from chicken_farm.src.db.tbl_info import InfoTable
from chicken_farm.src.db.tbl_depository import DepositoryTable

from chicken_farm.src.model_prof.fund_netvalue import FundNetValue
from chicken_farm.src.model_prof.fund_backtest import FundBacktest

from chicken_farm.src.module.aip_mod import StupidPlan

from chicken_farm.src.util.tools import XAlphaTools
from chicken_farm.src.util.tools import SheetTools
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


def transport_netvalue(cpus=8):

    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    buy_list = SheetTools.read_buy_list()
    for code in buy_list:
        res = pool.apply_async(_upload_netvalue_and_info, args=(code, ))
        results.append((code, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res:
            successes.append(code)
        else:
            fails.append(code)

    logger.info(f"Transport net value:{successes} successful. fails:{fails}.")
    return successes, fails


def transport_backtest_data(cpus=8):

    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fund_list = DepositoryTable().get_all_holding()
    for fund in fund_list:
        res = pool.apply_async(_upload_backtest_data, args=(fund.code, ))
        results.append((fund.code, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res:
            successes.append(code)
        else:
            fails.append(code)

    logger.info(f"Transport backtest data:{successes} successful. fails:{fails}.")
    return successes, fails


def _upload_netvalue_and_info(code):
    '''
    把基金的历史净值上传至 db_netvalue 数据库中
    并更新 db_fund.tbl_info 中的信息
    '''
    try:
        fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)

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


def _upload_backtest_data(code):
    '''
    向 db_backtest 数据库上传基金的，半年、一年、三年回测数据
    有新的计划就向 aip_plans 中加
    '''
    aip_plans = [StupidPlan()]

    try:
        for plan in aip_plans:
            backtest_df = pd.DataFrame()
            for cycle in plan.InvestmentCycles:
                df = plan.analysis_realtime(code=code, cycle=cycle)
                backtest_df = pd.concat([backtest_df, df])

            FundBacktest(code).to_sql(backtest_df)
            logger.info(f"Upload backtest data({code}) success.")
        return True

    except Exception as error:
        logger.error(f"Upload backtest data occur error:{error}.")
        return False







