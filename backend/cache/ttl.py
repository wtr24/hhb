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
    "ta_pattern_daily": 900,    # 15-minute TTL for chart-pattern detection on daily timeframe
    "ta_pattern_weekly": 3600,  # 1-hour TTL for chart-pattern detection on weekly timeframe
    "gilt_curve": 86400,          # 24h — BoE publishes once daily
    "vix_term_structure": 900,    # 15m — matches ingestion schedule
    "fear_greed": 3600,           # 1h — composite score
    "macro_curves": 900,          # 15m — /api/macro/curves endpoint
    "macro_indicators": 3600,     # 1h — /api/macro/indicators endpoint
    "macro_risk": 900,            # 15m — /api/macro/risk endpoint
    "macro_sentiment": 3600,      # 1h — /api/macro/sentiment endpoint
}


def cache_set(redis_client, key: str, data: Any, ttl_key: str) -> None:
    """Serialise data to JSON and store in Redis with the TTL for ttl_key."""
    redis_client.set(key, json.dumps(data, default=str), ex=TTL[ttl_key])


def cache_get(redis_client, key: str) -> Optional[dict]:
    """Return the cached dict for key, or None on a cache miss."""
    raw = redis_client.get(key)
    return json.loads(raw) if raw else None
