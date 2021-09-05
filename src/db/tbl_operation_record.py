from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, CHAR, BIGINT

from chicken_farm.src.db.db_fund import Database


Base = declarative_base()


class OperationRecordTable(Base):

    __tablename__ = 'tbl_operation_record'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    operate_id = Column(VARCHAR(20), nullable=False)
    name = Column(VARCHAR(255), nullable=False)
    code = Column(CHAR(6), nullable=False)
    operate_type = Column(VARCHAR(32), nullable=False)
    amount = Column(DECIMAL(10, 2))
    info_after_change = Column(VARCHAR(2048), nullable=False)
    info_before_change = Column(VARCHAR(2048), nullable=False)
    operate_time = Column(DateTime, default=datetime.now(), nullable=False)
    comment = Column(VARCHAR(255))

    @staticmethod
    def get_by_operate_id(operate_id):
        return Database().query(OperationRecordTable).filter_by(operate_id=operate_id).first()
