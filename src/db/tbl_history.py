from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, CHAR, BIGINT


Base = declarative_base()


class HistoryTable(Base):

    __tablename__ = 'tbl_history'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    code = Column(CHAR(6))
    position = Column(DECIMAL(10, 2), default=0)
    netvalue = Column(DECIMAL(10, 4), default=0)
    profit = Column(DECIMAL(10, 2), default=0)
    profit_rate = Column(DECIMAL(5, 4), default=0)
    record_time = Column(DateTime, default=datetime.now())
