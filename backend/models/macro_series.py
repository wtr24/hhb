from sqlalchemy import Column, String, Numeric, TIMESTAMP, Index
from .base import Base


class MacroSeries(Base):
    __tablename__ = "macro_series"

    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    series_id = Column(String(30), primary_key=True, nullable=False)
    value = Column(Numeric(18, 6))
    source = Column(String(20), default="fred")

    __table_args__ = (
        Index("ix_macro_series_id_time", "series_id", "time"),
    )
