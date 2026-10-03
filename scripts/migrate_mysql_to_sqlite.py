"""
一次性数据迁移：MySQL → SQLite。

在仍可连接原 MySQL 时运行本脚本，把原 4 个 MySQL 库中的全部表与数据
完整写入目标 SQLite 文件（默认配置中的 DB_PATH）。各表行数会与原表逐一比对。

前置：运行环境中仍需可 import pymysql（pip install pymysql，仅迁移期使用）。

用法（仓库根目录）：
    .venv/bin/python scripts/migrate_mysql_to_sqlite.py
可选：
    --target /path/to/new.db     覆盖目标 SQLite 路径（默认取 .env 的 DB_PATH）
MySQL 连接信息仍从旧环境变量读取时，可在命令前临时提供，或直接修改下方默认值。
"""
import os
import sys
import argparse

import pandas as pd
from sqlalchemy import create_engine

from src.util.config import Config
from src.db.connection import _apply_sqlite_pragmas
from sqlalchemy import event


# 原 MySQL 连接信息（如与本地不一致，按需修改或通过环境变量覆盖）
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_ADDRESS = os.getenv("MYSQL_ADDRESS", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASES = ["db_fund", "db_netvalue", "db_backtest", "db_etf"]


def mysql_engine(database):
    url = (f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
           f"@{MYSQL_ADDRESS}:{MYSQL_PORT}/{database}")
    return create_engine(url)


def list_tables(engine):
    from sqlalchemy import text
    with engine.connect() as conn:
        rows = conn.execute(text("SHOW TABLES")).fetchall()
    return [r[0] for r in rows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target")
    args = parser.parse_args()

    target = args.target or Config().db_path
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)

    dst = create_engine(f"sqlite:///{target}", future=True)
    event.listen(dst, "connect", _apply_sqlite_pragmas)

    total_ok = True
    for database in MYSQL_DATABASES:
        src = mysql_engine(database)
        try:
            tables = list_tables(src)
        except Exception as error:
            print(f"[ERROR] 无法连接/读取 {database}: {error}")
            total_ok = False
            continue

        print(f"\n=== {database} ({len(tables)} tables) ===")
        for table in tables:
            df = pd.read_sql_table(table, src)
            df.to_sql(table, dst, if_exists="replace", index=False)
            with dst.connect() as conn:
                from sqlalchemy import text
                n_dst = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")).scalar()
            same = n_dst == len(df)
            total_ok &= same
            print(f"  {'OK ' if same else 'DIFF'} {table}: "
                  f"mysql={len(df)} sqlite={n_dst}")

    print("\n迁移结果:", "全部一致" if total_ok else "存在差异，请检查")
    sys.exit(0 if total_ok else 1)


if __name__ == "__main__":
    main()
