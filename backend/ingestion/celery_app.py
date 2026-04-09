from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "hhbfin",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["ingestion.tasks"],
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "ingest-ohlcv-every-5min": {
            "task": "ingestion.tasks.ingest_ohlcv_batch",
            "schedule": timedelta(minutes=5),
        },
        "ingest-macro-every-1h": {
            "task": "ingestion.tasks.ingest_macro_batch",
            "schedule": timedelta(hours=1),
        },
        "ingest-fx-every-30s": {
            "task": "ingestion.tasks.ingest_fx_rates",
            "schedule": timedelta(seconds=30),
        },
        "ingest-treasury-every-15m": {
            "task": "ingestion.tasks.ingest_treasury_curve",
            "schedule": timedelta(minutes=15),
        },
        "compute-nightly-pivot-points": {
            "task": "ingestion.tasks.compute_nightly_pivot_points",
            "schedule": crontab(hour=20, minute=0),
        },
        "compute-nightly-candlestick-stats": {
            "task": "ingestion.tasks.compute_nightly_candlestick_stats",
            "schedule": crontab(hour=21, minute=0),
        },
        "ingest-boe-gilt-curve-daily": {
            "task": "ingestion.tasks.ingest_boe_gilt_curve",
            "schedule": crontab(hour=18, minute=0),
        },
        "ingest-vix-every-15m": {
            "task": "ingestion.tasks.ingest_vix_term_structure",
            "schedule": timedelta(minutes=15),
        },
        "ingest-cboe-pcr-daily": {
            "task": "ingestion.tasks.ingest_cboe_pcr",
            "schedule": crontab(hour=19, minute=0),
        },
        "compute-breadth-snapshot-daily": {
            "task": "ingestion.tasks.compute_breadth_snapshot",
            "schedule": crontab(hour=22, minute=0),
        },
        "ingest-ons-daily": {
            "task": "ingestion.tasks.ingest_ons_series",
            "schedule": crontab(hour=6, minute=0),
        },
        "ingest-ecb-gdp-daily": {
            "task": "ingestion.tasks.ingest_ecb_gdp",
            "schedule": crontab(hour=6, minute=15),
        },
        "ingest-boe-rate-daily": {
            "task": "ingestion.tasks.ingest_boe_policy_rate",
            "schedule": crontab(hour=6, minute=30),
        },
        "ingest-bls-nfp-daily": {
            "task": "ingestion.tasks.ingest_bls_nfp",
            "schedule": crontab(hour=7, minute=0),
        },
        "ingest-ecb-dfr-daily": {
            "task": "ingestion.tasks.ingest_ecb_dfr",
            "schedule": crontab(hour=6, minute=45),
        },
        "scrape-tiktok-hourly": {
            "task": "ingestion.tasks.scrape_tiktok",
            "schedule": timedelta(hours=1),
        },
    },
)
