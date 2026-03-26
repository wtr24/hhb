---
phase: 02-data-ingestion-foundation
plan: "05"
subsystem: ingestion-scheduling
tags: [celery, beat, scheduling, tdd]
dependency_graph:
  requires: ["02-03", "02-04"]
  provides: ["celery-beat-schedule"]
  affects: ["all-4-ingestion-tasks"]
tech_stack:
  added: []
  patterns: ["celery-beat-timedelta-schedule"]
key_files:
  created:
    - backend/tests/ingestion/test_celery.py
  modified:
    - backend/ingestion/celery_app.py
decisions:
  - "beat_schedule uses timedelta intervals (not crontab) for sub-minute precision (30s FX)"
  - "Schedule keys follow pattern ingest-<type>-every-<interval> for readability"
metrics:
  duration: 58s
  completed: "2026-03-26"
  tasks_completed: 1
  files_modified: 2
---

# Phase 2 Plan 05: Celery Beat Schedule Configuration Summary

Celery beat_schedule populated with all 4 ingestion tasks using timedelta intervals — OHLCV every 5 min, macro every 1 h, FX every 30 s, treasury every 15 min.

## Objective

Wire the Celery beat schedule to fire all 4 ingestion tasks (OHLCV, macro, FX, treasury) on their correct intervals. This is the scheduling glue that makes ingestion automatic.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Beat schedule failing tests | 3c1ea89 | backend/tests/ingestion/test_celery.py |
| 1 (GREEN) | Populate beat_schedule | d867ba6 | backend/ingestion/celery_app.py |

## What Was Built

### backend/ingestion/celery_app.py

Replaced the empty `beat_schedule={}` placeholder with a populated schedule of 4 entries:

- `ingest-ohlcv-every-5min` → `ingestion.tasks.ingest_ohlcv_batch`, `timedelta(minutes=5)`
- `ingest-macro-every-1h` → `ingestion.tasks.ingest_macro_batch`, `timedelta(hours=1)`
- `ingest-fx-every-30s` → `ingestion.tasks.ingest_fx_rates`, `timedelta(seconds=30)`
- `ingest-treasury-every-15m` → `ingestion.tasks.ingest_treasury_curve`, `timedelta(minutes=15)`

Added `from datetime import timedelta` import.

### backend/tests/ingestion/test_celery.py

7 tests covering beat schedule validation:

- `test_beat_schedule_has_ohlcv` — entry key, task name, schedule interval
- `test_beat_schedule_has_macro` — entry key, task name, schedule interval
- `test_beat_schedule_has_fx` — entry key, task name, schedule interval
- `test_beat_schedule_has_treasury` — entry key, task name, schedule interval
- `test_beat_schedule_exactly_4_entries` — exactly 4 entries, no extras
- `test_all_task_names_are_valid` — task name strings resolve to real functions in ingestion.tasks
- `test_celery_app_timezone_utc` — timezone is UTC

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- backend/ingestion/celery_app.py: FOUND
- backend/tests/ingestion/test_celery.py: FOUND
- Commit 3c1ea89 (RED): FOUND
- Commit d867ba6 (GREEN): FOUND
- `beat_schedule={}` placeholder: REMOVED
- 7/7 tests passing
