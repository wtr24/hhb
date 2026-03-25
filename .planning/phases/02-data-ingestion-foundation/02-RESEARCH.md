# Phase 02: Data Ingestion Foundation - Research

**Researched:** 2026-03-25
**Domain:** Celery task scheduling, yfinance/FRED/Frankfurter/US Treasury data ingestion, Redis TTL caching + token bucket rate limiting, TimescaleDB hypertable design, FastAPI WebSocket + Redis pub/sub fan-out
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Celery Beat Scheduling:**
- D-01: Always-on scheduling — tasks fire 24/7 regardless of market hours. Outside market hours, yfinance returns stale/unchanged data; fallback chain handles it. No timezone or market calendar logic in Phase 2.
- D-02: Task failure handling — Celery autoretry with exponential backoff: 3 attempts at 60s / 300s / 900s delays. After all retries exhausted, task logs failure. Beat fires again on next natural schedule cycle.
- D-03: yfinance OHLCV scheduled refresh interval — every 5 minutes.
- D-04: Ticker universe for scheduled tasks — hardcoded seed list: AAPL, MSFT, LLOY.L, BARC.L, ^FTSE, ^FTMC, BTC-USD, GBP=X, EURUSD=X (at minimum). Dynamic watchlist-driven scheduling deferred to Phase 3.

**Redis Caching + Rate Limits:**
- D-05: TTL values from spec §5 table: live quotes 15s, FX 30s, fundamentals 24h, macro 1h, yield curve 15m. Do not re-derive.
- D-06: Rate limit token buckets — one per API source: Finnhub 60/min, FMP 250/day, Alpha Vantage 25/day, CoinGecko 13/hr. Celery workers check before firing.

**WebSocket Broadcaster:**
- D-07: Per-entity Redis pub/sub channels: `quotes:AAPL`, `macro:CPI`, `fx:GBPUSD`. Frontend subscribes via `{"action": "subscribe", "channels": [...]}`.
- D-08: Flat message format with `channel`, `ticker`, `price`, `change`, `change_pct`, `volume`, `timestamp`, `stale` fields.
- D-09: On subscribe with no recent data — server reads latest row from TimescaleDB and sends immediately.
- D-10: Single asyncio background task at FastAPI lifespan startup. One Redis pub/sub connection total. No per-connection subscribers.

**On-Demand Quote Trigger:**
- D-11: On cache/DB miss — fire `ingest_ticker.apply_async()` immediately, poll TimescaleDB up to 10s. Return 200 if data arrives, 503 `{"error": "ingestion_timeout", "retry_after": 15}` if timeout.

**REST API Surface:**
- D-12: Phase 2 endpoints: `GET /api/quote/{ticker}`, `GET /api/macro/{series}`, `POST /api/ingest/trigger/{ticker}`
- D-13: `/api/quote/{ticker}` response — OHLCV + fundamentals combined (price, change_pct, open/high/low/close, volume, stale, fundamentals:{pe_ratio, ev_ebitda, market_cap, debt_equity})
- D-14: `/api/macro/{series}` friendly names mapped to FRED IDs: cpi→CPIAUCSL, gdp→GDP, fed_funds→FEDFUNDS, unemployment→UNRATE
- D-15: `/api/macro/{series}` returns 24-month time series array with series, fred_id, observations, stale, last_updated
- D-16: Yield curve REST endpoint deferred to Phase 4/5. Phase 2 only ingests and stores it.
- D-17: FX REST endpoint deferred to Forex module phase. Phase 2 only ingests and caches FX data.

**Claude's Discretion:**
- TimescaleDB hypertable schemas for fundamentals, macro, news, screener, factors, dividends, COT — column design and compression policies
- Async vs sync Redis client for WebSocket subscriber — use `redis.asyncio` for background listener; existing sync `redis_client.py` stays for Celery/health
- FRED macro series mapping table completeness — include at minimum: CPI, Core CPI, PCE, GDP, Fed Funds, UNRATE, 10Y/2Y Treasury as macro proxy

### Deferred Ideas (OUT OF SCOPE)

- `/api/fx/{base}/{quote}` REST endpoint — Phase 2 ingests only
- `/api/macro/yield_curve` REST endpoint — deferred to Phase 4/5
- Dynamic ticker universe (Redis-backed active ticker set) — deferred to Phase 3
- Market hours-aware scheduling — deferred indefinitely
- Dead letter queue for failed Celery tasks — deferred

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INGEST-01 | Celery workers ingest yfinance OHLCV + fundamentals for any ticker on demand and on schedule | Celery 5.6 beat_schedule with timedelta, autoretry_for pattern, yfinance 1.2.0 Ticker.history() + .info |
| INGEST-02 | FRED ingestion worker fetches macro series (CPI, PCE, GDP, unemployment, Fed Funds, yield curve) on 1h schedule | FRED REST API `/fred/series/observations` with api_key + series_id params |
| INGEST-03 | Redis TTL caching enforced per data type (per spec §5 table) | redis-py 7.4.0 SET with EX param; TTL values from spec §5 |
| INGEST-04 | Rate limit token buckets in Redis protect all API sources | Lua-script atomic token bucket pattern via redis EVAL |
| INGEST-05 | Fallback chain: Live API → Redis cache → TimescaleDB last-known → stale warning → error | Layered try/read pattern; `stale` flag on all responses |
| INGEST-06 | All ingested data written to TimescaleDB — nothing cache-only | SQLAlchemy async session, INSERT ON CONFLICT DO NOTHING on hypertables |
| INGEST-07 | Frankfurter FX rates ingested on 30s schedule for major pairs + GBP crosses | Frankfurter `https://api.frankfurter.dev/v1/latest?base=USD&symbols=...` |
| INGEST-08 | US Treasury XML yield curve ingested on 15m schedule | `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={YYYYMM}` |
| INGEST-09 | FastAPI WebSocket broadcaster subscribes to Redis pub/sub and fans out to all connected browser clients | FastAPI lifespan + asyncio.create_task + redis.asyncio pubsub |

</phase_requirements>

---

## Summary

Phase 2 wires four distinct data pipelines (yfinance OHLCV/fundamentals, FRED macro, Frankfurter FX, US Treasury XML) into Celery beat workers, backs everything with Redis TTL caching and token bucket rate limiters, persists all data to new TimescaleDB hypertables, exposes REST endpoints for quote and macro data, and connects the existing WebSocket ConnectionManager stub to a Redis pub/sub fan-out architecture.

The primary complexity is threefold: (1) yfinance's unofficial nature means 429 rate limiting is a real operational risk — workers must stagger requests and rely on Celery's exponential backoff rather than hammering Yahoo Finance; (2) the async/sync boundary in the FastAPI stack requires the WebSocket pub/sub listener to use `redis.asyncio` while Celery workers use the existing sync Redis client; (3) TimescaleDB hypertable ON CONFLICT constraints require column-based conflict detection, not constraint-based, and primary keys must include the time partition column.

**Primary recommendation:** Use Celery 5.6 `autoretry_for` with `retry_backoff=True` and fixed `countdown` values (not backoff multipliers) to hit the exact 60s/300s/900s delays specified in D-02. Use a single Lua script for atomic Redis token bucket checks before each API call. Deploy `redis.asyncio` (built into redis-py 7.4.0) for the WebSocket background listener — no extra package needed.

---

## Standard Stack

### Core (already in requirements.txt)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| celery | 5.6.2 | Beat scheduler + workers | Already installed; current latest |
| redis | 7.4.0 | Cache, pub/sub, token buckets | Already installed; includes `redis.asyncio` built in |
| sqlalchemy | 2.0.48 | Async DB session for TimescaleDB | Already installed; async engine needed for tasks |
| fastapi | 0.135.2 | REST + WebSocket API | Already installed |
| alembic | 1.18.4 | DB migrations | Already installed; established pattern from Phase 1 |

### New Dependencies (add to requirements.txt)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | 1.2.0 | OHLCV + fundamentals from Yahoo Finance | All equity/ETF/index ingest tasks |
| requests | 2.32.x | HTTP calls to FRED, Frankfurter, US Treasury | Sync HTTP in Celery worker context |
| aiohttp | 3.x | Async HTTP for FastAPI-side fetch (D-11 polling) | on-demand trigger endpoint only |
| asyncpg | 0.30.x | Async PostgreSQL driver for SQLAlchemy async engine | Required for `create_async_engine` |
| pandas | 2.x | DataFrame manipulation for yfinance, Treasury XML parse | yfinance returns DataFrames; XML has tabular structure |
| lxml | 5.x | XML parsing for US Treasury yield curve | Faster than stdlib xml.etree for large XML |

**Version verification (checked 2026-03-25):**
```bash
pip index versions yfinance  # latest: 1.2.0
pip index versions redis     # latest: 7.4.0 (7.3.0 installed — upgrade needed)
pip index versions celery    # latest: 5.6.2 (already installed)
```

Note: `redis.asyncio` is included in redis-py 7.x — no `aioredis` package needed. The old `aioredis` package is abandoned; do NOT use it.

**Installation:**
```bash
pip install yfinance==1.2.0 requests asyncpg pandas lxml
pip install --upgrade redis==7.4.0
```

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| yfinance | Finnhub REST for quotes | Finnhub 60/min limit consumed fast; yfinance unlimited for history |
| requests (sync) in workers | httpx | requests is battle-tested in Celery; httpx adds no value in sync worker context |
| lxml for Treasury XML | stdlib xml.etree | lxml is faster, better namespace handling for Treasury's Atom XML |
| redis.asyncio (built-in) | aioredis package | aioredis is abandoned (last release 2022); redis.asyncio is the maintained path |

---

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── ingestion/
│   ├── celery_app.py        # EXISTING — add beat_schedule entries
│   ├── tasks.py             # EXISTING — add ingest_ohlcv, ingest_macro, ingest_fx, ingest_treasury
│   ├── sources/
│   │   ├── yfinance_source.py     # yfinance fetch + fundamentals logic
│   │   ├── fred_source.py         # FRED REST calls
│   │   ├── frankfurter_source.py  # Frankfurter FX calls
│   │   └── treasury_source.py     # US Treasury XML parse
│   └── __init__.py
├── cache/
│   ├── __init__.py          # EXISTING (empty)
│   ├── ttl.py               # TTL constants from spec §5
│   └── rate_limiter.py      # Lua-based token bucket
├── models/
│   ├── base.py              # EXISTING
│   ├── ohlcv.py             # EXISTING
│   ├── fundamentals.py      # NEW
│   ├── macro_series.py      # NEW
│   ├── fx_rate.py           # NEW
│   └── yield_curve.py       # NEW
├── api/
│   ├── main.py              # EXISTING — add new routers
│   ├── routes/
│   │   ├── quote.py         # GET /api/quote/{ticker}
│   │   ├── macro.py         # GET /api/macro/{series}
│   │   └── ingest.py        # POST /api/ingest/trigger/{ticker}
│   ├── websocket.py         # EXISTING — extend with channel fan-out
│   ├── redis_client.py      # EXISTING — add async_redis_client variant
│   └── database.py          # EXISTING — add async engine
└── alembic/versions/
    └── 0002_ingestion_hypertables.py  # NEW
```

### Pattern 1: Celery Beat Schedule Population

**What:** Fill the empty `beat_schedule={}` dict in `celery_app.py` with `timedelta`-based schedules per D-01 through D-04.

**When to use:** All periodic ingest tasks.

```python
# Source: Celery 5.6 docs — https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
from datetime import timedelta

app.conf.beat_schedule = {
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
}
```

### Pattern 2: Celery autoretry with Fixed Countdown (D-02)

**What:** Use `bind=True` + `self.retry(countdown=N)` to enforce the exact 60s/300s/900s delays from D-02. Do NOT use `retry_backoff=True` here — that uses exponential multipliers, not the exact values specified.

**When to use:** All ingest tasks that call external APIs.

```python
# Source: Celery 5.6 docs tasks.html#automatic-retry-for-known-exceptions
from celery import Task
from celery.exceptions import MaxRetriesExceededError

RETRY_COUNTDOWNS = [60, 300, 900]  # D-02 specified delays

@app.task(bind=True, max_retries=3)
def ingest_ohlcv_batch(self):
    try:
        _do_ingest()
    except Exception as exc:
        attempt = self.request.retries  # 0-indexed
        countdown = RETRY_COUNTDOWNS[min(attempt, len(RETRY_COUNTDOWNS) - 1)]
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error("ingest_ohlcv_batch exhausted retries", exc_info=exc)
```

### Pattern 3: Redis Token Bucket (INGEST-04)

**What:** Atomic Lua script checks token availability before each API call. Single EVAL call — no MULTI/EXEC race condition.

**When to use:** Before every call to Finnhub, FMP, Alpha Vantage, CoinGecko. NOT needed for yfinance (unofficial, no formal limit), Frankfurter (unlimited), FRED (unlimited), US Treasury (unlimited).

```python
# Source: redis.io/tutorials/howtos/ratelimiting + standard token bucket pattern
TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])  -- tokens per second
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

def check_rate_limit(redis_client, source: str, capacity: int, refill_rate: float) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    import time
    result = redis_client.eval(
        TOKEN_BUCKET_LUA, 1, f"ratelimit:{source}",
        capacity, refill_rate, time.time()
    )
    return bool(result)
```

### Pattern 4: Redis TTL Cache Helper (INGEST-03)

**What:** Thin helper that serializes JSON to Redis with TTL from spec §5. Returns cached value or None on miss.

```python
# backend/cache/ttl.py
import json
from typing import Any, Optional

# TTL values from spec §5 — authoritative source
TTL = {
    "quote": 15,          # live quotes 15s
    "fx": 30,             # FX rates 30s
    "fundamentals": 86400, # 24h
    "macro": 3600,        # FRED 1h
    "yield_curve": 900,   # 15m
    "news": 300,          # 5m
    "screener": 900,      # 15m
    "crypto_marketcap": 600,  # 10m
}

def cache_set(redis_client, key: str, data: Any, ttl_key: str) -> None:
    redis_client.set(key, json.dumps(data), ex=TTL[ttl_key])

def cache_get(redis_client, key: str) -> Optional[dict]:
    raw = redis_client.get(key)
    return json.loads(raw) if raw else None
```

### Pattern 5: Fallback Chain (INGEST-05)

**What:** Every data fetch attempt walks the chain: Live API → Redis cache → TimescaleDB latest → stale flag.

```python
# Canonical fallback chain pattern for all ingest sources
async def get_quote_with_fallback(ticker: str, redis_client, db_session) -> dict:
    # Step 1: Redis cache hit
    cached = cache_get(redis_client, f"quote:{ticker}", "quote")
    if cached:
        return {**cached, "stale": False}

    # Step 2: Live API call
    try:
        data = fetch_from_yfinance(ticker)
        cache_set(redis_client, f"quote:{ticker}", data, "quote")
        await write_to_timescaledb(db_session, ticker, data)
        await publish_to_redis_pubsub(redis_client, f"quotes:{ticker}", data)
        return {**data, "stale": False}
    except Exception:
        pass

    # Step 3: TimescaleDB last-known
    row = await db_session.execute(
        select(OHLCV).where(OHLCV.ticker == ticker).order_by(OHLCV.time.desc()).limit(1)
    )
    if row := row.scalar_one_or_none():
        return {**row_to_dict(row), "stale": True}

    # Step 4: Error state
    return None
```

### Pattern 6: FastAPI Lifespan + Async Redis Pub/Sub Listener (INGEST-09)

**What:** Single asyncio background task started at lifespan startup. One `redis.asyncio` pub/sub connection. Fans out to `ConnectionManager` by channel.

**When to use:** The WebSocket broadcaster wiring in D-10.

```python
# Source: FastAPI lifespan docs + redis.asyncio pubsub pattern
from contextlib import asynccontextmanager
import asyncio
import redis.asyncio as aioredis
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: wire Redis pub/sub listener
    async_redis = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    task = asyncio.create_task(_redis_pubsub_listener(async_redis))
    yield
    # Shutdown: cancel listener, close connection
    task.cancel()
    await async_redis.aclose()

async def _redis_pubsub_listener(async_redis: aioredis.Redis):
    pubsub = async_redis.pubsub()
    await pubsub.psubscribe("quotes:*", "macro:*", "fx:*")
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            channel = message["channel"]
            data = json.loads(message["data"])
            await manager.broadcast_to_channel(channel, data)
```

### Pattern 7: Extended ConnectionManager with Channel Fan-Out (INGEST-09)

**What:** Replace broadcast-all with per-channel subscription map. Extend existing `ConnectionManager` stub.

```python
# Extension of existing backend/api/websocket.py ConnectionManager
class ConnectionManager:
    def __init__(self):
        self.channel_subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def subscribe(self, websocket: WebSocket, channel: str):
        self.channel_subscriptions.setdefault(channel, set()).add(websocket)

    def unsubscribe_all(self, websocket: WebSocket):
        for subs in self.channel_subscriptions.values():
            subs.discard(websocket)

    async def broadcast_to_channel(self, channel: str, message: dict):
        for ws in list(self.channel_subscriptions.get(channel, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.unsubscribe_all(ws)

    async def send_initial_snapshot(self, websocket: WebSocket, channel: str, db_session):
        """D-09: send latest DB row immediately on subscribe."""
        row = await _fetch_latest_for_channel(channel, db_session)
        if row:
            await websocket.send_json({**row, "stale": True, "channel": channel})
```

### Pattern 8: TimescaleDB INSERT with ON CONFLICT (INGEST-06)

**What:** Idempotent upsert for hypertable rows. Must use `index_elements` (column names), NOT `constraint` name — TimescaleDB doesn't support constraint-based ON CONFLICT on hypertables.

```python
# Source: TimescaleDB upsert docs + SQLAlchemy postgresql dialect
from sqlalchemy.dialects.postgresql import insert

async def upsert_ohlcv(session: AsyncSession, rows: list[dict]):
    stmt = insert(OHLCV).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["time", "ticker"])
    await session.execute(stmt)
    await session.commit()
```

### Pattern 9: yfinance Ticker Fetch

**What:** Fetch OHLCV + fundamentals for a single ticker. Use `Ticker.history()` for price data and `Ticker.info` for fundamentals dict.

**Known pitfall:** `.info` makes a full quoteSummary API call — it's slower than `fast_info` and subject to 429 rate limiting. Use `fast_info` for real-time price fields (last_price, market_cap) and `info` only for fundamentals like pe_ratio that aren't in fast_info. Add `time.sleep(0.5)` between batch ticker fetches.

```python
import yfinance as yf
import time

def fetch_ohlcv_and_fundamentals(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    hist = t.history(period="1d", interval="5m")  # recent OHLCV bars

    # fast_info for real-time price fields (avoids quoteSummary call)
    fi = t.fast_info

    # .info for fundamentals — may 429, should be caught by Celery retry
    info = t.info

    return {
        "ohlcv": hist.reset_index().to_dict(orient="records"),
        "price": fi.last_price,
        "market_cap": fi.market_cap,
        "fundamentals": {
            "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "market_cap": info.get("marketCap"),
            "debt_equity": info.get("debtToEquity"),
        }
    }

def fetch_ohlcv_batch(tickers: list[str]) -> list[dict]:
    results = []
    for ticker in tickers:
        results.append(fetch_ohlcv_and_fundamentals(ticker))
        time.sleep(0.5)  # prevent 429 from Yahoo Finance
    return results
```

### Pattern 10: FRED API Call

**What:** Synchronous GET request to FRED observations endpoint. API key from env var.

```python
# Source: FRED API docs https://fred.stlouisfed.org/docs/api/fred/series_observations.html
import requests
import os

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES_MAP = {
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "pce": "PCEPI",
    "gdp": "GDP",
    "fed_funds": "FEDFUNDS",
    "unemployment": "UNRATE",
    "treasury_10y": "GS10",
    "treasury_2y": "GS2",
}

def fetch_fred_series(series_id: str, observation_start: str = None) -> list[dict]:
    params = {
        "api_key": os.environ["FRED_API_KEY"],
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 300,  # ~24 months of monthly data with buffer
    }
    if observation_start:
        params["observation_start"] = observation_start

    r = requests.get(FRED_BASE, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["observations"]
```

### Pattern 11: Frankfurter FX Fetch

**What:** GET `/v1/latest` with base=USD and target symbols. No API key needed.

```python
# Source: Frankfurter API docs https://frankfurter.dev/v1/
import requests

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1"
GBP_CROSSES = ["GBP", "EUR", "JPY", "CHF", "AUD", "CAD", "NZD", "NOK", "SEK"]
MAJOR_PAIRS = ["USD", "GBP", "EUR", "JPY", "CHF", "AUD", "CAD"]

def fetch_fx_rates(base: str = "USD") -> dict:
    r = requests.get(
        f"{FRANKFURTER_BASE}/latest",
        params={"base": base, "symbols": ",".join(MAJOR_PAIRS + GBP_CROSSES)},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # {"amount": 1.0, "base": "USD", "date": "...", "rates": {...}}
```

### Pattern 12: US Treasury XML Fetch and Parse

**What:** GET Treasury XML for current month, parse Atom/XML with lxml, extract tenor fields.

```python
# Source: US Treasury XML feed docs https://home.treasury.gov/treasury-daily-interest-rate-xml-feed
import requests
import lxml.etree as ET
from datetime import date

TREASURY_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"

TENOR_FIELDS = [
    "BC_1MONTH", "BC_2MONTH", "BC_3MONTH", "BC_6MONTH",
    "BC_1YEAR", "BC_2YEAR", "BC_3YEAR", "BC_5YEAR",
    "BC_7YEAR", "BC_10YEAR", "BC_20YEAR", "BC_30YEAR",
]

def fetch_treasury_yield_curve() -> list[dict]:
    year_month = date.today().strftime("%Y%m")
    r = requests.get(
        TREASURY_URL,
        params={"data": "daily_treasury_yield_curve", "field_tdr_date_value": year_month},
        timeout=30,
    )
    r.raise_for_status()

    root = ET.fromstring(r.content)
    ns = {"m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
          "d": "http://schemas.microsoft.com/ado/2007/08/dataservices"}

    rows = []
    for entry in root.findall(".//d:BC_1YEAR/../..", ns):
        row = {"date": _get_field(entry, "NEW_DATE", ns)}
        for field in TENOR_FIELDS:
            row[field.lower()] = _get_float(entry, field, ns)
        rows.append(row)
    return rows
```

### Anti-Patterns to Avoid

- **Do NOT use `retry_backoff=True`** for D-02's exact 60s/300s/900s delays — it uses exponential multipliers, not fixed values. Use `countdown=` explicitly.
- **Do NOT use constraint-based ON CONFLICT on TimescaleDB hypertables** — use `index_elements` (column names) only. Constraint-based ON CONFLICT is not supported on TimescaleDB hypertables.
- **Do NOT create per-connection Redis pub/sub subscribers** — one global listener fans out (D-10). Per-connection subscribers leak Redis connections.
- **Do NOT use the old `aioredis` package** — it was abandoned in 2022. Use `redis.asyncio` from the redis-py 7.x package.
- **Do NOT call `yf.Ticker.info` in a tight loop** — it triggers Yahoo Finance's 429 rate limiter. Add `time.sleep(0.5)` between tickers or batch with `yf.download()`.
- **Do NOT use `create_engine` (sync) in async FastAPI route handlers** — Phase 1 established sync engine for migrations only. Add async engine via `create_async_engine` + asyncpg for all Phase 2 route handlers.
- **Do NOT store FX/yield curve data in Redis only** — INGEST-06 requires all ingested data written to TimescaleDB. Redis is cache only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting across workers | Custom counter with Redis INCR | Lua script token bucket | INCR is not atomic with conditional decrement; Lua makes it atomic |
| OHLCV history download | Manual Yahoo Finance HTTP calls | `yfinance.Ticker.history()` | Yahoo Finance endpoint format changes; yfinance handles cookie auth, session management, pagination |
| FRED data fetch | Custom XML/JSON parser | Standard `requests.get` to `/fred/series/observations?file_type=json` | FRED has stable JSON endpoint; no parser needed |
| Currency conversion rates | Build ECB/BOE scraper | Frankfurter API at `api.frankfurter.dev/v1/latest` | Frankfurter aggregates ECB + BOC; updated daily 16:00 CET; zero-cost, no key |
| Treasury XML namespace handling | stdlib xml.etree + manual namespace | lxml.etree with namespace dict | Treasury uses OData Atom format with nested namespaces; lxml handles this cleanly |
| Async PostgreSQL driver | Sync psycopg2 in async context | asyncpg via `create_async_engine("postgresql+asyncpg://...")` | Sync psycopg2 blocks the event loop; asyncpg is the correct async driver for SQLAlchemy 2.x |

**Key insight:** The external data sources (FRED, Frankfurter, US Treasury) are all stable REST/XML endpoints with no authentication. The only data source requiring care is yfinance — it is an unofficial scraper subject to Yahoo Finance 429s, not a formal API.

---

## TimescaleDB Hypertable Schemas (Claude's Discretion)

### New Tables Required (migration 0002)

**`fundamentals` table** — 24h TTL cache target, versioned by time
```sql
CREATE TABLE fundamentals (
    time         TIMESTAMPTZ NOT NULL,
    ticker       VARCHAR(20) NOT NULL,
    pe_ratio     NUMERIC(10,4),
    ev_ebitda    NUMERIC(10,4),
    market_cap   BIGINT,
    debt_equity  NUMERIC(10,4),
    source       VARCHAR(20),
    PRIMARY KEY (time, ticker)
);
SELECT create_hypertable('fundamentals', 'time', if_not_exists => TRUE);
CREATE INDEX ix_fundamentals_ticker_time ON fundamentals (ticker, time DESC);
```

**`macro_series` table** — FRED observations, one row per series per date
```sql
CREATE TABLE macro_series (
    time         TIMESTAMPTZ NOT NULL,
    series_id    VARCHAR(30) NOT NULL,
    value        NUMERIC(18,6),
    source       VARCHAR(20) DEFAULT 'fred',
    PRIMARY KEY (time, series_id)
);
SELECT create_hypertable('macro_series', 'time', if_not_exists => TRUE);
CREATE INDEX ix_macro_series_id_time ON macro_series (series_id, time DESC);
```

**`fx_rates` table** — Frankfurter FX, one row per base/quote pair per timestamp
```sql
CREATE TABLE fx_rates (
    time         TIMESTAMPTZ NOT NULL,
    base         VARCHAR(3) NOT NULL,
    quote        VARCHAR(3) NOT NULL,
    rate         NUMERIC(18,8) NOT NULL,
    source       VARCHAR(20) DEFAULT 'frankfurter',
    PRIMARY KEY (time, base, quote)
);
SELECT create_hypertable('fx_rates', 'time', if_not_exists => TRUE);
CREATE INDEX ix_fx_rates_pair_time ON fx_rates (base, quote, time DESC);
```

**`yield_curve` table** — US Treasury XML, one row per date with all tenors as columns
```sql
CREATE TABLE yield_curve (
    time         TIMESTAMPTZ NOT NULL PRIMARY KEY,
    bc_1month    NUMERIC(8,4),
    bc_2month    NUMERIC(8,4),
    bc_3month    NUMERIC(8,4),
    bc_6month    NUMERIC(8,4),
    bc_1year     NUMERIC(8,4),
    bc_2year     NUMERIC(8,4),
    bc_3year     NUMERIC(8,4),
    bc_5year     NUMERIC(8,4),
    bc_7year     NUMERIC(8,4),
    bc_10year    NUMERIC(8,4),
    bc_20year    NUMERIC(8,4),
    bc_30year    NUMERIC(8,4),
    source       VARCHAR(20) DEFAULT 'us_treasury'
);
SELECT create_hypertable('yield_curve', 'time', if_not_exists => TRUE);
```

**Compression policy** (all tables): Apply after 7 days (yield_curve is single-key, no segmentby needed; others segment by ticker/series_id):
```sql
ALTER TABLE ohlcv SET (timescaledb.compress, timescaledb.compress_segmentby = 'ticker');
SELECT add_compression_policy('ohlcv', compress_after => INTERVAL '7 days');
-- Repeat for fundamentals, macro_series, fx_rates, yield_curve
```

**chunk_time_interval:** Use default (7 days) for all tables. OHLCV is high-frequency; 7-day chunks are appropriate.

---

## Common Pitfalls

### Pitfall 1: yfinance 429 Rate Limiting
**What goes wrong:** Yahoo Finance returns 429 "Too Many Requests" during batch ticker loops, especially when `.info` is called per ticker. Workers crash or return empty data.
**Why it happens:** yfinance is an unofficial scraper — Yahoo Finance sees rapid requests from the same IP and rate-limits them. The issue is widespread as of 2025-2026 with no official fix.
**How to avoid:** (1) `time.sleep(0.5)` between ticker fetches in batch tasks; (2) Separate the `info` (fundamentals) fetch from the `history` (OHLCV) fetch — call `.info` less frequently (every 24h per fundamentals TTL); (3) Let Celery's autoretry at 60s handle occasional 429s; (4) Use `yf.download([list])` for bulk price history where possible.
**Warning signs:** `YFRateLimitError` or `requests.exceptions.HTTPError: 429` in Celery worker logs.

### Pitfall 2: async/sync Engine Confusion
**What goes wrong:** Phase 1 created a sync SQLAlchemy engine (`create_engine`, psycopg2). Using this engine in async FastAPI route handlers blocks the event loop and causes timeouts under load.
**Why it happens:** psycopg2 is synchronous; it blocks the asyncio event loop when called from an async context.
**How to avoid:** Add a second engine in `database.py` using `create_async_engine("postgresql+asyncpg://...")`. Use the async engine + `AsyncSession` for all Phase 2 route handlers. Keep the sync engine for Alembic migrations only (established Phase 1 pattern).
**Warning signs:** FastAPI endpoints hang; response latency spikes; Celery tasks still work (they're not async).

### Pitfall 3: TimescaleDB ON CONFLICT Constraint Limitation
**What goes wrong:** Using `on_conflict_do_nothing(constraint="ohlcv_pkey")` raises an error on TimescaleDB hypertables even though the constraint exists.
**Why it happens:** TimescaleDB partitions data into chunks; constraint-based ON CONFLICT doesn't propagate across chunk boundaries.
**How to avoid:** Always use `on_conflict_do_nothing(index_elements=["time", "ticker"])` (column names), never `constraint=`. Verify primary key columns match exactly.
**Warning signs:** `ERROR: there is no unique or exclusion constraint matching the ON CONFLICT specification`

### Pitfall 4: Redis pub/sub Message Type Filtering
**What goes wrong:** The pub/sub listener processes subscription confirmation messages (`type == "subscribe"`) as data, sending garbage to WebSocket clients.
**Why it happens:** Redis sends a `{"type": "subscribe", ...}` message on successful subscription; `listen()` yields all message types.
**How to avoid:** Filter on `message["type"] in ("message", "pmessage")` before processing. Pass `ignore_subscribe_messages=True` to `get_message()` if using polling instead of `listen()`.
**Warning signs:** WebSocket clients receive `{"type": "subscribe", "pattern": null, "channel": "...", "data": 1}` events.

### Pitfall 5: Beat Duplication from Worker Startup
**What goes wrong:** If both beat and worker containers run the same command, beat fires tasks twice (once from each container).
**Why it happens:** Celery beat must only run in exactly one process.
**How to avoid:** Phase 1 already established distinct commands: `beat` container runs `celery -A ingestion.celery_app beat`, `worker` container runs `celery -A ingestion.celery_app worker`. Do NOT change this. Verify in docker-compose.yml.

### Pitfall 6: US Treasury XML Stale Data (Weekend/Holiday)
**What goes wrong:** Treasury XML on weekends/holidays returns the last available business day's data, not today's. The `time` field in the row may be 2-3 days old.
**Why it happens:** Treasury only publishes yield curve data on business days when markets are open.
**How to avoid:** Parse the actual date from the XML `NEW_DATE` field as the row timestamp — do not use `datetime.now()` as the timestamp. This prevents duplicate rows and correctly represents data currency.

### Pitfall 7: Frankfurter Stale Rates on Weekends
**What goes wrong:** FX rates from Frankfurter (ECB-sourced) don't update on weekends — the API returns the last Friday's rates.
**Why it happens:** ECB fixes exchange rates once per business day at 16:00 CET.
**How to avoid:** Use the `date` field from the API response as the row timestamp. Set `stale: true` in WebSocket messages when `date != today`. The 30s schedule can still fire — it just writes the same value idempotently (ON CONFLICT DO NOTHING).

### Pitfall 8: FastAPI lifespan Background Task Leak
**What goes wrong:** The Redis pub/sub listener task keeps running after the app shuts down, or reconnection after Redis restart causes duplicate listeners.
**Why it happens:** Without explicit `task.cancel()` in the lifespan teardown, asyncio tasks outlive the app process.
**How to avoid:** Store the task reference in the lifespan and call `task.cancel()` followed by `await async_redis.aclose()` in the shutdown block.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `aioredis` package for async Redis | `redis.asyncio` (built into redis-py ≥4.2) | 2022 | aioredis abandoned; redis.asyncio is the maintained path |
| `@app.on_event("startup")` in FastAPI | `@asynccontextmanager lifespan` function | FastAPI 0.93+ | on_event deprecated; lifespan is the current pattern |
| celery `@app.task(autoretry_for=..., retry_backoff=True)` | `bind=True` + explicit `countdown=` for fixed delays | Always | `retry_backoff=True` uses exponential multipliers — not suitable for exact delay values |
| TimescaleDB `create_hypertable` without `if_not_exists` | `create_hypertable('table', 'time', if_not_exists => TRUE)` | TSD 2.x+ | Idempotent migrations; established in Phase 1 already |

**Deprecated/outdated:**
- `aioredis` PyPI package: abandoned, do not use — redis-py ≥4.2 includes `redis.asyncio`
- `@app.on_event("startup"/"shutdown")`: deprecated in FastAPI — use lifespan context manager
- `yfinance.download()` with `group_by="ticker"` for fundamentals: does not return fundamentals; `Ticker.info` is still needed for PE, EV/EBITDA, etc.

---

## Open Questions

1. **yfinance .info reliability for LSE tickers**
   - What we know: yfinance supports `.L` suffix tickers; LLOY.L, BARC.L, ^FTSE are listed as required
   - What's unclear: Some `info` fields (pe_ratio, ev_ebitda) may be None for LSE tickers where Yahoo Finance doesn't populate them
   - Recommendation: Handle None gracefully in fundamentals dict; populate what's available; log missing fields. Phase 2 success criteria doesn't require non-null fundamentals for LSE tickers specifically.

2. **US Treasury XML field names post Feb 2025 change**
   - What we know: Treasury added 1.5-month CMT and 6-week bill rates in February 2025; XML feed changed
   - What's unclear: Exact new element names (BC_1_5MONTH? something else?)
   - Recommendation: At implementation time, fetch a live sample and inspect element names before hardcoding the field list. The tenor column list in the yield_curve schema above should be verified against a live response.

3. **FRED API key required for yield curve series (GS10, GS2)**
   - What we know: GS10 and GS2 are standard FRED series; FRED API is free with signup
   - What's unclear: Whether Phase 1's `.env.example` already documents FRED_API_KEY
   - Recommendation: Verify `.env.example` has FRED_API_KEY entry. Phase 1 notes say "keys populated before Phase 2 ingestion."

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Container stack | ✓ | 29.2.1 | — |
| Python 3.14 (host) | Local testing only | ✓ | 3.14 | — |
| redis-py (in image) | All cache/pubsub | ✓ (in requirements.txt) | 7.4.0 (needs upgrade from 7.3.0) | — |
| yfinance | INGEST-01 | Not in requirements.txt | 1.2.0 (to add) | No fallback — required |
| asyncpg | Async DB session | Not in requirements.txt | Latest | No fallback for async engine |
| lxml | Treasury XML parse | Not in requirements.txt | Latest | stdlib xml.etree (slower, workable) |
| FRED API key | INGEST-02 | Unknown — needs .env setup | — | No fallback — required |
| Frankfurter API | INGEST-07 | No key needed | — | exchangerate.host as backup |
| US Treasury XML | INGEST-08 | No key needed | — | FRED GS10/GS2 as proxy (less granular) |

**Missing dependencies with no fallback:**
- `yfinance`, `asyncpg`, `requests` — must be added to `requirements.txt` before implementation
- FRED API key — must be populated in `.env` before INGEST-02 tasks can run

**Missing dependencies with fallback:**
- `lxml` — stdlib `xml.etree.ElementTree` is viable; lxml preferred for namespace handling
- Redis upgrade to 7.4.0 — 7.3.0 works for all operations; upgrade is nice-to-have

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (to be added — not in requirements.txt) |
| Config file | `pytest.ini` or `pyproject.toml` — none exists yet (Wave 0 gap) |
| Quick run command | `pytest backend/tests/ -x -q` |
| Full suite command | `pytest backend/tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INGEST-01 | Celery beat fires without duplication; worker processes task | unit | `pytest backend/tests/test_tasks.py::test_ingest_ohlcv_task -x` | ❌ Wave 0 |
| INGEST-01 | `GET /api/quote/AAPL` returns OHLCV data | integration | `pytest backend/tests/test_quote_api.py::test_get_quote_aapl -x` | ❌ Wave 0 |
| INGEST-01 | `GET /api/quote/LLOY.L` returns LSE data | integration | `pytest backend/tests/test_quote_api.py::test_get_quote_lse -x` | ❌ Wave 0 |
| INGEST-02 | `GET /api/macro/fred/GDP` returns FRED data | integration | `pytest backend/tests/test_macro_api.py::test_get_macro_gdp -x` | ❌ Wave 0 |
| INGEST-03 | Redis TTL enforced — second call within TTL uses cache | unit | `pytest backend/tests/test_cache.py::test_ttl_cache_hit -x` | ❌ Wave 0 |
| INGEST-04 | Token bucket returns False after capacity exhausted | unit | `pytest backend/tests/test_rate_limiter.py::test_token_bucket_exhausted -x` | ❌ Wave 0 |
| INGEST-05 | Fallback chain returns stale=True from DB when API down | unit | `pytest backend/tests/test_fallback.py::test_fallback_to_db -x` | ❌ Wave 0 |
| INGEST-06 | All data written to DB — Redis eviction doesn't lose data | integration | `pytest backend/tests/test_persistence.py::test_data_written_to_db -x` | ❌ Wave 0 |
| INGEST-07 | `GET /api/rates/frankfurter` returns FX rates | integration | `pytest backend/tests/test_fx_api.py::test_get_fx_rates -x` | ❌ Wave 0 |
| INGEST-08 | `GET /api/rates/treasury` returns yield curve | integration | `pytest backend/tests/test_treasury_api.py::test_get_treasury_curve -x` | ❌ Wave 0 |
| INGEST-09 | WebSocket client receives pub/sub messages on subscribed channel | integration | `pytest backend/tests/test_websocket.py::test_ws_channel_fanout -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/ -x -q -m "not slow"`
- **Per wave merge:** `pytest backend/tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/__init__.py` — package init
- [ ] `backend/tests/conftest.py` — shared fixtures (mock Redis, mock DB session, mock yfinance)
- [ ] `backend/tests/test_tasks.py` — covers INGEST-01 Celery task unit tests
- [ ] `backend/tests/test_quote_api.py` — covers INGEST-01 REST endpoint
- [ ] `backend/tests/test_macro_api.py` — covers INGEST-02 REST endpoint
- [ ] `backend/tests/test_cache.py` — covers INGEST-03 TTL cache
- [ ] `backend/tests/test_rate_limiter.py` — covers INGEST-04 token bucket
- [ ] `backend/tests/test_fallback.py` — covers INGEST-05 fallback chain
- [ ] `backend/tests/test_persistence.py` — covers INGEST-06
- [ ] `backend/tests/test_websocket.py` — covers INGEST-09
- [ ] Framework install: add `pytest==8.x pytest-asyncio==0.24.x` to `requirements.txt`

---

## Sources

### Primary (HIGH confidence)
- Celery 5.6.2 docs — beat_schedule, autoretry_for, countdown parameters
- redis-py 7.x asyncio docs — `redis.asyncio` pubsub `listen()` and `psubscribe()` patterns
- TimescaleDB docs — `create_hypertable`, `add_compression_policy`, ON CONFLICT limitations on hypertables
- FastAPI lifespan docs — `@asynccontextmanager lifespan` pattern, `asyncio.create_task`
- pip index — confirmed versions: yfinance 1.2.0, celery 5.6.2, redis 7.4.0

### Secondary (MEDIUM confidence)
- Frankfurter API live response verification — base URL `https://api.frankfurter.dev`, `/v1/latest?base=USD&symbols=...`, `date`/`rates` response fields
- FRED API docs summary — `/fred/series/observations` endpoint, `api_key`/`series_id`/`file_type=json` params, response `observations[]`
- US Treasury XML feed search — URL format `?data=daily_treasury_yield_curve&field_tdr_date_value=YYYYMM`, OData Atom XML with `BC_1YEAR` etc. field names; Feb 2025 addition of 1.5M CMT

### Tertiary (LOW confidence — flag for validation at implementation)
- yfinance `.info` field names for fundamentals (`forwardPE`, `enterpriseToEbitda`, `debtToEquity`) — these are Yahoo Finance internal field names subject to change; verify against live ticker at implementation
- US Treasury XML exact element names post-Feb 2025 — fetch a live sample before hardcoding field list
- yfinance 429 behavior with `time.sleep(0.5)` sufficiency — real-world behavior depends on Yahoo Finance server load; may need higher delays

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified against pip registry; redis.asyncio confirmed in redis-py 7.x
- Architecture: HIGH — Celery beat/worker split established in Phase 1; all patterns sourced from official docs
- TimescaleDB schemas: HIGH — ON CONFLICT constraint limitation verified against TimescaleDB GitHub issues + docs
- yfinance field names: MEDIUM — confirmed via documentation but subject to Yahoo Finance changes
- US Treasury XML structure: MEDIUM — URL format confirmed; exact field names post-Feb 2025 need live verification
- Pitfalls: HIGH — yfinance 429 is widely reported and confirmed; other pitfalls sourced from official docs

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 for stable libraries; 2026-04-01 for yfinance (fast-moving re: Yahoo Finance compatibility)
