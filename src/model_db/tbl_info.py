from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, CHAR

from apollo.src.model_db.database import Database

Base = declarative_base()


class InfoTable(Base):

    __tablename__ = 'tbl_info'

    name = Column(VARCHAR(255), unique=True, nullable=False)
    code = Column(CHAR(6), primary_key=True)
    rate = Column(DECIMAL(5, 4))
    feeinfo = Column(VARCHAR(255))
    url = Column(VARCHAR(255))
    update_time = Column(DateTime, onupdate=datetime.now(), default=datetime.now())

    @staticmethod
    def get_by_code(code):
        return Database().query(InfoTable).filter_by(code=code).first()
