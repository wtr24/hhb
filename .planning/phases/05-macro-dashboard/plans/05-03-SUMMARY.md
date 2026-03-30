---
phase: 05-macro-dashboard
plan: "03"
subsystem: ingestion
tags: [celery, timescaledb, ons, bls, ecb, boe, macro-series]

# Dependency graph
requires:
  - phase: 05-macro-dashboard
    plan: "00"
    provides: macro_series table, SCHEDULE_* constants, TTL entries

provides:
  - ons_source.py: fetch UK CPI/unemployment/GDP from ONS beta API
  - bls_source.py: fetch US NFP from BLS API v2 (graceful if BLS_API_KEY unset)
  - ecb_source.py: fetch Eurozone GDP and ECB DFR policy rate via SDMX REST
  - boe_rate_source.py: fetch BoE Bank Rate (IUMABEDR) via IADB CSV endpoint
  - 5 new Celery tasks wired into beat schedule
  - Beat schedule at 15 total entries

affects: [05-04-api-routes, 05-05-frontend, macro_series rows ONS_CPI/ONS_UNEMPLOYMENT/ONS_GDP/BLS_NFP/ECB_GDP/ECB_DFR/BOE_RATE]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - ONS two-step pattern: GET timeseries/{code}/dataset to find dataset_id, then GET datasets/{id}/timeseries/{code}/data
    - BLS API v2 POST with JSON body: seriesid, startyear, endyear, registrationkey
    - ECB SDMX REST CSV: TIME_PERIOD + OBS_VALUE columns, quarterly format YYYY-QN
    - Beat schedule staggered 06:00-07:00 UTC to avoid simultaneous DB writes

key-files:
  created:
    - backend/ingestion/sources/ons_source.py
    - backend/ingestion/sources/bls_source.py
    - backend/ingestion/sources/ecb_source.py
    - backend/ingestion/sources/boe_rate_source.py
  modified:
    - backend/ingestion/tasks.py
    - backend/ingestion/celery_app.py

key-decisions:
  - "ONS beta API only (api.beta.ons.gov.uk) — api.ons.gov.uk retired November 2024"
  - "BLS_API_KEY graceful degradation: returns [] with warning if env var unset, not an error"
  - "ecb_source.py has both fetch_ecb_gdp() and fetch_ecb_dfr() — GDP uses MNA dataflow, DFR uses FM dataflow"
  - "Beat schedule staggered: ONS 06:00, ECB GDP 06:15, BoE Rate 06:30, ECB DFR 06:45, BLS 07:00"
  - "5 tasks total (plan said 4 but also required ingest_ecb_dfr for MACRO-10)"

metrics:
  duration: 201s
  completed: "2026-03-30T20:14:07Z"
  tasks_completed: 3
  files_created: 4
  files_modified: 2
---

# Phase 5 Plan 03: ONS / BLS / ECB / BoE Policy Rate Ingestion Workers Summary

Four ingestion source files created and five Celery tasks wired with staggered beat schedule entries, storing into `macro_series` with distinct `series_id` prefixes per D-22/D-23/D-24/D-25.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 5-03-1 | Create ons_source.py and boe_rate_source.py | 958ebd0 |
| 5-03-2 | Create bls_source.py and ecb_source.py | d167151 |
| 5-03-3 | Add 5 Celery tasks and beat schedule entries | 92949f1 |

## What Was Built

**ons_source.py** — ONS beta API two-step pattern. First fetches `timeseries/{code}/dataset` to find `dataset_id`, then `datasets/{id}/timeseries/{code}/data`. Parses three date formats (monthly "2026 Jan", quarterly "2026 Q1", annual "2025"). Stores: `ONS_CPI` (L522), `ONS_UNEMPLOYMENT` (LF2Q), `ONS_GDP` (ABMI).

**boe_rate_source.py** — BoE IADB CSV endpoint for Bank Rate series (IUMABEDR). Identical User-Agent requirement as `boe_source.py`. Parses tab-delimited CSV, finds value column by checking `"IUMABEDR"` in field name. Returns 403-aware error message.

**bls_source.py** — BLS API v2 POST endpoint for CES0000000001 (Total Nonfarm Payrolls). Requires `BLS_API_KEY` env var; gracefully returns `[]` with a warning message if unset. Handles `REQUEST_SUCCEEDED` status check.

**ecb_source.py** — ECB SDMX REST API in CSV format. `fetch_ecb_gdp()` uses MNA dataflow for Eurozone GDP growth rate; `fetch_ecb_dfr()` uses FM dataflow for ECB Deposit Facility Rate. Both parse `TIME_PERIOD`/`OBS_VALUE` columns, handle quarterly (`YYYY-QN`) and monthly (`YYYY-MM`) formats.

**Five new Celery tasks** in tasks.py: `ingest_ons_series`, `ingest_bls_nfp`, `ingest_ecb_gdp`, `ingest_boe_policy_rate`, `ingest_ecb_dfr`. All use `on_conflict_do_nothing(index_elements=["time", "series_id"])`.

**Beat schedule** now has 15 entries total. New entries staggered 06:00-07:00 UTC to avoid simultaneous TimescaleDB write contention.

## Deviations from Plan

### Auto-added: ingest_ecb_dfr task

**Rule 2 — Missing critical functionality**

The plan's task list (Task 5-03-3) explicitly included `ingest_ecb_dfr` in the code block but the intro text said "four Celery tasks". The success criteria at the bottom of the plan clearly states "5 new tasks" and includes `ingest_ecb_dfr` for MACRO-10. Added per spec.

No other deviations — plan executed as written.

## Known Stubs

None — all source files implement real HTTP fetches. BLS graceful degradation (returns `[]`) is intentional design, not a stub.

## Self-Check: PASSED

Files verified:
- `backend/ingestion/sources/ons_source.py` — FOUND
- `backend/ingestion/sources/bls_source.py` — FOUND
- `backend/ingestion/sources/ecb_source.py` — FOUND
- `backend/ingestion/sources/boe_rate_source.py` — FOUND
- `backend/ingestion/tasks.py` — modified, 5 new tasks present
- `backend/ingestion/celery_app.py` — 15 beat schedule entries confirmed

Commits verified: 958ebd0, d167151, 92949f1
