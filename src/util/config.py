import os
import json
import threading
from pathlib import Path
from datetime import datetime

from dotenv import dotenv_values


# 仓库根目录（src/util/config.py 向上两级），配置与日志默认锚定于此
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / '.env'


def _parse_backtest_value(raw):
    """
    把 .env 中的字符串值转换为合适的 Python 类型：
    true/false → 布尔；整数/浮点 → 数值；{...}/[...] → JSON；其余 → 字符串。
    """
    value = raw.strip()
    low = value.lower()
    if low in ('true', 'false'):
        return low == 'true'
    if value[:1] in ('{', '['):
        return json.loads(value)
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


class Config(object):

    _instance_lock = threading.Lock()

    def __init__(self):
        # FARM_CONFIG_PATH 可选；缺省直接读仓库根 .env，无需任何环境变量
        config_path = os.getenv("FARM_CONFIG_PATH") or str(DEFAULT_CONFIG_PATH)
        if not os.path.isfile(config_path):
            raise Exception(
                f"Please check config file exist. config_path: {config_path}. "
                f"Copy .env.example to .env and fill in your settings.")
        self.config_path = config_path
        self.config_data = self._read_from_env(config_path)

    def __new__(cls, *args, **kwargs):
        if not hasattr(Config, "_instance"):
            with Config._instance_lock:
                if not hasattr(Config, "_instance"):
                    Config._instance = object.__new__(cls)
        return Config._instance

    def _read_from_env(self, path):
        # dotenv_values 只解析文件，不污染进程环境变量
        # strip_quotes 处理引号；行内说明统一写成「空格 + #」形式
        return {k: v for k, v in dotenv_values(path).items()
                if v is not None and v != ''}

    def _get(self, key):
        return self.config_data.get(key)

    @property
    def db_path(self):
        """
        SQLite 数据库文件路径（零安装）。
        相对路径相对仓库根解析；缺省 data/chickenfarm.db。
        文件与父目录在建立连接/写入时自动创建。
        """
        raw = self._get("DB_PATH") or os.path.join('data', 'chickenfarm.db')
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = REPO_ROOT / path
        return str(path)

    @property
    def export_aip_plot_path(self):
        # 导出的回测分析图的路径
        path = self._get("EXPORT_AIP_PLOT_PATH")
        path = os.path.join(path, datetime.today().strftime('%Y-%m-%d'))
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def backtest_config(self):
        # 回测相关配置（下单口径、类型覆盖、采样窗口等），均为 BACKTEST_ 前缀的可选项
        result = {}
        for key, value in self.config_data.items():
            if key.startswith("BACKTEST_"):
                name = key[len("BACKTEST_"):].lower()
                result[name] = _parse_backtest_value(value)
        return result

    @property
    def export_stats_path(self):
        # 回测统计结果（p 值/效应量/CI/稳健性）导出目录，与图同级 stats/
        path = os.path.join(self._get("EXPORT_AIP_PLOT_PATH"),
                            datetime.today().strftime('%Y-%m-%d'), 'stats')
        os.makedirs(path, exist_ok=True)
        return path
