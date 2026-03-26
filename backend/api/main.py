import asyncio
import json
import logging
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .health import router as health_router
from .websocket import router as ws_router, manager
from .routes.quote import router as quote_router
from .routes.macro import router as macro_router
from .routes.ingest import router as ingest_router
from .redis_client import get_async_redis_url

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Redis pub/sub listener lifecycle (per D-10).
    Single asyncio background task. One Redis pub/sub connection total.
    """
    async_redis = aioredis.Redis.from_url(get_async_redis_url(), decode_responses=True)
    task = asyncio.create_task(_redis_pubsub_listener(async_redis))
    logger.info("Redis pub/sub listener started")
    yield
    # Shutdown: cancel listener, close connection (Research Pitfall 8)
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(ws_router, tags=["websocket"])
app.include_router(quote_router)
app.include_router(macro_router)
app.include_router(ingest_router)


@app.get("/")
def root():
    return {"status": "HHBFIN TERMINAL API"}
