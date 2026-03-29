import json
import logging
from datetime import datetime, timezone

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .celery_app import app
from .config import SEED_TICKERS, RETRY_COUNTDOWNS
from .sources.yfinance_source import fetch_ohlcv_and_fundamentals, fetch_ohlcv_batch
from .sources.fred_source import fetch_fred_series
from .sources.frankfurter_source import fetch_fx_rates
from .sources.treasury_source import fetch_treasury_yield_curve
from api.database import SessionLocal
from api.redis_client import redis_client
from cache.rate_limiter import check_rate_limit
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
        if not check_rate_limit(redis_client, "yfinance"):
            logger.warning("Rate limit exceeded for yfinance, retrying")
            raise self.retry(countdown=RETRY_COUNTDOWNS[0])
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
        if not check_rate_limit(redis_client, "yfinance"):
            logger.warning("Rate limit exceeded for yfinance, retrying")
            raise self.retry(countdown=RETRY_COUNTDOWNS[0])
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


@app.task(bind=True, max_retries=3)
def ingest_macro_batch(self):
    """Scheduled task: ingest all FRED macro series."""
    from .config import FRED_SERIES_MAP
    try:
        if not check_rate_limit(redis_client, "fred"):
            logger.warning("Rate limit exceeded for fred, retrying")
            raise self.retry(countdown=RETRY_COUNTDOWNS[0])
        with SessionLocal() as session:
            for friendly_name, fred_id in FRED_SERIES_MAP.items():
                try:
                    observations = fetch_fred_series(fred_id)
                    rows = [
                        {"time": obs["date"], "series_id": fred_id,
                         "value": obs["value"], "source": "fred"}
                        for obs in observations
                    ]
                    if rows:
                        from models.macro_series import MacroSeries
                        stmt = pg_insert(MacroSeries.__table__).values(rows)
                        stmt = stmt.on_conflict_do_nothing(index_elements=["time", "series_id"])
                        session.execute(stmt)
                        session.commit()
                        # Cache latest value
                        cache_set(redis_client, f"macro:{friendly_name}", {
                            "series": friendly_name, "fred_id": fred_id,
                            "latest": observations[0] if observations else None,
                        }, "macro")
                        # Publish to Redis pub/sub
                        redis_client.publish(f"macro:{friendly_name}",
                            json.dumps({"channel": f"macro:{friendly_name}",
                                       "series": friendly_name,
                                       "value": observations[0]["value"] if observations else None,
                                       "stale": False}, default=str))
                except Exception as e:
                    logger.error(f"FRED ingest failed for {fred_id}: {e}")
    except Exception as exc:
        attempt = self.request.retries
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error("ingest_macro_batch exhausted retries", exc_info=exc)


@app.task(bind=True, max_retries=3)
def ingest_fx_rates(self):
    """Scheduled task: ingest Frankfurter FX rates for major pairs + GBP crosses."""
    try:
        if not check_rate_limit(redis_client, "frankfurter"):
            logger.warning("Rate limit exceeded for frankfurter, retrying")
            raise self.retry(countdown=RETRY_COUNTDOWNS[0])
        data = fetch_fx_rates("USD")
        api_date = data.get("date", "")
        try:
            row_time = datetime.fromisoformat(api_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            row_time = datetime.now(timezone.utc)

        rows = []
        for quote_currency, rate in data.get("rates", {}).items():
            rows.append({
                "time": row_time,
                "base": "USD",
                "quote": quote_currency,
                "rate": rate,
                "source": "frankfurter",
            })

        if rows:
            from models.fx_rate import FXRate
            with SessionLocal() as session:
                stmt = pg_insert(FXRate.__table__).values(rows)
                stmt = stmt.on_conflict_do_nothing(index_elements=["time", "base", "quote"])
                session.execute(stmt)
                session.commit()

            # Cache + publish per pair
            for row in rows:
                pair_key = f"{row['base']}{row['quote']}"
                msg = {"channel": f"fx:{pair_key}", "base": row["base"],
                       "quote": row["quote"], "rate": float(row["rate"]),
                       "timestamp": row_time.isoformat(), "stale": False}
                cache_set(redis_client, f"fx:{pair_key}", msg, "fx")
                redis_client.publish(f"fx:{pair_key}", json.dumps(msg, default=str))
    except Exception as exc:
        attempt = self.request.retries
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error("ingest_fx_rates exhausted retries", exc_info=exc)


@app.task(bind=True, max_retries=3)
def ingest_treasury_curve(self):
    """Scheduled task: ingest US Treasury XML yield curve."""
    try:
        if not check_rate_limit(redis_client, "us_treasury"):
            logger.warning("Rate limit exceeded for us_treasury, retrying")
            raise self.retry(countdown=RETRY_COUNTDOWNS[0])
        curve_rows = fetch_treasury_yield_curve()
        if curve_rows:
            from models.yield_curve import YieldCurve
            db_rows = []
            for row in curve_rows:
                db_row = {"time": row["date"], "source": "us_treasury"}
                for field in ["bc_1month", "bc_2month", "bc_3month", "bc_6month",
                              "bc_1year", "bc_2year", "bc_3year", "bc_5year",
                              "bc_7year", "bc_10year", "bc_20year", "bc_30year"]:
                    db_row[field] = row.get(field)
                db_rows.append(db_row)

            with SessionLocal() as session:
                stmt = pg_insert(YieldCurve.__table__).values(db_rows)
                stmt = stmt.on_conflict_do_nothing(index_elements=["time"])
                session.execute(stmt)
                session.commit()

            # Cache latest curve
            latest = curve_rows[-1] if curve_rows else None
            if latest:
                cache_set(redis_client, "yield_curve:latest", {
                    "date": latest["date"].isoformat() if hasattr(latest["date"], "isoformat") else str(latest["date"]),
                    **{k: v for k, v in latest.items() if k != "date"}
                }, "yield_curve")
    except Exception as exc:
        attempt = self.request.retries
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error("ingest_treasury_curve exhausted retries", exc_info=exc)


@app.task
def compute_nightly_pivot_points():
    """
    Nightly Celery beat task — TA-07.
    For each seed ticker, reads the most recent completed daily bar from TimescaleDB,
    computes all 5 pivot point methods, and upserts into pivot_points table.
    """
    from analysis.pivot_points import compute_all_methods
    from models.pivot_points import PivotPoints

    for ticker in SEED_TICKERS:
        try:
            with SessionLocal() as session:
                row = (
                    session.query(OHLCV)
                    .filter(OHLCV.ticker == ticker, OHLCV.interval == "1d")
                    .order_by(OHLCV.time.desc())
                    .first()
                )
                if row is None:
                    logger.warning(f"pivot_points: no daily bar for {ticker}, skipping")
                    continue

                high = float(row.high)
                low = float(row.low)
                close = float(row.close)
                open_ = float(row.open)
                bar_time = row.time

                methods = compute_all_methods(high, low, close, open_)

                # Delete existing rows for this ticker/timeframe/date to allow upsert
                session.query(PivotPoints).filter(
                    PivotPoints.ticker == ticker,
                    PivotPoints.timeframe == "1d",
                    PivotPoints.time == bar_time,
                ).delete(synchronize_session=False)

                for m in methods:
                    pivot_row = PivotPoints(
                        time=bar_time,
                        ticker=ticker,
                        timeframe="1d",
                        method=m["method"],
                        pp=m["pp"],
                        r1=m.get("r1"),
                        r2=m.get("r2"),
                        r3=m.get("r3"),
                        s1=m.get("s1"),
                        s2=m.get("s2"),
                        s3=m.get("s3"),
                    )
                    session.add(pivot_row)
                session.commit()
            logger.info(f"pivot_points computed: {ticker} 5 methods")
        except Exception as exc:
            logger.error(f"pivot_points failed for {ticker}: {exc}", exc_info=True)


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
