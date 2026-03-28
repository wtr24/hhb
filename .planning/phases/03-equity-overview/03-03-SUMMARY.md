---
phase: 03-equity-overview
plan: 03
subsystem: frontend
tags: [lightweight-charts, candlestick, multi-timeframe, chart-grid, expand-collapse, websocket, ohlcv, equity-ui]

# Dependency graph
requires:
  - phase: 03-02
    provides: earnings/dividends/news endpoints; Finnhub WS live quotes in Redis pub/sub
  - phase: 03-01
    provides: OHLCV model with interval column; equity route stubs; async DB session pattern
provides:
  - CandleChart component (lightweight-charts v5 API — addSeries/CandlestickSeries/createSeriesMarkers)
  - ChartPanel 4-grid with expand/collapse (D-05, D-06)
  - GET /api/equity/ohlcv/{ticker}/{interval} — serves 1d/1wk/1h/4h with on-demand yfinance ingest
  - useEquityData hook (parallel OHLCV + earnings + dividends fetch)
  - useEquityWebSocket hook (subscribes to quotes:{ticker} + fx:USDGBP channels)
  - TypeScript equity types: OHLCVBar, Quote, ChartMarker, Timeframe, TimeRange
  - Chart config constants using TERMINAL theme (chartConfig.ts)
affects:
  - 03-04 through 03-06 (chart components available for full module assembly)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - CandleChart uses useRef pattern — chart created once in useEffect([]), data updated in useEffect([data]), never remounted
    - createSeriesMarkers (v5) replaces series.setMarkers() (v4 removed) — instance stored in ref for cleanup
    - OHLCV endpoint triggers on-demand yfinance ingest when no DB rows exist for intraday intervals
    - intraday bars (1h/4h) returned as Unix seconds; daily/weekly as YYYY-MM-DD string (lightweight-charts requirement)
    - WebSocket reconnects after 3s on disconnect; unsubscribes on ticker change or unmount

key-files:
  created:
    - frontend/src/types/equity.ts
    - frontend/src/lib/chartConfig.ts
    - frontend/src/components/equity/CandleChart.tsx
    - frontend/src/components/equity/ChartPanel.tsx
    - frontend/src/hooks/useEquityData.ts
    - frontend/src/hooks/useEquityWebSocket.ts
    - backend/api/routes/equity.py
  modified: []

key-decisions:
  - "lightweight-charts v5 addSeries(CandlestickSeries, opts) used — addCandlestickSeries() removed in v5"
  - "createSeriesMarkers() used for earnings/dividend markers — series.setMarkers() removed in v5"
  - "Intraday time format is Unix seconds (not ISO string) — lightweight-charts v5 requirement for sub-day intervals"
  - "On-demand yfinance ingest added for 1h/4h when no DB rows exist — avoids empty charts on first load"
  - "ChartPanel escape handler uses document.addEventListener (not window) — consistent with DOM event pattern"

# Metrics
duration: 199s
completed: 2026-03-28
---

# Phase 3 Plan 03: Wave 2 — CandleChart + ChartPanel + OHLCV Endpoint Summary

**4-panel multi-timeframe candlestick chart grid using lightweight-charts v5 API; expand/collapse with Escape key; OHLCV endpoint with on-demand intraday ingest; WebSocket hook for live quote updates**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~199s |
| Tasks completed | 2/2 |
| Files created | 7 |
| Files modified | 0 |

## What Was Built

### Task 1: Types + Chart Config + OHLCV Endpoint + CandleChart

**frontend/src/types/equity.ts** — Complete TypeScript type definitions for the equity module: `OHLCVBar`, `Quote`, `ChartMarker`, `Timeframe`, `TimeRange`, and `TIMEFRAME_LABELS` mapping.

**frontend/src/lib/chartConfig.ts** — Chart styling constants (`CHART_OPTIONS`, `CANDLE_STYLE`) importing from `TERMINAL` theme. Covers layout, grid lines, price/time scale borders, and candlestick colors.

**frontend/src/components/equity/CandleChart.tsx** — Single chart component using lightweight-charts v5 exclusively:
- Chart created once via `useEffect([], [])` stored in `useRef<IChartApi>`
- Series created via `chart.addSeries(CandlestickSeries, CANDLE_STYLE)` — v5 API
- Data updates via `seriesRef.current.setData()` in `useEffect([data])` — no remounting
- Markers via `createSeriesMarkers(series, markers)` — v5 API; stored in ref for cleanup
- `ResizeObserver` handles container resize without chart recreation
- Expanded mode shows `1D/1W/1M/1Y/5Y` time range buttons using `chart.timeScale().setVisibleRange()`

**frontend/src/hooks/useEquityData.ts** — Fetches OHLCV data for all 4 timeframes plus earnings and dividend dates in parallel via `Promise.all`. Maps earnings to `aboveBar arrowDown` markers (amber) and dividends to `belowBar circle` markers (green).

**backend/api/routes/equity.py** — Added `GET /api/equity/ohlcv/{ticker}/{interval}`:
- Validates interval against `{1d, 1wk, 1h, 4h}`; returns 400 on invalid
- Queries DB for existing bars; triggers on-demand yfinance ingest if no rows found
- Intraday (1h/4h) returned as Unix seconds; daily/weekly as `YYYY-MM-DD` strings
- Cached 5m for intraday (quote tier), 1h for daily/weekly (fundamentals tier)
- All existing Wave 1 endpoints (earnings, dividends, news) preserved unchanged

### Task 2: ChartPanel + WebSocket Hook

**frontend/src/components/equity/ChartPanel.tsx** — 4-panel chart grid (D-05) with expand/collapse (D-06):
- Default: CSS `grid-cols-2 grid-rows-2` rendering all 4 timeframes simultaneously
- Click any panel sets `expandedPanel` state → renders single chart at full width
- Escape key listener via `document.addEventListener` collapses expanded panel
- Expanded panel shows timeframe label + `[ESC] COLLAPSE` button
- All charts receive combined `[...earningsMarkers, ...dividendMarkers]` (D-07)

**frontend/src/hooks/useEquityWebSocket.ts** — Live quote WebSocket hook:
- Connects to `ws://localhost:8000/ws`
- On open: subscribes to `quotes:{ticker}` and `fx:USDGBP` channels
- On message: updates `Quote` state when channel matches `quotes:{ticker}`
- On close: reconnects after 3 seconds
- On ticker change: cleanup closes connection and clears quote state; new connection opened
- On unmount: unsubscribes channels, closes WebSocket

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

The OHLCV endpoint serves data but the ChartPanel and CandleChart components are not yet wired into the main App.tsx `activeTab === "EQUITY"` branch. This is intentional — plan 03-04 (EquityModule assembly) is the designated plan for wiring all components into the App shell. The individual components are fully functional and tested-by-construction.

## Self-Check: PASSED

- frontend/src/types/equity.ts — FOUND
- frontend/src/lib/chartConfig.ts — FOUND
- frontend/src/components/equity/CandleChart.tsx — FOUND
- frontend/src/components/equity/ChartPanel.tsx — FOUND
- frontend/src/hooks/useEquityData.ts — FOUND
- frontend/src/hooks/useEquityWebSocket.ts — FOUND
- backend/api/routes/equity.py — FOUND
- Commit 2e56e89 (Task 1) — FOUND
- Commit bcf693d (Task 2) — FOUND
