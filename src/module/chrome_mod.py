import pandas as pd
from decimal import Decimal

from ChickenFarm.src.util.chrome import ChromeDriver
from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


def get_assets():

    positions = ChromeDriver().query_position()

    df = pd.DataFrame(columns=['name', 'code', 'position'])
    for p in positions:
        if len(p) == 0:  # 跳过空行
            continue

        p = p.replace(' ', '\n').split('\n')
        """
        ['易方达蓝筹精选混合（005827）', '混合型最新净值：2.1693（12-29）',
            '3,647.09', '-77.91', '-2.10%', '买入卖出明细']
        也可能有个状态 '有在途交易'
        ['前海开源金银珠宝混合A（001302）', '混合型最新净值：1.2200（12-29）', '1,272.01', '有在途交易', '22.01', '1.78%', '买入卖出明细']
        """
        print(p)
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

    return df
