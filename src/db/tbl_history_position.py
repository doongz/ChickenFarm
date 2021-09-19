from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, BIGINT

from ChickenFarm.src.db.types import Filed


Base = declarative_base()


class HistroyPositionTable(Base):

    __tablename__ = 'tbl_history_position'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.now())
    total = Column(DECIMAL(10, 2))

    FACTURE = Column(DECIMAL(10, 2), name=Filed.FACTURE)
    RESOURCE = Column(DECIMAL(10, 2), name=Filed.RESOURCE)
    SEMI = Column(DECIMAL(10, 2), name=Filed.SEMI)
    MEDICAL = Column(DECIMAL(10, 2), name=Filed.MEDICAL)
    CONSUME = Column(DECIMAL(10, 2), name=Filed.CONSUME)
    FINANCE = Column(DECIMAL(10, 2), name=Filed.FINANCE)
    HK = Column(DECIMAL(10, 2), name=Filed.HK)
    US = Column(DECIMAL(10, 2), name=Filed.US)

    comment = Column(VARCHAR(255))