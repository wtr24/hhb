"""
FX rate REST endpoint.

Closes EQUITY-11: GET /api/fx/{base}/{quote} returns latest rate from fx_rates table.
Deferred from Phase 2 (D-17 in 02-CONTEXT.md).
"""
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_db
from ..redis_client import get_redis
from cache.ttl import cache_get, cache_set
from models.fx_rate import FXRate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["fx"])


@router.get("/fx/{base}/{quote}")
async def get_fx_rate(base: str, quote: str, db: AsyncSession = Depends(get_async_db)):
    """
    Return the latest FX rate for a currency pair.

    Checks Redis cache first, then queries TimescaleDB fx_rates table.
    Returns the most recent row ordered by time descending.
    """
    redis_client = get_redis()
    pair_key = f"fx:{base.upper()}{quote.upper()}"

    # Step 1: Redis cache hit
    cached = cache_get(redis_client, pair_key)
    if cached:
        return {**cached, "stale": False}

    # Step 2: TimescaleDB latest row
    result = await db.execute(
        select(FXRate)
        .where(FXRate.base == base.upper())
        .where(FXRate.quote == quote.upper())
        .order_by(desc(FXRate.time))
        .limit(1)
    )
    row = result.scalar_one_or_none()

    if row:
        response = {
            "base": base.upper(),
            "quote": quote.upper(),
            "rate": float(row.rate),
            "timestamp": row.time.isoformat(),
            "stale": True,
        }
        cache_set(redis_client, pair_key, response, "fx")
        return response

    # Step 3: No data available
    return JSONResponse(
        status_code=404,
        content={"error": "fx_rate_not_found", "pair": f"{base.upper()}/{quote.upper()}"},
    )
