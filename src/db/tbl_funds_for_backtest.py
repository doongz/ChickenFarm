from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, CHAR

from ChickenFarm.src.db.db_fund import Database

Base = declarative_base()


class FundsForBacktestTable(Base):

    __tablename__ = 'tbl_funds_for_backtest'

    name = Column(VARCHAR(256), unique=True, nullable=False)
    code = Column(CHAR(6), primary_key=True)
    filed = Column(VARCHAR(255))
    update_time = Column(DateTime, onupdate=datetime.now(),
                         default=datetime.now())
    create_time = Column(DateTime, default=datetime.now())
    comment = Column(VARCHAR(255))
    buy_rate = Column(DECIMAL(5, 4))
    sell_rate_info = Column(VARCHAR(255))
    url = Column(VARCHAR(255))

    @staticmethod
    def get_by_code(code):
        return Database().query(FundsForBacktestTable).filter_by(code=code).first()

    @staticmethod
    def get_by_filed(filed):
        # 包含持仓和清仓的基金
        return Database().query(FundsForBacktestTable).filter_by(filed=filed).all()

    @staticmethod
    def get_all_code():
        code_list = [f.code for f in Database().query(
            FundsForBacktestTable).all()]
        return code_list

    @staticmethod
    def get_all():
        return Database().query(FundsForBacktestTable).all()
