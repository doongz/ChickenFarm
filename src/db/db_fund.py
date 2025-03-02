import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ChickenFarm.src.util.config import Config


config = Config()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=Singleton):

    def __init__(self):
        # self.engine = create_engine(
        #     f"mysql+pymysql://{config.db_username}:{config.db_password}@{config.db_address}:{config.db_port}/{config.db_fund}"
        # )
        self.engine = create_engine(
            f"mysql+pymysql://{config.db_username}@{config.db_address}:{config.db_port}/{config.db_fund}"
        )
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

    def update_tbl(self, clz):
        return self.session.update(clz)

    def save(self, obj):
        if not self.session.object_session(obj):
            self.add(obj)
        self.session.commit()

    def execute(self, stmt):
        return self.session.execute(stmt)
