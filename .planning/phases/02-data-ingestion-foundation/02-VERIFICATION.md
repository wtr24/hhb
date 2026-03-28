---
phase: 02-data-ingestion-foundation
verified: 2026-03-28T00:00:00Z
status: gaps_found
score: 16/18 must-haves verified
re_verification: false
gaps:
  - truth: "Rate limit token buckets in Redis protect all API sources (INGEST-04)"
    status: failed
    reason: "check_rate_limit is built and exported but never called in any ingestion task or source file. D-06 states 'Celery workers check before firing' but no task calls check_rate_limit."
    artifacts:
      - path: "backend/cache/rate_limiter.py"
        issue: "ORPHANED — exported but no caller exists in production code"
      - path: "backend/ingestion/tasks.py"
        issue: "Does not import or call check_rate_limit before any API fetch"
      - path: "backend/ingestion/sources/yfinance_source.py"
        issue: "No rate limit check before yfinance calls"
      - path: "backend/ingestion/sources/fred_source.py"
        issue: "No rate limit check before FRED API calls"
      - path: "backend/ingestion/sources/frankfurter_source.py"
        issue: "No rate limit check before Frankfurter API calls"
    missing:
      - "Call check_rate_limit(redis_client, 'finnhub') (or applicable source name) in tasks.py before each API fetch, or inside each source function"
      - "Note: yfinance has no named source in RATE_LIMITS — either add 'yfinance' entry or document exemption"
  - truth: "Fallback chain: Live API -> Redis cache -> TimescaleDB last-known -> stale warning -> error (INGEST-05)"
    status: partial
    reason: "The implemented fallback chain order is Redis cache -> TimescaleDB -> on-demand Celery ingest -> error. This matches the plan task spec (02-03 Task 2) but differs from REQUIREMENTS.md INGEST-05 wording ('Live API -> Redis cache -> TimescaleDB last-known'). The implementation returns stale=True for TimescaleDB hits and fires Celery on total miss. The stale flag is correctly set. The REQUIREMENTS.md text appears to describe the Celery worker's internal chain, not the endpoint chain — but this ambiguity is a documentation discrepancy, not a code failure. Marking partial rather than failed because the stale warning and error behaviors are correctly implemented and the plan task spec is satisfied."
    artifacts:
      - path: "backend/api/routes/quote.py"
        issue: "Chain is: Redis hit (stale=False) -> TimescaleDB hit (stale=True) -> Celery ingest + poll -> 503. Does not attempt live API call directly from endpoint — delegates to Celery. This is intentional per D-11 but differs from INGEST-05 literal text."
    missing:
      - "Clarify REQUIREMENTS.md INGEST-05 wording to match implemented chain, or document that 'Live API' means the async Celery path"
human_verification:
  - test: "Celery beat worker fires tasks on schedule"
    expected: "celery -A ingestion.celery_app beat starts and logs task fires at correct intervals (5m OHLCV, 1h macro, 30s FX, 15m treasury)"
    why_human: "Cannot verify beat scheduler fires without running the Docker stack"
  - test: "GET /api/quote/AAPL returns non-empty OHLCV + fundamentals after first ingest"
    expected: "Response contains ticker, price, open/high/low/close, volume, stale=false, fundamentals dict"
    why_human: "Requires live TimescaleDB + running Celery worker to populate data"
  - test: "GET /api/macro/cpi returns 24-month time series after FRED ingest"
    expected: "Response contains series='cpi', fred_id='CPIAUCSL', observations list with date+value pairs"
    why_human: "Requires FRED_API_KEY env var and running Celery worker"
  - test: "WebSocket channel subscription delivers initial snapshot then live updates"
    expected: "Client subscribes to quotes:AAPL, receives stale=true snapshot immediately, then live updates as ingest_ticker fires"
    why_human: "Requires browser WebSocket client or wscat to test"
---

# Phase 02: Data Ingestion Foundation Verification Report

**Phase Goal:** Core ingestion pipeline live — Celery workers running on schedule, yfinance/FRED/Frankfurter/US Treasury data flowing into TimescaleDB via Redis rate-limited cache
**Verified:** 2026-03-28T00:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All 4 new hypertables exist in TimescaleDB after migration | ✓ VERIFIED | `0002_ingestion_hypertables.py` creates fundamentals, macro_series, fx_rates, yield_curve with `create_hypertable` + `if_not_exists` |
| 2 | SQLAlchemy async engine available for route handlers | ✓ VERIFIED | `database.py` exports `async_engine`, `AsyncSessionLocal`, `get_async_db` with `postgresql+asyncpg://` |
| 3 | Test infrastructure is runnable with pytest | ✓ VERIFIED | `conftest.py` + `tests/ingestion/` with 7 test files present and substantive |
| 4 | Redis TTL caching sets correct expiry per data type | ✓ VERIFIED | `cache/ttl.py` TTL dict: quote=15, fx=30, fundamentals=86400, macro=3600, yield_curve=900 |
| 5 | Token bucket rate limiter atomically checks via Lua script | ✓ VERIFIED | `cache/rate_limiter.py` uses EVAL with Lua TOKEN_BUCKET_LUA; RATE_LIMITS matches spec exactly |
| 6 | Rate limit constants match spec | ✓ VERIFIED | Finnhub 60/60s, FMP 250/86400s, Alpha Vantage 25/86400s, CoinGecko 13/3600s — all correct |
| 7 | Rate limit token buckets protect all API sources in practice | ✗ FAILED | `check_rate_limit` built and exported but never called in any task or source. D-06 violated. |
| 8 | yfinance fetches OHLCV bars + fundamentals for any ticker | ✓ VERIFIED | `yfinance_source.py` uses `yf.Ticker.history()` + `fast_info` + `t.info`, handles LSE tickers via yfinance ticker format |
| 9 | Celery task uses autoretry with 60s/300s/900s countdown | ✓ VERIFIED | All tasks use `bind=True, max_retries=3` + `RETRY_COUNTDOWNS[min(attempt, len-1)]` pattern |
| 10 | GET /api/quote/{ticker} returns OHLCV + fundamentals with stale flag | ✓ VERIFIED | `quote.py` implements full chain: cache hit → DB hit (stale=True) → Celery ingest + 10s poll → 503 |
| 11 | Fallback chain: cache → DB → on-demand Celery → error | ? PARTIAL | Chain is correctly implemented per plan task spec; stale flag correctly set. INGEST-05 text in requirements differs from plan — see gaps. |
| 12 | FRED worker fetches macro series and stores to TimescaleDB | ✓ VERIFIED | `ingest_macro_batch` iterates FRED_SERIES_MAP, calls `fetch_fred_series`, upserts to `macro_series` table |
| 13 | Frankfurter worker fetches FX rates every 30s | ✓ VERIFIED | `ingest_fx_rates` calls `fetch_fx_rates("USD")`, upserts to `fx_rates`, beat fires every 30s |
| 14 | US Treasury XML worker parses yield curve tenors and stores to TimescaleDB | ✓ VERIFIED | `treasury_source.py` parses 12 TENOR_FIELDS from XML, `ingest_treasury_curve` upserts to `yield_curve` table |
| 15 | GET /api/macro/{series} returns 24-month time series | ✓ VERIFIED | `macro.py` queries `.limit(300)` with desc order, uses FRED_SERIES_MAP friendly name mapping |
| 16 | Celery beat fires all 4 tasks on correct intervals | ✓ VERIFIED | `celery_app.py` beat_schedule: OHLCV 5min, macro 1h, FX 30s, treasury 15min — task names match `ingestion.tasks.*` |
| 17 | WebSocket clients subscribe to channels via JSON message | ✓ VERIFIED | `websocket.py` handles `{"action": "subscribe", "channels": [...]}`, calls `manager.subscribe(ws, channel)` |
| 18 | Redis pub/sub listener runs as single asyncio background task | ✓ VERIFIED | `main.py` lifespan creates single `asyncio.create_task(_redis_pubsub_listener)`, `psubscribe("quotes:*", "macro:*", "fx:*")`, fans out to `manager.broadcast_to_channel` |

**Score:** 16/18 truths verified (1 failed, 1 partial)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/models/fundamentals.py` | Fundamentals SQLAlchemy model | ✓ VERIFIED | `class Fundamentals` with time+ticker PK, pe_ratio, ev_ebitda, market_cap, debt_equity |
| `backend/models/macro_series.py` | MacroSeries SQLAlchemy model | ✓ VERIFIED | `class MacroSeries` with time+series_id PK |
| `backend/models/fx_rate.py` | FXRate SQLAlchemy model | ✓ VERIFIED | `class FXRate` with time+base+quote PK |
| `backend/models/yield_curve.py` | YieldCurve SQLAlchemy model | ✓ VERIFIED | `class YieldCurve` with 12 tenor columns |
| `backend/alembic/versions/0002_ingestion_hypertables.py` | Migration for 4 hypertables | ✓ VERIFIED | All 4 tables + `create_hypertable` calls + compression policies |
| `backend/api/database.py` | Async engine + session factory | ✓ VERIFIED | Exports `async_engine`, `AsyncSessionLocal`, `get_async_db` |
| `backend/cache/ttl.py` | TTL constants + cache helpers | ✓ VERIFIED | TTL dict, `cache_set`, `cache_get` |
| `backend/cache/rate_limiter.py` | Lua-based token bucket | ✓ WIRED-BUT-ORPHANED | Implementation correct; never called in production paths |
| `backend/ingestion/config.py` | Seed tickers + FRED map + schedules | ✓ VERIFIED | SEED_TICKERS, FRED_SERIES_MAP, RETRY_COUNTDOWNS, SCHEDULE_* constants |
| `backend/ingestion/sources/yfinance_source.py` | yfinance fetch functions | ✓ VERIFIED | `fetch_ohlcv_and_fundamentals`, `fetch_ohlcv_batch` |
| `backend/ingestion/tasks.py` | Celery ingest tasks | ✓ VERIFIED | `ingest_ohlcv_batch`, `ingest_ticker`, `ingest_macro_batch`, `ingest_fx_rates`, `ingest_treasury_curve` |
| `backend/api/routes/quote.py` | GET /api/quote/{ticker} | ✓ VERIFIED | Full fallback chain + stale flag |
| `backend/ingestion/sources/fred_source.py` | FRED API fetch functions | ✓ VERIFIED | `fetch_fred_series` with FRED_API_KEY env check |
| `backend/ingestion/sources/frankfurter_source.py` | Frankfurter FX fetch | ✓ VERIFIED | `fetch_fx_rates` with TARGET_CURRENCIES including GBP |
| `backend/ingestion/sources/treasury_source.py` | US Treasury XML parse | ✓ VERIFIED | `fetch_treasury_yield_curve` with lxml + TENOR_FIELDS + namespace parsing |
| `backend/api/routes/macro.py` | GET /api/macro/{series} | ✓ VERIFIED | `get_macro_series` with FRED_SERIES_MAP lookup + 300-row query |
| `backend/api/routes/ingest.py` | POST /api/ingest/trigger/{ticker} | ✓ VERIFIED | `trigger_ingest` calls `ingest_ticker.apply_async` |
| `backend/ingestion/celery_app.py` | beat_schedule with 4 entries | ✓ VERIFIED | All 4 entries with correct task names and timedelta intervals |
| `backend/api/websocket.py` | ConnectionManager + channel fan-out | ✓ VERIFIED | `broadcast_to_channel`, `subscribe`, `send_initial_snapshot` |
| `backend/api/main.py` | FastAPI lifespan + pub/sub listener | ✓ VERIFIED | `lifespan` creates background `_redis_pubsub_listener`, all routers included |
| `backend/api/redis_client.py` | Async Redis URL helper | ✓ VERIFIED | `get_async_redis_url` exported |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `alembic/versions/0002_*.py` | TimescaleDB | `create_hypertable` calls | ✓ WIRED | Pattern `create_hypertable.*if_not_exists` found in all 4 tables |
| `cache/rate_limiter.py` | Redis | `redis_client.eval` Lua | ✓ WIRED (impl) / ✗ ORPHANED (usage) | Lua eval call exists in `check_rate_limit`; no caller in production code |
| `api/routes/quote.py` | `cache/ttl.py` | `cache_get/cache_set` calls | ✓ WIRED | `cache_get(redis_client, f"quote:{ticker}")` and `cache_set` present |
| `api/routes/quote.py` | `ingestion/tasks.py` | `ingest_ticker.apply_async` on cache miss | ✓ WIRED | `ingest_ticker.apply_async(args=[ticker])` on no-data path |
| `ingestion/tasks.py` | `ingestion/sources/yfinance_source.py` | `fetch_ohlcv_and_fundamentals` call | ✓ WIRED | Direct import + call in `ingest_ohlcv_batch` and `ingest_ticker` |
| `api/routes/macro.py` | `ingestion/config.py` | `FRED_SERIES_MAP` lookup | ✓ WIRED | `from ingestion.config import FRED_SERIES_MAP` + `FRED_SERIES_MAP[series]` |
| `ingestion/sources/treasury_source.py` | TimescaleDB yield_curve | XML rows via TENOR_FIELDS | ✓ WIRED | `TENOR_FIELDS` used in XML parse; rows upserted to YieldCurve in tasks.py |
| `ingestion/celery_app.py` | `ingestion/tasks.py` | task name strings in beat_schedule | ✓ WIRED | All 4 entries use `ingestion.tasks.ingest_*` names matching actual function names |
| `api/main.py` | `api/websocket.py` | lifespan starts pubsub listener → `manager.broadcast_to_channel` | ✓ WIRED | `_redis_pubsub_listener` in lifespan; calls `manager.broadcast_to_channel(channel, data)` |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `api/routes/quote.py` | `ohlcv_row`, `fund_row` | `select(OHLCV)` + `select(Fundamentals)` from TimescaleDB | Yes — DB queries on `OHLCV.ticker` with desc time ordering | ✓ FLOWING |
| `api/routes/macro.py` | `rows` | `select(MacroSeries).where(series_id == fred_id).limit(300)` | Yes — real DB query with filter | ✓ FLOWING |
| `api/websocket.py` | `row` in `send_initial_snapshot` | `_fetch_latest_for_channel` queries OHLCV/MacroSeries/FXRate per channel type | Yes — real DB queries per channel | ✓ FLOWING |
| `api/main.py` | `data` in pubsub listener | `pubsub.listen()` from Redis pub/sub; published by `ingest_ticker` and other tasks | Yes — published by Celery tasks after real API fetch + DB write | ✓ FLOWING |

---

## Behavioral Spot-Checks

Step 7b: SKIPPED — requires running Docker stack (TimescaleDB, Redis, Celery). No standalone entry points are testable without services.

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INGEST-01 | 02-03, 02-05 | Celery workers ingest yfinance OHLCV + fundamentals on demand and on schedule | ✓ SATISFIED | `ingest_ohlcv_batch` (scheduled) + `ingest_ticker` (on-demand) both present; beat fires every 5min |
| INGEST-02 | 02-04, 02-05 | FRED ingestion worker fetches macro series on 1h schedule | ✓ SATISFIED | `ingest_macro_batch` iterates FRED_SERIES_MAP; beat fires every 1h |
| INGEST-03 | 02-02 | Redis TTL caching enforced per data type per spec §5 | ✓ SATISFIED | `cache/ttl.py` TTL dict correct; `cache_set/cache_get` used in all routes and tasks |
| INGEST-04 | 02-02 | Rate limit token buckets protect all API sources | ✗ BLOCKED | Token bucket Lua script built and correct, but `check_rate_limit` is never called in any task or source |
| INGEST-05 | 02-03 | Fallback chain: Live API → Redis cache → TimescaleDB last-known → stale warning → error | ? PARTIAL | Stale flag and error correctly implemented; chain order in endpoint is cache→DB→Celery→error (per D-11 plan spec), not literal INGEST-05 text. Functional behavior is correct; requirements text is ambiguous. |
| INGEST-06 | 02-01 | All ingested data written to TimescaleDB — nothing cache-only | ✓ SATISFIED | All 4 tasks (`ingest_ohlcv_batch`, `ingest_macro_batch`, `ingest_fx_rates`, `ingest_treasury_curve`) write to DB before/alongside cache operations |
| INGEST-07 | 02-04, 02-05 | Frankfurter FX rates ingested on 30s schedule for major pairs + GBP crosses | ✓ SATISFIED | `ingest_fx_rates` fires every 30s; TARGET_CURRENCIES includes GBP; USD-to-all-pairs approach covers major pairs including GBP |
| INGEST-08 | 02-04, 02-05 | US Treasury XML yield curve ingested on 15m schedule | ✓ SATISFIED | `ingest_treasury_curve` fires every 15min; all 12 TENOR_FIELDS parsed from XML |
| INGEST-09 | 02-06 | FastAPI WebSocket broadcaster subscribes to Redis pub/sub and fans out | ✓ SATISFIED | Lifespan-managed `_redis_pubsub_listener` with `psubscribe("quotes:*", "macro:*", "fx:*")`; fans out via `broadcast_to_channel` to channel-subscribed clients only |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/cache/rate_limiter.py` | 33 | `check_rate_limit` defined but never called from production code | ✗ Blocker | INGEST-04 unsatisfied; API sources have no rate protection |
| `backend/ingestion/tasks.py` | 24-26 | `health_check_task` is a placeholder returning `{"status": "celery_ok"}` | ℹ Info | Not in any requirement; acceptable for health probe use |

No TODO/FIXME/HACK/PLACEHOLDER comments found in Phase 2 production files. No empty `return []` or `return {}` stubs found. No hardcoded empty props patterns.

---

## Human Verification Required

### 1. Celery Beat Schedule Fires

**Test:** Start the Docker stack (`docker compose up`) and check Celery beat logs.
**Expected:** Log lines confirming `ingest-ohlcv-every-5min`, `ingest-fx-every-30s`, `ingest-macro-every-1h`, `ingest-treasury-every-15m` fire on schedule.
**Why human:** Cannot verify beat fires without running Redis + Celery.

### 2. GET /api/quote/AAPL returns live data

**Test:** After Celery runs at least one `ingest_ohlcv_batch`, `curl http://localhost:8000/api/quote/AAPL`.
**Expected:** JSON with `ticker`, `price` (float), `open/high/low/close/volume`, `stale: false`, `fundamentals` dict.
**Why human:** Requires running stack with FRED_API_KEY and live internet access.

### 3. GET /api/macro/cpi returns 24-month observations

**Test:** After `ingest_macro_batch` runs, `curl http://localhost:8000/api/macro/cpi`.
**Expected:** JSON with `series: "cpi"`, `fred_id: "CPIAUCSL"`, `observations` list with date+value entries.
**Why human:** Requires `FRED_API_KEY` env var + running Celery.

### 4. WebSocket channel subscription delivers initial snapshot then live updates

**Test:** Connect to `ws://localhost:8000/ws`, send `{"action": "subscribe", "channels": ["quotes:AAPL"]}`.
**Expected:** Server sends `{"action": "subscribed", "channels": ["quotes:AAPL"]}` immediately; then sends latest OHLCV row (stale=true) if data exists; then sends live updates as `ingest_ticker` fires.
**Why human:** Requires browser/wscat WebSocket client + running Docker stack.

---

## Gaps Summary

Two gaps identified:

**Gap 1 (BLOCKER): INGEST-04 — Rate limiter built but never enforced.**
`check_rate_limit` is a complete, correct Lua-based token bucket implementation that was designed per D-06 ("Celery workers check before firing"). However, no ingestion task or source function imports or calls it. The rate limiter is an orphaned module — it exists, it is correct, it is exported, but it has zero production callers. INGEST-04 requires it to "protect all API sources." This is a wiring gap: the artifact passes levels 1-3 (exists, substantive, exported) but fails level 3 in the opposite direction — nothing calls into it.

**Gap 2 (WARNING): INGEST-05 — Requirements text ambiguity vs. implementation.**
The implementation follows D-11 (endpoint fires Celery on DB miss, polls for 10s) and the plan task spec precisely. The `stale=True` flag is correctly set for DB-only hits and `stale=False` for fresh data. The REQUIREMENTS.md text states the chain order as "Live API → Redis cache → TimescaleDB last-known" which is internally inconsistent with D-11 (which makes the endpoint fire Celery, not call a live API directly). This is a documentation gap. The implementation is functionally correct and achieves the intended user experience (stale warning on old data, error on total miss). Recommended action: update REQUIREMENTS.md INGEST-05 text to match the actual chain.

---

_Verified: 2026-03-28T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
