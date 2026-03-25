from sqlalchemy import Column, String, Numeric, TIMESTAMP, Index
from .base import Base


class FXRate(Base):
    __tablename__ = "fx_rates"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    base = Column(String(3), primary_key=True, nullable=False)
    quote = Column(String(3), primary_key=True, nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    source = Column(String(20), default="frankfurter")

    __table_args__ = (
        Index("ix_fx_rates_pair_time", "base", "quote", "time"),
    )
