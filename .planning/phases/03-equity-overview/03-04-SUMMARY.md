---
phase: 03-equity-overview
plan: 04
subsystem: api
tags: [finnhub, yfinance, insider-clustering, short-interest, fundamentals, react, bloomberg-terminal, wave2]

# Dependency graph
requires:
  - phase: 03-01
    provides: cluster_insiders(), fetch_short_interest(), fetch_insider_transactions(), equity route stubs, Fundamentals model
  - phase: 03-02
    provides: equity route stubs, cache helpers, news endpoint pattern
provides:
  - GET /api/equity/fundamentals/{ticker} — DB query + yfinance ROE fallback, 24h cache
  - GET /api/equity/short-interest/{ticker} — Finnhub short interest, US-only guard
  - GET /api/equity/insiders/{ticker} — cluster_insiders() + Finnhub data, US-only guard
  - FundamentalsPanel.tsx — compact 5-metric panel with stale badge
  - ShortInterestPanel.tsx — % float / short interest / date with US-only fallback
  - InsiderPanel.tsx — buy/sell ratio, MULTI-BUY signal badge, US-only fallback
  - NewsPanel.tsx — scrollable news feed with 5m auto-refresh
affects:
  - 03-03 (chart panel can link to fundamentals)
  - 03-05 (options panel completes the sidebar)
  - 03-06 (equity module assembly uses all 4 panels)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wave 2 endpoints replace stubs by adding AsyncSession DB dep + yfinance ROE supplement + Finnhub source calls
    - US-only guard pattern: ticker.endswith(".L") or ticker.startswith("^") -> available=False response
    - Frontend panels use useEffect fetch + useState for data/loading/error triad
    - 5-minute auto-refresh via setInterval in useEffect cleanup with clearInterval
    - Terminal aesthetic: text-xs, text-terminal-amber labels, text-terminal-green values, border-terminal-border dividers

key-files:
  created:
    - frontend/src/components/equity/FundamentalsPanel.tsx
    - frontend/src/components/equity/ShortInterestPanel.tsx
    - frontend/src/components/equity/InsiderPanel.tsx
    - frontend/src/components/equity/NewsPanel.tsx
  modified:
    - backend/api/routes/equity.py (fundamentals/short-interest/insiders Wave 2 implementation)
    - backend/tests/api/test_equity.py (Wave 2 test classes unskipped, new tests, stub class updated)

key-decisions:
  - "Fundamentals endpoint uses AsyncSession DB dep (same as quote.py) for latest Fundamentals row; falls back to yfinance.info.returnOnEquity if roe is None in DB"
  - "Short interest and insiders use macro TTL (1h) not news TTL — data changes less frequently than news"
  - "TestEquityStubs class updated: removed 501 assertions for now-implemented Wave 2 endpoints; options stub test retained"
  - "Fundamentals test uses app.dependency_overrides[get_async_db] pattern with async generator override for clean DB mocking"
  - "ROE from yfinance info dict is a decimal (e.g. 0.45) — FundamentalsPanel detects and converts to percentage display"

patterns-established:
  - "US-only guard: if ticker.endswith('.L') or ticker.startswith('^'): return {'available': False, 'message': '...US tickers only...'}"
  - "Wave stub removal: remove @pytest.mark.skip from test class + replace simple shape assertions with full mock tests"
  - "Frontend panel triad: useEffect fetch on ticker change, loading/error/data state, terminal-styled compact display"

requirements-completed: [EQUITY-06, EQUITY-07, EQUITY-08, EQUITY-10]

# Metrics
duration: ~5min
completed: 2026-03-28
---

# Phase 3 Plan 04: Wave 2 — Fundamentals, Short Interest, Insider, News Panels Summary

**Fundamentals/short-interest/insider backend endpoints (Wave 2) and 4 frontend sidebar panels with terminal styling, US-only guards, MULTI-BUY signal badge, and 5-minute news auto-refresh**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-28T22:19:21Z
- **Completed:** 2026-03-28T22:24:11Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- `GET /api/equity/fundamentals/{ticker}` — queries Fundamentals table for P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap; supplements ROE from yfinance if absent in DB; 24h cache (EQUITY-06)
- `GET /api/equity/short-interest/{ticker}` — Finnhub short interest with pct_float computation; `available=False` + US-only message for LSE/.L and index/^ tickers (EQUITY-07)
- `GET /api/equity/insiders/{ticker}` — Finnhub insider transactions fed to `cluster_insiders()`; returns buy_count, sell_count, buy_sell_ratio, multi_insider, clusters (EQUITY-08)
- Wave 2 test classes unskipped: 10 new tests added (TestFundamentalsShape, TestShortInterest, TestLseTicker, TestInsiders); 19 pass, 1 skip (options Wave 3)
- `FundamentalsPanel.tsx` — 5-metric compact panel; market cap T/B/M formatter; ROE as percentage; STALE badge; 24h cache label
- `ShortInterestPanel.tsx` — % float, short interest, date display; `[US ONLY]` badge for LSE/index tickers
- `InsiderPanel.tsx` — buy (green) / sell (red) counts, B/S ratio, cluster count; amber `MULTI-BUY` badge when multi_insider=True
- `NewsPanel.tsx` — scrollable headlines with source and relative timestamp; 5m setInterval refresh; FinBERT `[--]` placeholder; STALE badge; overflow-y-auto list

## Task Commits

1. **Task 1: Fundamentals + short interest + insider backend endpoints** — `dc6a3b1` (feat)
2. **Task 2: Frontend panels — Fundamentals, Short Interest, Insider, News** — `22afd00` (feat)

## Files Created/Modified

- `backend/api/routes/equity.py` — fundamentals/short-interest/insiders Wave 2 handlers replacing 501 stubs; imports added (get_async_db, fetch_short_interest, fetch_insider_transactions, cluster_insiders, Fundamentals)
- `backend/tests/api/test_equity.py` — TestEquityStubs updated (501 stubs for Wave 2 removed); TestFundamentalsShape, TestShortInterest, TestLseTicker, TestInsiders added (all unskipped)
- `frontend/src/components/equity/FundamentalsPanel.tsx` — D-01 right sidebar, 5 valuation metrics with formatters, STALE badge (new)
- `frontend/src/components/equity/ShortInterestPanel.tsx` — D-01 right sidebar, short interest display with US-only fallback (new)
- `frontend/src/components/equity/InsiderPanel.tsx` — D-01 right sidebar, insider clustering with MULTI-BUY signal, US-only fallback (new)
- `frontend/src/components/equity/NewsPanel.tsx` — D-11 bottom-right, scrollable headlines with 5m refresh and FinBERT placeholder (new)

## Decisions Made

- Fundamentals endpoint uses `AsyncSession` DB dependency (same as quote.py) — consistent with existing async DB pattern; yfinance ROE fallback fires only when DB `roe` column is null
- Short interest and insiders use `macro` TTL (1h) rather than `news` TTL (5m) — corporate short interest and insider transactions update infrequently; cache hit rate is more important than freshness here
- `TestEquityStubs` class pruned: removed 501 assertion tests for endpoints now returning real data; kept options stub assertion (Wave 3 not yet implemented)
- Fundamentals tests use `app.dependency_overrides[get_async_db]` with an async generator override function — cleanest way to inject mock DB session without requiring a running database
- ROE from yfinance `info.get("returnOnEquity")` returns a decimal (0.45 = 45%); FundamentalsPanel normalises by multiplying by 100 only when the absolute value is ≤ 5

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated TestEquityStubs to remove stale 501 assertions**
- **Found during:** Task 1 verification (pytest run)
- **Issue:** `TestEquityStubs.test_fundamentals_endpoint_registered` asserted `status_code == 501` but fundamentals now returns 200; test was failing
- **Fix:** Removed the three now-incorrect 501 assertions from TestEquityStubs (fundamentals, short-interest, insiders); kept options stub test; updated class docstring
- **Files modified:** `backend/tests/api/test_equity.py`
- **Verification:** All 19 tests pass after fix
- **Committed in:** dc6a3b1 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in existing stub tests contradicting new Wave 2 implementation)
**Impact on plan:** Required for test suite correctness. Wave 2 tests added as planned; the stub class was an expected casualty of implementing the endpoints.

## Issues Encountered

None beyond the stale stub test assertion (documented above).

## User Setup Required

None - no external service configuration required for this plan's work.

## Known Stubs

- `backend/api/routes/equity.py` — `GET /api/equity/options/{ticker}` returns 501. This is the last Wave 0 stub. Wave 3 (plan 03-05) implements it.
- `frontend/src/components/equity/NewsPanel.tsx` — Sentiment badge shown as `[--]` placeholder. Phase 7 FinBERT integration will replace this with bullish/bearish/neutral labels.

## Self-Check: PASSED

All key files confirmed present:
- FOUND: backend/api/routes/equity.py
- FOUND: backend/tests/api/test_equity.py
- FOUND: frontend/src/components/equity/FundamentalsPanel.tsx
- FOUND: frontend/src/components/equity/ShortInterestPanel.tsx
- FOUND: frontend/src/components/equity/InsiderPanel.tsx
- FOUND: frontend/src/components/equity/NewsPanel.tsx
- FOUND: .planning/phases/03-equity-overview/03-04-SUMMARY.md

Commits dc6a3b1 (Task 1) and 22afd00 (Task 2) verified in git log.

## Next Phase Readiness

- All 4 sidebar/bottom panels ready for wiring into EquityModule layout (plan 03-06)
- Fundamentals, short interest, and insider endpoints fully tested — plan 03-06 can fetch and render immediately
- US-only routing consistent across short-interest and insiders — plan 03-06 needs no special LSE handling
- NewsPanel 5m refresh is self-contained — plan 03-06 just mounts the component
- Options chain endpoint (03-05) is the only remaining 501 stub before full equity module is functional

---
*Phase: 03-equity-overview*
*Completed: 2026-03-28*
