"""SQLAlchemy model for pivot_points hypertable."""
from sqlalchemy import Column, String, Float, DateTime
from .base import Base


class PivotPoints(Base):
    __tablename__ = "pivot_points"

    time = Column(DateTime(timezone=True), primary_key=True)
    ticker = Column(String(20), primary_key=True)
    timeframe = Column(String(5), primary_key=True)
    method = Column(String(20), primary_key=True)
    pp = Column(Float, nullable=False)
    r1 = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    r3 = Column(Float, nullable=True)
    s1 = Column(Float, nullable=True)
    s2 = Column(Float, nullable=True)
    s3 = Column(Float, nullable=True)
