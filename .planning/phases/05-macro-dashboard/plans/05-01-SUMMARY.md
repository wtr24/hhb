---
phase: "05"
plan: "05-01"
subsystem: ingestion
tags: [boe, gilt-curve, celery, ingestion, macro]
dependency_graph:
  requires: [05-00]
  provides: [boe_source, ingest_boe_gilt_curve, gilt_curve_ingestion]
  affects: [gilt_curve hypertable, Redis gilt_curve:latest cache]
tech_stack:
  added: []
  patterns: [requests-get-with-user-agent, csv-dictreader-tab-delimited, celery-task-explicit-name, pg-insert-on-conflict-do-nothing]
key_files:
  created:
    - backend/ingestion/sources/boe_source.py
  modified:
    - backend/ingestion/tasks.py
    - backend/ingestion/celery_app.py
    - backend/tests/macro/test_boe_source.py
decisions:
  - BoE IADB requires User-Agent header (Mozilla/5.0) — BoE returns 403 without it; explicitly documented in module docstring
  - Beat schedule set to 18:00 UTC — BoE gilt market closes ~16:00 BST, 18:00 UTC covers DST transitions
  - on_conflict_do_nothing uses index_elements=["time", "source"] matching gilt_curve composite PK
  - Missing tenor values (blank fields) treated as None per BoE publishing pattern for short-end tenors
metrics:
  duration_seconds: 113
  completed_date: "2026-03-30"
  tasks_completed: 3
  files_modified: 4
---

# Phase 05 Plan 01: BoE Gilt Curve Ingestion Worker Summary

## One-liner

BoE IADB IUDMNZC nominal zero-coupon gilt curve ingestor with User-Agent bypass, tab-CSV parsing, 11-tenor mapping, and nightly 18:00 UTC Celery beat schedule.

## What Was Built

Three deliverables completing the BoE gilt curve ingestion pipeline:

1. **`backend/ingestion/sources/boe_source.py`** — New source module with `fetch_boe_gilt_curve()`. Calls the BoE IADB endpoint with required `User-Agent: Mozilla/5.0 (compatible; HHBFin/1.0)` header. Parses the tab-delimited CSV response, maps 11 `IUDMNZC.AX` column codes to `tenor_*` keys, handles blank fields (None), and returns a list of dicts with UTC datetimes.

2. **`backend/ingestion/tasks.py`** — Added `ingest_boe_gilt_curve` Celery task with explicit `name="ingestion.tasks.ingest_boe_gilt_curve"` parameter. Task rate-checks, fetches, upserts all historical rows to `gilt_curve` hypertable (on_conflict_do_nothing), and caches the latest row under `gilt_curve:latest`.

3. **`backend/ingestion/celery_app.py`** — Beat schedule entry `"ingest-boe-gilt-curve-daily"` at `crontab(hour=18, minute=0)`.

4. **`backend/tests/macro/test_boe_source.py`** — Replaced 5 Wave 0 `pytest.skip` stubs with 6 real unit tests using `unittest.mock.patch`. All tests pass without HTTP calls.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 5-01-1 | Create boe_source.py | d7bd5f6 | backend/ingestion/sources/boe_source.py |
| 5-01-2 | Add Celery task + beat schedule | 67b3839 | backend/ingestion/tasks.py, backend/ingestion/celery_app.py |
| 5-01-3 | Replace test stubs with unit tests | e869bf8 | backend/tests/macro/test_boe_source.py |

## Verification Results

- `pytest backend/tests/macro/test_boe_source.py -x -q`: **6 passed** (0 skipped, 0 failed)
- `ast.parse` on all modified files: **syntax OK**

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — all test stubs replaced with real tests. `ingest_boe_gilt_curve` task imports `GiltCurve` model created in plan 05-00; no placeholder data flows to UI.

## Self-Check: PASSED
