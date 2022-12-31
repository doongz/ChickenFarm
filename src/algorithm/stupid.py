'''
是一种愚蠢的算法，每周固定投入资金
'''
from ChickenFarm.src.algorithm.algorithm import Algorithm

from ChickenFarm.src.util.log import get_logger


logger = get_logger(__file__)


class StupidAlgorithm(Algorithm):

    # def __init__(self, code, start, end, amount=100):
    #     # 如果重写了__init__ 时，要继承父类的构造方法，可以使用 super 关键字：
    #     # https://www.runoob.com/w3cnote/python-extends-init.html
    #     super(子类，self).__init__(参数1，参数2，....)

    def invest_weekly(self):
        """
        每周定投，
        todo: ut 
        :return res:    list
        """
        if self.buy_df.empty:
            return []
        logger.debug(f"Invest weekly, {self.name} {self.code} "
                     f"start:{self.start} end:{self.end}.")

        total = [0] * 5  # 存放对应星期合计买的份数
        count = [0] * 5  # 存放对应星期的成本

        for index, row in self.buy_df.iterrows():
            weekday = int(row['date'].weekday())
            # amount金额除以当日累计净值得到购买基金份额，并计算累计份额
            total[weekday] = total[weekday] + \
                self._amount/float(row['totvalue'])
            count[weekday] += self._amount

        res = []
        for index, unit in enumerate(total):
            profit_rate = round(
                (self.sell_price*unit-count[index])/count[index], 4)
            res.append(profit_rate)
            logger.debug(f"每周 {index+1} 定投，累计投入 {count[index]} 单位金额，"
                         f"最终卖出 {round(self.sell_price*unit,2)} 单位金额，"
                         f"收益率 {100*profit_rate}% ;")
        return res
