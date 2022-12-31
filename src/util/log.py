import logging
import logging.config

from ChickenFarm.src.util.config import Config


logging.config.fileConfig(Config().log_path)


def get_logger(filename):
    logger = logging.getLogger(filename)
    return logger
