from sqlalchemy import Column, String, Numeric, BigInteger, TIMESTAMP, Index
from .base import Base


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    ticker = Column(String(20), primary_key=True, nullable=False)
    pe_ratio = Column(Numeric(10, 4))
    ev_ebitda = Column(Numeric(10, 4))
    market_cap = Column(BigInteger())
    debt_equity = Column(Numeric(10, 4))
    roe = Column(Numeric(10, 4))
    source = Column(String(20))

    __table_args__ = (
        Index("ix_fundamentals_ticker_time", "ticker", "time"),
    )
