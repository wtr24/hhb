from fastapi import APIRouter
from sqlalchemy import text
from .database import engine
from .redis_client import get_redis

router = APIRouter()

@router.get("/health")
def health_check():
    status = {"status": "ok", "services": {}}

    # Redis check
    try:
        r = get_redis()
        r.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {e}"
        status["status"] = "degraded"

    # TimescaleDB check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["services"]["timescaledb"] = "ok"
    except Exception as e:
        status["services"]["timescaledb"] = f"error: {e}"
        status["status"] = "degraded"

    return status
