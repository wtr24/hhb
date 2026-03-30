"""SQLAlchemy model for vix_term_structure hypertable — 15m VIX spot/3M/6M snapshots."""
from sqlalchemy import Column, String, Float, Boolean, DateTime
from .base import Base


class VixTermStructure(Base):
    __tablename__ = "vix_term_structure"

    time = Column(DateTime(timezone=True), primary_key=True)
    spot_vix = Column(Float, nullable=False)
    vix_3m = Column(Float, nullable=True)
    vix_6m = Column(Float, nullable=True)
    contango = Column(Boolean, nullable=True)
    regime = Column(String(20), nullable=True)
