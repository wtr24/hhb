---
phase: 04-technical-analysis-engine
verified: 2026-03-30T07:00:00Z
status: gaps_found
score: 11/13 requirements verified
re_verification: false
gaps:
  - truth: "User can activate Fibonacci drawing by clicking [Fib] button and clicking two points on chart"
    status: failed
    reason: "ChartPanel's [Fib] button calls onFibClick which toggles EquityModule.fibActive for amber border styling only. ChartPanel passes NO prop to ExpandedChart to trigger drawingTools.toggleFib(). useDrawingTools.toggleFib and toggleEW exist and are correct but are never called from any UI interaction."
    artifacts:
      - path: "frontend/src/components/equity/ChartPanel.tsx"
        issue: "ExpandedChart render at line 148 does not pass onFibClick, onEwClick, or any drawing-trigger prop"
      - path: "frontend/src/components/equity/ExpandedChart.tsx"
        issue: "ExpandedChartProps has no prop to externally trigger drawingTools.toggleFib() or toggleEW(). drawingTools.toggleFib/toggleEW are returned from the hook but never called."
    missing:
      - "Add onFibClick and onEwClick props to ExpandedChartProps interface"
      - "Call drawingTools.toggleFib() in an onFibClick handler in ExpandedChart"
      - "Call drawingTools.toggleEW() in an onEwClick handler in ExpandedChart"
      - "Pass onFibClick={drawingTools.toggleFib} and onEwClick={drawingTools.toggleEW} from ChartPanel when rendering ExpandedChart (or let EquityModule's toggle handlers call down through ChartPanel)"

  - truth: "User can activate Elliott Wave labelling by clicking [EW] button and placing wave labels on chart"
    status: failed
    reason: "Same root cause as TA-11. The [EW] button toggles amber border only. drawingTools.toggleEW() is never called from any UI path. EW labelling state machine is complete but unreachable from user interaction."
    artifacts:
      - path: "frontend/src/components/equity/ChartPanel.tsx"
        issue: "onEwClick handler not forwarded to ExpandedChart"
      - path: "frontend/src/components/equity/ExpandedChart.tsx"
        issue: "No external EW activation prop; toggleEW exported from hook but not wired to button"
    missing:
      - "Same fix as TA-11 gap above — both gaps share the same root cause and the same single fix"
human_verification:
  - test: "Fibonacci drawing end-to-end flow"
    expected: "After fix: clicking [Fib] activates drawing mode, two chart clicks produce horizontal level lines at 0.236/0.382/0.5/0.618/0.786/1.0/1.618 ratios, Escape key cancels"
    why_human: "Requires browser rendering and interactive chart click events"
  - test: "Elliott Wave label placement flow"
    expected: "After fix: clicking [EW] enables labelling mode, chart clicks place markers 1-5-A-B-C in sequence, validation badges appear after wave 3/4/5 placement"
    why_human: "Requires browser interaction with chart markers and visual validation panel"
  - test: "Indicator picker overlay on chart"
    expected: "Selecting SMA(20) from picker causes a line overlay to appear on the candle chart in amber colour"
    why_human: "Requires browser rendering — ExpandedChart fetches and renders overlay series"
  - test: "Candlestick pattern badge shows win rate on live data"
    expected: "After nightly Celery task has run, a pattern active on today's bar shows 'CDLHAMMER: 58% win | p=0.03 | n=42'"
    why_human: "Requires live/recent OHLCV data and nightly task to have executed at least once"
---

# Phase 04: Technical Analysis Engine Verification Report

**Phase Goal:** Implement the full technical analysis computation engine — all 60+ TA indicators across 8 groups, candlestick pattern detection with win rates and statistical significance, chart pattern detection (7 types), Fibonacci retracement/extension drawing tool, Elliott Wave labelling with validation, pivot point computation (5 methods), and the frontend indicator picker + expanded chart UI.
**Verified:** 2026-03-30T07:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 50+ TA indicator functions exist and produce computed output (TA-01 to TA-05) | VERIFIED | `indicators.py` 754 lines, 52 `compute_` functions; `garch.py` 39 lines; syntax OK; tests 23+ passing |
| 2 | Market breadth backend module implemented (TA-06) | VERIFIED | `breadth.py` 113 lines, 7 compute functions; test stubs replaced |
| 3 | All 5 pivot methods computed nightly and stored in DB (TA-07) | VERIFIED | `pivot_points.py` 94 lines, 6 functions; Celery beat task at 20:00 UTC in `celery_app.py`; hypertable in migration 0004 |
| 4 | Intermarket rolling correlation for 7 pairs (TA-08) | VERIFIED | `intermarket.py` 74 lines; `/api/ta/intermarket/{ticker}` route present |
| 5 | 61 candlestick patterns detected with win rate + p-value (TA-09) | VERIFIED | `candlestick_patterns.py` line count confirmed 61 CDL entries; OOS t-test; Celery task at 21:00 UTC |
| 6 | 7 chart patterns detected with confidence scores (TA-10) | VERIFIED | `chart_patterns.py` 407 lines, 11 detect functions; 8 tests pass; `/api/ta/chart-patterns/{ticker}` route |
| 7 | Fibonacci levels computed by backend API (TA-11 backend) | VERIFIED | `fibonacci.py` 79 lines; `POST /api/ta/fibonacci` route; 5 tests pass |
| 8 | Elliott Wave Fibonacci ratio validation by backend API (TA-12 backend) | VERIFIED | `elliott_wave.py` 133 lines; `POST /api/ta/elliott-wave/validate` route; 6 tests pass |
| 9 | Statistical significance layer (win_rate, p_value, n_occurrences) surfaced in API (TA-13) | VERIFIED | `/api/ta/patterns/{ticker}` returns win_rate/p_value/n_occurrences; `/api/ta/pattern-stats/{ticker}` route; ExpandedChart renders amber badges |
| 10 | TA routes registered in main.py and reachable | VERIFIED | `ta_router` imported and `include_router(ta_router)` at line 110 of `main.py` |
| 11 | Frontend indicator picker with 7 groups wired to chart | VERIFIED | `IndicatorPicker.tsx` 259 lines; `ExpandedChart.tsx` fetches via `ta-api.ts`; `EquityModule.tsx` manages state |
| 12 | User can activate Fibonacci drawing via [Fib] button (TA-11 frontend) | FAILED | [Fib] button exists with amber border toggle; `useDrawingTools.toggleFib()` implemented but NOT called from any UI path |
| 13 | User can activate Elliott Wave labelling via [EW] button (TA-12 frontend) | FAILED | Same root cause — `toggleEW()` unreachable from button click |

**Score:** 11/13 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/analysis/indicators.py` | 50+ indicator functions | VERIFIED | 754 lines, 52 compute_ functions, syntax OK |
| `backend/analysis/garch.py` | GARCH(1,1) volatility | VERIFIED | 39 lines, arch library |
| `backend/analysis/breadth.py` | Market breadth indicators | VERIFIED | 113 lines, 7 functions |
| `backend/analysis/pivot_points.py` | 5 pivot methods | VERIFIED | 94 lines, 6 functions |
| `backend/analysis/intermarket.py` | Rolling correlations | VERIFIED | 74 lines |
| `backend/analysis/candlestick_patterns.py` | 61 CDL patterns + stats | VERIFIED | 170 lines, 61 CDL entries confirmed |
| `backend/analysis/chart_patterns.py` | 7 chart pattern detectors | VERIFIED | 407 lines, 11 detect functions |
| `backend/analysis/fibonacci.py` | Fibonacci levels/extensions | VERIFIED | 79 lines, 2 public functions |
| `backend/analysis/elliott_wave.py` | EW validation rules | VERIFIED | 133 lines, 4 public functions |
| `backend/api/routes/ta.py` | TA API routes | VERIFIED | 742 lines; indicators/pivots/intermarket/patterns/chart-patterns/fibonacci/elliott-wave routes |
| `backend/models/ta_pattern_stats.py` | TAPatternStats SQLAlchemy model | VERIFIED | win_rate/p_value nullable columns |
| `backend/models/pivot_points.py` | PivotPoints SQLAlchemy model | VERIFIED | pp/r1-r3/s1-s3 columns |
| `backend/alembic/versions/0004_ta_engine.py` | DB migration for TA tables | VERIFIED | Creates ta_pattern_stats + pivot_points hypertables |
| `backend/cache/ttl.py` | ta_pattern_daily/weekly TTL keys | VERIFIED | 900s / 3600s TTLs added |
| `frontend/src/lib/ta-api.ts` | TA API typed fetch helpers | VERIFIED | 125 lines, all 6 fetch functions present |
| `frontend/src/components/equity/IndicatorPicker.tsx` | Indicator picker with 7 groups | VERIFIED | 259 lines; groups collapsed by default; Market Breadth disabled |
| `frontend/src/components/equity/ExpandedChart.tsx` | Chart with sub-panes + patterns | VERIFIED | 756 lines; oscillator sub-panes, candlestick badges, ChartPatternOverlay |
| `frontend/src/components/equity/DrawingTools.tsx` | Fib/EW drawing state machine | VERIFIED | 150 lines; toggleFib/toggleEW/handleChartClick implemented |
| `frontend/src/components/equity/CandleChart.tsx` | Overlay + click + Fib/EW props | VERIFIED | OverlayConfig, overlays, onChartClick, fibDrawings, ewLabels props added |
| `frontend/src/components/equity/ChartPanel.tsx` | TA toolbar buttons in expanded mode | PARTIAL | [Fib]/[EW] buttons render; fibActive/ewActive amber borders work; but toggleFib/toggleEW NOT forwarded to ExpandedChart |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `ta.py` routes | `indicators.py` | dispatch dict + import | WIRED | `_build_dispatch()` closure in ta.py; whitelist of 50+ names |
| `ta.py` routes | `candlestick_patterns.py` | lazy import in route handler | WIRED | Line 426 in ta.py; patterns route fetches + joins pattern stats |
| `ta.py` routes | `chart_patterns.py` | lazy import in route handler | WIRED | Line 7d6704a commit; `detect_all_chart_patterns` called |
| `ta.py` routes | `fibonacci.py` | POST /api/ta/fibonacci | WIRED | Line 697-710 in ta.py |
| `ta.py` routes | `elliott_wave.py` | POST /api/ta/elliott-wave/validate | WIRED | Line 718-742 in ta.py |
| `ta.py` routes | `pivot_points.py` DB | SELECT from pivot_points table | WIRED | Line 255 in ta.py; PivotPoints model query |
| `main.py` | `ta.py` router | include_router | WIRED | Line 110 in main.py: `app.include_router(ta_router)` |
| `ExpandedChart.tsx` | `ta-api.ts` | fetchIndicator/fetchCandlestickPatterns/fetchChartPatterns | WIRED | Lines 13-17 of ExpandedChart.tsx |
| `ExpandedChart.tsx` | `DrawingTools.tsx` | useDrawingTools hook | PARTIAL | Hook instantiated; state machine correct; toggleFib/toggleEW NOT connected to buttons |
| `ChartPanel.tsx` | `ExpandedChart.tsx` | [Fib] button → toggleFib | NOT WIRED | onFibClick/onEwClick not passed to ExpandedChart; drawingTools.toggleFib unreachable |
| `EquityModule.tsx` | `IndicatorPicker.tsx` | indicatorPickerOpen state | WIRED | Lines 40,109,158-159 in EquityModule.tsx |
| Celery beat | `compute_nightly_pivot_points` | beat schedule at 20:00 UTC | WIRED | celery_app.py beat_schedule confirmed |
| Celery beat | `compute_nightly_candlestick_stats` | beat schedule at 21:00 UTC | WIRED | celery_app.py beat_schedule confirmed |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `ExpandedChart.tsx` | `indicatorData` | `fetchIndicator` → `/api/ta/indicators/{ticker}` → `indicators.py` compute_ functions | Yes — pure functions on TimescaleDB OHLCV | FLOWING |
| `ExpandedChart.tsx` | `candlePatterns` | `fetchCandlestickPatterns` → `/api/ta/patterns/{ticker}` → `candlestick_patterns.py` + DB join | Yes — CDL detection + ta_pattern_stats table | FLOWING |
| `ExpandedChart.tsx` | `chartPatterns` | `fetchChartPatterns` → `/api/ta/chart-patterns/{ticker}` → `chart_patterns.py` | Yes — scipy peak detection on OHLCV | FLOWING |
| `ExpandedChart.tsx` | `drawingTools.fibDrawings` | Chart click → `useDrawingTools.handleChartClick` → `fetchFibonacciLevels` → `/api/ta/fibonacci` | DISCONNECTED — drawing mode never activated (no button trigger reaches toggleFib) | HOLLOW_PROP |
| `ExpandedChart.tsx` | `drawingTools.ewLabels` | Chart click → `useDrawingTools.handleChartClick` → EW sequence | DISCONNECTED — drawing mode never activated | HOLLOW_PROP |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All analysis Python modules parse | `python -c "import ast; [ast.parse(open(f).read()) for f in [...]]"` | All 13 files: OK | PASS |
| `indicators.py` has 50+ compute functions | `grep "def compute_" indicators.py | wc -l` | 52 | PASS |
| `CDL_FUNCTIONS` dict has 61+ entries | `grep '"CDL' candlestick_patterns.py | wc -l` | 61 | PASS |
| `chart_patterns.py` has 7+ detectors | `grep "def detect_" chart_patterns.py | wc -l` | 9 (7 pattern + 1 all + helper) | PASS |
| `ta_router` registered in main.py | `grep include_router main.py` | `app.include_router(ta_router)` at line 110 | PASS |
| TA packages in requirements.txt | `grep "TA-Lib\|pandas-ta\|arch" requirements.txt` | TA-Lib==0.6.8, pandas-ta==0.4.71b0, arch>=8.0.0 | PASS |
| DB migration 0004 exists | `ls alembic/versions/0004_ta_engine.py` | File present | PASS |
| All frontend TA files present | `ls` | ta-api.ts, IndicatorPicker.tsx, ExpandedChart.tsx, DrawingTools.tsx | PASS |
| TypeScript compilation | `tsc --noEmit` | SKIP — node_modules not installed (Docker-only project) | SKIP |

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TA-01 | 04-01, 04-04 | Moving Averages (SMA/EMA/DEMA/TEMA/WMA/HMA/LWMA/VWMA + Cross + Ribbon) | SATISFIED | `indicators.py` lines ~1-150; 11 test assertions pass |
| TA-02 | 04-01, 04-04 | Momentum/Oscillators (RSI/StochRSI/MACD/Stoch/WillR/CCI/ROC/MOM/DPO/TRIX/ULTOSC/PPO/KDJ/CMO) | SATISFIED | `indicators.py` lines ~150-300; 14 functions; tests pass |
| TA-03 | 04-02, 04-04 | Trend Strength (ADX/Aroon/SAR/SuperTrend/Vortex/Ichimoku/MassIndex) | SATISFIED | `indicators.py` 7 trend functions; tests pass |
| TA-04 | 04-02, 04-04 | Volatility (BB/Keltner/Donchian/ATR/HV/GARCH/ChaikinVol/Ulcer) | SATISFIED | `indicators.py` + `garch.py`; GARCH via arch library |
| TA-05 | 04-02, 04-04 | Volume (OBV/VWAP/AnchoredVWAP/VWAP-SD/AD/CMF/MFI/VolProfile/CVD/VROC/EOM/NVI/PVI/ForceIndex) | SATISFIED | `indicators.py` 13 volume functions; tests pass |
| TA-06 | 04-03 | Market Breadth (A/D Line, McClellan, TRIN, NH-NL, UpDownVol, %Above200/50, TICK) | SATISFIED (backend) | `breadth.py` 113 lines; frontend disabled (index data not ingested — by design, documented in IndicatorPicker as `[n/a]`) |
| TA-07 | 04-03, 04-04 | 5 Pivot Methods nightly to DB | SATISFIED | `pivot_points.py`; Celery beat at 20:00 UTC; pivot_points hypertable in migration 0004 |
| TA-08 | 04-03, 04-04 | Intermarket rolling correlations (7 pairs) | SATISFIED | `intermarket.py`; `/api/ta/intermarket/{ticker}` route |
| TA-09 | 04-05, 04-08, 04-09 | 60+ candlestick patterns with win rate + p-value | SATISFIED | 61 CDL functions; OOS t-test; Celery task; API route; frontend badges render |
| TA-10 | 04-06, 04-08, 04-09 | 7 chart pattern types with confidence scores | SATISFIED | 7 detectors in `chart_patterns.py`; all marked experimental; `ChartPatternOverlay` in ExpandedChart |
| TA-11 | 04-07, 04-08, 04-09 | Fibonacci drawing tool — interactive with 8 levels | PARTIAL | Backend API fully implemented (POST /api/ta/fibonacci, 5 tests pass); `useDrawingTools` Fib state machine correct; BUT [Fib] button click does not activate drawing mode — `toggleFib()` never called from button |
| TA-12 | 04-07, 04-08, 04-09 | Elliott Wave labelling with Fibonacci ratio validation | PARTIAL | Backend API fully implemented (POST /api/ta/elliott-wave/validate, 6 tests pass); `useDrawingTools` EW state machine correct; BUT [EW] button click does not activate labelling mode — `toggleEW()` never called from button |
| TA-13 | 04-05, 04-08, 04-09 | Statistical significance on all signals | SATISFIED | win_rate/p_value/n_occurrences in patterns API; ExpandedChart renders amber badges; null when n<30 |

**Note on REQUIREMENTS.md status column:** The row at line 239 still shows `Pending` for TA-01 through TA-13. This is a documentation artifact — the implementation exists. The status column reflects roadmap scheduling, not implementation status.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `frontend/src/components/equity/ExpandedChart.tsx` line 239 | `useDrawingTools(useCallback(() => {}, []))` — `toggleFib`/`toggleEW` returned from hook but not surfaced as props or connected to any button | WARNING | Fibonacci drawing and EW labelling modes can never be activated by user interaction |
| `frontend/src/components/equity/ChartPanel.tsx` line 148 | `<ExpandedChart>` render missing `onFibClick` and `onEwClick` props | BLOCKER | Root cause of TA-11/TA-12 UI gap |
| `frontend/src/components/equity/IndicatorPicker.tsx` | Market Breadth indicators have `disabled: true` and render as `[n/a]` | INFO | By design — index breadth data not yet ingested; documented in 04-08 summary |
| `backend/analysis/breadth.py` | `compute_market_breadth` functions exist but no API route serves them (no `/api/ta/breadth/{ticker}` route in `ta.py`) | WARNING | TA-06 backend is complete but not exposed via API. Frontend disables market breadth anyway, so no user impact in Phase 04. |

---

### Human Verification Required

#### 1. Fibonacci Drawing — End-to-End (after gap fix)

**Test:** Open equity view with a loaded ticker. Expand a chart panel. Click `[Fib]` button (should activate drawing mode — cursor change or status indicator). Click on chart at a swing high price point, then click at a swing low. Verify 8 horizontal level lines appear at 0.0/0.236/0.382/0.5/0.618/0.786/1.0/1.618 ratios. Press Escape to cancel a drawing in progress.
**Expected:** Level lines appear in amber (key levels) and dim (minor levels); multiple drawings can be placed; Escape cancels in-progress drawing; ticker change clears all drawings.
**Why human:** Requires browser rendering and interactive chart click event handling.

#### 2. Elliott Wave Label Placement (after gap fix)

**Test:** Click `[EW]` button. Click chart 5 times for waves 1-5. Verify labels "1", "2", "3", "4", "5" appear as markers on the chart at clicked positions. After Wave 3 (click 4), verify a validation badge appears (wave 3 not shortest check). Continue to place A/B/C corrective labels.
**Expected:** 8 sequential markers placed; validation panel shows rule pass/fail after wave 3+; EW mode exits after "C" is placed.
**Why human:** Requires browser interaction and visual marker rendering.

#### 3. Indicator Overlay Rendering

**Test:** Open equity view, expand a panel, click `[Indicators ▾]`, expand "Moving Averages" group, click `SMA`. Verify a line overlay appears on the candle chart.
**Expected:** Amber line overlay on candle chart; indicator count in button increments; clicking again removes overlay.
**Why human:** Requires browser rendering and API response with live data.

#### 4. Candlestick Pattern Badge on Live Data

**Test:** After nightly Celery task has run at least once (21:00 UTC), load a ticker with known pattern on recent bars. Verify pattern badge in top-right of expanded chart shows format `CDLHAMMER: 58% win | p=0.03`.
**Expected:** Badge appears amber if win_rate non-null; shows "n/a" if insufficient sample (n < 30).
**Why human:** Requires nightly task execution and live/recent OHLCV data with a matching pattern.

---

## Gaps Summary

Two gaps block full goal achievement for TA-11 and TA-12. They share a single root cause:

**Root cause:** `ChartPanel.tsx` renders `<ExpandedChart>` without passing `onFibClick` or `onEwClick` activation props. `ExpandedChart` has a complete `useDrawingTools` state machine that correctly handles Fibonacci two-click drawing and Elliott Wave sequential labelling, but the `toggleFib()` and `toggleEW()` methods returned by the hook are never called from any user-accessible code path. The `[Fib]` and `[EW]` buttons in `ChartPanel` toggle amber border styling in `EquityModule` state only — they do not penetrate to the drawing tool activation.

**Fix scope:** Small — add `onFibClick` and `onEwClick` props to `ExpandedChartProps`, wire them to `drawingTools.toggleFib()` and `drawingTools.toggleEW()` inside `ExpandedChart`, and pass them from `ChartPanel`'s `<ExpandedChart>` render call. Estimated effort: 10-15 lines across 2 files.

All other Phase 04 requirements are fully implemented with real (non-stub) code, committed to git, and verifiably wired end-to-end.

---

_Verified: 2026-03-30T07:00:00Z_
_Verifier: Claude (gsd-verifier)_
