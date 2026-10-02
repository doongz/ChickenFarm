'''
是一种愚蠢的算法，每周固定投入资金
'''
from src.algorithm.algorithm import Algorithm

from src.util.log import get_logger


logger = get_logger(__file__)


class StupidAlgorithm(Algorithm):

    def invest_daily(self):
        """
        在同样 N 个完整交易周内每个交易日买入（5N 笔），C 日盯市。
        fund 每笔固定金额；etf 每笔固定手数。
        :return profit_rate:    float；窗口为空时返回 None
        """
        if self.buy_df.empty:
            return None
        logger.debug(f"Invest daily, {self.name} {self.code}({self.fund_type}) "
                     f"start:{self.start} mark:{self.end}.")

        total = 0  # 存放合计买的份额
        count = 0  # 存放合计花费本金

        for index, row in self.buy_df.iterrows():
            shares, cost = self.place_order(self.execution_price(row))
            total += shares
            count += cost

        profit_rate = round(
            (self.mark_price*total-count)/count, 4)
        logger.debug(f"每天定投，累计投入 {round(count,2)}，"
                        f"盯市市值 {round(self.mark_price*total,2)}，"
                        f"收益率 {100*profit_rate}% ;")
        return profit_rate

    def invest_weekly(self):
        """
        周一~周五分组：在同样 N 个完整周内仅在每周 w 当天买入（每组 N 笔），C 日盯市。
        fund 每笔固定金额（本金相同，份额浮动）；
        etf 每笔固定手数（份额相同，本金浮动，平均买入价为算术均值）。
        :return res:    list[float]，长度 5；窗口为空时返回 []
        """
        if self.buy_df.empty:
            return []
        logger.debug(f"Invest weekly, {self.name} {self.code}({self.fund_type}) "
                     f"start:{self.start} mark:{self.end}.")

        total = [0] * 5  # 存放对应星期合计份额
        count = [0] * 5  # 存放对应星期合计花费本金

        # 每个 week_df 的第 j 行即该周第 j 个工作日，5 组各取 N 笔
        for week in self.weeks:
            for j in range(5):
                shares, cost = self.place_order(
                    self.execution_price(week.iloc[j]))
                total[j] += shares
                count[j] += cost

        res = []
        for index, unit in enumerate(total):
            profit_rate = round(
                (self.mark_price*unit-count[index])/count[index], 4)
            res.append(profit_rate)
            logger.debug(f"每周 {index+1} 定投，累计投入 {round(count[index],2)}，"
                         f"盯市市值 {round(self.mark_price*unit,2)}，"
                         f"收益率 {100*profit_rate}% ;")
        return res
