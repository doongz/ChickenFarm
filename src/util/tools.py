import json

from chicken_farm.src.model_db.database import Database
from chicken_farm.src.model_db.tbl_operation_record import OperationRecordTable
from chicken_farm.src.model_db.tbl_depository import DepositoryTable, get_fund_dic_from_dpt
from chicken_farm.src.model_prof.fund_types import OperateType
from chicken_farm.src.config.key import KEY
from chicken_farm.src.util.log import get_logger


logger = get_logger(__file__)


def auth(func):
    # 验证是否有权限，必须需要参数 key
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


def record_operation(operate_type):
    """
    将操作前和操作后的 tbl_depository 中的基金进行记录
    必须需要参数 code
    """
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
            Database().add(opr) # 如果下面的函数发生异常，这里将会插入一条垃圾数据

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

