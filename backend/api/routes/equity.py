"""
Equity-specific REST endpoints.

Wave 0 stubs: fundamentals, short-interest, insiders, options return 501.
Wave 1 (plan 03-02): earnings, dividends, news implemented.
Wave 2 (plan 03-03): OHLCV multi-timeframe endpoint implemented.
Remaining stubs are replaced wave by wave in Phase 3 (Waves 2-3).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import yfinance as yf
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from api.redis_client import get_redis
from cache.ttl import cache_get, cache_set
from ingestion.sources.finnhub_source import fetch_company_news
from ..database import get_async_db
from models.ohlcv import OHLCV

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/equity", tags=["equity"])

VALID_INTERVALS = {"1d", "1wk", "1h", "4h"}
INTRADAY_INTERVALS = {"1h", "4h"}


@router.get("/ohlcv/{ticker}/{interval}")  # EQUITY-02, EQUITY-03
async def get_ohlcv(ticker: str, interval: str, db: AsyncSession = Depends(get_async_db)):
    """Return OHLCV bars for a ticker at a given interval (Wave 2).

    Supports intervals: 1d, 1wk, 1h, 4h.
    For intraday intervals (1h, 4h) time is returned as Unix seconds.
    For daily/weekly intervals time is returned as YYYY-MM-DD string.
    On DB miss for intraday, triggers on-demand yfinance fetch and stores result.
    Cached for 5m (quote tier) for intraday, 1h (fundamentals tier) for daily/weekly.
    """
    if interval not in VALID_INTERVALS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid interval '{interval}'. Valid: {sorted(VALID_INTERVALS)}"},
        )

    cache_tier = "quote" if interval in INTRADAY_INTERVALS else "fundamentals"
    cache_key = f"ohlcv:{ticker}:{interval}"

    redis_client = get_redis()
    cached = cache_get(redis_client, cache_key)
    if cached:
        return cached

    # Query DB for existing bars
    result = await db.execute(
        select(OHLCV)
        .where(OHLCV.ticker == ticker, OHLCV.interval == interval)
        .order_by(asc(OHLCV.time))
        .limit(500)
    )
    rows = result.scalars().all()

    if not rows and interval in INTRADAY_INTERVALS:
        # On-demand ingest for intraday data not yet in DB
        rows = await _ingest_intraday(ticker, interval, db)

    if not rows and interval not in INTRADAY_INTERVALS:
        # Daily/weekly: attempt on-demand fetch if no data in DB
        rows = await _ingest_daily(ticker, interval, db)

    bars = _rows_to_bars(rows, interval)
    response = {"ticker": ticker, "interval": interval, "bars": bars}
    cache_set(redis_client, cache_key, response, cache_tier)
    return response


async def _ingest_intraday(ticker: str, interval: str, db: AsyncSession):
    """Fetch intraday OHLCV from yfinance and upsert to DB. Returns list of OHLCV rows."""
    period = "60d" if interval == "1h" else "730d"
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        if df is None or df.empty:
            return []
        rows = []
        for ts, row in df.iterrows():
            ohlcv = OHLCV(
                time=ts.to_pydatetime(),
                ticker=ticker,
                interval=interval,
                open=float(row["Open"]) if row["Open"] is not None else None,
                high=float(row["High"]) if row["High"] is not None else None,
                low=float(row["Low"]) if row["Low"] is not None else None,
                close=float(row["Close"]) if row["Close"] is not None else None,
                volume=int(row["Volume"]) if row["Volume"] is not None else None,
                source="yfinance",
            )
            rows.append(ohlcv)
        # Upsert — merge on primary key (time, ticker, interval)
        for ohlcv_row in rows:
            await db.merge(ohlcv_row)
        await db.commit()
        return rows
    except Exception as exc:
        logger.warning("_ingest_intraday error for %s/%s: %s", ticker, interval, exc)
        await db.rollback()
        return []


async def _ingest_daily(ticker: str, interval: str, db: AsyncSession):
    """Fetch daily/weekly OHLCV from yfinance and upsert to DB. Returns list of OHLCV rows."""
    period = "max" if interval == "1wk" else "5y"
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        if df is None or df.empty:
            return []
        rows = []
        for ts, row in df.iterrows():
            ohlcv = OHLCV(
                time=ts.to_pydatetime(),
                ticker=ticker,
                interval=interval,
                open=float(row["Open"]) if row["Open"] is not None else None,
                high=float(row["High"]) if row["High"] is not None else None,
                low=float(row["Low"]) if row["Low"] is not None else None,
                close=float(row["Close"]) if row["Close"] is not None else None,
                volume=int(row["Volume"]) if row["Volume"] is not None else None,
                source="yfinance",
            )
            rows.append(ohlcv)
        for ohlcv_row in rows:
            await db.merge(ohlcv_row)
        await db.commit()
        return rows
    except Exception as exc:
        logger.warning("_ingest_daily error for %s/%s: %s", ticker, interval, exc)
        await db.rollback()
        return []


def _rows_to_bars(rows, interval: str) -> list:
    """Convert OHLCV model rows to chart-ready bar dicts.

    Intraday intervals return Unix timestamp (seconds) as time.
    Daily/weekly intervals return 'YYYY-MM-DD' string as time.
    """
    is_intraday = interval in INTRADAY_INTERVALS
    bars = []
    for row in rows:
        if is_intraday:
            # lightweight-charts requires Unix seconds for intraday
            t = row.time
            if hasattr(t, "timestamp"):
                time_val = int(t.timestamp())
            else:
                time_val = int(t)
        else:
            # lightweight-charts accepts 'YYYY-MM-DD' for daily/weekly
            t = row.time
            if hasattr(t, "strftime"):
                time_val = t.strftime("%Y-%m-%d")
            else:
                time_val = str(t)[:10]
        bars.append({
            "time": time_val,
            "open": float(row.open) if row.open is not None else None,
            "high": float(row.high) if row.high is not None else None,
            "low": float(row.low) if row.low is not None else None,
            "close": float(row.close) if row.close is not None else None,
            "volume": int(row.volume) if row.volume is not None else None,
        })
    return bars


@router.get("/earnings/{ticker}")  # EQUITY-04
async def get_earnings(ticker: str):
    """Return earnings calendar dates for a ticker (Wave 1).

    Returns a list of upcoming/recent earnings dates from yfinance.
    Cached for 24h (fundamentals tier).
    Falls back to empty list on yfinance errors.
    """
    redis_client = get_redis()

    # Cache check (24h TTL)
    cached = cache_get(redis_client, f"earnings:{ticker}")
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        df = t.get_earnings_dates(limit=12)
        if df is not None and not df.empty:
            # DatetimeIndex — convert to YYYY-MM-DD strings
            earnings_dates = [
                d.strftime("%Y-%m-%d") for d in df.index if d is not None
            ]
        else:
            earnings_dates = []
        response = {
            "ticker": ticker,
            "earnings_dates": earnings_dates,
            "source": "yfinance",
        }
    except Exception as exc:
        logger.warning("get_earnings yfinance error for %s: %s", ticker, exc)
        response = {
            "ticker": ticker,
            "earnings_dates": [],
            "source": "yfinance",
            "error": "unavailable",
        }

    cache_set(redis_client, f"earnings:{ticker}", response, "fundamentals")
    return response


@router.get("/dividends/{ticker}")  # EQUITY-05
async def get_dividends(ticker: str):
    """Return dividend history for a ticker (Wave 1).

    Returns a list of {"date": "YYYY-MM-DD", "amount": float} dicts from yfinance.
    Cached for 24h (fundamentals tier).
    Falls back to empty list on yfinance errors.
    """
    redis_client = get_redis()

    # Cache check (24h TTL)
    cached = cache_get(redis_client, f"dividends:{ticker}")
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        divs = t.dividends  # pandas Series with DatetimeIndex
        if divs is not None and len(divs) > 0:
            dividends = [
                {"date": idx.strftime("%Y-%m-%d"), "amount": float(val)}
                for idx, val in divs.items()
            ]
        else:
            dividends = []
        response = {
            "ticker": ticker,
            "dividends": dividends,
            "source": "yfinance",
        }
    except Exception as exc:
        logger.warning("get_dividends yfinance error for %s: %s", ticker, exc)
        response = {
            "ticker": ticker,
            "dividends": [],
            "source": "yfinance",
            "error": "unavailable",
        }

    cache_set(redis_client, f"dividends:{ticker}", response, "fundamentals")
    return response


@router.get("/fundamentals/{ticker}")  # EQUITY-06 (enhanced with ROE)
async def get_fundamentals(ticker: str):
    """Return fundamentals (P/E, EV/EBITDA, ROE, D/E, market cap). Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "fundamentals"})


@router.get("/short-interest/{ticker}")  # EQUITY-07
async def get_short_interest(ticker: str):
    """Return short interest data. US-only on free tier. Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "short_interest"})


@router.get("/insiders/{ticker}")  # EQUITY-08
async def get_insiders(ticker: str):
    """Return insider transaction clusters. US-only on free tier. Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "insiders"})


@router.get("/options/{ticker}")  # EQUITY-09
async def get_options(ticker: str):
    """Return options chain with Black-Scholes Greeks. Implemented in Wave 3."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "options"})


@router.get("/news/{ticker}")  # EQUITY-10
async def get_news(ticker: str):
    """Return company news headlines for a ticker (Wave 1).

    Fetches last 30 days of news from Finnhub REST API.
    Falls back to empty list with stale=True when API key absent or on error.
    Cached for 5m (news tier).
    """
    redis_client = get_redis()

    # Cache check (5m TTL)
    cached = cache_get(redis_client, f"news:{ticker}")
    if cached:
        return cached

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        response = {
            "ticker": ticker,
            "news": [],
            "stale": True,
            "error": "FINNHUB_API_KEY not configured",
        }
        # Don't cache the no-key case — key may be set soon
        return response

    now = datetime.now(tz=timezone.utc)
    to_date = now.strftime("%Y-%m-%d")
    from_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        raw_articles = fetch_company_news(ticker, api_key, from_date, to_date)
        news = [
            {
                "headline": a.get("headline", ""),
                "source": a.get("source", ""),
                "url": a.get("url", ""),
                "datetime": a.get("datetime", ""),
                "summary": a.get("summary", ""),
            }
            for a in (raw_articles or [])
        ]
        response = {
            "ticker": ticker,
            "news": news,
            "stale": False,
        }
    except Exception as exc:
        logger.warning("get_news finnhub error for %s: %s", ticker, exc)
        response = {
            "ticker": ticker,
            "news": [],
            "stale": True,
            "error": "unavailable",
        }

    cache_set(redis_client, f"news:{ticker}", response, "news")
    return response
