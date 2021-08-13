from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apollo.src.config.mysql import USER, PWD, ADDRESS, PORT, DB_FUND


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=Singleton):
    def __init__(self):
        engine = create_engine(f"mysql+pymysql://{USER}:{PWD}@{ADDRESS}:{PORT}/{DB_FUND}")
        # 创建DBSession类型:
        DBSession = sessionmaker(bind=engine)
        # 创建session对象:
        self.session = DBSession()

    def add(self, obj):
        # work
        self.session.add(obj)
        self.session.commit()

    def query(self, clz):
        # work
        return self.session.query(clz)

    def delete(self, obj):
        # work
        self.session.delete(obj)
        self.session.commit()

    def update(self):
        # work
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def update_tbl(self, clz):
        return self.session.update(clz)

    def save(self, obj):
        if not Session.object_session(obj):
            self.add(obj)
        self.session.commit()

    def execute(self, stmt):
        return self.session.execute(stmt)



