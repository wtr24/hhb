---
phase: "05"
plan: "05-04"
subsystem: macro-dashboard
tags: [fear-greed, macro-api, yield-curve, vix, sentiment, indicators]
dependency_graph:
  requires: [05-01, 05-02, 05-03]
  provides: [fear_greed_service, macro_curves_route, macro_indicators_route, macro_risk_route, macro_sentiment_route]
  affects: [frontend-macro-dashboard]
tech_stack:
  added: []
  patterns: [sync-session-for-compute-service, named-routes-before-wildcard, percentile-rank-normalisation]
key_files:
  created:
    - backend/analysis/fear_greed.py
  modified:
    - backend/api/routes/macro.py
    - backend/tests/macro/test_fear_greed.py
    - backend/tests/macro/test_macro_routes.py
decisions:
  - Named macro routes (curves/indicators/risk/sentiment) placed before {series} wildcard in macro.py to prevent FastAPI routing collision
  - Fear & Greed uses sync SessionLocal pattern (consistent with pivot_points task) not async db
  - Six equal-weighted components: VIX pctile (inverted), Put/Call (inverted), Breadth, HY Spread (inverted), SPX 125d Momentum, Safe Haven USD deviation (inverted)
metrics:
  duration: 197s
  completed: "2026-03-30T20:19:53Z"
  tasks: 3
  files: 4
---

# Phase 05 Plan 04: Fear & Greed Computation Service + All Four Macro API Routes Summary

## One-liner

Six-component Fear & Greed composite service plus four macro API routes (curves, indicators, risk, sentiment) with Redis caching and correct FastAPI route ordering.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 5-04-1 | Create fear_greed.py computation service | da168b5 | backend/analysis/fear_greed.py |
| 5-04-2 | Add four new API routes to macro.py | 72d7f23 | backend/api/routes/macro.py |
| 5-04-3 | Replace test stubs with real tests | 65ecdf6 | backend/tests/macro/test_fear_greed.py, backend/tests/macro/test_macro_routes.py |

## What Was Built

### fear_greed.py

`backend/analysis/fear_greed.py` implements the Fear & Greed composite computation service with:
- `_percentile_rank(series, current)` — normalises any value to 0–100 via cumulative rank; returns 50.0 on empty series (neutral default)
- `_score_to_band(score)` — maps composite to EXTREME FEAR / FEAR / NEUTRAL / GREED / EXTREME GREED bands
- `compute_fear_greed_composite(session)` — queries last 365 days of six components, each normalised, then equal-weighted average:
  1. VIX percentile (inverted — high VIX = fear = low score)
  2. CBOE Put/Call ratio (inverted)
  3. BREADTH_PCT200 market breadth (direct)
  4. BAMLH0A0HYM2 HY credit spread (inverted)
  5. ^GSPC 125-day momentum ROC (direct)
  6. DTWEXBGS trade-weighted USD vs 20-day SMA (inverted)
- Uses synchronous SessionLocal pattern — consistent with pivot_points and other Celery task patterns
- Graceful degradation: computes from however many components are available; returns neutral 50 only if all missing

### macro.py — Four new routes

All four routes placed BEFORE the `GET /api/macro/{series}` wildcard (line 487) to prevent FastAPI swallowing literal path segments as the `series` parameter.

- **GET /api/macro/curves** — US Treasury + UK gilt spot curves with historical overlays (1M ago, 1Y ago), 2s10s and 5s30s spread time series (90d), curve shape classifier (NORMAL/FLAT/INVERTED/HUMPED) with context string, real yield (GS10 - T10YIE). TTL key `macro_curves` (900s).
- **GET /api/macro/indicators** — CPI, Core CPI, PCE, GDP, Unemployment, Policy Rates for US/UK/EU. Each panel includes history list, MoM and YoY deltas. TTL key `macro_indicators` (3600s).
- **GET /api/macro/risk** — VIX term structure (90d history), contango flag, regime label, 1Y and 5Y percentile ranks, CBOE put/call ratio (90d). TTL key `macro_risk` (900s).
- **GET /api/macro/sentiment** — Calls `compute_fear_greed_composite` via sync SessionLocal (wrapped in try/except for resilience), plus SPX 10Y seasonality monthly average returns. TTL key `macro_sentiment` (3600s).

### Tests

Replaced all 13 Wave 0 `pytest.skip` stubs in both test files with 15 real tests:
- 7 unit tests for `fear_greed.py` functions including mock-session test for missing-component resilience
- 8 schema/import tests for the four new routes — verifiable without a live DB

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All routes return real computed data from TimescaleDB; no hardcoded placeholders flow to the response.

## Self-Check: PASSED

- backend/analysis/fear_greed.py: FOUND
- backend/api/routes/macro.py: FOUND (472 lines added, named routes at line 20, wildcard at 487)
- backend/tests/macro/test_fear_greed.py: FOUND
- backend/tests/macro/test_macro_routes.py: FOUND
- Commit da168b5: FOUND
- Commit 72d7f23: FOUND
- Commit 65ecdf6: FOUND
- pytest result: 15 passed, 0 failed
