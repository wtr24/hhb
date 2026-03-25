import time

TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

local elapsed = now - last_refill
local refilled = math.min(capacity, tokens + elapsed * refill_rate)

if refilled >= 1 then
    redis.call('HMSET', key, 'tokens', refilled - 1, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)
    return 1
else
    return 0
end
"""

RATE_LIMITS = {
    "finnhub":       {"capacity": 60,  "per_seconds": 60},
    "fmp":           {"capacity": 250, "per_seconds": 86400},
    "alpha_vantage": {"capacity": 25,  "per_seconds": 86400},
    "coingecko":     {"capacity": 13,  "per_seconds": 3600},
}


def check_rate_limit(redis_client, source: str) -> bool:
    """
    Return True if a request for source is within rate limits, False if throttled.

    Uses an atomic Lua token-bucket script to avoid race conditions.
    Unknown sources are always allowed (return True without hitting Redis).
    """
    if source not in RATE_LIMITS:
        return True
    limits = RATE_LIMITS[source]
    refill_rate = limits["capacity"] / limits["per_seconds"]
    result = redis_client.eval(
        TOKEN_BUCKET_LUA, 1, f"ratelimit:{source}",
        limits["capacity"], refill_rate, time.time()
    )
    return bool(result)
