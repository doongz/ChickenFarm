from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, CHAR

from ChickenFarm.src.db.db_fund import Database

Base = declarative_base()


class InvestmentsTable(Base):

    __tablename__ = 'tbl_investments'

    name = Column(VARCHAR(255), unique=True, nullable=False)
    code = Column(CHAR(6), primary_key=True)
    amount = Column(DECIMAL(10, 2), default=0)
    period = Column(VARCHAR(255))
    data = Column(VARCHAR(255))
    state = Column(VARCHAR(255))
    update_time = Column(DateTime, onupdate=datetime.now(),
                         default=datetime.now())
    create_time = Column(DateTime, default=datetime.now())

    @staticmethod
    def get_by_code(code):
        return Database().query(InvestmentsTable).filter_by(code=code).first()
