from sqlalchemy import Column, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from .base import Base


class TikTokVideo(Base):
    __tablename__ = "tiktok_videos"

    video_id    = Column(String(30), primary_key=True)
    account     = Column(String(100), nullable=False)
    url         = Column(Text, nullable=False)
    title       = Column(Text)
    upload_date = Column(String(20))
    segments    = Column(JSONB)
    full_text   = Column(Text)
    scraped_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())
    error       = Column(Text)
