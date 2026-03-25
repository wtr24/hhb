import json
from typing import Any, Optional

TTL = {
    "quote": 15,
    "fx": 30,
    "fundamentals": 86400,
    "macro": 3600,
    "yield_curve": 900,
    "news": 300,
    "screener": 900,
    "crypto_marketcap": 600,
}


def cache_set(redis_client, key: str, data: Any, ttl_key: str) -> None:
    """Serialise data to JSON and store in Redis with the TTL for ttl_key."""
    redis_client.set(key, json.dumps(data, default=str), ex=TTL[ttl_key])


def cache_get(redis_client, key: str) -> Optional[dict]:
    """Return the cached dict for key, or None on a cache miss."""
    raw = redis_client.get(key)
    return json.loads(raw) if raw else None
