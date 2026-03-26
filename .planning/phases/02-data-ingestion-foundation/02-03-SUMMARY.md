---
phase: 02-data-ingestion-foundation
plan: "03"
subsystem: ingestion
tags: [yfinance, celery, fastapi, redis, timescaledb, fallback-chain, tdd]

# Dependency graph
requires:
  - phase: 02-01
    provides: SQLAlchemy models (OHLCV, Fundamentals), async engine, database.py
  - phase: 02-02
    provides: cache_set/cache_get, check_rate_limit, SEED_TICKERS, RETRY_COUNTDOWNS, ingestion/config.py

provides:
  - yfinance data source (fetch_ohlcv_and_fundamentals, fetch_ohlcv_batch)
  - Celery ingest tasks (ingest_ohlcv_batch, ingest_ticker) with 60/300/900s retry
  - GET /api/quote/{ticker} endpoint with full INGEST-05 fallback chain
  - Redis pub/sub publishing on quotes:{ticker} channel

affects:
  - 02-04 (FRED macro ingestion — same task/retry pattern)
  - 02-05 (FX ingestion — same source/task pattern)
  - 02-06 (WebSocket broadcaster — subscribes to quotes:{ticker} pub/sub channels)
  - 03-equity-module (consumes GET /api/quote/{ticker})

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "yfinance fast_info.last_price for real-time price; t.info for fundamentals with independent try/except"
    - "time.sleep(0.5) between tickers in batch fetch to avoid Yahoo Finance 429"
    - "Celery retry: RETRY_COUNTDOWNS[min(attempt, len-1)] for bounded countdown lookup"
    - "on_conflict_do_nothing(index_elements=[time, ticker]) for idempotent DB upserts"
    - "Fallback chain: cache_get -> DB scalar_one_or_none -> apply_async + 20x0.5s poll -> 503"
    - "Relative imports (..database, ..redis_client) inside api/routes/ sub-package"

key-files:
  created:
    - backend/ingestion/sources/yfinance_source.py
    - backend/ingestion/sources/__init__.py
    - backend/api/routes/__init__.py
    - backend/api/routes/quote.py
    - backend/tests/ingestion/test_yfinance.py
  modified:
    - backend/ingestion/tasks.py
    - backend/api/main.py

key-decisions:
  - "Relative imports used in api/routes/quote.py (..database, ..redis_client) — consistent with health.py pattern, works inside the api package namespace"
  - "ingest_ticker lazy-imported inside get_quote function body to avoid circular import between api and ingestion packages"
  - "fetch_ohlcv_batch appends result outside try/except for the error case — failed tickers are skipped silently, not added as None"

requirements-completed: [INGEST-01, INGEST-05]

# Metrics
duration: 2min
completed: 2026-03-26
---

# Phase 2 Plan 03: yfinance Ingestion Pipeline and Quote REST Endpoint Summary

**yfinance OHLCV + fundamentals data source, Celery ingest tasks with 60/300/900s autoretry, and GET /api/quote/{ticker} with Redis cache -> DB -> on-demand ingest -> 503 fallback chain**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-26T06:42:49Z
- **Completed:** 2026-03-26T06:44:38Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `yfinance_source.py` fetches 5d/1d OHLCV bars + fast_info.last_price + .info fundamentals for any ticker including LSE `.L` suffix
- `fetch_ohlcv_batch` iterates seed tickers with `time.sleep(0.5)` to prevent Yahoo 429 rate limiting
- `tasks.py` wired with real `ingest_ohlcv_batch` (scheduled) and `ingest_ticker` (on-demand) tasks using `on_conflict_do_nothing` upserts and Redis pub/sub publishing on `quotes:{ticker}`
- Retry logic uses `RETRY_COUNTDOWNS[min(attempt, len-1)]` pattern for bounded 60/300/900s delays
- `GET /api/quote/{ticker}` implements full INGEST-05 fallback chain: Redis cache hit -> TimescaleDB latest row (stale=True) -> fire `ingest_ticker.apply_async` + 20x0.5s poll -> 503 with retry_after=15
- Response format matches D-13 spec: ticker, price, change_pct, OHLCV fields, stale flag, fundamentals nested dict
- 9 unit tests covering source structure, batch sleep behavior, task retry logic, and Redis publish — all passing

## Task Commits

1. **Task 1: yfinance source + Celery ingest tasks (TDD)** - `fad6857` (feat) — committed prior to this execution
2. **Task 2: Quote REST endpoint with fallback chain** - `0a52b04` (feat)

## Files Created/Modified

- `backend/ingestion/sources/__init__.py` — empty package init (existed)
- `backend/ingestion/sources/yfinance_source.py` — fetch_ohlcv_and_fundamentals + fetch_ohlcv_batch
- `backend/ingestion/tasks.py` — ingest_ohlcv_batch, ingest_ticker, _upsert_result helper
- `backend/api/routes/__init__.py` — empty package init (new)
- `backend/api/routes/quote.py` — GET /api/quote/{ticker} with full fallback chain + _build_quote_response
- `backend/api/main.py` — added quote_router registration
- `backend/tests/ingestion/test_yfinance.py` — 9 tests covering yfinance source and Celery tasks

## Decisions Made

- Used relative imports (`..database`, `..redis_client`) in `api/routes/quote.py` — consistent with `health.py` pattern, works correctly inside the `api` package namespace when `backend/` is on sys.path
- Lazy-imported `ingest_ticker` inside the `get_quote` function body to prevent circular imports between the `api` and `ingestion` packages at module load time
- Task 1 was already implemented and committed (`fad6857`) from a prior execution — verified tests pass and moved directly to Task 2

## Deviations from Plan

### Continuation from partial execution

Task 1 (yfinance source + Celery ingest tasks) was already committed as `fad6857` before this agent was spawned. Verified `python -m pytest backend/tests/ingestion/test_yfinance.py` passes (9 tests). Proceeded directly to Task 2.

### Auto-fixed: relative imports in api/routes sub-package

**Rule 3 - Blocking issue fix:** `quote.py` is in `api/routes/`, a sub-package of `api/`. Using `from api.database` would fail when the module is imported as part of the `api` package. Switched to relative imports `from ..database` and `from ..redis_client` — matching the established pattern in `health.py`.

## Known Stubs

- `change_pct` is always `None` in quote responses — previous close comparison is not yet implemented. This is intentional per D-13 which notes this is "computed when we have previous close". No future plan is yet assigned; will be addressed in equity module (Phase 3).

## Self-Check: PASSED

Files confirmed on disk:
- FOUND: backend/ingestion/sources/yfinance_source.py
- FOUND: backend/ingestion/sources/__init__.py
- FOUND: backend/api/routes/__init__.py
- FOUND: backend/api/routes/quote.py
- FOUND: backend/api/main.py (modified)
- FOUND: backend/ingestion/tasks.py (modified)
- FOUND: backend/tests/ingestion/test_yfinance.py

Commits confirmed:
- FOUND: fad6857 (feat(02-03): yfinance source + Celery ingest tasks with TDD)
- FOUND: 0a52b04 (feat(02-03): add quote REST endpoint with fallback chain)
