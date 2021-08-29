import os
import inspect
import logging
from logging.config import fileConfig

from chicken_farm.src.util.config import Config


logging.config.fileConfig(Config().log_path)


def get_logger(filename):
    logger = logging.getLogger(filename)
    return logger


def get_logger_abandon(path="/Users/zhangdong/Desktop/fund.log"):

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

