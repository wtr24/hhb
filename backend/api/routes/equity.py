"""
Equity-specific REST endpoints.

Wave 0 stubs: fundamentals, short-interest, insiders, options return 501.
Wave 1 (plan 03-02): earnings, dividends, news implemented.
Remaining stubs are replaced wave by wave in Phase 3 (Waves 2-3).
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import yfinance as yf
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.redis_client import get_redis
from cache.ttl import cache_get, cache_set
from ingestion.sources.finnhub_source import fetch_company_news

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/equity", tags=["equity"])


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
