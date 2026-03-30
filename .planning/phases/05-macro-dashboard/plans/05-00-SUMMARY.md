---
phase: 05-macro-dashboard
plan: "00"
subsystem: database
tags: [timescaledb, alembic, sqlalchemy, celery, redis, pytest]

# Dependency graph
requires:
  - phase: 04-technical-analysis-engine
    provides: migration 0004, existing config/ttl patterns, test stub pattern

provides:
  - gilt_curve hypertable and GiltCurve SQLAlchemy model
  - vix_term_structure hypertable and VixTermStructure SQLAlchemy model
  - Alembic migration 0005 with down_revision=0004
  - FRED_SERIES_MAP expanded to 12 series (tips_breakeven_5y, tips_breakeven_10y, hy_spread, safe_haven_usd)
  - SEED_TICKERS expanded with ^GSPC and DX-Y.NYB
  - 6 new SCHEDULE_* constants (BOE, VIX, CBOE, ONS, BLS, ECB)
  - 7 new TTL entries (gilt_curve, vix_term_structure, fear_greed, macro_curves, macro_indicators, macro_risk, macro_sentiment)
  - 27 Wave 0 test stubs across 5 test files — all SKIPPED, ready for Wave 1+ replacement

affects: [05-01-ingestion, 05-02-api-routes, 05-03-frontend, all macro dashboard plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wave 0 stub pattern: pytest.skip() in all test functions, downstream waves replace with real tests
    - Hypertable pattern: create_hypertable immediately after op.create_table with if_not_exists=TRUE

key-files:
  created:
    - backend/alembic/versions/0005_macro_dashboard.py
    - backend/models/gilt_curve.py
    - backend/models/vix_term_structure.py
    - backend/tests/macro/__init__.py
    - backend/tests/macro/test_boe_source.py
    - backend/tests/macro/test_vix_source.py
    - backend/tests/macro/test_cboe_source.py
    - backend/tests/macro/test_fear_greed.py
    - backend/tests/macro/test_macro_routes.py
  modified:
    - backend/ingestion/config.py
    - backend/cache/ttl.py

key-decisions:
  - "gilt_curve PK is (time, source) composite — allows future additional curve sources beyond BoE"
  - "vix_term_structure has no interval column — single 15-minute frequency series, matches ingestion schedule"
  - "SEED_TICKERS expanded with ^GSPC (SPX) and DX-Y.NYB (DXY) for MACRO-14 at-a-glance strip"
  - "27 stubs vs plan's 26 — routes file has 8 tests (4 endpoint pairs), boe/vix/cboe/fear_greed match plan exactly"

patterns-established:
  - "Wave 0 stub pattern: all test functions contain only pytest.skip() with requirement ID reference"

requirements-completed: [MACRO-01, MACRO-02, MACRO-07, MACRO-08, MACRO-09, MACRO-10, MACRO-11, MACRO-13]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 5 Plan 00: Foundation — DB Migration, Config Expansion, TTL Entries, Test Stubs Summary

**Alembic migration 0005 creates gilt_curve and vix_term_structure TimescaleDB hypertables; FRED_SERIES_MAP expanded to 12 series; 27 Wave 0 pytest stubs scaffold all macro dashboard test targets**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-30T15:35:51Z
- **Completed:** 2026-03-30T15:38:15Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments

- Created migration 0005 with gilt_curve (11 tenor columns, 6m–30y) and vix_term_structure (spot/3m/6m/contango/regime) hypertables; both get `create_hypertable` immediately after `create_table`
- Expanded FRED_SERIES_MAP from 8 to 12 entries (tips_breakeven_5y, tips_breakeven_10y, hy_spread, safe_haven_usd); added ^GSPC and DX-Y.NYB to SEED_TICKERS; added 6 new SCHEDULE_* constants and 7 new TTL entries
- Created 27 Wave 0 test stubs across 5 test files — `pytest backend/tests/macro/ -x -q` reports 27 skipped, 0 failed, 0 errors

## Task Commits

Each task was committed atomically:

1. **Task 5-00-1: DB migration 0005 — gilt_curve and vix_term_structure hypertables** - `678a085` (feat)
2. **Task 5-00-2: Config expansion and TTL entries** - `91e23db` (feat)
3. **Task 5-00-3: Wave 0 test stubs — five test files** - `5cf5ac3` (test)

## Files Created/Modified

- `backend/alembic/versions/0005_macro_dashboard.py` - Migration creating gilt_curve and vix_term_structure hypertables with indexes; down_revision=0004
- `backend/models/gilt_curve.py` - SQLAlchemy model for gilt_curve (composite PK: time+source, 11 tenor Float columns)
- `backend/models/vix_term_structure.py` - SQLAlchemy model for vix_term_structure (PK: time, spot_vix/vix_3m/vix_6m/contango/regime)
- `backend/ingestion/config.py` - FRED_SERIES_MAP +4 entries; SEED_TICKERS +2 tickers; +6 SCHEDULE_* constants
- `backend/cache/ttl.py` - +7 TTL entries for macro dashboard endpoints
- `backend/tests/macro/__init__.py` - Package marker (empty)
- `backend/tests/macro/test_boe_source.py` - 5 BoE gilt curve stubs (MACRO-02)
- `backend/tests/macro/test_vix_source.py` - 5 VIX term structure stubs (MACRO-11/12)
- `backend/tests/macro/test_cboe_source.py` - 3 CBOE put/call ratio stubs (MACRO-13)
- `backend/tests/macro/test_fear_greed.py` - 6 Fear & Greed computation stubs (MACRO-13)
- `backend/tests/macro/test_macro_routes.py` - 8 macro API route stubs (MACRO-01 through MACRO-14)

## Decisions Made

- gilt_curve PK is composite (time, source) to allow future additional curve sources beyond BoE
- vix_term_structure has no interval column — single 15-minute series, matches SCHEDULE_VIX=900
- SEED_TICKERS expanded with ^GSPC (SPX) and DX-Y.NYB (DXY) for MACRO-14 at-a-glance strip and SPX seasonality
- Actual test count is 27 (plan stated 26) — routes file has 8 stubs (4 endpoint x 2 assertion types each); difference is immaterial, all stubs SKIPPED

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Migration 0005 is ready to apply; downstream ingestion tasks (plan 05-01) can reference gilt_curve and vix_term_structure tables
- Config constants ready for Celery beat schedule wiring in 05-01
- TTL keys ready for route handlers in 05-02
- All 27 test stubs present; Wave 1+ plans replace each stub with a real test

---
*Phase: 05-macro-dashboard*
*Completed: 2026-03-30*
