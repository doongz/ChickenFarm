import pandas as pd
from decimal import Decimal

from ChickenFarm.src.db.db_fund import Database
from ChickenFarm.src.db.tbl_assets import AssetsTable
from ChickenFarm.src.db.tbl_investments import InvestmentsTable
from ChickenFarm.src.db.tbl_history import HistoryTable
from ChickenFarm.src.db.tbl_funds_for_backtest import FundsForBacktestTable
from ChickenFarm.src.util.industry_class import get_fileds_en
from ChickenFarm.src.util.chrome import ChromeDriver
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


def get_assets():

    positions = ChromeDriver().query_assets()

    df = pd.DataFrame(columns=['name', 'code', 'position'])
    for p in positions:
        if len(p) == 0:  # 跳过空行
            continue

        p = p.replace(' ', '\n').split('\n')
        """
        ['易方达蓝筹精选混合（005827）', '混合型最新净值：2.1693（12-29）',
            '3,647.09', '-77.91', '-2.10%', '买入卖出明细']
        也可能有个状态 '有在途交易'
        ['前海开源金银珠宝混合A（001302）', '混合型最新净值：1.2200（12-29）',
            '1,272.01', '有在途交易', '22.01', '1.78%', '买入卖出明细']
        """
        if p[-3] == '--':
            p[-3] = "0.00"
        if p[-2] == '--':
            p[-2] = "0.00%"
        tmp_pd = pd.DataFrame({'name': [p[0][:-8]],
                               'code': [p[0][-7:-1]],
                               'netvalue': [p[1].split("：")[1].split("（")[0]],
                               'position': [Decimal(p[2].replace(",", "")).quantize(Decimal('0.00'))],
                               'profit': [Decimal(p[-3].replace(",", "")).quantize(Decimal('0.00'))],
                               'profit_rate': [Decimal(p[-2][:-1]).quantize(Decimal('0.0000')) / 100],
                               })
        df = pd.concat([df, tmp_pd])
    df = df.reset_index(drop=True)
    return df


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


def get_investments():
    investments = ChromeDriver().query_investments()
    df = pd.DataFrame(
        columns=['name', 'code', 'amount', 'period', 'data', 'state'])
    for inv in investments:
        if len(inv) == 0:  # 跳过空行
            continue
        if not ("每周" in inv or "星期" in inv):  # 去掉无效的行
            continue
        inv = inv.replace(' ', '\n').split('\n')

        """
        ['005669', '前海开源公用事业股票', '活期宝', '农业银行', '|', '1578',
            '10.00', '每周', '星期一', '2023-01-03', '正常', '暂不支持']
        """
        tmp_pd = pd.DataFrame({'name': [inv[1]],
                               'code': [inv[0]],
                               'amount': [Decimal(inv[6]).quantize(Decimal('0.00'))],
                               'period': [inv[7]],
                               'data': [inv[8]],
                               'state': [inv[10]],
                               })
        df = pd.concat([df, tmp_pd])
    df = df.reset_index(drop=True)
    return df


def update_investments(row, *args, **kwargs):
    """
    上传基金最新定投数据
    name      华安纳斯达克100ETF联接(QDII)A
    code                             040046
    amount                            20.00
    period                             每周
    data                             星期一
    state                              正常
    Name: 0, dtype: object
    """
    fund = InvestmentsTable.get_by_code(row['code'])

    if not fund:
        logger.info(f"Add fund {row['code']} in tbl_investments.")
        fund = InvestmentsTable()

        fund.name = row['name']
        fund.code = row['code']
        fund.amount = row['amount']
        fund.period = row['period']
        fund.data = row['data']
        fund.state = row['state']
        Database().add(fund)
    else:
        fund.name = row['name']
        fund.amount = row['amount']
        fund.period = row['period']
        fund.data = row['data']
        fund.state = row['state']

        Database().update()

    logger.info(f"Update investment {fund.name}({fund.code}), "
                f"amount({fund.amount}), period({fund.period}), "
                f"data({fund.data}), state({fund.state}).")


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
