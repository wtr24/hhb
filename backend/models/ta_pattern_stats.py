"""SQLAlchemy model for ta_pattern_stats hypertable."""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from .base import Base


class TAPatternStats(Base):
    __tablename__ = "ta_pattern_stats"

    time = Column(DateTime(timezone=True), primary_key=True)
    ticker = Column(String(20), primary_key=True)
    timeframe = Column(String(5), primary_key=True)
    pattern_name = Column(String(50), primary_key=True)
    n_occurrences = Column(Integer, nullable=False)
    n_wins = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    is_bullish = Column(Boolean, nullable=False)
