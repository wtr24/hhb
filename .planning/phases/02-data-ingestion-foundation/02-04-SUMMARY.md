---
phase: 02-data-ingestion-foundation
plan: "04"
subsystem: ingestion-sources
tags: [fred, frankfurter, treasury, macro, celery, fastapi, tdd]
dependency_graph:
  requires: ["02-01", "02-02", "02-03"]
  provides: ["fred_source", "frankfurter_source", "treasury_source", "macro_endpoint", "trigger_endpoint"]
  affects: ["celery_beat_schedule"]
tech_stack:
  added: ["lxml", "requests"]
  patterns: ["TDD red-green", "Celery bind=True max_retries=3", "pg_insert ON CONFLICT DO NOTHING", "Redis pub/sub + cache_set"]
key_files:
  created:
    - backend/ingestion/sources/fred_source.py
    - backend/ingestion/sources/frankfurter_source.py
    - backend/ingestion/sources/treasury_source.py
    - backend/api/routes/macro.py
    - backend/api/routes/ingest.py
    - backend/tests/ingestion/test_fred.py
    - backend/tests/ingestion/test_frankfurter.py
    - backend/tests/ingestion/test_treasury.py
  modified:
    - backend/ingestion/tasks.py
    - backend/api/main.py
decisions:
  - "Followed existing SessionLocal context-manager pattern (with SessionLocal() as session) instead of plan's _get_sync_session() helper — consistent with tasks.py established pattern"
  - "MaxRetriesExceededError imported from celery.exceptions — missing from plan's task code but required to catch exhausted retries"
  - "Lazy imports used for model classes inside Celery tasks (from models.X import Y) — avoids circular imports at module load time"
metrics:
  duration: 216s
  completed_date: "2026-03-26T06:53:42Z"
  tasks_completed: 2
  files_created: 8
  files_modified: 2
---

# Phase 2 Plan 04: FRED / Frankfurter / Treasury Ingestion Sources Summary

FRED macro, Frankfurter FX, and US Treasury yield curve source modules with Celery ingest tasks, macro time-series endpoint, and on-demand trigger endpoint — 3 new data pipelines delivering CPI/GDP/FX/yield curve data to TimescaleDB.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (TDD) | FRED + Frankfurter + Treasury source modules | b75b5e2 | fred_source.py, frankfurter_source.py, treasury_source.py + 3 test files |
| 2 | Celery tasks + macro and trigger endpoints | ead8fd1 | tasks.py, macro.py, ingest.py, main.py |

## What Was Built

### Source Modules

**`backend/ingestion/sources/fred_source.py`**
- `fetch_fred_series(series_id, limit=300)` — fetches FRED REST API observations
- Validates `FRED_API_KEY` env var (raises `ValueError` if missing)
- Filters out missing values (FRED uses `"."` for unavailable data)
- Returns `[{"date": "YYYY-MM-DD", "value": float}, ...]`

**`backend/ingestion/sources/frankfurter_source.py`**
- `fetch_fx_rates(base="USD")` — fetches from `api.frankfurter.dev/v1/latest`
- No API key required (free, open API)
- `TARGET_CURRENCIES = ["GBP", "EUR", "JPY", "CHF", "AUD", "CAD", "NZD", "NOK", "SEK"]`
- Returns full Frankfurter response dict with `amount`, `base`, `date`, `rates`

**`backend/ingestion/sources/treasury_source.py`**
- `fetch_treasury_yield_curve()` — fetches US Treasury XML for current month
- Uses `lxml.etree` to parse Atom feed with Microsoft DataServices namespaces
- All 12 `TENOR_FIELDS`: BC_1MONTH through BC_30YEAR
- Uses `NEW_DATE` from XML as timestamp (not `datetime.now()`) — per Research Pitfall 6
- Returns `[{"date": datetime(utc), "bc_1month": float|None, ...}, ...]`

### Celery Tasks (added to tasks.py)

- **`ingest_macro_batch`**: iterates all FRED series in `FRED_SERIES_MAP`, upserts to `macro_series` table, caches + publishes to Redis
- **`ingest_fx_rates`**: fetches Frankfurter USD rates, upserts to `fx_rates` table, caches + publishes per pair
- **`ingest_treasury_curve`**: fetches Treasury XML, upserts to `yield_curve` table, caches latest curve
- All 3 use `RETRY_COUNTDOWNS = [60, 300, 900]` pattern with `MaxRetriesExceededError`

### REST Endpoints

- **`GET /api/macro/{series}`** — returns D-15 format with `series`, `fred_id`, `observations[]`, `stale`, `last_updated`; validates series name against `FRED_SERIES_MAP`; Redis cache (3600s TTL)
- **`POST /api/ingest/trigger/{ticker}`** — fires `ingest_ticker.apply_async`; returns `{"status": "triggered", "ticker": ..., "task_id": ...}`

## Test Results

```
13 passed in 0.58s
```

All 3 source test files pass with mocked HTTP responses (`unittest.mock.patch("requests.get")`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Used existing SessionLocal pattern instead of _get_sync_session()**
- **Found during:** Task 2
- **Issue:** Plan's Celery task code referenced `_get_sync_session()` helper that doesn't exist in tasks.py; existing tasks use `with SessionLocal() as session`
- **Fix:** Used `with SessionLocal() as session` context manager consistently with existing pattern
- **Files modified:** backend/ingestion/tasks.py

**2. [Rule 2 - Missing] Added MaxRetriesExceededError import**
- **Found during:** Task 2
- **Issue:** Plan's task code catches `MaxRetriesExceededError` but the import was missing
- **Fix:** Added `from celery.exceptions import MaxRetriesExceededError` to imports
- **Files modified:** backend/ingestion/tasks.py

## Known Stubs

None — all data flows are wired. Celery beat schedule (which activates these tasks on a timer) is deferred to Plan 05 as documented in the plan.

## Self-Check: PASSED

All created files confirmed present on disk. Both feature commits (b75b5e2, ead8fd1) confirmed in git log. All 13 tests pass.
