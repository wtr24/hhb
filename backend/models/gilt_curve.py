"""SQLAlchemy model for gilt_curve hypertable — BoE daily nominal zero-coupon spot curve."""
from sqlalchemy import Column, String, Float, DateTime
from .base import Base


class GiltCurve(Base):
    __tablename__ = "gilt_curve"

    time = Column(DateTime(timezone=True), primary_key=True)
    source = Column(String(20), primary_key=True, default="boe")
    tenor_6m = Column(Float, nullable=True)
    tenor_1y = Column(Float, nullable=True)
    tenor_2y = Column(Float, nullable=True)
    tenor_3y = Column(Float, nullable=True)
    tenor_5y = Column(Float, nullable=True)
    tenor_7y = Column(Float, nullable=True)
    tenor_10y = Column(Float, nullable=True)
    tenor_15y = Column(Float, nullable=True)
    tenor_20y = Column(Float, nullable=True)
    tenor_25y = Column(Float, nullable=True)
    tenor_30y = Column(Float, nullable=True)
