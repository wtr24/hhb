"""
Equity-specific REST endpoints.

Wave 0 stubs: all replaced.
Wave 1 (plan 03-02): earnings, dividends, news implemented.
Wave 2 (plan 03-03): OHLCV multi-timeframe endpoint implemented.
Wave 2 (plan 03-04): fundamentals, short-interest, insiders implemented.
Wave 3 (plan 03-05): options chain with Black-Scholes Greeks implemented.
"""
import logging
import os
import statistics
from datetime import date, datetime, timedelta, timezone

import yfinance as yf
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, asc
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
from analysis.black_scholes import bs_greeks, iv_percentile_rank
from models.fundamentals import Fundamentals
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

    result = await db.execute(
        select(OHLCV)
        .where(OHLCV.ticker == ticker, OHLCV.interval == interval)
        .order_by(asc(OHLCV.time))
        .limit(500)
    )
    rows = result.scalars().all()

    if not rows and interval in INTRADAY_INTERVALS:
        rows = await _ingest_intraday(ticker, interval, db)

    if not rows and interval not in INTRADAY_INTERVALS:
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
    """Convert OHLCV model rows to chart-ready bar dicts."""
    is_intraday = interval in INTRADAY_INTERVALS
    bars = []
    for row in rows:
        if is_intraday:
            t = row.time
            time_val = int(t.timestamp()) if hasattr(t, "timestamp") else int(t)
        else:
            t = row.time
            time_val = t.strftime("%Y-%m-%d") if hasattr(t, "strftime") else str(t)[:10]
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
    """Return earnings calendar dates for a ticker (Wave 1)."""
    redis_client = get_redis()
    cached = cache_get(redis_client, f"earnings:{ticker}")
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        df = t.get_earnings_dates(limit=12)
        earnings_dates = (
            [d.strftime("%Y-%m-%d") for d in df.index if d is not None]
            if df is not None and not df.empty
            else []
        )
        response = {"ticker": ticker, "earnings_dates": earnings_dates, "source": "yfinance"}
    except Exception as exc:
        logger.warning("get_earnings yfinance error for %s: %s", ticker, exc)
        response = {"ticker": ticker, "earnings_dates": [], "source": "yfinance", "error": "unavailable"}

    cache_set(redis_client, f"earnings:{ticker}", response, "fundamentals")
    return response


@router.get("/dividends/{ticker}")  # EQUITY-05
async def get_dividends(ticker: str):
    """Return dividend history for a ticker (Wave 1)."""
    redis_client = get_redis()
    cached = cache_get(redis_client, f"dividends:{ticker}")
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        divs = t.dividends
        dividends = (
            [{"date": idx.strftime("%Y-%m-%d"), "amount": float(val)} for idx, val in divs.items()]
            if divs is not None and len(divs) > 0
            else []
        )
        response = {"ticker": ticker, "dividends": dividends, "source": "yfinance"}
    except Exception as exc:
        logger.warning("get_dividends yfinance error for %s: %s", ticker, exc)
        response = {"ticker": ticker, "dividends": [], "source": "yfinance", "error": "unavailable"}

    cache_set(redis_client, f"dividends:{ticker}", response, "fundamentals")
    return response


@router.get("/fundamentals/{ticker}")  # EQUITY-06
async def get_fundamentals(ticker: str, db: AsyncSession = Depends(get_async_db)):
    """Return fundamentals (P/E, EV/EBITDA, ROE, D/E, market cap). Wave 2."""
    redis_client = get_redis()
    cached = cache_get(redis_client, f"fundamentals:{ticker}")
    if cached:
        return cached

    result = await db.execute(
        select(Fundamentals)
        .where(Fundamentals.ticker == ticker)
        .order_by(desc(Fundamentals.time))
        .limit(1)
    )
    fund_row = result.scalar_one_or_none()

    pe_ratio = ev_ebitda = roe = debt_equity = market_cap = None
    stale = True

    if fund_row:
        pe_ratio = float(fund_row.pe_ratio) if fund_row.pe_ratio is not None else None
        ev_ebitda = float(fund_row.ev_ebitda) if fund_row.ev_ebitda is not None else None
        roe = float(fund_row.roe) if fund_row.roe is not None else None
        debt_equity = float(fund_row.debt_equity) if fund_row.debt_equity is not None else None
        market_cap = int(fund_row.market_cap) if fund_row.market_cap is not None else None
        stale = False

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
    if ticker.endswith(".L") or ticker.startswith("^"):
        return {
            "ticker": ticker,
            "available": False,
            "message": "Short interest data available for US tickers only (Finnhub free tier limitation)",
        }

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return {"ticker": ticker, "available": False, "message": "FINNHUB_API_KEY not configured"}

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
        response = {"ticker": ticker, "available": False, "message": "Short interest unavailable on Finnhub free tier"}
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
    if ticker.endswith(".L") or ticker.startswith("^"):
        return {
            "ticker": ticker,
            "available": False,
            "message": "Insider transaction data available for US tickers only (Finnhub free tier limitation)",
        }

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return {"ticker": ticker, "available": False, "message": "FINNHUB_API_KEY not configured"}

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
    """Return options chain with Black-Scholes Greeks (Wave 3).

    Returns full calls/puts chain for the nearest expiry with delta, gamma, vega, theta
    computed via Black-Scholes using yfinance-provided impliedVolatility.
    IV surface grid computed across nearest 5 expiries.
    IV percentile rank computed across strikes of nearest-expiry chain.
    LSE tickers (.L suffix) return available=False (no options on Yahoo for UK stocks).
    Cached 15m (quote tier).
    """
    # LSE tickers have no options data on Yahoo Finance
    if ticker.endswith(".L"):
        return {
            "ticker": ticker,
            "available": False,
            "message": "Options not available for LSE tickers",
        }

    redis_client = get_redis()
    cache_key = f"options:{ticker}"
    cached = cache_get(redis_client, cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        expiries = t.options  # list of expiry date strings: ['2026-04-25', ...]
        if not expiries:
            response = {"ticker": ticker, "available": False, "message": "Options data unavailable"}
            cache_set(redis_client, cache_key, response, "quote")
            return response

        # Limit to nearest 5 expiries to stay within rate limits
        expiries = list(expiries[:5])

        # Current stock price
        info = t.info
        S = info.get("currentPrice") or info.get("regularMarketPrice", 100.0) or 100.0
        S = float(S)

        # Risk-free rate: hardcoded fallback
        # TODO: pull from yield_curve table bc_3month when Phase 8 wires it
        r = 0.045

        # Build full chain for nearest expiry
        nearest_expiry = expiries[0]
        expiry_date = date.fromisoformat(nearest_expiry)
        today = date.today()
        T_nearest = max((expiry_date - today).days / 365.0, 0.001)

        chain = t.option_chain(nearest_expiry)

        def _build_contracts(df, option_type: str) -> list:
            contracts = []
            for _, row in df.iterrows():
                sigma = float(row.get("impliedVolatility") or 0.0)
                strike = float(row.get("strike") or 0.0)
                greeks = bs_greeks(S, strike, T_nearest, r, sigma, option_type)
                contracts.append({
                    "strike": strike,
                    "bid": float(row.get("bid") or 0.0),
                    "ask": float(row.get("ask") or 0.0),
                    "lastPrice": float(row.get("lastPrice") or 0.0),
                    "volume": int(row.get("volume") or 0) if row.get("volume") is not None else 0,
                    "openInterest": int(row.get("openInterest") or 0) if row.get("openInterest") is not None else 0,
                    "iv": round(sigma, 4),
                    "delta": greeks["delta"],
                    "gamma": greeks["gamma"],
                    "vega": greeks["vega"],
                    "theta": greeks["theta"],
                })
            return contracts

        calls = _build_contracts(chain.calls, "call")
        puts = _build_contracts(chain.puts, "put")

        # Compute IV percentile rank across strikes of nearest-expiry chain
        # (rough rank across current chain IV values; 52-week rank is Phase 8)
        all_ivs = [c["iv"] for c in calls + puts if c["iv"] and c["iv"] > 0]
        median_iv = statistics.median(all_ivs) if all_ivs else 0.0
        iv_rank = iv_percentile_rank(median_iv, all_ivs) if all_ivs else 0.0

        # Build IV surface grid across nearest 5 expiries
        surface_strikes: list[float] = []
        surface_expiries: list[str] = []
        iv_matrix: list[list[float]] = []

        for exp in expiries:
            try:
                exp_chain = t.option_chain(exp)
                exp_date = date.fromisoformat(exp)
                exp_strikes = [float(r["strike"]) for _, r in exp_chain.calls.iterrows() if r.get("strike")]
                exp_ivs_by_strike = {
                    float(r["strike"]): float(r.get("impliedVolatility") or 0.0)
                    for _, r in exp_chain.calls.iterrows()
                }
                if not surface_strikes:
                    # Use first expiry strikes as the canonical strike axis
                    surface_strikes = sorted(exp_strikes)
                surface_expiries.append(exp)
                col = [exp_ivs_by_strike.get(s, 0.0) for s in surface_strikes]
                iv_matrix.append(col)
            except Exception as exp_exc:
                logger.debug("IV surface fetch error for expiry %s: %s", exp, exp_exc)
                surface_expiries.append(exp)
                iv_matrix.append([0.0] * len(surface_strikes))

        # Transpose: iv_matrix[row=strike_index][col=expiry_index]
        if iv_matrix and surface_strikes:
            n_strikes = len(surface_strikes)
            n_expiries = len(surface_expiries)
            transposed = [
                [iv_matrix[ei][si] if ei < len(iv_matrix) and si < len(iv_matrix[ei]) else 0.0
                 for ei in range(n_expiries)]
                for si in range(n_strikes)
            ]
        else:
            transposed = []

        iv_surface = {
            "strikes": surface_strikes,
            "expiries": surface_expiries,
            "iv_matrix": transposed,
        }

        response = {
            "ticker": ticker,
            "available": True,
            "expiry": nearest_expiry,
            "expiries": expiries,
            "current_price": S,
            "iv_rank": iv_rank,
            "calls": calls,
            "puts": puts,
            "iv_surface": iv_surface,
            "source": "yfinance+black_scholes",
        }
        cache_set(redis_client, cache_key, response, "quote")
        return response

    except Exception as exc:
        logger.warning("get_options error for %s: %s", ticker, exc)
        return {"ticker": ticker, "available": False, "message": "Options data unavailable"}


@router.get("/news/{ticker}")  # EQUITY-10
async def get_news(ticker: str):
    """Return company news headlines for a ticker (Wave 1)."""
    redis_client = get_redis()
    cached = cache_get(redis_client, f"news:{ticker}")
    if cached:
        return cached

    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return {"ticker": ticker, "news": [], "stale": True, "error": "FINNHUB_API_KEY not configured"}

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
        response = {"ticker": ticker, "news": news, "stale": False}
    except Exception as exc:
        logger.warning("get_news finnhub error for %s: %s", ticker, exc)
        response = {"ticker": ticker, "news": [], "stale": True, "error": "unavailable"}

    cache_set(redis_client, f"news:{ticker}", response, "news")
    return response
