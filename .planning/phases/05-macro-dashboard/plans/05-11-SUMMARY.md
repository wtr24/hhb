---
plan: 05-11
phase: 05
status: completed
completed: 2026-03-31
requirements: [MACRO-07, MACRO-08, MACRO-09]
commits:
  - 6cee935
---

# Summary: Plan 05-11 — Fix INDICATORS Schema Mismatch

## What Was Done

Fixed the runtime schema mismatch in the `/api/macro/indicators` endpoint that caused
all current-value displays in the INDICATORS sub-tab to render as `undefined`.

**Root cause:** `macro.py` response dict used short keys (`"us"`, `"uk"`, `"eu"`) but
the TypeScript `IndicatorPanel` interface declared `current_us`, `current_uk`, `current_eu`.
TypeScript accepted the mismatch at compile time (structural widening), but at runtime all
five indicator panels (CPI, Core CPI, PCE, GDP, Unemployment) showed blank current values.

## Changes Made

**`backend/api/routes/macro.py`** (9 key renames, 1 cache bust added):

| Panel | Old key | New key |
|-------|---------|---------|
| cpi | `"us"` | `"current_us"` |
| cpi | `"uk"` | `"current_uk"` |
| core_cpi | `"us"` | `"current_us"` |
| pce | `"us"` | `"current_us"` |
| gdp | `"us"` | `"current_us"` |
| gdp | `"uk"` | `"current_uk"` |
| gdp | `"eu"` | `"current_eu"` |
| unemployment | `"us"` | `"current_us"` |
| unemployment | `"uk"` | `"current_uk"` |

Also added `redis_client.delete("macro_indicators:latest")` before `cache_set` to ensure
stale cached responses with old field names are not served after deployment.

`policy_rates` block (`"fed"`, `"boe"`, `"ecb"`) was not modified — those keys already
matched the frontend interface exactly.

## No Frontend Changes Required

`useMacroData.ts` `IndicatorPanel` interface and all `IndicatorsTab.tsx` accessors were
already using the correct `current_*` naming. Zero frontend files modified.

## Requirements Unblocked

- **MACRO-07** (CPI/Core CPI/PCE panels) — current values now flow correctly
- **MACRO-08** (Labour: NFP/Unemployment panels) — current values now flow correctly
- **MACRO-09** (GDP US/UK/EU panels) — all three `current_*` fields now present

Phase 05 score: 14/14 truths verified (previously 13/14 — one blocker resolved).
