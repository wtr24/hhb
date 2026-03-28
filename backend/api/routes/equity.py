"""
Equity-specific REST endpoints.

Wave 0 stubs: options returns 501.
Wave 1 (plan 03-02): earnings, dividends, news implemented.
Wave 2 (plan 03-04): fundamentals, short-interest, insiders implemented.
Remaining stub (options) is replaced in Wave 3.
"""
import logging
import os
from datetime import datetime, timedelta, timezone

import yfinance as yf
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_db
from ..redis_client import get_redis
from cache.ttl import cache_get, cache_set
from ingestion.sources.finnhub_source import (
    fetch_company_news,
    fetch_short_interest,
    fetch_insider_transactions,
)
from analysis.insider import cluster_insiders
from models.fundamentals import Fundamentals

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


@router.get("/fundamentals/{ticker}")  # EQUITY-06
async def get_fundamentals(ticker: str, db: AsyncSession = Depends(get_async_db)):
    """Return fundamentals (P/E, EV/EBITDA, ROE, D/E, market cap). Wave 2.

    Queries Fundamentals table for latest row, then supplements ROE from yfinance
    if not present in DB. Cached 24h (fundamentals tier).
    """
    redis_client = get_redis()

    cached = cache_get(redis_client, f"fundamentals:{ticker}")
    if cached:
        return cached

    # Query DB for latest fundamentals row
    result = await db.execute(
        select(Fundamentals)
        .where(Fundamentals.ticker == ticker)
        .order_by(desc(Fundamentals.time))
        .limit(1)
    )
    fund_row = result.scalar_one_or_none()

    pe_ratio = None
    ev_ebitda = None
    roe = None
    debt_equity = None
    market_cap = None
    stale = True

    if fund_row:
        pe_ratio = float(fund_row.pe_ratio) if fund_row.pe_ratio is not None else None
        ev_ebitda = float(fund_row.ev_ebitda) if fund_row.ev_ebitda is not None else None
        roe = float(fund_row.roe) if fund_row.roe is not None else None
        debt_equity = float(fund_row.debt_equity) if fund_row.debt_equity is not None else None
        market_cap = int(fund_row.market_cap) if fund_row.market_cap is not None else None
        stale = False

    # Supplement ROE from yfinance if not in DB
    if roe is None:
        try:
            info = yf.Ticker(ticker).info
            raw_roe = info.get("returnOnEquity")
            if raw_roe is not None:
                roe = float(raw_roe)
        except Exception as exc:
            logger.warning("get_fundamentals yfinance ROE fetch error for %s: %s", ticker, exc)

    response = {
        "ticker": ticker,
        "pe_ratio": pe_ratio,
        "ev_ebitda": ev_ebitda,
        "roe": roe,
        "debt_equity": debt_equity,
        "market_cap": market_cap,
        "stale": stale,
        "source": "yfinance",
    }

    cache_set(redis_client, f"fundamentals:{ticker}", response, "fundamentals")
    return response


@router.get("/short-interest/{ticker}")  # EQUITY-07
async def get_short_interest(ticker: str):
    """Return short interest data. US-only on Finnhub free tier. Wave 2."""
    # LSE tickers (.L suffix) and indices (^ prefix) not supported on free tier
    if ticker.endswith(".L") or ticker.startswith("^"):
        return {
            "ticker": ticker,
            "available": False,
            "message": "Short interest data available for US tickers only (Finnhub free tier limitation)",
        }

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return {
            "ticker": ticker,
            "available": False,
            "message": "FINNHUB_API_KEY not configured",
        }

    redis_client = get_redis()
    cached = cache_get(redis_client, f"short_interest:{ticker}")
    if cached:
        return cached

    try:
        data = fetch_short_interest(ticker, api_key)
    except Exception as exc:
        logger.warning("get_short_interest error for %s: %s", ticker, exc)
        data = None

    if not data:
        response = {
            "ticker": ticker,
            "available": False,
            "message": "Short interest unavailable on Finnhub free tier",
        }
        cache_set(redis_client, f"short_interest:{ticker}", response, "macro")
        return response

    short_interest = data.get("shortInterest")
    shares_outstanding = data.get("sharesOutstanding")
    pct_float = None
    if short_interest is not None and shares_outstanding and shares_outstanding > 0:
        pct_float = round(short_interest / shares_outstanding * 100, 4)

    response = {
        "ticker": ticker,
        "available": True,
        "short_interest": short_interest,
        "shares_outstanding": shares_outstanding,
        "pct_float": pct_float,
        "date": data.get("date"),
        "source": "finnhub",
    }
    cache_set(redis_client, f"short_interest:{ticker}", response, "macro")
    return response


@router.get("/insiders/{ticker}")  # EQUITY-08
async def get_insiders(ticker: str):
    """Return insider transaction clusters. US-only on Finnhub free tier. Wave 2."""
    # LSE tickers (.L suffix) and indices (^ prefix) not supported on free tier
    if ticker.endswith(".L") or ticker.startswith("^"):
        return {
            "ticker": ticker,
            "available": False,
            "message": "Insider transaction data available for US tickers only (Finnhub free tier limitation)",
        }

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return {
            "ticker": ticker,
            "available": False,
            "message": "FINNHUB_API_KEY not configured",
        }

    redis_client = get_redis()
    cached = cache_get(redis_client, f"insiders:{ticker}")
    if cached:
        return cached

    try:
        transactions = fetch_insider_transactions(ticker, api_key)
    except Exception as exc:
        logger.warning("get_insiders error for %s: %s", ticker, exc)
        transactions = []

    clustered = cluster_insiders(transactions)
    response = {
        "ticker": ticker,
        "available": True,
        "buy_count": clustered["buy_count"],
        "sell_count": clustered["sell_count"],
        "buy_sell_ratio": clustered["buy_sell_ratio"],
        "multi_insider": clustered["multi_insider"],
        "clusters": clustered["clusters"],
        "source": "finnhub",
    }
    cache_set(redis_client, f"insiders:{ticker}", response, "macro")
    return response


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
