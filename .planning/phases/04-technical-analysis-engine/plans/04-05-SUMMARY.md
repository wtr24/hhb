---
plan: 04-05
phase: 04
subsystem: technical-analysis
tags: [candlestick-patterns, ta-lib, statistical-significance, celery, fastapi]
dependency_graph:
  requires: [04-00, 04-03, 04-04]
  provides: [candlestick-pattern-detection, pattern-win-rates, nightly-pattern-stats-task, patterns-api]
  affects: [backend/analysis, backend/ingestion, backend/api/routes/ta.py]
tech_stack:
  added: [scipy.stats.ttest_1samp]
  patterns: [OOS train/test split, t-test vs random baseline, lazy CDL function dispatch]
key_files:
  created:
    - backend/analysis/candlestick_patterns.py
  modified:
    - backend/ingestion/tasks.py
    - backend/ingestion/celery_app.py
    - backend/api/routes/ta.py
    - backend/tests/analysis/test_patterns.py
decisions:
  - "OOS split is last 20% of bars (not a fixed date) — consistent with plan spec D-10"
  - "task function placed in tasks.py (not celery_app.py) to follow existing project pattern; beat schedule in celery_app.py"
  - "lazy import of candlestick_patterns inside task body to avoid circular import at module load"
  - "n_wins defaults to 0 for None cases in DB insert — n_wins column is NOT NULL per model schema"
  - "unused import text removed from ta.py patterns route (select() is sufficient for async query)"
metrics:
  duration: 234s
  completed: "2026-03-29"
  tasks: 3
  files: 5
---

# Phase 04 Plan 05: Candlestick Patterns + Statistical Significance Summary

## One-liner

61 TA-Lib CDL pattern detections with per-pattern win rates and t-test p-values via nightly Celery task, persisted to `ta_pattern_stats`, served via two new FastAPI routes.

## What Was Built

### Task 4-05-1: `backend/analysis/candlestick_patterns.py` (created)

- `CDL_FUNCTIONS` dict with all 61 TA-Lib CDL* functions
- `detect_all_patterns(opens, highs, lows, closes)` — runs all patterns, returns `{name: np.ndarray}` with +100 (bullish) / -100 (bearish) / 0 (none)
- `compute_pattern_stats(signals, closes, min_n=30)` — computes win rate and one-sample t-test p-value against 0.5 baseline using last 20% OOS bars; returns `None` for win_rate/p_value when n < 30
- `build_pattern_stats_for_ticker(opens, highs, lows, closes)` — calls both above, returns list of dicts ready for DB insert

### Task 4-05-2: Nightly Celery beat task (tasks.py + celery_app.py)

- `compute_nightly_candlestick_stats` registered as `ingestion.compute_nightly_candlestick_stats`
- Fetches full daily OHLCV history per seed ticker, computes all 61 pattern stats
- DELETE + INSERT upsert pattern into `ta_pattern_stats` per ticker/timeframe/date
- Beat schedule: `crontab(hour=21, minute=0)` in `celery_app.py` (after pivot task at 20:00)
- Per-ticker exception handling — errors log and continue without aborting

### Task 4-05-3: FastAPI routes + test replacement

Two new routes in `backend/api/routes/ta.py`:
- `GET /api/ta/patterns/{ticker}?timeframe=1d` — runs live CDL detection on last ~500 bars, extracts patterns active on last bar, joins with pre-computed stats from `ta_pattern_stats`, Redis TTL 300s
- `GET /api/ta/pattern-stats/{ticker}?timeframe=1d&pattern=CDLHAMMER` — returns all stored win rates and p-values from most recent nightly run, optionally filtered by pattern name

7 stub tests in `backend/tests/analysis/test_patterns.py` replaced with real assertions — all pass.

## Verification

```
pytest backend/tests/analysis/test_patterns.py -x -q
7 passed in 2.70s
```

## Success Criteria Check

- [x] `CDL_FUNCTIONS` has 61 patterns (>= 60)
- [x] `compute_pattern_stats` returns `None` win_rate when n < 30
- [x] `compute_pattern_stats` uses last 20% of data as OOS test set
- [x] Nightly Celery task registered at 21:00 UTC
- [x] `/api/ta/patterns/{ticker}` returns only patterns active on last bar
- [x] All 7 pattern tests pass

## Commits

| Hash | Message |
|------|---------|
| 082d5f3 | feat(04-05): add candlestick_patterns.py with 61 CDL functions, win rate and p-value stats |
| 9a0c67c | feat(04-05): register compute_nightly_candlestick_stats Celery beat task at 21:00 UTC |
| 8e95058 | feat(04-05): add /api/ta/patterns and /api/ta/pattern-stats routes; replace 7 test stubs |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Task function placed in tasks.py not celery_app.py**
- **Found during:** Task 4-05-2
- **Issue:** Plan specified file as `celery_app.py` but all existing task functions live in `tasks.py`. Placing a new `@app.task` decorated function in `celery_app.py` would create a circular import (celery_app.py imports nothing from tasks.py, but tasks.py imports `app` from celery_app.py)
- **Fix:** Task function added to `tasks.py`; beat schedule entry added to `celery_app.py`. This follows the established project pattern exactly.
- **Files modified:** `backend/ingestion/tasks.py`, `backend/ingestion/celery_app.py`
- **Commit:** 9a0c67c

**2. [Rule 2 - Missing critical functionality] Added numpy import to tasks.py**
- **Found during:** Task 4-05-2
- **Issue:** New task uses `np.array` to convert OHLCV rows to arrays; `numpy` was not previously imported in tasks.py
- **Fix:** Added `import numpy as np` to tasks.py imports
- **Files modified:** `backend/ingestion/tasks.py`
- **Commit:** 9a0c67c

**3. [Rule 1 - Bug] n_wins defaults to 0 for insufficient-data patterns in DB insert**
- **Found during:** Task 4-05-2
- **Issue:** `TAPatternStats.n_wins` column is `nullable=False`, but `compute_pattern_stats` returns `n_wins=None` when occurrences < 30
- **Fix:** `n_wins=stat["n_wins"] if stat["n_wins"] is not None else 0` in the Celery task
- **Files modified:** `backend/ingestion/tasks.py`
- **Commit:** 9a0c67c

## Known Stubs

None — all 7 test stubs replaced with real assertions; pattern detection and stats computation fully wired.

## Self-Check: PASSED
