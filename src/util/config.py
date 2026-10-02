import os
import yaml
import threading
from pathlib import Path
from datetime import datetime


# 仓库根目录（src/util/config.py 向上两级），配置与日志默认锚定于此
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / 'config.yaml'


class Config(object):

    _instance_lock = threading.Lock()

    def __init__(self):
        # FARM_CONFIG_PATH 可选；缺省直接读仓库根 config.yaml，无需任何环境变量
        config_path = os.getenv("FARM_CONFIG_PATH") or str(DEFAULT_CONFIG_PATH)
        if not os.path.isfile(config_path):
            raise Exception(
                f"Please check config file exist. config_path: {config_path}")
        self.config_data = self._read_from_yaml(config_path)

    def __new__(cls, *args, **kwargs):
        if not hasattr(Config, "_instance"):
            with Config._instance_lock:
                if not hasattr(Config, "_instance"):
                    Config._instance = object.__new__(cls)
        return Config._instance

    def _read_from_yaml(self, path):
        with open(path) as file:
            data = yaml.safe_load(file)
        return data

    @property
    def db_username(self):
        # 数据库账号
        return self.config_data.get("DB_USERNAME")

    @property
    def db_password(self):
        # 数据库密码
        return self.config_data.get("DB_PASSWORD")

    @property
    def db_address(self):
        # 数据库连接地址
        return self.config_data.get("DB_ADDRESS")

    @property
    def db_port(self):
        # 数据库连接端口
        return self.config_data.get("DB_PORT")

    @property
    def db_fund(self):
        # 回测标的清单库（仅含 tbl_funds_for_backtest）
        return self.config_data.get("DB_FUND")

    @property
    def db_netvalue(self):
        # 存放净值数据的数据库
        return self.config_data.get("DB_NETVALUE")

    @property
    def db_backtest(self):
        # 存放回测数据的数据库
        return self.config_data.get("DB_BACKTEST")

    @property
    def db_etf(self):
        # 存放 ETF 日线行情的数据库
        return self.config_data.get("DB_ETF")

    @property
    def export_aip_plot_path(self):
        # 导出的回测分析图的路径
        path = self.config_data.get("EXPORT_AIP_PLOT_PATH")
        path = os.path.join(path, datetime.today().strftime('%Y-%m-%d'))
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def backtest_config(self):
        # 回测相关配置（下单口径、类型覆盖、采样步长等），可选，缺省为空
        return self.config_data.get("BACKTEST")

    @property
    def export_stats_path(self):
        # 回测统计结果（p 值/效应量/CI/稳健性）导出目录，与图同级 stats/
        path = os.path.join(self.config_data.get("EXPORT_AIP_PLOT_PATH"),
                            datetime.today().strftime('%Y-%m-%d'), 'stats')
        os.makedirs(path, exist_ok=True)
        return path
