from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, CHAR

from ChickenFarm.src.db.db_fund import Database

Base = declarative_base()


class AssetsTable(Base):

    __tablename__ = 'tbl_assets'

    name = Column(VARCHAR(255), unique=True, nullable=False)
    code = Column(CHAR(6), primary_key=True)
    filed = Column(VARCHAR(255))
    position = Column(DECIMAL(10, 2), default=0)
    netvalue = Column(DECIMAL(10, 4), default=0)
    profit = Column(DECIMAL(10, 2), default=0)
    profit_rate = Column(DECIMAL(5, 4), default=0)
    update_time = Column(DateTime, onupdate=datetime.now(),
                         default=datetime.now())
    create_time = Column(DateTime, default=datetime.now())
    comment = Column(VARCHAR(255))
    buy_rate = Column(DECIMAL(5, 4))
    sell_rate_info = Column(VARCHAR(255))
    url = Column(VARCHAR(255))

    @staticmethod
    def get_by_code(code):
        return Database().query(AssetsTable).filter_by(code=code).first()

    @staticmethod
    def get_holding_by_filed(filed):
        # 仅包含持仓中的基金
        res = []
        for fund in Database().query(AssetsTable).filter_by(filed=filed).all():
            if fund.position != 0:
                res.append(fund)
        return res

    @staticmethod
    def get_all():
        return Database().query(AssetsTable).all()

    def get_attrs(self):
        attrs = []
        for attr in self.__dir__():
            if attr.startswith('_') or attr.startswith('get'):
                continue
            if attr == 'metadata':
                continue
            attrs.append(attr)
        return attrs
