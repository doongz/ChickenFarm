import pandas as pd
import multiprocessing
from pandas.testing import assert_frame_equal

from apollo.src.model_db.tbl_depository import DepositoryTable
from apollo.src.module.aip_mod import upload_backtest_data


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)


def run_speed(cpus=8):

    results = []
    job_cnt = min(multiprocessing.cpu_count(), int(cpus))
    pool = multiprocessing.Pool(processes=job_cnt)

    fund_list = DepositoryTable().get_all_holding()
    for fund in fund_list:
        ret = pool.apply_async(upload_backtest_data, args=(fund.code, ))
        results.append((fund.code, ret))
    pool.close()
    pool.join()

    logger.info(f"Transport-Speed {len(fund_list)} data successful.")

if __name__ == "__main__":

    run_speed()


