---
phase: 03-equity-overview
plan: 05
subsystem: api+frontend
tags: [options, black-scholes, greeks, iv-surface, iv-rank, canvas-heatmap, yfinance, wave3]

# Dependency graph
requires:
  - phase: 03-01
    provides: bs_greeks(), iv_percentile_rank() in analysis/black_scholes.py; equity route stubs
  - phase: 03-03
    provides: OHLCV endpoint pattern, equity route structure, yfinance import
  - phase: 03-04
    provides: Wave 2 endpoint patterns, US-only guard, cache patterns, frontend panel conventions

provides:
  - GET /api/equity/options/{ticker} — full options chain with BS Greeks, IV surface, IV rank; 15m cache
  - OptionsChain.tsx — calls-left/strike-centre/puts-right table with Greeks (D-08, D-10)
  - IVSurface.tsx — HTML canvas heatmap with ivToColor gradient (D-09)

affects:
  - 03-06 (equity module assembly can now mount OptionsChain + IVSurface)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - options endpoint builds _build_contracts() helper for calls/puts from yfinance DataFrame
    - IV surface: iterate 5 expiries, build strike-axis from first expiry, transpose to [row=strike][col=expiry]
    - IV rank: statistics.median() of all chain IVs passed to iv_percentile_rank()
    - IVSurface canvas: useRef<HTMLCanvasElement>, useEffect([surfaceData]), fillRect grid
    - ivToColor: two-segment linear interpolation dark->amber (t<0.5) then amber->red (t>=0.5)
    - OptionsChain: strike merge from calls+puts union set; ATM detected by closest strike to current_price

key-files:
  created:
    - frontend/src/components/equity/OptionsChain.tsx
    - frontend/src/components/equity/IVSurface.tsx
  modified:
    - backend/api/routes/equity.py (options endpoint Wave 3 implementation replacing 501 stub)
    - backend/tests/api/test_equity.py (TestOptionsChain unskipped with 6 new tests; TestEquityStubs stub assertion removed)

key-decisions:
  - "Risk-free rate hardcoded at 0.045 with TODO comment — pulling from yield_curve table is Phase 8 scope"
  - "IV rank computed across current chain IV values (cross-strike percentile), not 52-week history — 52-week rank deferred to Phase 8 screener"
  - "IV surface uses first expiry strike axis as canonical strikes for all expiry columns — consistent strike axis for heatmap rendering"
  - "TestEquityStubs: removed test_options_endpoint_registered (was asserting 501) — options now returns 200"
  - "IVSurface uses HTML Canvas not a charting library — compact heatmap strip, no D3 or recharts dependency"

requirements-completed: [EQUITY-09]

# Metrics
duration: ~412s
completed: 2026-03-28
---

# Phase 3 Plan 05: Wave 3 — Options Chain Endpoint + OptionsChain/IVSurface Components Summary

**Options chain endpoint with Black-Scholes Greeks for all rows; IV surface canvas heatmap and IV percentile rank badge; calls-left/strike-centre/puts-right table with per-row Greek columns**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~412s |
| Tasks completed | 2/2 |
| Files created | 2 |
| Files modified | 2 |

## What Was Built

### Task 1: Options Chain Backend Endpoint (EQUITY-09)

**backend/api/routes/equity.py** — `GET /api/equity/options/{ticker}`:
- LSE tickers (`.L` suffix) immediately return `{"available": false, "message": "Options not available for LSE tickers"}` — no yfinance call made
- Fetches `t.options` (list of expiry date strings) and limits to nearest 5 expiries
- Current price from `info.get("currentPrice")` with `regularMarketPrice` fallback
- Risk-free rate: `r = 0.045` (hardcoded with TODO comment to pull from yield_curve Phase 8)
- `_build_contracts()` helper: for each row in calls/puts DataFrame, computes `T = (expiry_date - today).days / 365.0`, calls `bs_greeks(S, strike, T, r, sigma, option_type)`, returns full dict with delta/gamma/vega/theta alongside strike/bid/ask/lastPrice/volume/openInterest/iv
- IV rank: `statistics.median()` of all chain IVs → `iv_percentile_rank(median_iv, all_ivs)` — cross-strike percentile rank (52-week rank is Phase 8)
- IV surface: iterates nearest 5 expiries, builds `strikes` list from first expiry, `iv_matrix[row=strike_idx][col=expiry_idx]` transposed from per-expiry columns
- Full response: `ticker, available, expiry, expiries, current_price, iv_rank, calls, puts, iv_surface, source`
- Exception handling: any yfinance error returns `{"available": false, "message": "Options data unavailable"}`
- 15m Redis cache via `cache_set(redis_client, f"options:{ticker}", response, "quote")`
- Imports: `from analysis.black_scholes import bs_greeks, iv_percentile_rank`, `import statistics`

**backend/tests/api/test_equity.py** — `TestOptionsChain` (6 tests, all unskipped):
- `test_options_chain`: mocks yfinance with 3-row calls/puts DataFrames; asserts available=True, calls/puts arrays, Greeks present
- `test_options_chain_greeks_are_numbers`: asserts delta is float in [-1, 1] for valid inputs
- `test_options_chain_iv_rank`: asserts iv_rank in [0, 100]
- `test_options_chain_iv_surface`: asserts iv_surface has strikes/expiries/iv_matrix keys
- `test_lse_ticker_returns_not_available`: asserts LLOY.L returns available=False with message containing "LSE" or "not available"
- `test_options_yfinance_error_returns_unavailable`: asserts yfinance exception returns available=False not 500

### Task 2: Frontend Options Chain Table + IV Surface Heatmap

**frontend/src/components/equity/OptionsChain.tsx** (262 lines) — D-08, D-09, D-10:
- Props: `{ ticker: string }` — fetches from `/api/equity/options/{ticker}` on ticker change
- Loading: amber `OPTIONS LOADING...` pulsing text
- Unavailable (LSE/error): `OPTIONS [NOT AVAILABLE]` message with reason text
- Header: `OPTIONS — {expiry}` left, amber `IV RANK: {X}%` badge right (D-09)
- Expiry selector: tab buttons for all 5 expiries; selected expiry highlighted amber; re-fetches chain on selection
- Table columns (D-08): `C.Delta | C.Gamma | C.Vega | C.Theta | C.Bid | C.Ask | C.IV | STRIKE | P.Bid | P.Ask | P.IV | P.Delta | P.Gamma | P.Vega | P.Theta`
- ATM row: `bg-[#1a1a1a]` highlight; amber strike column text; detected as closest strike to `current_price`
- ITM calls (delta > 0.5): lighter `bg-[#1a1a1a]/30` background
- `text-xs font-mono` throughout for terminal density
- Call values: `text-[#00d084]` (green); put values: `text-[#ff4444]` (red)
- Strike column: `text-[#ff9900]` (amber)

**frontend/src/components/equity/IVSurface.tsx** (143 lines) — D-09:
- Props: `{ surfaceData: IVSurfaceData | null }`
- Empty state: dim `IV SURFACE — NO DATA` placeholder
- HTML Canvas (no charting library): `useRef<HTMLCanvasElement>`, `useEffect([surfaceData])`
- `ivToColor(t)`: two-segment linear gradient — t<0.5: `#1a1a1a → #ff9900` (dark to amber); t≥0.5: `#ff9900 → #ff4444` (amber to red)
- Grid: `fillRect` cells with `cellW = drawW / nCols`, `cellH = drawH / nRows`, 1px gap between cells
- Labels: strike prices left axis (every 3rd), expiry dates bottom axis abbreviated (e.g. "Apr 25")
- 120px height, fills parent width with `className="w-full"`
- Exports `IVSurfaceData` interface for use by OptionsChain and future plan 03-06

## Task Commits

1. **Task 1: Options chain endpoint with Black-Scholes Greeks** — `33ab09c` (feat)
2. **Task 2: OptionsChain table + IVSurface canvas heatmap** — `986d745` (feat)

## Files Created/Modified

- `backend/api/routes/equity.py` — options endpoint Wave 3 replacing 501 stub; bs_greeks/iv_percentile_rank imports; statistics import (modified)
- `backend/tests/api/test_equity.py` — TestOptionsChain unskipped with 6 comprehensive tests; TestEquityStubs stale 501 assertion removed (modified)
- `frontend/src/components/equity/OptionsChain.tsx` — D-08/D-09/D-10 options chain table (new)
- `frontend/src/components/equity/IVSurface.tsx` — D-09 canvas heatmap with ivToColor gradient (new)

## Decisions Made

- Risk-free rate hardcoded at 0.045 — `yield_curve` table query deferred to Phase 8 (Phase 3 doesn't need live T-bill rates for the options display)
- IV rank uses cross-strike median IV percentile — simple and immediate; true 52-week IV rank requires storing historical option data (Phase 8 screener)
- IV surface canonical strikes from first expiry — ensures consistent row count across all expiry columns; later expiries may have different strike range but this gives a stable heatmap
- `statistics.median()` used for IV rank reference point — avoids extreme OTM outliers distorting the rank more than mean would, without requiring numpy for a single scalar computation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed stale test_options_endpoint_registered assertion**
- **Found during:** Task 1 verification (pytest run)
- **Issue:** `TestEquityStubs.test_options_endpoint_registered` asserted `status_code == 501` but options now returns 200 with full data; test was failing
- **Fix:** Removed the stale 501 assertion test from `TestEquityStubs`; class docstring updated to reflect Wave 3 completion
- **Files modified:** `backend/tests/api/test_equity.py`
- **Verification:** 24 tests pass after fix

---

**Total deviations:** 1 auto-fixed (Rule 1 — stale stub assertion, same pattern as Plan 04)
**Impact on plan:** Required for test suite correctness. The options 501 test was the expected casualty of implementing the endpoint.

## Known Stubs

None — all options chain functionality is wired end-to-end.

Remaining deferred items (intentional scope boundaries):
- `r = 0.045` risk-free rate — Phase 8 will replace with live yield curve query
- IV rank is cross-strike percentile, not 52-week — Phase 8 screener will add historical IV storage
- Frontend TypeScript compilation verified structurally (node_modules not installed locally; project runs in Docker)

## Self-Check: PASSED

- backend/api/routes/equity.py — FOUND
- backend/tests/api/test_equity.py — FOUND
- frontend/src/components/equity/OptionsChain.tsx — FOUND
- frontend/src/components/equity/IVSurface.tsx — FOUND
- Commit 33ab09c (Task 1) — FOUND
- Commit 986d745 (Task 2) — FOUND
- grep -c "501" backend/api/routes/equity.py — 0 (no stubs)
- grep "bs_greeks" backend/api/routes/equity.py — 2 matches
- grep "iv_percentile_rank" backend/api/routes/equity.py — 2 matches
- 24 tests pass, 0 skipped

---
*Phase: 03-equity-overview*
*Completed: 2026-03-28*
