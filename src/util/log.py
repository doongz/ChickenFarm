import inspect
import os
import logging
from logging.config import fileConfig

# logging.config.fileConfig(
#     os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.conf"))

# if os.name == 'nt':
#     LOG_FILENAME = os.path.join("controller_service.log")
# else:
#     LOG_FILENAME = os.path.join("/var/log/controller_service.log")

# preheat_log_dir = "/var/log/preheat/"


def get_logger_new(name):
    logger = logging.getLogger(name)
    return logger


def log_function_call(func):
    """
    Decorator to print function call details.

    This includes parameters names and effective values.
    """

    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(
            "{} = {!r}".format(*item) for item in func_args.items() if item[0] != 'password'
        )
        log = get_logger(f"{func.__module__}.{func.__qualname__}")
        log.info(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper




def get_logger(path="/Users/zhangdong/Desktop/fund.log"):

    logger = logging.getLogger(__file__)

    if logger.handlers:
        # 解决日志重复打印的问题
        return logger

    logger.setLevel(logging.DEBUG)
    # 建立一个filehandler来把日志记录在文件里，级别为debug以上
    fh = logging.FileHandler(path)
    fh.setLevel(logging.DEBUG)
    # 建立一个streamhandler来把日志打在CMD窗口上，级别为info以上
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # 设置日志格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s - %(lineno)s - %(levelname)s: %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    #将相应的handler添加在logger对象中
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

