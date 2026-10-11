"""Transport
1、将xalpha/新浪/akshare 的行情数据传输到 SQLite
2、将回测的数据传输到 SQLite

统一入口 update_market_data_multiprocess 按标的类型（fund/etf）自动分流。

并发模型：多进程 worker 只负责网络采集/回测计算并返回结果数据，
不直接写库；主进程收集结果后统一串行写入，避免 SQLite 多进程写冲突。
"""
import pandas as pd
import multiprocessing

from src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.db.db_netvalue import FundNetValue
from src.db.db_backtest import FundBacktest
from src.db.db_etf import ETFDaily
from src.module.backtest_mod import StupidPlan
from src.module.etf_mod import fetch_etf_daily
from src.module.etf_adjust import apply_forward_adjust
from src.db.db_fund import Database
from src.util.tools import XAlphaTools, FundTypeTools
from src.util.log import get_logger


logger = get_logger(__file__)


def transport_netvalue_multiprocess(code_list=None, fund_cpus=8):
    """
    多进程采集 xalpha 场外基金净值（worker 计算），主进程统一写库，
    并同步清单中的费率信息。

    :param code_list: 指定代码列表；None 时取清单中全部 fund 类型代码
    :return: (successes, fails)
    """
    job_cnt = min(multiprocessing.cpu_count(), int(fund_cpus))
    pool_1 = multiprocessing.Pool(processes=job_cnt)
    pool_2 = multiprocessing.Pool(processes=job_cnt)

    if code_list is None:
        code_list = [c for c in FundsForBacktestTable.get_all_code()
                     if FundTypeTools.classify(c) != 'etf']

    net_results = [(code, pool_1.apply_async(_fetch_netvalue, args=(code, )))
                   for code in code_list]
    info_results = [(code, pool_2.apply_async(_fetch_info, args=(code, )))
                    for code in code_list]

    pool_1.close(); pool_2.close()
    pool_1.join(); pool_2.join()

    successes, fails = [], []
    info_map = {}
    for code, res in info_results:
        info_map[code] = res.get()

    for code, res in net_results:
        net_df = res.get()
        info = info_map.get(code)
        # 主进程统一写库：净值表 + 标的清单费率信息
        if net_df is not None and info is not None:
            FundNetValue(code).to_sql(net_df)
            _apply_info(code, info)
            successes.append(code)
        else:
            fails.append(code)

    logger.info(f"Transport net value:{successes} successful. fails:{fails}.")
    return successes, fails


def transport_backtest_data_multiprocess(cpus=8):
    """
    多进程执行回测计算（worker），主进程统一写 db_backtest。
    """
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    code_list = FundsForBacktestTable.get_all_code()
    results = [(code, pool.apply_async(_compute_backtest, args=(code, )))
               for code in code_list]
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        backtest_df = res.get()
        if backtest_df is not None:
            # 主进程串行写入
            FundBacktest(code).to_sql(backtest_df)
            successes.append(code)
        else:
            fails.append(code)

    logger.info(
        f"Transport backtest data:{successes} successful. fails:{fails}.")
    return successes, fails


def _fetch_netvalue(code):
    '''worker：只拉取基金历史净值 DataFrame，不写库。'''
    try:
        return XAlphaTools.get_fundinfo_from_xalpha(code).price
    except Exception as error:
        logger.error(f"Fetch netvalue({code}) occurred an error: {error}.")
        return None


def _fetch_info(code):
    """
    worker：只拉取标的清单所需费率/来源信息（返回字典），不写库。
    """
    try:
        fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)
        return {'buy_rate': fundinfo.rate / 100,
                'sell_rate_info': str(fundinfo.feeinfo),
                'url': fundinfo._url}
    except Exception as error:
        logger.error(f"Fetch info({code}) occurred an error: {error}.")
        return None


def _apply_info(code, info):
    """主进程：把费率/来源更新到已有标的记录；新标的在 add_fund 中已写入。"""
    fund_dpt = FundsForBacktestTable.get_by_code(code)
    if fund_dpt is None:
        return
    fund_dpt.buy_rate = info['buy_rate']
    fund_dpt.sell_rate_info = info['sell_rate_info']
    fund_dpt.url = info['url']
    Database().update()


def transport_etf_daily_multiprocess(code_list=None, etf_cpus=4):
    """
    多进程采集 ETF 日线并合成前复权（worker 计算），主进程统一写 db_etf。
    仅处理类型为 etf 的标的。并发默认 4，避免触发新浪限流。

    :param code_list: 指定代码列表；None 时取清单中全部 etf 类型代码
    :return: (successes, fails)
    """
    job_cnt = min(multiprocessing.cpu_count(), int(etf_cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    if code_list is None:
        code_list = [c for c in FundsForBacktestTable.get_all_code()
                     if FundTypeTools.classify(c) == 'etf']
    results = [(code, pool.apply_async(_fetch_etf_daily, args=(code, )))
               for code in code_list]
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        price_df = res.get()
        if price_df is not None:
            # 主进程串行写入
            ETFDaily(code).to_sql(price_df)
            successes.append(code)
        else:
            fails.append(code)

    logger.info(
        f"Transport ETF daily:{successes} successful. fails:{fails}.")
    return successes, fails


def update_market_data_multiprocess(fund_cpus=8, etf_cpus=4):
    """
    行情采集统一入口：按标的类型分流。
    - fund：xalpha 历史净值（worker）→ 主进程写 SQLite + 同步清单费率
    - etf ：新浪（退避重试）→ akshare 兜底 → 前复权 → 主进程写 SQLite
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


def _fetch_etf_daily(code):
    '''worker：采集原始日线并合成前复权 DataFrame，不写库。'''
    try:
        price_df = fetch_etf_daily(code)
        return apply_forward_adjust(price_df, code)
    except Exception as error:
        logger.error(f"Fetch ETF daily({code}) occurred an error: {error}.")
        return None


def _compute_backtest(code):
    '''worker：汇总各周期回测 DataFrame，不写库。'''
    try:
        aip_plans = [StupidPlan()]
        backtest_df = pd.DataFrame()
        for plan in aip_plans:
            for cycle in plan.InvestmentCycles:
                df = plan.analysis_realtime(code, cycle)
                backtest_df = pd.concat([backtest_df, df])
        return backtest_df
    except Exception as error:
        logger.error(f"Compute backtest({code}) occurred an error: {error}.")
        return None


def transport_etf_minute_serial(code_list=None):
    """
    【串行】采集 ETF 1 分钟分时并由主进程逐只写库。
    新浪分钟接口每日仅约 10 次配额，严禁多进程；单只失败记入 fails 后继续，
    不中断整轮、不向上抛出。

    :param code_list: 指定代码列表；None 时取清单中全部 etf 类型代码
    :return: (successes, fails)
    """
    # 函数内导入，避免给周定投路径增加额外的模块加载耦合
    from src.module.etf_intraday_mod import fetch_etf_minute
    from src.db.db_etf_intraday import ETFMinute

    if code_list is None:
        code_list = [c for c in FundsForBacktestTable.get_all_code()
                     if FundTypeTools.classify(c) == 'etf']

    successes, fails = [], []
    for code in code_list:
        try:
            # 串行：取数与写库均在主进程逐只完成
            new_df = fetch_etf_minute(code)
            ETFMinute(code).upsert(new_df)
            successes.append(code)
        except Exception as error:
            # 单只失败不中断整轮
            logger.error(f"Fetch ETF minute({code}) occurred an error: {error}.")
            fails.append(code)

    logger.info(
        f"Transport ETF minute:{successes} successful. fails:{fails}.")
    return successes, fails
