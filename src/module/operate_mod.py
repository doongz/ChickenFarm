"""
回测标的清单（tbl_funds_for_backtest）维护：添加 / 删除。
添加时通过 xalpha 拉取基金名称、申赎费率与来源页。
"""
from src.db.db_fund import Database
from src.db.tbl_funds_for_backtest import FundsForBacktestTable
from src.util.tools import XAlphaTools
from src.util.exceptions import FundNotFoundError
from src.util.log import get_logger


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
    # 场内 ETF 在 xalpha 可能返回空费率（''/None），按 0 处理，避免 float 转换失败
    try:
        fund_dpt.buy_rate = float(fundinfo.rate) / 100
    except (TypeError, ValueError):
        fund_dpt.buy_rate = 0.0
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
