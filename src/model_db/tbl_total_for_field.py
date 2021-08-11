from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR

from apollo.src.model_db.database import Database


Base = declarative_base()


class TotalForField(Base):

    __tablename__ = 'tbl_total_for_field'

    filed = Column(VARCHAR(255), primary_key=True)
    buying = Column(DECIMAL(10, 2))
    selling = Column(DECIMAL(10, 2))
    position = Column(DECIMAL(10, 2))
    profit = Column(DECIMAL(10, 2))
    profit_rate = Column(DECIMAL(5, 4))
    update_time = Column(DateTime, onupdate=datetime.now, default=datetime.now)

    @staticmethod
    def get_by_filed(filed):
        return Database().query(TotalForField).filter_by(filed=filed).first()