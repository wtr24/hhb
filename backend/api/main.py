import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .health import router as health_router
from .websocket import router as ws_router, manager
from .routes.quote import router as quote_router
from .routes.macro import router as macro_router
from .routes.ingest import router as ingest_router
from .routes.fx import router as fx_router
from .routes.equity import router as equity_router
from .routes.ta import router as ta_router
from .routes.tiktok import router as tiktok_router
from .redis_client import get_async_redis_url

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Redis pub/sub listener and Finnhub WebSocket lifecycle.

    Starts two background tasks:
    1. Redis pub/sub listener (D-10) — fans out channel messages to WS clients.
    2. Finnhub WebSocket listener — ingests live US stock trade data into Redis.

    Both tasks are cancelled on shutdown and their connections are closed.
    """
    async_redis = aioredis.Redis.from_url(get_async_redis_url(), decode_responses=True)
    task = asyncio.create_task(_redis_pubsub_listener(async_redis))
    logger.info("Redis pub/sub listener started")

    # Finnhub WebSocket: live US quotes -> Redis quotes:{ticker} pub/sub
    finnhub_key = os.getenv("FINNHUB_API_KEY", "")
    if finnhub_key:
        from ingestion.sources.finnhub_ws import FinnhubWebSocket
        from api.redis_client import redis_client as sync_redis
        finnhub_ws = FinnhubWebSocket(finnhub_key, sync_redis)
        finnhub_task = asyncio.create_task(finnhub_ws.connect_and_listen())
        logger.info("Finnhub WebSocket listener started")
    else:
        finnhub_task = None
        logger.warning(
            "FINNHUB_API_KEY not set — live quotes disabled, "
            "falling back to yfinance polling for all tickers"
        )

    yield

    # Shutdown: cancel Finnhub WS task first, then pub/sub listener
    if finnhub_task is not None:
        finnhub_task.cancel()
        try:
            await finnhub_task
        except asyncio.CancelledError:
            pass
        logger.info("Finnhub WebSocket listener stopped")

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await async_redis.aclose()
    logger.info("Redis pub/sub listener stopped")


async def _redis_pubsub_listener(async_redis: aioredis.Redis):
    """Background task: subscribe to all data channels, fan out to WebSocket clients.
    Uses pattern subscribe (psubscribe) to catch all channels (per D-10).
    Filters on pmessage type to avoid subscription confirmations (Research Pitfall 4).
    """
    pubsub = async_redis.pubsub()
    await pubsub.psubscribe("quotes:*", "macro:*", "fx:*")
    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                channel = message["channel"]
                try:
                    data = json.loads(message["data"])
                except (json.JSONDecodeError, TypeError):
                    continue
                await manager.broadcast_to_channel(channel, data)
    except asyncio.CancelledError:
        await pubsub.punsubscribe("quotes:*", "macro:*", "fx:*")
        await pubsub.aclose()
        raise


app = FastAPI(title="HHBFin API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3009", "http://192.168.0.18:3009"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(ws_router, tags=["websocket"])
app.include_router(quote_router)
app.include_router(macro_router)
app.include_router(ingest_router)
app.include_router(fx_router)
app.include_router(equity_router)
app.include_router(ta_router)
app.include_router(tiktok_router)


@app.get("/")
def root():
    return {"status": "HHBFIN TERMINAL API"}
