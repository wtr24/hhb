# Phase 3: Equity Overview - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

The EQUITY tab of the terminal. User enters a ticker and gets a full Bloomberg DES/GP-equivalent view: live quote, multi-timeframe candlestick charts, earnings/dividend markers, fundamentals panel, short interest, insider transaction clustering, options chain with Greeks + IV surface, and a company news feed. Backend routes, Finnhub WebSocket integration, Black-Scholes pricer, and full frontend assembly all land in this phase.

Does NOT include: macro dashboard (Phase 5), forex module (Phase 6), crypto desk (Phase 6), screener (Phase 8), portfolio tracker (Phase 11).

</domain>

<decisions>
## Implementation Decisions

### Page Layout

- **D-01:** Bloomberg fixed-height grid layout. Nothing scrolls — all panels visible simultaneously like a real terminal. Layout zones:
  - **Top strip (full width):** Live quote bar — ticker, price, change, change%, volume, stale badge
  - **Left panel (~60% width, full height below strip):** 4-panel simultaneous chart view (W/D/4H/1H)
  - **Right sidebar (~40% width):** Fundamentals panel → Short interest → Insider clustering, stacked vertically
  - **Bottom row (full width):** Options chain (~60%) + Company news feed (~40%) side by side
- **D-02:** Stale data indicator — amber ⚠ badge shown inline on any panel that has `stale: true` data (carried forward from Phase 2 fallback chain).

### Ticker Entry

- **D-03:** Command bar at the top of the EQUITY module (above the grid). Terminal-style: `TICKER> ____` with amber cursor. User types a ticker and presses Enter to load all panels. Auto-uppercases input. Supports `.L` suffix for LSE tickers (LLOY.L, BARC.L) and index notation (^FTSE, ^FTMC).
- **D-04:** On Enter, all panels refresh simultaneously for the new ticker. Previous ticker data cleared. No history/autocomplete in Phase 3 — plain input only.

### Chart Panel Behaviour

- **D-05:** Default view is 4-panel simultaneous display (Weekly / Daily / 4H / 1H), all showing the same ticker. This satisfies EQUITY-02.
- **D-06:** Clicking any panel expands it to full-width within the chart zone, with a timeframe range selector (1D / 1W / 1M / 1Y / 5Y). This satisfies EQUITY-03. Pressing Escape or clicking the expanded panel again returns to 4-panel view.
- **D-07:** Earnings date markers (EQUITY-04) and dividend ex-date markers (EQUITY-05) appear as vertical lines on all chart panels and on the expanded single-chart view.

### Options Chain Display

- **D-08:** Standard side-by-side layout — calls on the left, puts on the right, strike price in the centre column. Columns: Strike | Call Delta | Call Bid | Call Ask | Call IV | Strike | Put Bid | Put Ask | Put Delta | Put IV.
- **D-09:** IV surface shown as a compact heatmap above the options table. IV percentile rank shown as a badge in the table header (e.g. `IV RANK: 73%`).
- **D-10:** Greeks shown per row (delta, gamma, vega, theta). Calculated client-side using Black-Scholes — backend provides the raw option data (bid/ask/expiry/strike), frontend or backend computes Greeks.

### News Feed

- **D-11:** Company news feed sits in the bottom-right panel alongside the options chain. Scrollable list within its fixed panel. Each item: headline, source, timestamp, sentiment badge (bullish/bearish/neutral from FinBERT or Finnhub sentiment score). Refreshes every 5 minutes (EQUITY-10).

### FX-Adjusted Returns

- **D-12:** GBP toggle button in the quote strip. When active, all price/return figures shown in GBP using GBP/USD rate from Phase 2 FX ingestion (fx_rates table). Toggle state persists while the user stays on the EQUITY tab. Satisfies EQUITY-11.

### LSE / Index Support

- **D-13:** `.L` suffix tickers (LLOY.L, BARC.L) and index tickers (^FTSE, ^FTMC) work identically to US tickers throughout all panels. No special casing in the UI — yfinance handles the data fetch differences transparently (EQUITY-12).

### Claude's Discretion

- Exact grid CSS implementation (CSS Grid or Flexbox, panel sizing details)
- Black-Scholes implementation location (backend compute endpoint vs frontend calculation)
- Loading states within each panel (skeleton vs spinner vs dim + stale badge)
- Insider clustering visualisation detail (table vs mini bar chart for buy/sell ratio)
- Short interest display format within the sidebar panel
- WebSocket reconnect / error handling in the frontend

</decisions>

<specifics>
## Specific Ideas

- The ticker command bar should feel like a Bloomberg terminal command line — `TICKER> ` prefix, amber blinking cursor, monospace font. Not a styled search box.
- The 4-panel chart grid should feel like a proper multi-monitor trading setup compressed into one screen — all timeframes visible simultaneously is the core value.
- The Bloomberg grid approach means every pixel is used. Dense is good. Scrolling = failure.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec (authoritative for all design decisions)
- `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md` — Full terminal design spec: Bloomberg aesthetic rules, colour palette, keyboard navigation patterns, data freshness badges, density requirements. Read §3 (UI Aesthetic) and §5 (Data Layer / TTL) before designing any panel.

### Requirements
- `.planning/REQUIREMENTS.md` — EQUITY-01 through EQUITY-12 are the acceptance criteria for this phase. Read all 12 before planning.

### Phase 2 Context (prior decisions that affect Phase 3)
- `.planning/phases/02-data-ingestion-foundation/02-CONTEXT.md` — D-07 (WebSocket channel structure), D-08 (message format with stale flag), D-09 (initial snapshot on subscribe), D-13 (quote endpoint response shape), D-17 (FX endpoint dependency note for EQUITY-11).

### Existing Frontend Shell
- `frontend/src/App.tsx` — Current EQUITY tab renders a stub. Phase 3 replaces the `<main>` content area. Do NOT change the tab nav or keyboard handler — add inside the `activeTab === "EQUITY"` branch only.
- `frontend/src/lib/theme.ts` — TERMINAL colour constants (BG, AMBER, GREEN, RED, DIM, BORDER) and MODULE_TABS type. All new components must use these constants, not raw hex values.

### Chart Library
- Phase 3 uses `lightweight-charts` (TradingView Apache 2.0) — locked in PROJECT.md. Research must cover lightweight-charts v4 API: `createChart`, `addCandlestickSeries`, `setMarkers` for earnings/dividend lines, and multi-chart layout patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/hooks/useKeyboard.ts` — keyboard event handler already wired; extend for Escape key (collapse expanded chart panel) and Enter key (submit ticker input).
- `frontend/src/lib/theme.ts` — TERMINAL constants; all panels use `bg-terminal-bg`, `text-terminal-amber`, `border-terminal-border`.
- `backend/api/websocket.py` — `ConnectionManager.broadcast_to_channel()` already wired to Redis pub/sub. Frontend WebSocket client subscribes to `quotes:{ticker}` to receive live quote updates.
- `backend/api/routes/quote.py` — `GET /api/quote/{ticker}` returns OHLCV + fundamentals + stale flag. Phase 3 frontend calls this on ticker entry.
- `backend/api/redis_client.py` — async Redis client already available for any new backend routes.

### Established Patterns
- TailwindCSS v4 CSS-first config (`@theme {}`) — no `tailwind.config.js`. All custom utilities defined in CSS.
- `text-xs` base font size throughout — maintain this in all equity panels.
- `border-terminal-border` (`#1a1a1a`) for all panel dividers.
- FastAPI routers mounted at `/api/*` in `main.py` — new equity routes follow same pattern.

### Integration Points
- `frontend/src/App.tsx` line 41 — `<main>` tag currently renders `[{activeTab}] MODULE READY`. Phase 3 replaces this with a conditional: `{activeTab === "EQUITY" && <EquityModule />}`.
- `backend/api/main.py` — new routes for Phase 3 (Finnhub proxy, options chain, short interest, insider data) registered here alongside existing quote/macro/ingest routers.
- `backend/ingestion/tasks.py` — Celery tasks for Finnhub data (short interest, insider transactions, company news) added here alongside existing ingest tasks.

</code_context>

<deferred>
## Deferred Ideas

- Ticker autocomplete / search history — deferred to Phase 12 (Watchlist & Alerts).
- Level 2 order book for equities — out of scope (Constraints: equity L2 not available free-tier).
- Analyst consensus estimates — limited via FMP free tier only; deferred to screener phase if feasible.
- Real-time options Greeks streaming — Phase 3 uses snapshot via REST; streaming Greeks deferred.
- Global command bar (`:ticker AAPL`, `:macro CPI` from any module) — powerful feature, deferred to Phase 12.

</deferred>

---

*Phase: 03-equity-overview*
*Context gathered: 2026-03-28*
