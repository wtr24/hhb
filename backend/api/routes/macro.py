import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_db
from ..redis_client import get_redis
from cache.ttl import cache_get, cache_set
from models.macro_series import MacroSeries
from ingestion.config import FRED_SERIES_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["macro"])


@router.get("/macro/{series}")
async def get_macro_series(series: str, db: AsyncSession = Depends(get_async_db)):
    """Return macro time series per D-14/D-15.
    Uses friendly name (e.g. 'cpi') mapped to FRED ID (e.g. 'CPIAUCSL').
    Returns last 24 months of observations by default.
    """
    if series not in FRED_SERIES_MAP:
        return JSONResponse(status_code=404, content={
            "error": f"Unknown series '{series}'. Available: {list(FRED_SERIES_MAP.keys())}"
        })

    fred_id = FRED_SERIES_MAP[series]
    redis_client = get_redis()

    # Check cache first
    cached = cache_get(redis_client, f"macro_series:{series}")
    if cached:
        return cached

    # Query TimescaleDB for last 24 months (~730 days)
    result = await db.execute(
        select(MacroSeries)
        .where(MacroSeries.series_id == fred_id)
        .order_by(desc(MacroSeries.time))
        .limit(300)
    )
    rows = result.scalars().all()

    if not rows:
        return JSONResponse(status_code=404, content={
            "error": f"No data for series '{series}' ({fred_id}). Run ingestion first."
        })

    observations = [
        {"date": row.time.isoformat(), "value": float(row.value) if row.value else None}
        for row in rows
    ]

    response = {
        "series": series,
        "fred_id": fred_id,
        "observations": observations,
        "stale": False,
        "last_updated": rows[0].time.isoformat() if rows else None,
    }

    cache_set(redis_client, f"macro_series:{series}", response, "macro")
    return response
