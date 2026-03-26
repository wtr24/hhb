import asyncio
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_db
from ..redis_client import get_redis
from cache.ttl import cache_get, cache_set
from models.ohlcv import OHLCV
from models.fundamentals import Fundamentals

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["quotes"])


@router.get("/quote/{ticker}")
async def get_quote(ticker: str, db: AsyncSession = Depends(get_async_db)):
    redis_client = get_redis()

    # Step 1: Redis cache hit
    cached = cache_get(redis_client, f"quote:{ticker}")
    if cached:
        return {**cached, "stale": False}

    # Step 2: TimescaleDB latest row
    ohlcv_result = await db.execute(
        select(OHLCV).where(OHLCV.ticker == ticker).order_by(desc(OHLCV.time)).limit(1)
    )
    ohlcv_row = ohlcv_result.scalar_one_or_none()

    fund_result = await db.execute(
        select(Fundamentals).where(Fundamentals.ticker == ticker).order_by(desc(Fundamentals.time)).limit(1)
    )
    fund_row = fund_result.scalar_one_or_none()

    if ohlcv_row:
        response = _build_quote_response(ticker, ohlcv_row, fund_row, stale=True)
        cache_set(redis_client, f"quote:{ticker}", response, "quote")
        return response

    # Step 3: No data — fire on-demand ingest (per D-11)
    from ingestion.tasks import ingest_ticker
    ingest_ticker.apply_async(args=[ticker])

    # Poll TimescaleDB for up to 10 seconds
    for _ in range(20):
        await asyncio.sleep(0.5)
        result = await db.execute(
            select(OHLCV).where(OHLCV.ticker == ticker).order_by(desc(OHLCV.time)).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            fund_result2 = await db.execute(
                select(Fundamentals).where(Fundamentals.ticker == ticker).order_by(desc(Fundamentals.time)).limit(1)
            )
            fund_row2 = fund_result2.scalar_one_or_none()
            response = _build_quote_response(ticker, row, fund_row2, stale=False)
            cache_set(redis_client, f"quote:{ticker}", response, "quote")
            return response

    # Step 4: Timeout — 503
    return JSONResponse(
        status_code=503,
        content={"error": "ingestion_timeout", "retry_after": 15}
    )


def _build_quote_response(ticker: str, ohlcv, fund, stale: bool) -> dict:
    """Build response per D-13 format."""
    response = {
        "ticker": ticker,
        "price": float(ohlcv.close) if ohlcv.close else None,
        "change_pct": None,  # computed when we have previous close
        "open": float(ohlcv.open) if ohlcv.open else None,
        "high": float(ohlcv.high) if ohlcv.high else None,
        "low": float(ohlcv.low) if ohlcv.low else None,
        "close": float(ohlcv.close) if ohlcv.close else None,
        "volume": int(ohlcv.volume) if ohlcv.volume else None,
        "stale": stale,
        "fundamentals": None,
    }
    if fund:
        response["fundamentals"] = {
            "pe_ratio": float(fund.pe_ratio) if fund.pe_ratio else None,
            "ev_ebitda": float(fund.ev_ebitda) if fund.ev_ebitda else None,
            "market_cap": int(fund.market_cap) if fund.market_cap else None,
            "debt_equity": float(fund.debt_equity) if fund.debt_equity else None,
        }
    return response
