import json
import decimal
from chinese_calendar import is_workday
from datetime import datetime, timedelta

from apollo.src.model_db.database import Database
from apollo.src.model_db.tbl_operation_record import OperationRecordTable
from apollo.src.model_db.tbl_depository import DepositoryTable, get_fund_dic_from_dpt
from apollo.src.model_prof.fund_types import OperateType
from apollo.src.config.key import KEY
from apollo.src.util.log import get_logger


logger = get_logger(__file__)


# 得到当前日期是否为股票交易日
def is_trade_day(date):
    '''
    :param date  string '2021-08-13'
    '''
    date = datetime.strptime(date, '%Y-%m-%d')
    if is_workday(date):
        if date.isoweekday() < 6:
            return True
    return False


# 两个日期之间连续日期列表
def get_between_day(begin_date,end_date):
    date_list = []
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += timedelta(days=1)
    return date_list


# 验证是否有权限，必须需要参数 key
def auth(func):
    def wrapper(*args, **kwargs):

        key = kwargs.get("key", None)
        if not key:
            logger.error("Your operation key is empty.")
            raise Exception('Your operation key is empty.')
        if key != KEY:
            logger.error("Your operation key is wrong.")
            raise Exception('Your operation key is wrong.')
        logger.info("Authentication success.")

        func(*args, **kwargs)

    return wrapper


# 将操作前和操作后的 tbl_depository 中的基金进行记录
# 必须需要参数 code
def record_operation(operate_type):
    def inner(func):
        def wrapper(*args, **kwargs):

            code = kwargs.get("code")
            dpt_before_change = get_fund_dic_from_dpt(code)

            opr = OperationRecordTable()
            opr.name = dpt_before_change.get('name', 'xxxxxx')
            opr.code = dpt_before_change.get('code', 'xxxxxx')
            opr.operate_type = operate_type
            opr.amount = kwargs.get("amount", None)
            opr.info_after_change = "Waiting for operation"
            opr.info_before_change = json.dumps(dpt_before_change)
            Database().add(opr)

            func(*args, **kwargs)

            dpt_after_change = get_fund_dic_from_dpt(code)
            if operate_type != OperateType.DELETE:
                opr.name = dpt_after_change.get('name')
                opr.code = dpt_after_change.get('code')
            opr.info_after_change = json.dumps(dpt_after_change)
            Database().update()
            logger.info(f"Record {opr.name}({opr.code}) operation:{opr.operate_type} "
                        f"amount:{opr.amount} to tbl_operation_record.")

        return wrapper
    return inner


 