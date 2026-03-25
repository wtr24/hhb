---
phase: 02-data-ingestion-foundation
plan: 01
subsystem: database
tags: [sqlalchemy, timescaledb, alembic, asyncpg, pytest, hypertables]

# Dependency graph
requires:
  - phase: 01-infrastructure-bootstrap
    provides: TimescaleDB container, Alembic migration chain (0001 ohlcv hypertable), sync SQLAlchemy engine pattern

provides:
  - SQLAlchemy models for fundamentals, macro_series, fx_rates, yield_curve
  - Async SQLAlchemy engine and AsyncSessionLocal factory in backend/api/database.py
  - Alembic migration 0002 creating 4 new hypertables with compression policies
  - pytest test scaffold with schema correctness tests

affects: [02-02, 02-03, 02-04, 02-05, 03-equity-module, 04-macro-dashboard]

# Tech tracking
tech-stack:
  added: [yfinance==1.2.0, asyncpg==0.30.0, pandas>=2.0.0, lxml>=5.0.0, pytest>=8.0.0, pytest-asyncio>=0.24.0, requests>=2.32.0]
  patterns:
    - Async SQLAlchemy engine (postgresql+asyncpg://) alongside sync engine for migrations
    - async_sessionmaker with expire_on_commit=False for async route handlers
    - Alembic create_hypertable immediately after op.create_table with if_not_exists => TRUE
    - add_compression_policy for all hypertables after 30 days

key-files:
  created:
    - backend/models/fundamentals.py
    - backend/models/macro_series.py
    - backend/models/fx_rate.py
    - backend/models/yield_curve.py
    - backend/alembic/versions/0002_ingestion_hypertables.py
    - backend/conftest.py
    - backend/tests/ingestion/conftest.py
    - backend/tests/ingestion/test_schemas.py
  modified:
    - backend/requirements.txt
    - backend/models/__init__.py
    - backend/api/database.py

key-decisions:
  - "Added async engine alongside sync engine in database.py — sync stays for Alembic/Celery, async for FastAPI route handlers"
  - "Compression policies added for all 5 hypertables in migration 0002 (including ohlcv from 0001) — 30-day interval"
  - "YieldCurve has 12 tenor columns (bc_1month..bc_30year) with time-only PK — one row per business day"
  - "fx_rates PK is composite (time, base, quote) — supports multiple pairs per timestamp"

patterns-established:
  - "Model pattern: follow OHLCV style (Column imports from sqlalchemy, relative .base import, __table_args__ tuple)"
  - "Migration pattern: op.create_table then op.execute create_hypertable then op.create_index"
  - "Test pattern: SQLAlchemy inspect for schema assertions without live DB"

requirements-completed: [INGEST-06]

# Metrics
duration: 3min
completed: 2026-03-25
---

# Phase 2 Plan 1: Data Ingestion Foundation — Schema Models, Async Engine, and Hypertable Migration Summary

**4 new TimescaleDB hypertables (fundamentals, macro_series, fx_rates, yield_curve) with SQLAlchemy async engine and pytest schema scaffold**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T21:05:13Z
- **Completed:** 2026-03-25T21:07:34Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Created 4 SQLAlchemy models matching OHLCV pattern with correct PKs (fundamentals: time+ticker, macro_series: time+series_id, fx_rates: time+base+quote, yield_curve: time-only)
- Extended backend/api/database.py with async_engine, AsyncSessionLocal, and get_async_db() while preserving sync engine for Alembic and Celery
- Wrote Alembic migration 0002 creating all 4 hypertables plus compression policies for all 5 tables (including ohlcv from 0001)
- Built pytest schema test scaffold (13 tests) covering table names, PKs, and column presence — all passing without a live DB

## Task Commits

Each task was committed atomically:

1. **Task 1: SQLAlchemy models + async engine** - `8f080b6` (feat)
2. **Task 2: Alembic migration + test scaffold** - `aa4a029` (feat)

## Files Created/Modified

- `backend/requirements.txt` — added yfinance, asyncpg, pandas, lxml, pytest, pytest-asyncio, requests
- `backend/models/fundamentals.py` — Fundamentals model (time+ticker PK, PE/EV/MCap/D-E columns)
- `backend/models/macro_series.py` — MacroSeries model (time+series_id PK, value, source=fred)
- `backend/models/fx_rate.py` — FXRate model (time+base+quote PK, rate, source=frankfurter)
- `backend/models/yield_curve.py` — YieldCurve model (time PK, 12 tenor columns bc_1month..bc_30year)
- `backend/models/__init__.py` — updated exports for all 5 models
- `backend/api/database.py` — added async_engine, AsyncSessionLocal, get_async_db (sync preserved)
- `backend/alembic/versions/0002_ingestion_hypertables.py` — creates 4 hypertables + compression policies
- `backend/conftest.py` — sys.path setup for pytest
- `backend/tests/ingestion/conftest.py` — mock_redis and mock_async_session fixtures
- `backend/tests/ingestion/test_schemas.py` — 13 schema tests, all passing

## Decisions Made

- Kept sync engine unchanged in database.py — Alembic and Celery tasks use psycopg2, async engine uses asyncpg. No migration of existing code needed.
- Compression policies for all 5 hypertables added in 0002 migration (including ohlcv from 0001) — cleaner to have all policies in one place than spread across migrations.
- YieldCurve uses time-only PK rather than time+source — one canonical yield curve snapshot per day from US Treasury.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 4 model classes importable and schema-verified without a live DB
- Async engine ready for Phase 2 route handlers (02-02 through 02-05)
- Test infrastructure operational with pytest — 13 tests pass
- Migration 0002 ready to apply via `docker compose exec api alembic upgrade head` once DB is running

---
*Phase: 02-data-ingestion-foundation*
*Completed: 2026-03-25*
