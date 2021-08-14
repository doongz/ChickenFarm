import pandas as pd
from pandas.testing import assert_frame_equal

from apollo.src.service.aip_service import invest_week_with_start_interval
from apollo.src.service.aip_service import invest_week_with_start_interval_speed


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows',None)
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180) # 设置打印宽度(**重要**)


def main(is_speed=True):

    if is_speed:
        df = invest_week_with_start_interval_speed('005827', ('2021-01-08', '2021-02-23'), '2021-08-09', 100)
    else:
        df = invest_week_with_start_interval('005827', ('2021-01-08', '2021-02-23'), '2021-08-09', 100)
    print(df)


if __name__ == "__main__":

    main(is_speed=True)


