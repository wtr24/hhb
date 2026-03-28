# Phase 4: Technical Analysis Engine - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

The full TA math engine for the EQUITY tab. Delivers: all 60+ indicators across 8 groups (A–H), candlestick pattern detection with per-asset win rates + p-values, chart pattern detection (7 types with confidence scores), Fibonacci retracement/extension drawing tool, Elliott Wave manual labelling tool with Fibonacci ratio validation, all 5 pivot point methods, and the indicator picker frontend wired to the existing expanded chart view.

Does NOT include: macro dashboard (Phase 5), forex module (Phase 6), crypto desk (Phase 7), backtester, portfolio tracker, or a dedicated TA screener tab.

</domain>

<decisions>
## Implementation Decisions

### Indicator Picker UX

- **D-01:** Each chart panel in the expanded chart view has an `[Indicators ▾]` button in the panel header. Clicking it opens a grouped dropdown/modal with the full indicator list. Same header also shows `[Fib]` and `[EW]` buttons for drawing tools.
- **D-02:** Indicators only render on the **expanded single-chart view** — the 4-panel simultaneous view (W/D/4H/1H) stays clean with candles only. Avoids cramming indicator overlays into tiny panels.
- **D-03:** Indicator picker is **grouped by category**: Moving Averages, Momentum, Trend Strength, Volatility, Volume, Market Breadth, Pivot Points. Matches the A–H grouping in requirements. Collapsible sections.
- **D-04:** **Unlimited indicators** per chart — no cap enforced. User decides how dense to go. Bloomberg terminals are famously dense.
- **D-05:** Oscillator indicators (RSI, MACD, Stochastic, Williams %R, etc.) render in a **sub-pane below the candlestick chart** at ~25% height, with candles taking ~75%. Each oscillator gets its own sub-pane stacked vertically. Overlay indicators (Moving Averages, Bollinger Bands, etc.) render directly on the candle chart.
- **D-06:** Indicator **parameters are editable per instance** — clicking an active indicator opens a small inline parameter editor (e.g. RSI period, MACD 12/26/9). Parameters stored in component state (session-only). Standard analyst workflow.

### Win Rate / P-Value Storage Model

- **D-07:** Candlestick pattern win rates and p-values are **pre-computed nightly** via a Celery beat task per ticker in the seed list. Results stored in a `ta_pattern_stats` TimescaleDB table. FastAPI reads pre-computed values — no on-demand computation at request time. Matches the `compute_nightly` pattern used for pivot points (TA-07).
- **D-08:** **Win rate definition:** next-bar close-to-close. Win = price closes higher on the bar immediately following pattern detection. Simple, unambiguous, consistent across all timeframes.
- **D-09:** Statistical significance layer (win rate + p-value, TA-13) applies to **candlestick patterns only** (the 60+ TA-Lib patterns, TA-09). Standard indicator signals (RSI > 70, MACD crossover) show current values only — no stats badge. Scopes TA-13 tightly to the requirements.
- **D-10:** Pattern stats only computed when **n ≥ 30 occurrences** in historical data (out-of-sample only, as specified in requirements). Below that threshold, the badge shows "insufficient data" rather than a misleading stat.

### Fibonacci + Elliott Wave Drawing Tools

- **D-11:** **Fibonacci retracement tool:** activated by `[Fib]` button in expanded chart panel header. Enters drawing mode, user clicks a swing high then a swing low (or vice versa) — two clicks define the range, levels appear immediately. Drawing mode cancelled by pressing Escape or clicking `[Fib]` again.
- **D-12:** Fibonacci levels drawn: 0.236 / 0.382 / 0.5 / 0.618 / 0.786 / 1.0 / 1.618 / 2.618 — as specified in TA-11.
- **D-13:** **Elliott Wave labelling tool:** activated by `[EW]` button. Enters sequential labelling mode — each click on a bar places the next label in sequence: 1 → 2 → 3 → 4 → 5 → A → B → C. After each placement, automatic Fibonacci ratio validation fires and shows a pass/fail badge (Wave 3 shortest check, Wave 4 overlap check per TA-12).
- **D-14:** All drawings are **session-only** — not persisted to DB. Drawings clear on ticker change, timeframe change, or page refresh. No per-user drawing storage needed in Phase 4.
- **D-15:** Fibonacci levels **clear on timeframe change**. Drawings are tied to a specific bar/timeframe context; crossing timeframes would require re-anchoring to different bar indices.

### Chart Pattern Detection

- **D-16:** **Heuristic algorithms from scratch** using `scipy.signal.find_peaks` + geometric constraints + neckline validation. One detection function per pattern. No third-party pattern library — none covers all 7 required patterns reliably. Matches the `backend/analysis/` computation module pattern.
- **D-17:** **Confidence scoring** based on: geometric symmetry of the pattern structure + volume confirmation (volume rising at breakout). Score is a float 0.0–1.0.
- **D-18:** Detected patterns shown as **shaded region on the candle chart** spanning the pattern's bar range, with a label at the breakout point (e.g. `H&S 72%`). All 7 pattern types labelled "experimental" in the UI as specified in TA-10.
- **D-19:** Pattern detection runs **on-demand** when the user is on the expanded chart — computed from cached OHLCV in TimescaleDB, not a background task (unlike candlestick pattern stats). Results cached in Redis with TTL matching the chart timeframe (daily patterns cache for 15m, weekly for 1h).

### Claude's Discretion

- Which lightweight-charts API to use for oscillator sub-pane vs main chart pane (chart.addLineSeries vs separate chart instance)
- Exact indicator picker modal/dropdown styling (position, size, animation)
- Color palette for indicator overlays (Claude picks from terminal palette)
- How multiple oscillator sub-panes stack when user adds RSI + MACD simultaneously
- TA-Lib vs pandas-ta fallback routing per indicator (use TA-Lib for speed where available, pandas-ta as fallback)
- Exact parameter UI layout for indicator editing

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Spec (authoritative for all design and data decisions)
- `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md` — §8 (Math Engine — TA indicator groups A–H, candlestick patterns §O, chart patterns) and §5 (TTL/caching table for all data types). Read §8 in full before planning any backend computation task.

### Requirements
- `.planning/REQUIREMENTS.md` — TA-01 through TA-13 are the acceptance criteria for this phase. All 13 must be satisfied.

### Prior Phase Context (chart panels + codebase patterns)
- `.planning/phases/03-equity-overview/03-CONTEXT.md` — D-05 (4-panel layout), D-06 (expanded chart behaviour), D-01 (Bloomberg fixed-height grid). Phase 4 extends the expanded chart view from Phase 3 — do not change the 4-panel layout.

### Existing Frontend Components
- `frontend/src/components/equity/ChartPanel.tsx` — existing chart panel component. Phase 4 adds indicator picker button, Fib/EW buttons to the panel header, and oscillator sub-pane support below the candle area.
- `frontend/src/components/equity/CandleChart.tsx` — existing lightweight-charts candle chart. Phase 4 adds overlay series (MAs, BBands, etc.) and integrates sub-pane oscillators.
- `frontend/src/components/equity/EquityModule.tsx` — top-level equity module. Phase 4 wires indicator state (active indicators + parameters) into the module state.
- `frontend/src/lib/theme.ts` — terminal colour constants. All new components must use these.

### Existing Backend Analysis Module
- `backend/analysis/black_scholes.py` — pattern reference for math computation modules (pure functions, no DB calls, called from routes).
- `backend/api/routes/equity.py` — Phase 4 adds `/api/ta/` routes here or in a new `backend/api/routes/ta.py`.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/analysis/` module: established pattern for pure math computation (black_scholes, insider). TA computation functions follow the same pattern.
- `ChartPanel.tsx` + `CandleChart.tsx`: Phase 4 extends these — indicator overlays add to existing lightweight-charts instances, not new components.
- `backend/ingestion/celery_app.py`: Celery beat task registration for nightly `compute_ta_stats` follows the same pattern as existing ingestion tasks.
- `backend/cache/ttl.py`: TTL constants — Phase 4 adds entries for pattern detection cache (daily: 15m, weekly: 1h).
- `backend/alembic/versions/`: DB migrations follow the existing versioned pattern. Phase 4 adds a migration for `ta_pattern_stats` hypertable.

### Established Patterns
- Rate limit token buckets: Phase 4 backend computation is internal (no external API calls for indicator math) — no rate limiting needed for TA routes.
- Fallback chain: Live API → Redis cache → TimescaleDB applies to OHLCV data fetched for indicator computation. TA results served from `ta_pattern_stats` (pre-computed) or Redis (pattern detection cache).
- Bloomberg terminal aesthetic: amber/green on black, dense, no scrolling in fixed panels. Indicator picker modal can scroll internally.

### Integration Points
- `EquityModule.tsx` → `ChartPanel.tsx`: Pass active indicator state + parameters down as props. Indicator picker updates state in EquityModule.
- `CandleChart.tsx`: Add `addLineSeries` / `addHistogramSeries` calls for overlay/oscillator indicators using lightweight-charts API.
- `GET /api/ta/indicators/{ticker}?indicator=RSI&period=14&timeframe=1d` — new route returns pre-computed or on-demand indicator values.
- `GET /api/ta/patterns/{ticker}?timeframe=1d` — returns candlestick pattern detections for today's bar + win rate stats.
- `GET /api/ta/chart-patterns/{ticker}?timeframe=1d` — returns chart pattern detections (H&S, Double Top, etc.) with confidence scores.

</code_context>

<specifics>
## Specific Ideas

- The `[Indicators ▾]`, `[Fib]`, and `[EW]` buttons are in the expanded chart panel header — same header that shows the timeframe selector and expand/collapse button from Phase 3.
- Fibonacci level lines are horizontal lines spanning the full chart width — classic retracement tool appearance.
- Elliott Wave labels placed on chart as small text tags at the selected bar's high (for peaks) or low (for troughs). Fibonacci validation badge appears inline after label 3 (Wave 3 shortest check) and after label 4 (overlap check).
- Candlestick pattern badge design: `Hammer: 65% win | n=43 | p=0.03` in amber text as a small tag overlaid at the relevant bar.
- Chart pattern shaded region uses a semi-transparent amber/orange fill to stay readable against the dark terminal background.

</specifics>

<deferred>
## Deferred Ideas

- Persisting drawings (Fibonacci levels, Elliott Wave labels) to DB per-ticker — adds significant scope. Consider for a future "drawing notebook" phase.
- Statistical significance layer for regular indicator signals (RSI crossovers, MACD crossovers) — would require defining trigger rules for each indicator. Consider after Phase 4 validates the candlestick pattern stats pipeline.
- Indicator alert triggers (e.g. "notify me when RSI > 70") — belongs in the Watchlist + Alerts phase.
- ML-based confidence scoring for chart patterns — requires labelled training data. Deferred indefinitely.

</deferred>

---

*Phase: 04-technical-analysis-engine*
*Context gathered: 2026-03-28*
