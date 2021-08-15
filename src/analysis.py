import pandas as pd
from pandas.testing import assert_frame_equal

from apollo.src.model_db.tbl_depository import DepositoryTable
from apollo.src.module.aip_mod import invest_week_with_start_interval
from apollo.src.module.aip_mod import invest_week_with_start_interval_speed
from apollo.src.module.aip_mod import upload_backtest_data


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)


def run(is_speed=True):

    # if is_speed:
    #     df = invest_week_with_start_interval_speed('005827', ('2021-01-08', '2021-02-23'), '2021-08-09', 100)
    # else:
    #     df = invest_week_with_start_interval('005827', ('2021-01-08', '2021-02-23'), '2021-08-09', 100)
    # print(df)
    fund_list = DepositoryTable().get_all_holding()
    for fund in fund_list[:2]:
        upload_backtest_data(fund.code)
    print('end')



if __name__ == "__main__":

    run(is_speed=True)


