import redis
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    return redis_client


def get_async_redis_url() -> str:
    """Return Redis URL for async redis.asyncio client."""
    return REDIS_URL
