---
phase: "04"
plan: "04-03"
subsystem: backend-analysis
tags: [market-breadth, pivot-points, intermarket, celery, ta-indicators]
dependency_graph:
  requires: [04-02]
  provides: [TA-06, TA-07, TA-08]
  affects: [frontend-indicator-panels, nightly-celery-beat]
tech_stack:
  added: []
  patterns:
    - pure-function numpy analysis modules (no DB calls in analysis layer)
    - Celery task for nightly pivot point computation with per-ticker exception isolation
    - Log return rolling Pearson correlation for stationarity
key_files:
  created:
    - backend/analysis/pivot_points.py
    - backend/analysis/intermarket.py
  modified:
    - backend/ingestion/celery_app.py
    - backend/ingestion/tasks.py
    - backend/tests/analysis/test_indicators.py
    - backend/tests/analysis/test_pivot_points.py
decisions:
  - Celery task function placed in tasks.py (not celery_app.py as plan literally stated) — consistent with all existing task function placement; celery_app.py updated only for beat_schedule entry
  - crontab import added to celery_app.py (crontab not timedelta required for hour/minute precision)
  - compute_nightly_pivot_points uses delete+insert pattern (not upsert) since PivotPoints lacks a single-column conflict target
metrics:
  duration: 267s
  completed_date: "2026-03-29"
  tasks_completed: 4
  files_changed: 6
---

# Phase 04 Plan 03: Market Breadth, Pivot Points, Intermarket Correlations Summary

**One-liner:** Pure-function modules for market breadth (A/D Line, McClellan, TRIN), all 5 pivot point methods pre-computed nightly via Celery beat, and 7-pair intermarket rolling correlations — completing TA-06, TA-07, TA-08.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 4-03-1 | Market breadth module (TA-06) | 2f4fe54 | backend/analysis/breadth.py |
| 4-03-2 | Pivot points module + Celery task (TA-07) | a3b2c0d | backend/analysis/pivot_points.py, backend/ingestion/celery_app.py, backend/ingestion/tasks.py |
| 4-03-3 | Intermarket correlation module (TA-08) | e862f02 | backend/analysis/intermarket.py |
| 4-03-4 | Update test stubs for TA-06, TA-07, TA-08 | efbde0c | backend/tests/analysis/test_indicators.py, backend/tests/analysis/test_pivot_points.py |

## Verification

All 33 tests in `test_indicators.py` and `test_pivot_points.py` pass:

```
33 passed, 1 warning in 3.46s
```

- TA-06 breadth: McClellan oscillator+summation keys present and non-empty; TRIN = 1.0 for equal advances/declines/volumes; pct_above_sma values in 0–100 range
- TA-07 pivots: Standard PP ≈ 111.83; Camarilla r4/s4 keys present; Fibonacci r3 > r2 > r1 > pp > s1 > s2 > s3; DeMark r2/r3 correctly None; compute_all_methods returns 5 dicts each with pp/r1/s1
- TA-08 intermarket: Rolling correlation values all within -1.0 to +1.0

## Deviations from Plan

### Structural adjustment (no functional impact)

**1. [Rule 2 - Pattern] Celery task function placed in tasks.py, not celery_app.py**
- **Found during:** Task 2
- **Issue:** Plan said to add task function to `celery_app.py`, but all existing task functions (ingest_ohlcv_batch, ingest_macro_batch, etc.) are in `tasks.py`. Adding a task function to celery_app.py would break the include-based autodiscovery pattern and be inconsistent with the codebase convention.
- **Fix:** `compute_nightly_pivot_points` placed in `tasks.py`; `celery_app.py` updated only for beat_schedule entry (plus crontab import).
- **Files modified:** backend/ingestion/tasks.py, backend/ingestion/celery_app.py

## Known Stubs

None — all Wave-0 stubs for TA-06, TA-07, TA-08 replaced with real assertions in this plan.

## Self-Check: PASSED
