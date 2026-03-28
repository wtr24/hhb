from sqlalchemy import Column, String, Numeric, BigInteger, TIMESTAMP, Index
from .base import Base


class OHLCV(Base):
    __tablename__ = "ohlcv"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    ticker = Column(String(20), primary_key=True, nullable=False)
    open = Column(Numeric(18, 6))
    high = Column(Numeric(18, 6))
    low = Column(Numeric(18, 6))
    close = Column(Numeric(18, 6))
    volume = Column(BigInteger())
    source = Column(String(20))
    interval = Column(String(5), default='1d', nullable=False)

    __table_args__ = (
        Index("ix_ohlcv_ticker_time_interval", "ticker", "time", "interval"),
    )
