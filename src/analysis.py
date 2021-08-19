import pandas as pd
import multiprocessing
from pandas.testing import assert_frame_equal

from chicken_farm.src.model_db.tbl_depository import DepositoryTable
from chicken_farm.src.model_prof.fund_types import Filed
from chicken_farm.src.model_prof.fund_backtest import FundBacktest
from chicken_farm.src.module.aip_mod import StupidPlan
from chicken_farm.src.plot.aip_plot import export_aip_violin_plot_by_filed
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


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

    print(f"Transport backtest data:{len(successes)} successful. fails:{fails}")


def export_violin_plot(cpus=8):

    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fileds = Filed().get_fileds()
    for filed in fileds:
        if filed == Filed.MILITARY:
            continue
        res = pool.apply_async(export_aip_violin_plot_by_filed, args=(filed, ))
        results.append((filed, res))
    pool.close()
    pool.join()

    successes, fails = [], []
    for code, res in results:
        if res:
            successes.append(code)
        else:
            fails.append(code)

    print(f"Export violin plot:{len(successes)} successful. fails:{fails}")

if __name__ == "__main__":

    export_violin_plot()


