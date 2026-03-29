---
phase: "04"
plan: "04-08"
subsystem: frontend
tags: [ta, indicators, chart, ui, react]
dependency_graph:
  requires: [04-04]
  provides: [indicator-picker-ui, expanded-chart-sub-panes, overlay-series, ta-api-client]
  affects: [equity-module, chart-panel, candle-chart]
tech_stack:
  added: []
  patterns:
    - separate lightweight-charts instances per oscillator sub-pane
    - OverlayConfig defined in CandleChart (canonical), re-exported by ExpandedChart (avoids circular import)
    - 200ms debounced fetch on activeIndicators change
    - CSS-positioned horizontal bar chart for Volume Profile (not a chart library series)
key_files:
  created:
    - frontend/src/lib/ta-api.ts
    - frontend/src/components/equity/IndicatorPicker.tsx
    - frontend/src/components/equity/ExpandedChart.tsx
  modified:
    - frontend/src/components/equity/CandleChart.tsx
    - frontend/src/components/equity/ChartPanel.tsx
    - frontend/src/components/equity/EquityModule.tsx
decisions:
  - OverlayConfig defined in CandleChart to avoid circular import with ExpandedChart
  - Separate lightweight-charts chart per oscillator pane (not addSeries on paneIndex>0) for layout simplicity
  - 200ms debounce on indicator fetches to avoid burst on rapid toggle
  - Volume Profile uses CSS div-based histogram overlay (not chart series) per plan spec
  - IndicatorPicker groups all start collapsed (openGroups useState, not persisted)
  - Market Breadth indicators disabled=true with DIM color and no click handler
  - TA state clears on ticker change (activeIndicators, fibActive, ewActive, pickerOpen)
metrics:
  duration: 606s
  completed: "2026-03-29"
  tasks: 4
  files: 6
---

# Phase 4 Plan 8: Frontend — Indicator Picker, Sub-Panes, Overlay Series Summary

**One-liner:** Full TA frontend wiring — typed API client, indicator picker modal with 7 groups, oscillator sub-panes with separate chart instances, and overlay series rendering on the main candle chart.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | TA API client module | 54dd9ec | `frontend/src/lib/ta-api.ts` |
| 2 | IndicatorPicker component | 3244c1d | `frontend/src/components/equity/IndicatorPicker.tsx` |
| 3 | ExpandedChart with oscillator sub-panes | fd6e7ef | `frontend/src/components/equity/ExpandedChart.tsx` |
| 4 | ChartPanel, CandleChart, EquityModule updates | 6026496 | 3 files modified |

## What Was Built

### ta-api.ts
Typed fetch helpers for all `/api/ta/` routes:
- `fetchIndicator` — general indicator endpoint with URLSearchParams builder
- `fetchPivots`, `fetchChartPatterns`, `fetchCandlestickPatterns`
- `fetchFibonacciLevels` (POST), `validateElliottWave` (POST)

### IndicatorPicker.tsx
Dropdown panel (280px wide, 400px max-height, scrollable) with:
- 7 indicator groups: Moving Averages, Momentum, Trend Strength, Volatility, Volume, Market Breadth, Pivot Points
- All groups start collapsed; click heading to expand/collapse
- Terminal-aesthetic `[✓]`/`[ ]` monospace checkboxes
- Active indicator: amber text + check mark
- Market Breadth: disabled (DIM color, not clickable — index data not yet ingested)
- Dismiss on Escape key and click-outside via useEffect listeners

### ExpandedChart.tsx
Wraps CandleChart with oscillator sub-pane management:
- `computePaneHeights`: 75% main / 25% oscillators for 1 indicator; proportional for N; min 60px per sub-pane
- 200ms debounced fetch on ticker/timeframe/activeIndicators change
- `extractSeriesData` normalises various API response shapes (times+values, MACD, STOCH, ADX)
- Overlay indicators: build `OverlayConfig[]` and pass to CandleChart
- Oscillator sub-panes: separate `createChart` instances per pane with reference lines
- Reference lines: RSI (30/50/70), MACD/OBV/CMF (0), CCI (±100), ADX (20/40), MFI (20/50/80)
- VOL_PROFILE: CSS-based horizontal bar chart on right edge (not a chart series)
- Inline param editor: click label → number inputs → Enter applies → triggers re-fetch

### CandleChart.tsx changes
- Added `OverlayConfig` interface (canonical definition)
- Added `overlays?: OverlayConfig[]` prop
- Added `overlaySeriesRef` to track series for cleanup
- New `useEffect([overlays])`: removes previous overlay series, adds new `LineSeries` for each

### ChartPanel.tsx changes
- Added TA props: `onIndicatorsClick`, `onFibClick`, `onEwClick`, `activeIndicatorCount`, `fibActive`, `ewActive`, `activeIndicators`, `onToggleIndicator`, `onIndicatorParamChange`, `onRemoveIndicator`, `indicatorPickerOpen`, `onCloseIndicatorPicker`
- Expanded mode header: `[Indicators ▾ (N)]`, `[Fib]`, `[EW]` buttons with amber border when active
- TA buttons only appear in expanded mode (4-panel grid header unchanged — D-02 preserved)
- Expanded mode now renders `<ExpandedChart>` instead of bare `<CandleChart>`
- `<IndicatorPicker>` positioned absolutely below the Indicators button

### EquityModule.tsx changes
- Added state: `activeIndicators`, `fibActive`, `ewActive`, `indicatorPickerOpen`
- `handleToggleIndicator`: adds/removes indicator by name, generates unique id from params
- `handleIndicatorParamChange`: updates params and rebuilds id
- `handleRemoveIndicator`: removes by id
- `handleTickerSubmit`: clears all indicator state on ticker change

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Circular import between CandleChart and ExpandedChart**
- **Found during:** Task 4 (Task 4-08-4 wiring)
- **Issue:** Plan specified `OverlayConfig` defined in `ExpandedChart.tsx` and imported into `CandleChart.tsx`. This would create a circular dependency: CandleChart → ExpandedChart → CandleChart.
- **Fix:** Defined `OverlayConfig` in `CandleChart.tsx` (which has no upstream component dependencies). `ExpandedChart` imports and re-exports it. `ChartPanel` gets it transitively.
- **Files modified:** `CandleChart.tsx`, `ExpandedChart.tsx`
- **Commit:** 6026496

## Known Stubs

- `[Fib]` and `[EW]` buttons toggle `fibActive`/`ewActive` state but no drawing mode is wired — the actual Fibonacci overlay drawing and Elliott Wave labelling UX will be implemented when the chart interaction layer is built (Phase 5 or dedicated plan). The buttons render correctly with active border styling.
- VOL_PROFILE histogram positions bars by index (top-to-bottom), which assumes bins are ordered from high price to low. Backend `compute_volume_profile` bin ordering should be verified when testing.

## Self-Check: PASSED

All 6 files verified present. All 4 task commits verified in git log:
- 54dd9ec: feat(04-08): add TA API client module ta-api.ts
- 3244c1d: feat(04-08): add IndicatorPicker component
- fd6e7ef: feat(04-08): add ExpandedChart with oscillator sub-panes
- 6026496: feat(04-08): wire TA controls into ChartPanel, CandleChart, EquityModule
