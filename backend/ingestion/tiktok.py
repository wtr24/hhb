"""
TikTok transcript ingestion — fetches new videos from tracked accounts
and transcribes them via the Proactor API.

Called as a Celery task (scrape_tiktok) on an hourly beat schedule.
Already-scraped videos are skipped via the tiktok_videos primary key.
"""
import asyncio
import logging
import os
import random
import re
import uuid
from typing import Optional

import httpx
import yt_dlp

logger = logging.getLogger(__name__)

PROACTOR_URL = "https://api.proactor.ai:7788/v1/tourists/files/transcription"


# ── yt-dlp ────────────────────────────────────────────────────────────────────

def fetch_account_videos(account: str, max_videos: int = 10) -> list[dict]:
    """Synchronous — safe to call from a Celery worker thread."""
    handle = account.lstrip("@")
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": max_videos,
        "no_warnings": True,
    }
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.tiktok.com/@{handle}", download=False)
        for entry in (info or {}).get("entries", []):
            vid_url = entry.get("url") or entry.get("webpage_url") or ""
            vid_id = entry.get("id") or _extract_id(vid_url)
            if not vid_id:
                continue
            videos.append({
                "id": vid_id,
                "url": f"https://www.tiktok.com/@{handle}/video/{vid_id}",
                "title": entry.get("title"),
                "upload_date": entry.get("upload_date"),
            })
    return videos


def _extract_id(url: str) -> Optional[str]:
    m = re.search(r"/video/(\d+)", url)
    return m.group(1) if m else None


# ── Proactor transcription ────────────────────────────────────────────────────

async def _transcribe_async(video_url: str, video_id: str) -> list[dict]:
    language = os.getenv("PROACTOR_LANGUAGE", "en")
    payload = {
        "track_id": f"{uuid.uuid4()}_{video_id}",
        "fileUrl": video_url,
        "language": language,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(PROACTOR_URL, json=payload)
        resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise ValueError(f"Proactor error {body.get('code')}: {body.get('msg')}")
    return body.get("data", [])


def _segments_to_text(segments: list[dict]) -> str:
    return " ".join(s["text"] for s in segments if s.get("text"))


# ── Main scrape loop ──────────────────────────────────────────────────────────

def run_scrape() -> dict:
    """
    Entry point called by the Celery task.
    Returns a summary dict for logging.
    """
    accounts_raw = os.getenv("TIKTOK_ACCOUNTS", "")
    accounts = [a.strip() for a in accounts_raw.split(",") if a.strip()]
    if not accounts:
        logger.info("TikTok scrape: no accounts configured (set TIKTOK_ACCOUNTS)")
        return {"skipped": True}

    from api.database import SessionLocal
    from models.tiktok_video import TikTokVideo
    import json as _json

    total_new = 0
    total_errors = 0

    with SessionLocal() as db:
        for account in accounts:
            logger.info(f"TikTok: checking @{account.lstrip('@')} ...")
            try:
                videos = fetch_account_videos(account)
            except Exception as e:
                logger.warning(f"TikTok: failed to list videos for {account}: {e}")
                continue

            for i, v in enumerate(videos):
                vid_id = v["id"]

                # Skip already-scraped
                existing = db.get(TikTokVideo, vid_id)
                if existing:
                    logger.debug(f"TikTok: {vid_id} already scraped — skip")
                    continue

                logger.info(f"TikTok: new video {v['url']}")
                segments: list[dict] = []
                full_text = ""
                error: Optional[str] = None

                try:
                    segments = asyncio.run(_transcribe_async(v["url"], vid_id))
                    full_text = _segments_to_text(segments)
                    logger.info(f"TikTok: {len(segments)} segments for {vid_id}")
                    total_new += 1
                except Exception as e:
                    error = str(e)
                    total_errors += 1
                    logger.warning(f"TikTok: transcription failed for {vid_id}: {e}")

                db.add(TikTokVideo(
                    video_id=vid_id,
                    account=account.lstrip("@"),
                    url=v["url"],
                    title=v.get("title"),
                    upload_date=v.get("upload_date"),
                    segments=segments or None,
                    full_text=full_text or None,
                    error=error,
                ))
                db.commit()

                # Random delay between transcription calls
                if i < len(videos) - 1 and not error:
                    delay = random.uniform(3.0, 10.0)
                    import time
                    time.sleep(delay)

    logger.info(f"TikTok scrape done: {total_new} new, {total_errors} errors")
    return {"new": total_new, "errors": total_errors}
