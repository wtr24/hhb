from celery import Celery
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
    },
)
