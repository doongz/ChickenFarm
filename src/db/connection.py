"""
统一 SQLite 引擎工厂。

整个项目使用单个 SQLite 文件（零安装、无需账号），替代原 MySQL。
每个连接开启 WAL 日志与 busy_timeout：
- WAL：读写可并发，采集/回测期间读取不被写入阻塞；
- busy_timeout：锁被短暂占用时自动等待而非立刻报 database is locked。
"""
from sqlalchemy import create_engine, event

from src.util.config import Config
from src.util.log import get_logger


logger = get_logger(__file__)

BUSY_TIMEOUT_MS = 10000   # 锁等待上限 10s

_engine = None


def _apply_sqlite_pragmas(dbapi_conn, _record):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


def get_engine():
    """返回指向配置 DB_PATH 的唯一 SQLite 引擎（首次调用时创建文件与父目录）。"""
    global _engine
    if _engine is None:
        db_path = Config().db_path
        engine = create_engine(f"sqlite:///{db_path}",
                               future=True)
        event.listen(engine, "connect", _apply_sqlite_pragmas)
        logger.debug(f"SQLite engine ready, db_path:{db_path}.")
        _engine = engine
    return _engine
