"""Transport
1、将xalpha/新浪/akshare 的行情数据传输到自建数据库
2、将回测的数据传输到自建数据库

统一入口 update_market_data_multiprocess 按标的类型（fund/etf）自动分流。
"""
import pandas as pd
import multiprocessing

from src.db.db_fund import Database
from src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.db.db_netvalue import FundNetValue
from src.db.db_backtest import FundBacktest
from src.db.db_etf import ETFDaily
from src.module.backtest_mod import StupidPlan
from src.module.etf_mod import fetch_etf_daily
from src.module.etf_adjust import apply_forward_adjust
from src.util.tools import XAlphaTools, FundTypeTools
from src.util.log import get_logger


logger = get_logger(__file__)


def transport_netvalue_multiprocess(code_list=None, fund_cpus=8):
    """
    将 xalpha 的场外基金净值传输到 db_netvalue，并同步清单中的费率信息。
    净值上传与信息更新各自独立进程池，同一代码两项均成功才算成功。

    :param code_list: 指定代码列表；None 时取清单中全部 fund 类型代码
    :return: (successes, fails)
    """
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(fund_cpus))
    pool_1 = multiprocessing.Pool(processes=job_cnt)
    pool_2 = multiprocessing.Pool(processes=job_cnt)

    if code_list is None:
        code_list = [c for c in FundsForBacktestTable.get_all_code()
                     if FundTypeTools.classify(c) != 'etf']
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
    将回测的数据传输到 db_backtest
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


def transport_etf_daily_multiprocess(code_list=None, etf_cpus=4):
    """
    多进程采集 ETF 日线行情（含前复权）并上传 db_etf。
    仅处理类型为 etf 的标的。并发默认 4，避免触发新浪限流。

    :param code_list: 指定代码列表；None 时取清单中全部 etf 类型代码
    :return: (successes, fails)
    """
    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(etf_cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    if code_list is None:
        code_list = [c for c in FundsForBacktestTable.get_all_code()
                     if FundTypeTools.classify(c) == 'etf']
    for code in code_list:
        res = pool.apply_async(_upload_etf_daily, args=(code, ))
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
        f"Transport ETF daily:{successes} successful. fails:{fails}.")
    return successes, fails


def update_market_data_multiprocess(fund_cpus=8, etf_cpus=4):
    """
    行情采集统一入口：按标的类型分流。
    - fund：xalpha 历史净值写 db_netvalue + 同步清单费率信息
    - etf ：新浪（退避重试）→ akshare 兜底 → 前复权 → db_etf
    :return: {'fund': (successes, fails), 'etf': (successes, fails)}
    """
    code_list = FundsForBacktestTable.get_all_code()
    fund_codes = [c for c in code_list if FundTypeTools.classify(c) != 'etf']
    etf_codes = [c for c in code_list if FundTypeTools.classify(c) == 'etf']

    logger.info(f"Update market data: fund codes:{fund_codes}, "
                f"etf codes:{etf_codes}.")

    fund_result = transport_netvalue_multiprocess(
        code_list=fund_codes, fund_cpus=fund_cpus)
    etf_result = transport_etf_daily_multiprocess(
        code_list=etf_codes, etf_cpus=etf_cpus)

    return {'fund': fund_result, 'etf': etf_result}


def _upload_etf_daily(code):
    '''
    采集单只 ETF 原始日线，合成前复权价并上传 db_etf。
    '''
    try:
        price_df = fetch_etf_daily(code)
        price_df = apply_forward_adjust(price_df, code)
        ETFDaily(code).to_sql(price_df)
        logger.info(f"Upload ETF daily({code}) success, rows:{len(price_df)}.")
        return True
    except Exception as error:
        logger.error(f"Upload ETF daily({code}) occurred an error: {error}.")
        return False


def _upload_backtest_data(code):
    '''
    向 db_backtest 数据库上传基金的，各周期回测数据
    有新的计划就向 aip_plans 中加
    '''
    try:
        aip_plans = [StupidPlan()]

        for plan in aip_plans:
            backtest_df = pd.DataFrame()
            for cycle in plan.InvestmentCycles:
                df = plan.analysis_realtime(code, cycle)
                backtest_df = pd.concat([backtest_df, df])

            FundBacktest(code).to_sql(backtest_df)
            logger.info(f"Upload backtest data({code}) success.")
        return True
    except Exception as error:
        logger.error(f"Upload backtest data({code}) occurred an error: {error}.")
        return False
