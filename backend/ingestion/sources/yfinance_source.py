import yfinance as yf
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def fetch_ohlcv_and_fundamentals(ticker: str) -> dict:
    """Fetch OHLCV bars + fundamentals for a single ticker."""
    t = yf.Ticker(ticker)
    hist = t.history(period="5d", interval="1d")
    ohlcv_rows = []
    for idx, row in hist.iterrows():
        ohlcv_rows.append({
            "time": idx.to_pydatetime().replace(tzinfo=timezone.utc),
            "ticker": ticker,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
            "source": "yfinance",
        })

    try:
        fi = t.fast_info
        price = fi.last_price
        market_cap = fi.market_cap
    except Exception:
        price = ohlcv_rows[-1]["close"] if ohlcv_rows else None
        market_cap = None

    try:
        info = t.info
        fundamentals = {
            "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "market_cap": info.get("marketCap") or market_cap,
            "debt_equity": info.get("debtToEquity"),
        }
    except Exception:
        fundamentals = {"pe_ratio": None, "ev_ebitda": None, "market_cap": market_cap, "debt_equity": None}

    return {
        "ohlcv": ohlcv_rows,
        "price": price,
        "fundamentals": fundamentals,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_ohlcv_batch(tickers: list) -> list:
    results = []
    for ticker in tickers:
        try:
            results.append(fetch_ohlcv_and_fundamentals(ticker))
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")
        time.sleep(0.5)  # prevent Yahoo Finance 429
    return results
