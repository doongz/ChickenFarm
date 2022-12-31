from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.db.tbl_assets import AssetsTable
from ChickenFarm.src.db.tbl_history import HistoryTable
from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.util.types import get_fileds_en
from ChickenFarm.src.util.tools import XAlphaTools
from ChickenFarm.src.util.exceptions import FundNotFoundError
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


def add_fund(code, *args, **kwargs):
    '''
    向 tbl_funds_for_backtest 添加第一次购买的基金
    '''
    fundinfo = XAlphaTools.get_fundinfo_from_xalpha(code)
    fund_dpt = FundsForBacktestTable.get_by_code(code)

    if fund_dpt:
        logger.error(
            f"{fund_dpt.code}({fund_dpt.name}) has been in tbl_funds_for_backtest.")
        raise Exception(
            f"{fund_dpt.code}({fund_dpt.name}) has been in tbl_funds_for_backtest.")

    fund_dpt = FundsForBacktestTable()
    fund_dpt.name = fundinfo.name
    fund_dpt.code = code
    fund_dpt.filed = kwargs.get("filed", None)
    fund_dpt.comment = kwargs.get("comment", None)
    fund_dpt.buy_rate = fundinfo.rate / 100
    fund_dpt.sell_rate_info = str(fundinfo.feeinfo)
    fund_dpt.url = fundinfo._url

    Database().add(fund_dpt)
    logger.info(f"Add {fund_dpt.name}({fund_dpt.code}) to tbl_funds_for_backtest successfully, "
                f"filed:{fund_dpt.filed}, comment:{fund_dpt.comment}.")


def delete_fund(code, *args, **kwargs):
    '''
    删除 tbl_funds_for_backtest 表中一条基金记录
    '''
    fund_dpt = FundsForBacktestTable.get_by_code(code)
    if not fund_dpt:
        raise FundNotFoundError(f"Not found {code} in tbl_funds_for_backtest.")

    Database().delete(fund_dpt)
    logger.info(
        f"Delete {fund_dpt.name}({fund_dpt.code}) from tbl_funds_for_backtest.")


def update_assets(row, *args, **kwargs):
    '''
    上传基金最新持仓，更新 tbl_assets 表中该基金的 position netvalue profit profit_rate 数据
    name           前海开源优质企业6个月持有混合C
    code                                   010718
    position                                 6.55
    netvalue                               0.5719
    profit                                  -3.45
    profit_rate                           -0.3450
    Name: 0, dtype: object
    '''
    fund_dpt = AssetsTable.get_by_code(row['code'])
    fundinfo = XAlphaTools.get_fundinfo_from_xalpha(row['code'])

    if not fund_dpt:
        logger.info(f"Add fund {row['code']} in tbl_assets.")
        fund_dpt = AssetsTable()

        fund_dpt.name = fundinfo.name
        fund_dpt.code = row['code']

        fileds = get_fileds_en()
        options = f"{fundinfo.name} {row['code']} Choose filed:\n" + "0 - None\n"
        for i, filed in enumerate(fileds):
            options += f"{i+1} - {filed}\n"
        choose = int(input(options + ": "))
        filed = None if choose == 0 else fileds[choose-1]
        fund_dpt.filed = filed

        fund_dpt.position = row['position']
        fund_dpt.netvalue = row['netvalue']
        fund_dpt.profit = row['profit']
        fund_dpt.profit_rate = row['profit_rate']
        fund_dpt.comment = kwargs.get("comment", None)
        fund_dpt.buy_rate = fundinfo.rate / 100
        fund_dpt.sell_rate_info = str(fundinfo.feeinfo)
        fund_dpt.url = fundinfo._url

        Database().add(fund_dpt)
    else:
        fund_dpt.position = row['position']
        fund_dpt.netvalue = row['netvalue']
        fund_dpt.profit = row['profit']
        fund_dpt.profit_rate = row['profit_rate']

        Database().update()

    logger.info(f"Update asserts {fund_dpt.name}({fund_dpt.code}), "
                f"position({fund_dpt.position}), netvalue({fund_dpt.netvalue}), "
                f"profit({fund_dpt.profit}), profit_rate({fund_dpt.profit_rate}).")


def record_history():
    funds_obj = AssetsTable.get_all()

    for fobj in funds_obj:
        if fobj.position == 0:
            continue

        hs = HistoryTable()
        hs.code = fobj.code
        hs.position = fobj.position
        hs.netvalue = fobj.netvalue
        hs.profit = fobj.profit
        hs.profit_rate = fobj.profit_rate
        Database().add(hs)

    logger.info(
        f"Record {len(funds_obj)} funds history to tbl_history successfully.")
