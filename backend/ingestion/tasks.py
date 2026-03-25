import json
import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

from .celery_app import app
from .config import SEED_TICKERS, RETRY_COUNTDOWNS
from .sources.yfinance_source import fetch_ohlcv_and_fundamentals, fetch_ohlcv_batch
from api.database import SessionLocal
from api.redis_client import redis_client
from cache.ttl import cache_set
from models.ohlcv import OHLCV
from models.fundamentals import Fundamentals

logger = logging.getLogger(__name__)


@app.task
def health_check_task():
    """Placeholder task to verify Celery worker is processing tasks."""
    return {"status": "celery_ok"}


@app.task(bind=True, max_retries=3)
def ingest_ohlcv_batch(self):
    """Scheduled batch task: fetch and upsert OHLCV + fundamentals for all seed tickers."""
    try:
        results = fetch_ohlcv_batch(SEED_TICKERS)
        with SessionLocal() as session:
            for result in results:
                _upsert_result(session, result)
            session.commit()
    except Exception as exc:
        attempt = self.request.retries
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        logger.error(f"ingest_ohlcv_batch failed (attempt {attempt}): {exc}")
        raise self.retry(exc=exc, countdown=countdown)


@app.task(bind=True, max_retries=3)
def ingest_ticker(self, ticker: str):
    """On-demand single ticker ingest task."""
    try:
        result = fetch_ohlcv_and_fundamentals(ticker)
        with SessionLocal() as session:
            _upsert_result(session, result)
            session.commit()

        # Build the message for pub/sub and cache
        msg = {
            "channel": f"quotes:{ticker}",
            "ticker": ticker,
            "price": result["price"],
            "change_pct": None,
            "stale": False,
            "timestamp": result["fetched_at"],
            "fundamentals": result["fundamentals"],
        }
        if result["ohlcv"]:
            last = result["ohlcv"][-1]
            msg.update({
                "open": last["open"],
                "high": last["high"],
                "low": last["low"],
                "close": last["close"],
                "volume": last["volume"],
            })

        redis_client.publish(f"quotes:{ticker}", json.dumps(msg, default=str))
        cache_set(redis_client, f"quote:{ticker}", msg, "quote")
    except Exception as exc:
        attempt = self.request.retries
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        logger.error(f"ingest_ticker({ticker}) failed (attempt {attempt}): {exc}")
        raise self.retry(exc=exc, countdown=countdown)


def _upsert_result(session, result: dict) -> None:
    """Upsert OHLCV rows and fundamentals from a fetch result dict."""
    for row in result.get("ohlcv", []):
        stmt = (
            pg_insert(OHLCV)
            .values(
                time=row["time"],
                ticker=row["ticker"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                source=row["source"],
            )
            .on_conflict_do_nothing(index_elements=["time", "ticker"])
        )
        session.execute(stmt)

    ticker = None
    if result.get("ohlcv"):
        ticker = result["ohlcv"][0]["ticker"]
    if ticker and result.get("fundamentals"):
        fund = result["fundamentals"]
        stmt = (
            pg_insert(Fundamentals)
            .values(
                time=datetime.now(timezone.utc),
                ticker=ticker,
                pe_ratio=fund.get("pe_ratio"),
                ev_ebitda=fund.get("ev_ebitda"),
                market_cap=fund.get("market_cap"),
                debt_equity=fund.get("debt_equity"),
                source="yfinance",
            )
            .on_conflict_do_nothing(index_elements=["time", "ticker"])
        )
        session.execute(stmt)
