from sqlalchemy import Column, String, Numeric, TIMESTAMP
from .base import Base


class YieldCurve(Base):
    __tablename__ = "yield_curve"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    bc_1month = Column(Numeric(8, 4))
    bc_2month = Column(Numeric(8, 4))
    bc_3month = Column(Numeric(8, 4))
    bc_6month = Column(Numeric(8, 4))
    bc_1year = Column(Numeric(8, 4))
    bc_2year = Column(Numeric(8, 4))
    bc_3year = Column(Numeric(8, 4))
    bc_5year = Column(Numeric(8, 4))
    bc_7year = Column(Numeric(8, 4))
    bc_10year = Column(Numeric(8, 4))
    bc_20year = Column(Numeric(8, 4))
    bc_30year = Column(Numeric(8, 4))
    source = Column(String(20), default="us_treasury")
