import pandas as pd
from sqlalchemy.orm import sessionmaker

from src.db.connection import get_engine


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=Singleton):

    def __init__(self):
        self.engine = get_engine()
        # 标的清单表自动建表（ORM metadata；首次使用、替代原 MySQL DDL）
        from src.db.tbl_funds_for_backtest import Base
        Base.metadata.create_all(self.engine)
        # 创建DBSession类型:
        DBSession = sessionmaker(bind=self.engine)
        # 创建session对象:
        self.session = DBSession()

    def dispose(self):
        self.engine.dispose()

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()

    def query(self, clz):
        return self.session.query(clz)

    def delete(self, obj):
        self.session.delete(obj)
        self.session.commit()

    def update(self):
        self.session.commit()

    def to_df(self, tbl_name):
        return pd.read_sql(tbl_name, self.engine)

    def rollback(self):
        self.session.rollback()

    def save(self, obj):
        if not self.session.object_session(obj):
            self.add(obj)
        self.session.commit()

    def execute(self, stmt):
        return self.session.execute(stmt)
