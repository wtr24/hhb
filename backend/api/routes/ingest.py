from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest/trigger/{ticker}")
async def trigger_ingest(ticker: str):
    """Manually trigger ingestion for a ticker. No auth — personal NAS tool."""
    from ingestion.tasks import ingest_ticker
    task = ingest_ticker.apply_async(args=[ticker])
    return {"status": "triggered", "ticker": ticker, "task_id": task.id}
