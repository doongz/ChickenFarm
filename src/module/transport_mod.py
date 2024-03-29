"""Transport
1、将xalpha的数据传输到自建数据库
2、将回测的数据传输到自建数据库
"""
import pandas as pd
import multiprocessing

from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from ChickenFarm.src.db.db_netvalue import FundNetValue
from ChickenFarm.src.db.db_backtest import FundBacktest
from ChickenFarm.src.module.backtest_mod import StupidPlan
from ChickenFarm.src.util.tools import XAlphaTools
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


def transport_netvalue_multiprocess(cpus=8):
    """
    将xalpha的数据传输到自建数据库
    """
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool_1 = multiprocessing.Pool(processes=job_cnt)
    pool_2 = multiprocessing.Pool(processes=job_cnt)

    code_list = FundsForBacktestTable.get_all_code()
    for code in code_list:
        res_1 = pool_1.apply_async(_upload_netvalue, args=(code, ))
        res_2 = pool_2.apply_async(_update_info, args=(code, ))
        results.append((code, res_1, res_2))

    pool_1.close()
    pool_2.close()
    pool_1.join()
    pool_2.join()

    successes, fails = [], []
    for code, res_1, res_2 in results:
        if res_1.get() and res_2.get():
            successes.append(code)
        else:
            fails.append(code)

    logger.info(f"Transport net value:{successes} successful. fails:{fails}.")
    return successes, fails


def transport_backtest_data_multiprocess(cpus=8):
    """
    将回测的数据传输到自建数据库
    """
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    code_list = FundsForBacktestTable.get_all_code()
    for code in code_list:
        res = pool.apply_async(_upload_backtest_data, args=(code, ))
        results.append((code, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res.get():
            successes.append(code)
        else:
            fails.append(code)

    logger.info(
        f"Transport backtest data:{successes} successful. fails:{fails}.")
    return successes, fails


def _upload_netvalue(code):
    '''
    把基金的历史净值上传至 db_netvalue 数据库中
    并更新 db_fund.tbl_info 中的信息
    '''
    try:
        fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)

        fund_val = FundNetValue(code)
        fund_val.to_sql(fundinfo.price)

        logger.info(f"Upload netvalue({code}) to the {fund_val.tbl} success.")
        return True

    except Exception as error:
        logger.error(f"Upload netvalue occurre an error: {error}.")
        return False


def _update_info(code):
    """
    更新 tbl_funds_for_backtest 中基金的 buy_rate sell_rate_info url
    """
    try:
        fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)
        fund_dpt = FundsForBacktestTable.get_by_code(code)

        fund_dpt.buy_rate = fundinfo.rate / 100
        fund_dpt.sell_rate_info = str(fundinfo.feeinfo)
        fund_dpt.url = fundinfo._url
        Database().update()
        logger.info(
            f"Update info({code}) to the tbl_funds_for_backtest success.")
        return True
    except Exception as error:
        logger.error(f"Upload info occurre an error: {error}.")
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
