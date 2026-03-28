# Phase 4: Technical Analysis Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Areas discussed:** Indicator Picker UX, Win rate / p-value storage model, Fibonacci + Elliott Wave drawing UX, Chart pattern detection approach

---

## Area 1: Indicator Picker UX

**Q: How does the user open the indicator picker?**
Options presented: Button on chart panel header / Command-bar style / Persistent sidebar
Selected: **Button on chart panel (Recommended)** — `[Indicators ▾]` in each panel header

**Q: Where do indicator overlays render?**
Options: Expanded chart only / Both 4-panel and expanded
Selected: **Expanded chart only** — keeps 4-panel view clean

**Q: What does the indicator picker show?**
Options: Grouped by category / Flat searchable list
Selected: **Grouped by category** — Moving Averages, Momentum, Trend, Volatility, Volume, Breadth, Pivot Points

**Q: How many indicators can be active on one chart at once?**
Options: Unlimited / Cap at 5 / Cap at 10
Selected: **Unlimited** — user decides density, Bloomberg terminals are famously dense

**Q: Where do oscillators render?**
Options: Sub-pane below expanded chart / Separate panels stacked
Selected: **Below expanded chart** — 75% candles, 25% oscillator sub-pane(s)

**Q: Can indicator parameters be customised?**
Options: Editable per instance / Fixed defaults only
Selected: **Yes, editable per instance** — click indicator to open inline parameter editor

---

## Area 2: Win Rate / P-Value Storage Model

**Q: How should win rates and p-values be computed and stored?**
Options: Pre-computed nightly in TimescaleDB / Lazy on first request / Real-time always
Selected: **Pre-computed nightly in TimescaleDB** — Celery beat task per ticker, stored in `ta_pattern_stats`

**Q: Win rate definition?**
Options: Next-bar close-to-close / N-bar forward return / Fixed forward window per timeframe
Selected: **Next-bar close-to-close** — price closes higher on bar immediately after pattern

**Q: Does the stats layer apply to regular indicators too?**
Options: Candlestick patterns only / All signal types
Selected: **Candlestick patterns only** — scopes TA-13 tightly; regular indicators show values only

---

## Area 3: Fibonacci + Elliott Wave Drawing UX

**Q: How does the user initiate a Fibonacci drawing?**
Options: Button in panel header + click-click / Keyboard shortcut + click-drag
Selected: **Button in panel header, then click-click** — `[Fib]` button → click swing high → click swing low

**Q: Do drawings persist across sessions?**
Options: Session-only / Persisted per ticker in TimescaleDB
Selected: **Session-only** — no DB drawing storage in Phase 4

**Q: How are Elliott Wave labels placed?**
Options: Click on bar to place next label in sequence / Type label then click
Selected: **Click on bar to place label** — sequential: 1→2→3→4→5→A→B→C; Fib validation fires after each

**Q: What happens to Fibonacci levels on timeframe change?**
Options: Levels clear on timeframe change / Levels scale proportionally
Selected: **Levels clear on timeframe change** — drawings tied to specific timeframe context

---

## Area 4: Chart Pattern Detection Approach

**Q: How should chart patterns be detected algorithmically?**
Options: Heuristic algorithms from scratch / Use mplfinance or similar / Minimal scope (H&S + Double Top/Bottom only)
Selected: **Heuristic algorithms from scratch** — `scipy.signal.find_peaks` + geometric constraints, one function per pattern

**Q: What factors go into confidence scores?**
Options: Geometric symmetry + volume confirmation / ML-based scoring / Pattern completion only (binary)
Selected: **Geometric symmetry + volume confirmation** — float 0.0–1.0 score

**Q: How are detected patterns shown on the chart?**
Options: Shaded region + label on chart / List below chart / Both overlay + list
Selected: **Shaded region + label on chart** — semi-transparent shaded region spanning pattern bars, label at breakout point with confidence %

---

*Discussion log generated: 2026-03-28*
