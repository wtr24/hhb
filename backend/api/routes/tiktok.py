from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from sqlalchemy import desc

router = APIRouter(prefix="/api/tiktok", tags=["tiktok"])


@router.get("/videos")
def list_videos(
    account: Optional[str] = Query(None, description="Filter by handle e.g. ceowatcher"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """List scraped TikTok videos, newest first."""
    from api.database import SessionLocal
    from models.tiktok_video import TikTokVideo

    with SessionLocal() as db:
        q = db.query(TikTokVideo)
        if account:
            q = q.filter(TikTokVideo.account == account.lstrip("@"))
        videos = (
            q.order_by(desc(TikTokVideo.scraped_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
    return {
        "count": len(videos),
        "videos": [
            {
                "video_id": v.video_id,
                "account": v.account,
                "url": v.url,
                "title": v.title,
                "upload_date": v.upload_date,
                "full_text": v.full_text,
                "scraped_at": v.scraped_at.isoformat() if v.scraped_at else None,
                "error": v.error,
            }
            for v in videos
        ],
    }


@router.get("/videos/{video_id}")
def get_video(video_id: str):
    """Get a single video with full segments."""
    from api.database import SessionLocal
    from models.tiktok_video import TikTokVideo

    with SessionLocal() as db:
        v = db.get(TikTokVideo, video_id)
    if not v:
        raise HTTPException(404, f"Video {video_id} not found")
    return {
        "video_id": v.video_id,
        "account": v.account,
        "url": v.url,
        "title": v.title,
        "upload_date": v.upload_date,
        "segments": v.segments,
        "full_text": v.full_text,
        "scraped_at": v.scraped_at.isoformat() if v.scraped_at else None,
        "error": v.error,
    }


@router.get("/accounts")
def list_accounts():
    """List all scraped accounts with video counts."""
    from api.database import SessionLocal
    from models.tiktok_video import TikTokVideo
    from sqlalchemy import func

    with SessionLocal() as db:
        rows = (
            db.query(
                TikTokVideo.account,
                func.count(TikTokVideo.video_id).label("video_count"),
                func.max(TikTokVideo.scraped_at).label("last_scraped"),
            )
            .group_by(TikTokVideo.account)
            .order_by(desc("last_scraped"))
            .all()
        )
    return {
        "accounts": [
            {
                "account": r.account,
                "video_count": r.video_count,
                "last_scraped": r.last_scraped.isoformat() if r.last_scraped else None,
            }
            for r in rows
        ]
    }


@router.post("/scrape")
def trigger_scrape():
    """Manually trigger a TikTok scrape immediately (same as hourly job)."""
    from ingestion.tasks import scrape_tiktok
    task = scrape_tiktok.apply_async()
    return {"status": "triggered", "task_id": task.id}
