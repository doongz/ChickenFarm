from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, DECIMAL, VARCHAR, BIGINT

from chicken_farm.src.db.db_fund import Database
from chicken_farm.src.db.types import Filed


Base = declarative_base()


class HistroyPositionTable(Base):

    __tablename__ = 'tbl_history_position'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.now())
    total = Column(DECIMAL(10, 2))

    ENERGY = Column(DECIMAL(10, 2), name=Filed.ENERGY)
    SEMI = Column(DECIMAL(10, 2), name=Filed.SEMI)
    METALS = Column(DECIMAL(10, 2), name=Filed.METALS)
    MEDICAL = Column(DECIMAL(10, 2), name=Filed.MEDICAL)
    SPIRIT = Column(DECIMAL(10, 2), name=Filed.SPIRIT)
    HK = Column(DECIMAL(10, 2), name=Filed.HK)
    US = Column(DECIMAL(10, 2), name=Filed.US)
    BLUE = Column(DECIMAL(10, 2), name=Filed.BLUE)
    FINANCE = Column(DECIMAL(10, 2), name=Filed.FINANCE)

    comment = Column(VARCHAR(255))