from celery import Celery
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
    beat_schedule={},  # Populated in Phase 2
)
