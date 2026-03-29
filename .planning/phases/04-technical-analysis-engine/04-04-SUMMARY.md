---
phase: 04-technical-analysis-engine
plan: "04"
subsystem: api
tags: [fastapi, ta-lib, pandas-ta, redis, timescaledb, numpy, technical-analysis]

# Dependency graph
requires:
  - phase: 04-01
    provides: indicators.py with 50+ pure computation functions
  - phase: 04-02
    provides: garch.py, volume indicators, breadth functions
  - phase: 04-03
    provides: pivot_points.py, intermarket.py, PivotPoints model

provides:
  - GET /api/ta/indicators/{ticker} with whitelist dispatch to 50+ indicators
  - GET /api/ta/pivots/{ticker} serving pre-computed pivot levels from DB
  - GET /api/ta/intermarket/{ticker} rolling correlations for intermarket pairs
  - TA router registered in main.py

affects: [frontend-ta-panel, phase-05-patterns, backtester]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Module-level dispatch dict using closures bound at call time (avoids eval)
    - Whitelist set for route parameter validation (injection prevention)
    - GARCH handled via explicit branch separate from main dispatch table
    - Direct redis.set(ex=N) for custom TTLs outside cache/ttl.py named tiers

key-files:
  created:
    - backend/api/routes/ta.py
  modified:
    - backend/api/main.py

key-decisions:
  - "Dispatch dict uses _build_dispatch() helper that creates closures with ohlcv arrays in scope — avoids global state, each request gets its own closure scope"
  - "plan specified 'from backend.api.deps import get_db, get_redis' but deps.py does not exist — used ..database.get_async_db and ..redis_client.get_redis to match equity.py pattern"
  - "GARCH sentinel set to None in dispatch dict; indicator route checks 'if indicator == GARCH' before dispatch — keeps GARCH visually listed but handled separately"
  - "Intermarket route aligns two time series on date keys before computing correlation — handles gaps/mismatched lengths between different instruments"

patterns-established:
  - "TA route pattern: fetch OHLCV -> build numpy arrays -> dispatch to pure function -> cache 300s"
  - "Pivot route pattern: query DB for latest rows by method -> deduplicate -> no cache (fast DB read)"
  - "Intermarket route pattern: align on date intersection -> compute rolling correlation -> cache 3600s"

requirements-completed: [TA-01, TA-02, TA-03, TA-04, TA-05, TA-06, TA-07, TA-08]

# Metrics
duration: 5min
completed: 2026-03-29
---

# Phase 04 Plan 04: TA API Routes Summary

**FastAPI TA routes exposing 50+ indicator functions, pivot point lookup, and intermarket rolling correlations — all wired to TimescaleDB with Redis caching**

## Performance

- **Duration:** 4 min 24s
- **Started:** 2026-03-29T20:11:45Z
- **Completed:** 2026-03-29T20:16:09Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `backend/api/routes/ta.py` with 3 routes covering all TA-01 through TA-08 requirements
- Whitelist enforcement (50+ indicator names) prevents injection; returns 400 for unknown names
- GARCH handled via separate branch using `garch.py` with minimum bar check
- Registered `ta_router` in `main.py` after existing router includes

## Task Commits

1. **Task 4-04-1: Create TA routes file** - `84761de` (feat)
2. **Task 4-04-2: Register TA router in main.py** - `0297421` (feat)

## Files Created/Modified

- `backend/api/routes/ta.py` — 3-route TA API file with whitelist dispatch, GARCH branch, pivot DB query, intermarket alignment
- `backend/api/main.py` — Added ta_router import and include_router call

## Decisions Made

- The plan specified `from backend.api.deps import get_db, get_redis` but `deps.py` does not exist in the project. Used `from ..database import get_async_db` and `from ..redis_client import get_redis` to match the established `equity.py` pattern (Rule 1 auto-fix).
- Dispatch dict uses a `_build_dispatch()` helper that creates closures per request, binding numpy arrays in closure scope rather than globals — avoids state leakage between concurrent requests.
- Intermarket route aligns two series on their date intersection before passing to `compute_rolling_correlation`, handling instruments with different trading calendars (e.g. CPIAUCSL monthly vs daily equities).
- GARCH listed as `None` sentinel in dispatch dict to make it visually present in the whitelist but routed to the explicit `if indicator == "GARCH"` branch.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed non-existent deps.py import**
- **Found during:** Task 4-04-1 (Create TA routes file)
- **Issue:** Plan specified `from backend.api.deps import get_db, get_redis` but `backend/api/deps.py` does not exist in the project
- **Fix:** Used `from ..database import get_async_db` and `from ..redis_client import get_redis` — exact pattern used by `equity.py`
- **Files modified:** `backend/api/routes/ta.py`
- **Verification:** Syntax check passes; import pattern confirmed in equity.py
- **Committed in:** `84761de` (Task 4-04-1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — wrong import path in plan)
**Impact on plan:** Necessary correctness fix. No scope creep.

## Issues Encountered

None beyond the deps.py import deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All TA indicator endpoints ready for frontend consumption (Phase 05 pattern detection, Phase 08 screener)
- `/api/ta/indicators/{ticker}?indicator=RSI&timeframe=1d` returns computed RSI when OHLCV data present
- Pivot endpoint returns 404 gracefully when nightly task hasn't run yet
- Intermarket endpoint returns partial results (with error fields) for pairs missing OHLCV data

---
*Phase: 04-technical-analysis-engine*
*Completed: 2026-03-29*

## Self-Check: PASSED

- `backend/api/routes/ta.py`: FOUND
- `backend/api/main.py`: FOUND (ta_router imported and included)
- Commit `84761de`: FOUND (feat(04-04): create TA API routes file)
- Commit `0297421`: FOUND (feat(04-04): register TA router in main.py)
