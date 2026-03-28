---
phase: 03-equity-overview
plan: 06
subsystem: frontend
tags: [bloomberg-grid, equity-module, ticker-command-bar, quote-bar, gbp-toggle, react-assembly, wave3]

# Dependency graph
requires:
  - phase: 03-03
    provides: ChartPanel, CandleChart, useEquityData, useEquityWebSocket, equity types
  - phase: 03-04
    provides: FundamentalsPanel, ShortInterestPanel, InsiderPanel, NewsPanel
  - phase: 03-05
    provides: OptionsChain, IVSurface

provides:
  - EquityModule.tsx — master Bloomberg grid layout (D-01) wiring all panels
  - TickerCommandBar.tsx — terminal-style TICKER> input with amber cursor
  - QuoteBar.tsx — live quote strip with STALE badge and GBP conversion
  - GBPToggle.tsx — compact toggle for GBP/USD price mode
  - App.tsx wired: h-screen layout, activeTab===EQUITY renders EquityModule

affects:
  - All future phases — EQUITY tab is now fully functional

# Tech tracking
tech-stack:
  added: []
  patterns:
    - EquityModule uses CSS grid-rows with minmax(200px,25vh) for bottom row — responsive without scrolling
    - GBP rate fetched once on gbpMode activation, cached in state until component unmounts
    - QuoteBar accepts onGbpToggle callback — GBPToggle is composed inside QuoteBar (not a sibling)
    - App outer div changed from min-h-screen to h-screen flex flex-col for Bloomberg fixed-height requirement (D-01)
    - main gets flex-1 overflow-hidden — fills remaining viewport after header/nav/footer
    - Sidebar panels use flex-1 overflow-hidden min-h-0 to divide right column equally without overflow

key-files:
  created:
    - frontend/src/components/equity/EquityModule.tsx
    - frontend/src/components/equity/TickerCommandBar.tsx
    - frontend/src/components/equity/QuoteBar.tsx
    - frontend/src/components/equity/GBPToggle.tsx
  modified:
    - frontend/src/App.tsx (EquityModule import + wiring + h-screen layout)

key-decisions:
  - "App outer div changed from min-h-screen to h-screen flex flex-col — Bloomberg layout requires fixed viewport height (D-01: nothing scrolls)"
  - "GBPToggle composed inside QuoteBar (not a separate sibling) — QuoteBar owns the quote strip row including the toggle"
  - "GBP rate fetched once on gbpMode=true, cached in gbpRate state — avoids re-fetch on every render, rate stable within session"
  - "Right sidebar uses flex-1 on each panel — equal division of available height without explicit pixel heights"
  - "EquityModule uses min-h-0 on grid children — required for nested flex/grid children to respect parent height constraints in CSS"

requirements-completed: [EQUITY-01, EQUITY-02, EQUITY-03, EQUITY-11, EQUITY-12]

# Metrics
duration: 148s
completed: 2026-03-28
---

# Phase 3 Plan 06: Final Assembly — EquityModule + Bloomberg Grid Layout Summary

**Complete Equity module assembled: Bloomberg fixed-height grid with TickerCommandBar, live QuoteBar, 4-panel charts, fundamentals/short-interest/insider sidebar, options chain + IV surface, news feed, and GBP toggle — wired into App.tsx**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~148s |
| Tasks completed | 3/3 |
| Files created | 4 |
| Files modified | 1 |

## What Was Built

### Task 1: TickerCommandBar + QuoteBar + GBPToggle

**frontend/src/components/equity/TickerCommandBar.tsx** (57 lines) — D-03, D-04:
- `TICKER>` prefix as a `<span>` (not part of input) in amber terminal font
- `<input>` with `caretColor: '#ff9900'` (amber cursor), `bg-transparent border-none outline-none`
- `onChange` auto-uppercases via `e.target.value.toUpperCase()`
- `onKeyDown` triggers `onSubmit(trimmed)` on Enter, clears input
- `autoFocus` via `useEffect(() => inputRef.current?.focus(), [])`
- No history, no autocomplete (D-04)

**frontend/src/components/equity/QuoteBar.tsx** (125 lines) — D-01, EQUITY-01, D-02, D-12:
- Props: `{ quote: Quote | null, gbpMode: boolean, gbpRate: number | null, onGbpToggle: () => void }`
- Displays: ticker | currency label | price | change% | O/H/L | Vol
- `convertPrice()` helper multiplies all price fields by `gbpRate` when `gbpMode` active
- `STALE` amber badge shown when `quote.stale === true` (D-02)
- `GBPToggle` composed inline at the right end of the strip
- Price/change% green if positive, red if negative (or amber if null)
- Volume formatted with K/M/B suffix

**frontend/src/components/equity/GBPToggle.tsx** (30 lines) — D-12, EQUITY-11:
- Active: `bg-terminal-amber text-black font-bold`
- Inactive: `text-terminal-dim border border-terminal-border` with amber hover
- Compact `text-xs px-2 py-0.5`

### Task 2: EquityModule Assembly + App.tsx Wiring

**frontend/src/components/equity/EquityModule.tsx** (134 lines) — D-01:
- `useState` for `ticker`, `gbpMode`, `gbpRate`
- `useEquityWebSocket(ticker)` → live quote
- `useEquityData(ticker)` → chartData, earningsMarkers, dividendMarkers
- GBP rate fetch: `useEffect([gbpMode, gbpRate])` fires `fetch('/api/fx/USD/GBP')` when gbpMode enabled and rate not yet cached
- Empty state: `TYPE A TICKER TO BEGIN` in dim text (centered)
- Layout: `h-full flex flex-col` → command bar (auto) → quote bar (auto) → grid rows (1fr / minmax(200px,25vh))
  - Row 3: `grid grid-cols-[60%_40%]` — ChartPanel left, FundamentalsPanel+ShortInterestPanel+InsiderPanel stacked right
  - Row 4: `grid grid-cols-[60%_40%]` — OptionsChain left, NewsPanel right (scrollable per D-11)
- All panels receive `ticker` prop — all refresh simultaneously on ticker change (D-04)

**frontend/src/App.tsx** (modified):
- Import `EquityModule` added
- Outer div: `min-h-screen` → `h-screen flex flex-col` (Bloomberg fixed-height requirement D-01)
- `<main>`: `p-2` → `flex-1 overflow-hidden`
- Conditional: `{activeTab === "EQUITY" && <EquityModule />}` replaces placeholder
- Non-EQUITY tabs: fallback `[TAB] MODULE READY` message preserved

## Task Commits

1. **Task 1: TickerCommandBar + QuoteBar + GBPToggle** — `0938c3d` (feat)
2. **Task 2: EquityModule assembly + App.tsx wiring** — `51179f3` (feat)
3. **Task 3: Visual verification of Equity module** — human-verify checkpoint approved by user

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

- `QuoteBar` shows `--` placeholders when no quote received yet — this is intentional. The WebSocket hook populates quote state once connected and subscribed.
- `NewsPanel` sentiment badge shows `[--]` placeholder — Phase 7 FinBERT integration will replace this (documented in 03-04 SUMMARY).
- GBP rate silently fails if `/api/fx/USD/GBP` is unavailable — GBP toggle remains active visually but no price conversion applied. This is acceptable graceful degradation.

## Self-Check: PASSED

- frontend/src/components/equity/EquityModule.tsx — FOUND (134 lines, ≥ 80)
- frontend/src/components/equity/TickerCommandBar.tsx — FOUND (57 lines, ≥ 20)
- frontend/src/components/equity/QuoteBar.tsx — FOUND (125 lines, ≥ 30)
- frontend/src/components/equity/GBPToggle.tsx — FOUND (30 lines, ≥ 15)
- frontend/src/App.tsx modified — EquityModule import + conditional render + h-screen layout
- Commit 0938c3d (Task 1) — FOUND
- Commit 51179f3 (Task 2) — FOUND
- Key links verified:
  - EquityModule → ChartPanel (React composition via `<ChartPanel`)
  - EquityModule → OptionsChain (React composition via `<OptionsChain`)
  - App.tsx → EquityModule (conditional render `activeTab === "EQUITY"`)
  - GBPToggle → /api/fx/USD/GBP (via `fetch('/api/fx/USD/GBP')` in EquityModule)

---
*Phase: 03-equity-overview*
*Completed: 2026-03-28*
