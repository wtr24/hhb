---
plan: 05-02
phase: 05
subsystem: ingestion
tags: [vix, cboe, breadth, celery, ingestion]
dependency_graph:
  requires: [05-00]
  provides: [vix_term_structure ingestion, cboe_pcr ingestion, breadth_pct200 persistence]
  affects: [macro_series, vix_term_structure hypertable, celery beat schedule]
tech_stack:
  added: [yfinance (VIX tickers), requests (CBOE CSV)]
  patterns: [on_conflict_do_nothing upsert, cache_set after DB write, lazy model imports in Celery tasks]
key_files:
  created:
    - backend/ingestion/sources/vix_source.py
    - backend/ingestion/sources/cboe_source.py
  modified:
    - backend/ingestion/tasks.py
    - backend/ingestion/celery_app.py
    - backend/tests/macro/test_vix_source.py
    - backend/tests/macro/test_cboe_source.py
decisions:
  - vix_source uses fast_info dict .get() with history(period="1d") fallback — fast_info key names differ between yfinance versions
  - VIX6M/VIX3M failures are non-fatal warnings, not errors — spot VIX is the critical value
  - compute_breadth_snapshot imports numpy inside task body (already at module level via np alias) to avoid shadowing
  - CBOE PCR flexible column detection handles both 'P/C Ratio' and future column renames without code change
metrics:
  duration: 162s
  completed: "2026-03-30T20:13:42Z"
  tasks_completed: 3
  files_changed: 6
---

# Phase 5 Plan 02: VIX Term Structure + CBOE Put/Call + Breadth Snapshot Ingestion Summary

**One-liner:** VIX spot/3M/6M term structure ingestion with regime classifier + CBOE equity PCR via free CSV + breadth snapshot computed from seed ticker 200-day SMA, all wired into Celery beat.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 5-02-1 | Create vix_source.py and cboe_source.py | 68be5e7 | 2 created |
| 5-02-2 | Add three Celery tasks + beat schedule entries | 22d1cd9 | 2 modified |
| 5-02-3 | Replace VIX and CBOE test stubs with real unit tests | cec1147 | 2 modified |

## Verification

```
pytest backend/tests/macro/test_vix_source.py backend/tests/macro/test_cboe_source.py -x -q
8 passed in 9.15s
```

## What Was Built

### vix_source.py
- `fetch_vix_term_structure(history_row_count)` fetches ^VIX, ^VIX3M, ^VIX6M via `yfinance.Ticker.fast_info`
- Fallback to `history(period="1d")` when `fast_info` returns None
- `_classify_regime(spot)` maps to LOW_VOL / NORMAL / ELEVATED / CRISIS per D-20 spec
- Computes `contango` bool (VIX3M > spot) and `history_depth_ok` flag (>= 252 rows)

### cboe_source.py
- `fetch_cboe_pcr()` downloads free CBOE equity put/call CSV
- Flexible column detection handles 'P/C Ratio' and similar variants
- Parses MM/DD/YYYY with ISO fallback; returns latest (last) row

### tasks.py additions
- `ingest_vix_term_structure` — 15-minute task, upserts to `vix_term_structure` hypertable, caches `vix_term_structure:latest`
- `ingest_cboe_pcr` — daily task, upserts `CBOE_PCR` series to `macro_series`
- `compute_breadth_snapshot` — nightly task, counts seed tickers above 200-day SMA, persists `BREADTH_PCT200` to `macro_series`

### celery_app.py additions
- `ingest-vix-every-15m`: `timedelta(minutes=15)`
- `ingest-cboe-pcr-daily`: `crontab(hour=19, minute=0)`
- `compute-breadth-snapshot-daily`: `crontab(hour=22, minute=0)`

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written. The plan referenced adding imports "after the existing BoE source import line" — plan 05-01 had already run in parallel and added that import, so the placement was correct.

## Known Stubs

None — all tests are real unit tests with mocked yfinance/requests. No placeholder data flows to UI.

## Self-Check: PASSED
