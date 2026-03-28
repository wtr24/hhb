"""
Finnhub REST API helper functions.

All calls respect the 60 req/min rate limit via check_rate_limit().
Returns empty structures (not exceptions) on HTTP errors.
"""
import logging
import requests

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"
_TIMEOUT = 10  # seconds


def _get_redis():
    """Lazy-import redis_client to avoid circular imports at module load time."""
    from api.redis_client import redis_client
    return redis_client


def _check_rate(source: str = "finnhub") -> bool:
    """Return True if rate limit allows the call, False otherwise."""
    from cache.rate_limiter import check_rate_limit
    return check_rate_limit(_get_redis(), source)


def fetch_short_interest(symbol: str, api_key: str) -> dict | None:
    """
    Fetch latest short interest data for a symbol from Finnhub.

    Parameters
    ----------
    symbol : str
        Ticker symbol (US only — LSE tickers return None on free tier).
    api_key : str
        Finnhub API key.

    Returns
    -------
    dict or None — latest short interest entry, or None on error / no data.
    """
    if not _check_rate():
        logger.warning("finnhub rate limit hit — skipping fetch_short_interest(%s)", symbol)
        return None

    url = f"{FINNHUB_BASE}/stock/short-interest"
    params = {"symbol": symbol, "token": api_key}
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        # Response: {"data": [...], "symbol": "AAPL"}
        entries = data.get("data") or []
        if not entries:
            return None
        # Return the most recent entry (last in list)
        return entries[-1]
    except requests.RequestException as exc:
        logger.error("finnhub fetch_short_interest error for %s: %s", symbol, exc)
        return None


def fetch_insider_transactions(symbol: str, api_key: str) -> list:
    """
    Fetch insider transaction history for a symbol from Finnhub.

    Parameters
    ----------
    symbol : str
        Ticker symbol.
    api_key : str
        Finnhub API key.

    Returns
    -------
    list[dict] — insider transaction records from the 'data' array.
    Empty list on error or no data.
    """
    if not _check_rate():
        logger.warning("finnhub rate limit hit — skipping fetch_insider_transactions(%s)", symbol)
        return []

    url = f"{FINNHUB_BASE}/stock/insider-transactions"
    params = {"symbol": symbol, "token": api_key}
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data") or []
    except requests.RequestException as exc:
        logger.error("finnhub fetch_insider_transactions error for %s: %s", symbol, exc)
        return []


def fetch_company_news(
    symbol: str,
    api_key: str,
    from_date: str,
    to_date: str,
) -> list:
    """
    Fetch company news articles for a symbol from Finnhub.

    Parameters
    ----------
    symbol : str
        Ticker symbol.
    api_key : str
        Finnhub API key.
    from_date : str
        Start date in YYYY-MM-DD format.
    to_date : str
        End date in YYYY-MM-DD format.

    Returns
    -------
    list[dict] — news article records. Empty list on error.
    """
    if not _check_rate():
        logger.warning("finnhub rate limit hit — skipping fetch_company_news(%s)", symbol)
        return []

    url = f"{FINNHUB_BASE}/company-news"
    params = {
        "symbol": symbol,
        "from": from_date,
        "to": to_date,
        "token": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json() or []
    except requests.RequestException as exc:
        logger.error("finnhub fetch_company_news error for %s: %s", symbol, exc)
        return []
