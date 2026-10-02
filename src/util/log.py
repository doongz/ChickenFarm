import logging
import logging.config

from src.util.config import REPO_ROOT


CONF_PATH = REPO_ROOT / 'src' / 'util' / 'log.conf'
LOG_FILE = REPO_ROOT / 'farm.log'

logging.config.fileConfig(
    str(CONF_PATH),
    defaults={'logfile': str(LOG_FILE)},
)


def get_logger(filename):
    logger = logging.getLogger(filename)
    return logger
