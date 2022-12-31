import os
import yaml
import threading


class Config(object):

    _instance_lock = threading.Lock()

    def __init__(self):
        config_path = os.getenv("FARM_CONFIG_PATH", None)
        if not config_path:
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
        # 存放个人基金的数据库
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
    def log_path(self):
        # 日志配置文件路径
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.conf")

    @property
    def position_csv_path(self):
        # 以csv方式输入的仓位信息
        return self.config_data.get("POSITION_CSV_PATH")

    @property
    def export_table_path(self):
        # 导出的个人数据统计表的路径
        path = self.config_data.get("EXPORT_TABLE_PATH")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def export_chart_path(self):
        # 导出的个人数据图的路径
        path = self.config_data.get("EXPORT_CHART_PATH")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def export_aip_plot_path(self):
        # 导出的回测分析图的路径
        path = self.config_data.get("EXPORT_AIP_PLOT_PATH")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def tiantian_username(self):
        # 天天基金账户
        return self.config_data.get("TIANTIAN_USERNAME")

    @property
    def tiantian_password(self):
        # 天天基金密码
        return self.config_data.get("TIANTIAN_PASSWORD")
