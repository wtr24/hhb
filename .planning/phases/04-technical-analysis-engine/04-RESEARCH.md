# Phase 4: Technical Analysis Engine - Research

**Researched:** 2026-03-29
**Domain:** Technical analysis computation (TA-Lib, pandas-ta, scipy, arch), lightweight-charts v5 multi-pane, TimescaleDB pattern stats persistence
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Indicator Picker UX**
- D-01: Each chart panel in the expanded chart view has an `[Indicators ▾]` button in the panel header. Same header also shows `[Fib]` and `[EW]` buttons.
- D-02: Indicators only render on the expanded single-chart view. The 4-panel simultaneous view stays clean with candles only.
- D-03: Indicator picker is grouped by category: Moving Averages, Momentum, Trend Strength, Volatility, Volume, Market Breadth, Pivot Points. Collapsible sections.
- D-04: Unlimited indicators per chart — no cap enforced.
- D-05: Oscillator indicators render in a sub-pane below the candlestick chart at ~25% height, with candles at ~75%. Each oscillator gets its own sub-pane stacked vertically. Overlay indicators render directly on the candle chart.
- D-06: Indicator parameters are editable per instance — clicking an active indicator opens a small inline parameter editor. Parameters stored in component state (session-only).

**Win Rate / P-Value Storage Model**
- D-07: Candlestick pattern win rates and p-values are pre-computed nightly via Celery beat task per ticker in seed list. Results stored in `ta_pattern_stats` TimescaleDB table. No on-demand computation at request time.
- D-08: Win rate definition: next-bar close-to-close. Win = price closes higher on the bar immediately following pattern detection.
- D-09: Statistical significance layer (TA-13) applies to candlestick patterns only. Standard indicator signals show current values only — no stats badge.
- D-10: Pattern stats computed only when n >= 30 occurrences. Below threshold badge shows "insufficient data".

**Fibonacci + Elliott Wave Drawing Tools**
- D-11: Fibonacci retracement activated by `[Fib]` button. Two-click mode: swing high then swing low. Levels appear immediately. Cancelled by Escape or re-clicking `[Fib]`.
- D-12: Fibonacci levels drawn: 0.236 / 0.382 / 0.5 / 0.618 / 0.786 / 1.0 / 1.618 / 2.618.
- D-13: Elliott Wave labelling tool (`[EW]` button). Sequential clicking places 1 → 2 → 3 → 4 → 5 → A → B → C. Fibonacci ratio validation fires after each placement.
- D-14: All drawings are session-only — not persisted to DB. Clear on ticker/timeframe change or page refresh.
- D-15: Fibonacci levels clear on timeframe change.

**Chart Pattern Detection**
- D-16: Heuristic algorithms from scratch using `scipy.signal.find_peaks` + geometric constraints + neckline validation. One detection function per pattern. No third-party pattern library.
- D-17: Confidence scoring based on geometric symmetry + volume confirmation. Score is float 0.0–1.0.
- D-18: Detected patterns shown as shaded region on candle chart spanning the pattern's bar range, with a label at the breakout point (e.g. `H&S 72%`). All 7 pattern types labelled "experimental" in UI.
- D-19: Pattern detection runs on-demand when user is on expanded chart — computed from cached OHLCV in TimescaleDB, not a background task. Results cached in Redis with TTL matching chart timeframe (daily patterns: 15m, weekly: 1h).

### Claude's Discretion
- Which lightweight-charts API to use for oscillator sub-pane vs main chart pane (chart.addLineSeries vs separate chart instance)
- Exact indicator picker modal/dropdown styling (position, size, animation)
- Color palette for indicator overlays (Claude picks from terminal palette)
- How multiple oscillator sub-panes stack when user adds RSI + MACD simultaneously
- TA-Lib vs pandas-ta fallback routing per indicator (use TA-Lib for speed where available, pandas-ta as fallback)
- Exact parameter UI layout for indicator editing

### Deferred Ideas (OUT OF SCOPE)
- Persisting drawings (Fibonacci levels, Elliott Wave labels) to DB per-ticker
- Statistical significance layer for regular indicator signals (RSI crossovers, MACD crossovers)
- Indicator alert triggers (belongs in Watchlist + Alerts phase)
- ML-based confidence scoring for chart patterns
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TA-01 | All Moving Averages — SMA, EMA, DEMA, TEMA, WMA, HMA, LWMA, VWMA + Golden/Death Cross + EMA Ribbon (8 EMAs) | TA-Lib provides SMA/EMA/DEMA/TEMA/WMA; pandas-ta provides HMA, VWMA as fallbacks; Ribbon is 8 addSeries calls |
| TA-02 | All Momentum/Oscillator indicators — RSI, StochRSI, MACD, Stochastic %K/%D, Williams %R, CCI, ROC, Momentum, DPO, TRIX, Ultimate Oscillator, PPO, KDJ, CMO | All available in TA-Lib; pandas-ta covers KDJ and any gaps |
| TA-03 | All Trend Strength indicators — ADX/+DI/-DI, Aroon, Parabolic SAR, SuperTrend, Vortex, Ichimoku Cloud, Mass Index | ADX/Aroon/SAR in TA-Lib; SuperTrend, Vortex, Ichimoku in pandas-ta |
| TA-04 | All Volatility indicators — Bollinger Bands + %B, Keltner Channel, Donchian Channel, ATR, Historical Vol (3 methods), GARCH(1,1), Chaikin Vol, Ulcer Index | BBands/ATR in TA-Lib; GARCH via arch library; Keltner/Donchian in pandas-ta |
| TA-05 | All Volume indicators — OBV, VWAP + Anchored VWAP + VWAP SD Bands, A/D Line, CMF, MFI, Volume Profile, CVD, VROC, Ease of Movement, NVI/PVI, Force Index | OBV/A-D/MFI in TA-Lib; VWAP/CVD/Volume Profile hand-rolled; others pandas-ta |
| TA-06 | All Market Breadth indicators — A/D Line, McClellan Oscillator + Summation, TRIN, New Highs-Lows, Up-Down Volume Ratio, % Above 200/50 SMA, TICK | Index-level data required from yfinance constituent lists; computed in Python |
| TA-07 | All 5 Pivot Point methods — Standard, Woodie's, Camarilla, Fibonacci, DeMark — computed nightly, stored in TimescaleDB, horizontal lines | Pure-math nightly Celery task; new `pivot_points` table or `ta_pattern_stats` table |
| TA-08 | Intermarket analysis — rolling correlation (30D/90D/1Y) for DXY/Gold, Yields/USD, VIX/SPX, Credit Spreads/Equities, Oil/CPI, Copper/Growth, BTC/SPX | OHLCV data from TimescaleDB; rolling correlation via pandas/scipy |
| TA-09 | 60+ candlestick patterns detected (TA-Lib) with per-asset historical win rate and p-value (n>=30, out-of-sample only) | TA-Lib CDL* functions; win rate from `ta_pattern_stats` hypertable; t-test via scipy.stats.ttest_1samp |
| TA-10 | Chart pattern detection — H&S, Inv H&S, Cup & Handle, Double Top/Bottom, Triangles, Flag/Pennant, Wedge — with confidence scores labelled "experimental" | scipy.signal.find_peaks + geometric constraints + OLS trendlines; custom per-pattern detectors |
| TA-11 | Fibonacci retracement/extension drawing tool — interactive on chart with 0.236/0.382/0.5/0.618/0.786/1.0/1.618/2.618 levels | lightweight-charts v5 addSeries(LineSeries) for each level; two-click drawing mode in component state |
| TA-12 | Elliott Wave manual labelling tool with automatic Fibonacci ratio validation (Wave 3 shortest, Wave 4 overlap, impulse/corrective guidelines) | Custom frontend drawing mode; validation logic in pure JS/TS after each label placement |
| TA-13 | Statistical significance layer — win rate, p-value, sample size, out-of-sample flag; context filter by trend/volume/key level | scipy.stats.ttest_1samp; stored in `ta_pattern_stats`; badge rendered in frontend at bar position |
</phase_requirements>

---

## Summary

Phase 4 builds the complete technical analysis math engine on top of the existing OHLCV data layer and lightweight-charts v5 chart from Phase 3. The backend computation layer follows the established `backend/analysis/` pure-functions pattern; all indicator math runs in Python and is returned via new `/api/ta/` routes. The key architectural split is: standard indicators computed on-demand per request from OHLCV (no persistence needed), candlestick pattern stats pre-computed nightly via Celery beat, and chart patterns computed on-demand and cached in Redis.

The two critical library decisions are: **TA-Lib 0.6.8** (current as of 2026-03-29), which since v0.6.5 ships binary wheels with the bundled C library — meaning `pip install TA-Lib` now works inside Docker without a multi-stage build or apt-get install step. For indicators not in TA-Lib (SuperTrend, Vortex, HMA, VWAP variants, Ichimoku), **pandas-ta 0.4.71b0** is the fallback. GARCH(1,1) volatility requires the **arch 8.0.0** package.

The frontend sub-pane architecture uses lightweight-charts v5's native pane API: `chart.addSeries(LineSeries, options, paneIndex)` where `paneIndex >= 1` creates oscillator panes automatically. The pane height is controlled via `chart.panes()[n].setHeight(pixels)`. This is the correct v5 API — the v4 `addLineSeries()` method was removed in v5. Fibonacci levels and Elliott Wave labels are implemented entirely as lightweight-charts series overlay elements (no separate canvas), keeping all drawing within the existing single chart instance.

**Primary recommendation:** Use TA-Lib 0.6.8 as primary library (add to requirements.txt; no Dockerfile changes needed for v0.6.8 wheels). pandas-ta as fallback. Add `arch>=8.0.0` for GARCH. All new backend code lives in `backend/analysis/indicators.py` and new files per domain. New `/api/ta/` route file. One Alembic migration for `ta_pattern_stats` + `pivot_points` hypertables.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| TA-Lib | 0.6.8 | 200+ indicators, 60+ candlestick CDL* functions | C-based speed; 60+ CDL patterns in one function call per pattern; industry standard |
| pandas-ta | 0.4.71b0 | Python-native indicators; covers SuperTrend, Vortex, Ichimoku, HMA, VWMA gaps | MIT; 212 indicators; direct pandas DataFrame integration |
| arch | 8.0.0 | GARCH(1,1) volatility model via `arch_model` | Only Python GARCH library that is actively maintained; well-documented API |
| scipy | >=1.11.0 | `find_peaks` for chart pattern detection; `ttest_1samp` for p-values; OLS regression | Already in requirements.txt |
| numpy | already installed | Array math for all indicator computations | Already installed as transitive dep |
| lightweight-charts | 5.1.0 | Multi-pane chart with oscillator sub-panes | Already installed; v5 pane API is stable |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| statsmodels | latest | OLS trendlines for triangle/channel detection | For chart pattern OLS fits (scipy.stats.linregress works too) |
| pandas | >=2.0.0 | DataFrame manipulation for all indicator inputs | Already in requirements.txt |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TA-Lib 0.6.8 | TA-Lib 0.4.x | 0.4.x requires separate C library install in Docker; 0.6.5+ wheels bundle the C lib — always prefer 0.6.5+ |
| pandas-ta | ta (another wrapper) | pandas-ta has 212 indicators vs fewer in ta; better maintained |
| arch | manually coded GARCH | arch uses MLE fitting, handles edge cases, convergence checks — do not hand-roll |
| scipy.stats.linregress | statsmodels OLS | linregress is sufficient for 2-point trendlines; statsmodels adds no value for chart patterns |

**Installation (add to backend/requirements.txt):**
```bash
TA-Lib==0.6.8
pandas-ta==0.4.71b0
arch>=8.0.0
```

**Verified current versions (2026-03-29):**
- TA-Lib: 0.6.8 (confirmed via `pip3 index versions TA-Lib`)
- arch: 8.0.0 (confirmed via `pip3 index versions arch`)
- pandas-ta: 0.4.71b0 (confirmed via PyPI search)
- lightweight-charts: 5.1.0 (confirmed in frontend/package.json)

---

## Architecture Patterns

### Recommended Project Structure (additions only)
```
backend/
├── analysis/
│   ├── indicators.py        # TA-Lib + pandas-ta wrappers, groups A-H
│   ├── patterns.py          # 60+ TA-Lib CDL* candlestick detection
│   ├── chart_patterns.py    # H&S, Double Top etc. via scipy.signal.find_peaks
│   ├── fibonacci.py         # Retracement/extension level math (pure functions)
│   ├── pivot_points.py      # 5 pivot methods as pure functions
│   ├── intermarket.py       # Rolling correlation computation
│   └── garch.py             # GARCH(1,1) wrapper
├── models/
│   ├── ta_pattern_stats.py  # new: TimescaleDB hypertable
│   └── pivot_points.py      # new: TimescaleDB hypertable (or embed in ta_pattern_stats)
├── api/routes/
│   └── ta.py                # new: /api/ta/* routes
└── alembic/versions/
    └── 0004_ta_engine.py    # new: ta_pattern_stats + pivot_points hypertables

frontend/src/
├── components/equity/
│   ├── IndicatorPicker.tsx  # grouped modal, collapsible, unlimited select
│   ├── ExpandedChart.tsx    # new: wraps CandleChart + oscillator sub-panes
│   └── DrawingTools.tsx     # Fibonacci + EW state machine
└── types/
    └── indicators.ts        # IndicatorConfig type, group enums
```

### Pattern 1: On-Demand Indicator Computation (Groups A-E, H)
**What:** Route receives `?indicator=RSI&period=14&timeframe=1d`, fetches OHLCV from TimescaleDB, runs TA-Lib/pandas-ta, returns array of `{time, value}` pairs.
**When to use:** All standard indicator values — computed fresh per request, cached in Redis with same TTL as OHLCV (`fundamentals` = 24h for daily, `quote` = 15s for intraday).

```python
# Source: TA-Lib Python wrapper docs + project analysis/black_scholes.py pattern
import talib
import numpy as np

def compute_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Pure function. Returns RSI array same length as closes (first period-1 values = NaN)."""
    return talib.RSI(closes, timeperiod=period)
```

### Pattern 2: Nightly Pre-Computed Pattern Stats (TA-09, TA-07, TA-13)
**What:** Celery beat task runs nightly, computes candlestick pattern win rates per ticker per pattern, stores in `ta_pattern_stats`. Route reads pre-computed values — no on-demand stat computation.
**When to use:** Candlestick pattern win rates + p-values (D-07), pivot points (TA-07).

```python
# Celery beat task — follows celery_app.py pattern
# Source: existing ingestion/tasks.py + celery_app.py (project codebase)
@app.task
def compute_nightly_pattern_stats():
    """Runs nightly. For each ticker × pattern × timeframe, compute win rate + p-value."""
    from scipy.stats import ttest_1samp
    # ...
    # win_rate = wins / n_occurrences
    # t_stat, p_value = ttest_1samp(outcomes, popmean=0.5)
    # store to ta_pattern_stats
```

### Pattern 3: lightweight-charts v5 Oscillator Sub-Pane
**What:** Oscillator indicators (RSI, MACD, etc.) go into pane index 1+. Main candle chart is pane 0. Each new oscillator gets the next pane index. Height set to 25% of total height.
**When to use:** Every oscillator indicator — RSI, MACD, Stochastic, Williams %R, CCI, etc. (D-05).

```typescript
// Source: https://tradingview.github.io/lightweight-charts/tutorials/how_to/panes
// paneIndex >= 1 creates oscillator sub-pane automatically
const rsiSeries = chart.addSeries(LineSeries, {
  color: '#F5A623',
  lineWidth: 1,
}, 1); // paneIndex 1

// Set oscillator pane height to ~25% of total container height
const totalHeight = containerRef.current.clientHeight;
chart.panes()[1]?.setHeight(Math.floor(totalHeight * 0.25));
```

### Pattern 4: Chart Pattern Detection (scipy.signal.find_peaks)
**What:** Sliding window over OHLCV bars; `find_peaks` identifies local highs/lows; geometric constraints validate pattern structure; confidence score from symmetry + volume confirmation.
**When to use:** All 7 chart pattern types (D-16, TA-10).

```python
# Source: scipy.signal docs + D-16 spec decision
from scipy.signal import find_peaks
import numpy as np

def detect_head_and_shoulders(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray):
    """Returns list of {start_idx, end_idx, confidence} for all H&S found."""
    peaks, _ = find_peaks(highs, prominence=highs.std() * 0.5)
    # 3-peak check: middle peak > both shoulders + within 3% height
    # neckline OLS fit through two troughs
    # confidence = geometric_symmetry_score * volume_confirmation_score
```

### Pattern 5: Fibonacci Level Rendering (drawing tool)
**What:** Two-click frontend state machine. On second click, compute 8 levels from price range, add 8 horizontal line series to pane 0 at constant y-value using lightweight-charts `PriceLine` or `LineSeries` with flat data.
**When to use:** When user activates `[Fib]` button (D-11, D-12).

```typescript
// PriceLine API is the correct approach for horizontal levels in lightweight-charts v5
// Source: lightweight-charts docs + D-11 decision
const fibLevels = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618];
fibLevels.forEach(ratio => {
  const price = swingLow + (swingHigh - swingLow) * (1 - ratio);
  candleSeries.createPriceLine({ price, color: '#F5A623', lineStyle: 2, axisLabelVisible: true, title: `${ratio}` });
});
```

### Anti-Patterns to Avoid
- **Separate chart instance per oscillator:** Do not create a new `createChart()` call per oscillator — use `paneIndex` parameter on the single chart instance. Multiple chart instances do not synchronize time axes.
- **On-demand candlestick pattern stats:** Computing win rates on-demand at request time is too slow (requires scanning full OHLCV history for each ticker). Pre-compute nightly per D-07.
- **Using TA-Lib 0.4.x in Docker:** Requires `apt-get install ta-lib` C library separately. Use 0.6.8+ which bundles the C library in the wheel.
- **Hand-rolling GARCH:** The `arch` library handles convergence failures, edge cases, and MLE fitting. Do not implement GARCH from scratch.
- **Storing indicator time-series in TimescaleDB:** Standard indicator values (RSI, MACD etc.) should NOT be stored — they are cheap to recompute from OHLCV and would consume enormous storage. Only store: pattern stats (nightly aggregates), pivot points (daily/weekly/monthly levels).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candlestick patterns (60+) | CDL pattern detection logic | `talib.CDLHAMMER`, `talib.CDLENGULFING`, etc. (one function per pattern) | TA-Lib implements all 60+ with correct multi-bar lookahead; hand-rolling each pattern is 2000+ lines of fragile code |
| GARCH volatility | MLE fitting loop | `arch_model(returns).fit()` | Convergence failures, numerical stability, score function — all handled by arch library |
| RSI, MACD, BBands, ATR, ADX | Indicator math | `talib.RSI()`, `talib.MACD()`, etc. | TA-Lib C implementation is 10-100x faster than Python loops on 500-bar arrays |
| SuperTrend | ATR + direction logic | `pandas_ta.supertrend(df)` | Non-trivial state machine; pandas-ta maintains it correctly |
| Ichimoku Cloud | Tenkan/Kijun/Senkou math | `pandas_ta.ichimoku(df)` | 5 components with different lookback windows; pandas-ta is correct reference impl |
| Statistical t-test | p-value formula | `scipy.stats.ttest_1samp(outcomes, popmean=0.5)` | Floating point precision issues in manual implementation |

**Key insight:** TA-Lib covers ~80% of the indicator surface area. pandas-ta covers the remaining 20%. Combined, there is no need to implement any indicator from scratch except VWAP variants (which require intraday bar-level accumulation from session open — no library standard exists) and Volume Profile (histogram computation is trivial with numpy).

---

## Runtime State Inventory

Step 2.5: SKIPPED — Phase 4 is a greenfield addition of new indicators, tables, routes, and frontend components. No renaming, refactoring, or migration of existing data. No stored runtime state is affected by this phase.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python pip | TA-Lib install | ✓ | 3.x | — |
| TA-Lib 0.6.8 | TA-01 through TA-09 | NOT YET (not in requirements.txt) | — | Add to requirements.txt; Docker rebuild |
| pandas-ta | TA-03/04/05 fallbacks | NOT YET (not in requirements.txt) | — | Add to requirements.txt |
| arch | TA-04 GARCH | NOT YET (not in requirements.txt) | — | Add to requirements.txt |
| scipy | chart pattern find_peaks, t-test | ✓ | >=1.11.0 (in requirements.txt) | — |
| lightweight-charts v5.1 | Frontend pane API | ✓ | 5.1.0 (in package.json) | — |
| TimescaleDB | ta_pattern_stats, pivot_points | ✓ | Running (Phase 1+) | — |
| Redis | Pattern detection cache | ✓ | Running (Phase 1+) | — |
| Celery beat | Nightly pattern stats task | ✓ | Running (Phase 2+) | — |

**Missing dependencies with no fallback:**
- TA-Lib 0.6.8 — required for TA-01 through TA-09; Plan 04-01 Wave 0 must add to requirements.txt
- pandas-ta — required for TA-03 SuperTrend/Vortex/Ichimoku; Plan 04-01 Wave 0
- arch — required for GARCH(1,1) in TA-04; Plan 04-03 Wave 0

**No Dockerfile changes needed:** TA-Lib 0.6.8+ ships binary wheels (manylinux_2_28) that bundle the C library. `pip install TA-Lib==0.6.8` in the Docker layer is sufficient — no `apt-get install ta-lib` required.

---

## Common Pitfalls

### Pitfall 1: TA-Lib NaN Padding on Array Inputs
**What goes wrong:** TA-Lib returns arrays with `NaN` for the first `period - 1` elements (the "lookback period"). If you return the raw array to the frontend, it includes null/NaN values that lightweight-charts rejects or renders as gaps.
**Why it happens:** TA-Lib requires a minimum number of bars before it can compute a valid result.
**How to avoid:** Strip leading NaN values and align the time array before returning: `valid_mask = ~np.isnan(values); times[valid_mask], values[valid_mask]`.
**Warning signs:** Frontend chart shows only a partial line that starts mid-way through the candle history.

### Pitfall 2: lightweight-charts v5 API Changes from v4
**What goes wrong:** Using deprecated v4 methods causes silent failures or TypeScript errors.
**Why it happens:** v5 removed `addCandlestickSeries()` → use `addSeries(CandlestickSeries)`. Removed `addLineSeries()` → use `addSeries(LineSeries)`. Removed `series.setMarkers()` → use `createSeriesMarkers()`. The existing CandleChart.tsx already uses the correct v5 API — follow its patterns.
**How to avoid:** Import series types (`LineSeries`, `HistogramSeries`, `AreaSeries`) from `'lightweight-charts'` and pass to `chart.addSeries(TypeClass, options, paneIndex)`.
**Warning signs:** TypeScript compile error `Property 'addLineSeries' does not exist on type 'IChartApi'`.

### Pitfall 3: Multiple Chart Instances Break Time Sync
**What goes wrong:** Creating a separate `createChart()` call for each oscillator sub-pane produces independent charts that don't synchronize crosshair or scroll.
**Why it happens:** Each `createChart()` is an independent chart widget.
**How to avoid:** Use `chart.addSeries(SeriesType, options, paneIndex)` where `paneIndex >= 1` — all panes on the same chart instance share time scale automatically.
**Warning signs:** Crosshair line doesn't span all panes; oscillator and candle chart scroll independently.

### Pitfall 4: TimescaleDB `create_hypertable` on Non-Empty Table
**What goes wrong:** Alembic migration fails if `ta_pattern_stats` already has rows when `create_hypertable` is called.
**Why it happens:** TimescaleDB requires the table to be empty when converting to hypertable.
**How to avoid:** Call `SELECT create_hypertable('ta_pattern_stats', 'time', if_not_exists => TRUE)` immediately after `op.create_table()` before any data is inserted — same pattern as migrations 0001-0003.
**Warning signs:** Alembic migration fails with `cannot create a hypertable on a non-empty table`.

### Pitfall 5: Market Breadth Data Source (TA-06)
**What goes wrong:** Market breadth indicators (McClellan Oscillator, TRIN, New Highs-Lows, % Above SMA) require advance/decline counts for entire index constituents — this is **index-level data**, not individual ticker data.
**Why it happens:** yfinance provides constituent-level OHLCV but not real-time advance/decline counts.
**How to avoid:** For TA-06, fetch yfinance OHLCV for all FTSE 100 / S&P 500 constituent tickers (already in seed list from Phase 2), then compute advance/decline/breadth metrics in Python from those bars. Use the last N bars to compute rolling breadth. This is a batch computation, not a streaming one.
**Warning signs:** Attempting to look up "advance-decline line" from a single API endpoint — no free API provides this pre-aggregated.

### Pitfall 6: pandas-ta Column Name Conflicts
**What goes wrong:** `pandas_ta.rsi(close)` returns a `pd.Series` with a name like `RSI_14`. If you call multiple pandas-ta functions on the same DataFrame, column names can collide or pandas issues warnings about duplicate column names.
**Why it happens:** pandas-ta uses period-parameterized names by default.
**How to avoid:** Call pandas-ta functions on isolated Series objects, not the full DataFrame. Extract the result as a numpy array immediately: `result = pandas_ta.rsi(close_series, length=14).to_numpy()`.

### Pitfall 7: GARCH arch Library Convergence Failures
**What goes wrong:** `arch_model(returns).fit()` raises `ConvergenceWarning` or returns `nan` parameters for assets with very short history or flat price series.
**Why it happens:** MLE optimization fails when there is insufficient variance in returns.
**How to avoid:** Wrap in try/except; require minimum 100 bars before running GARCH; check `res.params` for NaN before returning. Return `null` GARCH result gracefully when fitting fails.

### Pitfall 8: Fibonacci PriceLines vs LineSeries
**What goes wrong:** Using multiple zero-length `LineSeries` to draw horizontal Fibonacci levels is technically possible but adds series instances to the chart, which are visible in the legend and harder to remove atomically.
**Why it happens:** Developers reach for `addSeries` when `createPriceLine` is the right tool.
**How to avoid:** Use `candleSeries.createPriceLine({price, title, color})` for Fibonacci and pivot horizontal levels. `PriceLines` are attached to an existing series, do not create a new series in the legend, and are removed by calling `candleSeries.removePriceLine(line)`.

---

## Code Examples

Verified patterns from official sources and project codebase:

### TA-Lib GARCH Wrapper (arch library)
```python
# Source: https://arch.readthedocs.io/en/latest/univariate/univariate_volatility_modeling.html
from arch import arch_model
import numpy as np

def compute_garch_volatility(closes: np.ndarray) -> dict:
    """Returns GARCH(1,1) fitted params and 1-day forward vol estimate."""
    returns = np.diff(np.log(closes)) * 100  # percentage log returns
    if len(returns) < 100:
        return {"error": "insufficient data"}
    try:
        am = arch_model(returns, vol='Garch', p=1, q=1, dist='Normal')
        res = am.fit(disp='off')  # suppress convergence output
        forecast = res.forecast(horizon=1)
        vol_1d = float(np.sqrt(forecast.variance.values[-1, 0])) / 100  # back to decimal
        return {"omega": float(res.params['omega']), "alpha": float(res.params['alpha[1]']),
                "beta": float(res.params['beta[1]']), "vol_1d_forward": vol_1d}
    except Exception:
        return {"error": "garch fitting failed"}
```

### lightweight-charts v5 Oscillator Sub-Pane (TypeScript)
```typescript
// Source: https://tradingview.github.io/lightweight-charts/tutorials/how_to/panes
// Project CandleChart.tsx uses chart.addSeries(CandlestickSeries) pattern — same for LineSeries
import { LineSeries, HistogramSeries } from 'lightweight-charts';

// Add RSI to pane 1 (auto-creates if doesn't exist)
const rsiSeries = chartRef.current.addSeries(LineSeries, {
  color: '#F5A623',
  lineWidth: 1,
}, 1);

// Set pane proportions: candles 75%, each oscillator 25%
const totalH = containerRef.current.clientHeight;
chartRef.current.panes()[1]?.setHeight(Math.floor(totalH * 0.25));

rsiSeries.setData(rsiData); // [{time, value}]
```

### Nightly Pattern Stats Celery Task Structure
```python
# Source: existing ingestion/celery_app.py pattern + D-07/D-08 decisions
from scipy.stats import ttest_1samp

@app.task
def compute_nightly_pattern_stats():
    """For each ticker × CDL pattern, compute win rate (next-bar close-to-close) + p-value."""
    TICKERS = ["AAPL", "LLOY.L", ...]  # seed list
    CDL_FUNCS = {"CDLHAMMER": talib.CDLHAMMER, "CDLENGULFING": talib.CDLENGULFING, ...}
    for ticker in TICKERS:
        ohlcv = fetch_ohlcv_from_db(ticker, interval="1d")
        opens, highs, lows, closes = ohlcv
        for pattern_name, func in CDL_FUNCS.items():
            signals = func(opens, highs, lows, closes)
            # signals: +100 = bullish, -100 = bearish, 0 = not detected
            pattern_bars = np.where(signals != 0)[0]
            if len(pattern_bars) < 30:  # D-10: n >= 30
                continue
            # Out-of-sample: use last 30% of history only
            split = int(len(closes) * 0.7)
            oos_bars = pattern_bars[pattern_bars >= split]
            outcomes = [(1 if closes[i+1] > closes[i] else 0)
                        for i in oos_bars if i + 1 < len(closes)]
            if len(outcomes) < 30:
                continue
            win_rate = sum(outcomes) / len(outcomes)
            _, p_value = ttest_1samp(outcomes, popmean=0.5)
            # upsert to ta_pattern_stats
```

### Chart Pattern Detection (Head & Shoulders skeleton)
```python
# Source: scipy.signal.find_peaks docs + D-16/D-17 decisions
from scipy.signal import find_peaks
import numpy as np

def detect_head_and_shoulders(highs: np.ndarray, volumes: np.ndarray) -> list:
    """Returns list of {start_idx, end_idx, head_idx, confidence}."""
    prominence_threshold = highs.std() * 0.5
    peaks, _ = find_peaks(highs, prominence=prominence_threshold, distance=5)
    results = []
    for i in range(len(peaks) - 2):
        ls, head, rs = peaks[i], peaks[i+1], peaks[i+2]
        # Rule: head must be highest; shoulders within 5% of each other
        if highs[head] <= highs[ls] or highs[head] <= highs[rs]:
            continue
        shoulder_diff = abs(highs[ls] - highs[rs]) / highs[ls]
        if shoulder_diff > 0.05:
            continue
        # Volume: typically diminishes on right shoulder
        vol_confirmation = float(volumes[rs] < volumes[ls])
        symmetry = 1.0 - shoulder_diff / 0.05
        confidence = 0.7 * symmetry + 0.3 * vol_confirmation
        results.append({"start_idx": int(ls), "end_idx": int(rs),
                        "head_idx": int(head), "confidence": round(confidence, 3)})
    return results
```

### TimescaleDB `ta_pattern_stats` Table Schema
```python
# Source: existing models/ohlcv.py pattern + D-07/D-08/D-09/D-10 decisions
class TaPatternStats(Base):
    __tablename__ = "ta_pattern_stats"
    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)  # nightly compute time
    ticker = Column(String(20), primary_key=True, nullable=False)
    pattern_name = Column(String(50), primary_key=True, nullable=False)  # e.g. "CDLHAMMER"
    interval = Column(String(5), primary_key=True, nullable=False, default="1d")
    n_occurrences = Column(Integer, nullable=False)
    win_rate = Column(Numeric(5, 4))   # e.g. 0.6524
    p_value = Column(Numeric(10, 6))   # e.g. 0.031
    sample_size = Column(Integer)      # out-of-sample n
    out_of_sample = Column(Boolean, default=True)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TA-Lib requires C lib apt-get in Docker | TA-Lib 0.6.5+ ships binary wheels with bundled C lib | 2024 (0.6.5 release) | Single-line pip install in Docker — no multi-stage build needed |
| lightweight-charts `addLineSeries()` | `chart.addSeries(LineSeries, opts, paneIndex)` | v5.0 (2024) | Must use new API; project already uses correct v5 pattern in CandleChart.tsx |
| lightweight-charts `series.setMarkers()` | `createSeriesMarkers(series, markers)` | v5.0 (2024) | Already handled correctly in CandleChart.tsx |
| Manual pane management with separate chart instances | `chart.addSeries(..., paneIndex)` + `chart.panes()[n].setHeight()` | v5.0 (2024) | Single chart instance handles all panes with synchronized time axis |

**Deprecated/outdated:**
- TA-Lib 0.4.x: Requires separate C library installation. Use 0.6.8+ (bundled wheels).
- pandas-ta `df.ta.rsi()` extension syntax: Still works but prefer calling functions directly on Series objects to avoid DataFrame mutation side effects.

---

## Open Questions

1. **Market Breadth Constituent Data Source (TA-06)**
   - What we know: yfinance provides OHLCV per ticker; Phase 2 has a ticker seed list
   - What's unclear: Is the current seed list large enough to compute meaningful McClellan Oscillator? S&P 500 breadth needs 500 tickers; FTSE 100 needs 100.
   - Recommendation: Plan 04-04 should explicitly enumerate the constituent list and verify the seed list covers at least FTSE 100 and S&P 500. If the seed list is only 10-20 tickers, McClellan/TRIN will be meaningless — document limitation in UI as "index breadth not available (insufficient constituents)".

2. **VWAP on Daily Bars**
   - What we know: VWAP is theoretically an intraday metric (reset at session open). On daily bars there is no "session open accumulation."
   - What's unclear: Whether to compute daily VWAP as `sum(typical_price * volume) / sum(volume)` over a rolling N-day window or disable VWAP for daily/weekly timeframes.
   - Recommendation: Implement VWAP for intraday (1h/4h) bars only (session-cumulative from first bar of day). For daily timeframe, show rolling 20-day VWAP as a reasonable substitute. Document clearly in tooltip.

3. **CVD (Cumulative Volume Delta) Without Tick Data**
   - What we know: CVD requires bid/ask volume split per bar. yfinance only provides total volume.
   - What's unclear: Whether to approximate CVD using close position within bar range as a proxy.
   - Recommendation: Approximate CVD as `(close - low)/(high - low) * volume - (high - close)/(high - low) * volume` per bar (this is the Chaikin A/D multiplier applied to volume). Document clearly as approximation — not true order-flow CVD. True CVD requires tick data (Phase 7 Crypto via Binance is the only source that provides it).

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | `backend/conftest.py` (exists) |
| Quick run command | `pytest backend/tests/analysis/ -x -q` |
| Full suite command | `pytest backend/tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TA-01 | SMA/EMA/HMA return correct array shapes; Golden Cross detected | unit | `pytest backend/tests/analysis/test_indicators.py::test_moving_averages -x` | Wave 0 |
| TA-02 | RSI values in [0,100]; MACD histogram = MACD - signal | unit | `pytest backend/tests/analysis/test_indicators.py::test_momentum -x` | Wave 0 |
| TA-03 | ADX > 0; SAR alternates correctly; SuperTrend direction changes on trend flip | unit | `pytest backend/tests/analysis/test_indicators.py::test_trend_strength -x` | Wave 0 |
| TA-04 | BBands: upper > middle > lower; ATR > 0; GARCH fit returns omega/alpha/beta | unit | `pytest backend/tests/analysis/test_indicators.py::test_volatility -x` | Wave 0 |
| TA-05 | OBV cumulative; VWAP = sum(tp*v)/sum(v) | unit | `pytest backend/tests/analysis/test_indicators.py::test_volume -x` | Wave 0 |
| TA-06 | McClellan Oscillator = EMA19 - EMA39 of A-D | unit | `pytest backend/tests/analysis/test_indicators.py::test_breadth -x` | Wave 0 |
| TA-07 | Standard pivot PP = (H+L+C)/3; all 5 methods produce correct PP values | unit | `pytest backend/tests/analysis/test_pivot_points.py -x` | Wave 0 |
| TA-08 | 30D rolling correlation within [-1,1] | unit | `pytest backend/tests/analysis/test_indicators.py::test_intermarket -x` | Wave 0 |
| TA-09 | At least 3 CDL patterns detected on synthetic OHLCV; win rate in [0,1]; p-value in [0,1] | unit | `pytest backend/tests/analysis/test_patterns.py -x` | Wave 0 |
| TA-10 | H&S detected on synthetic 3-peak series; Double Top on 2-peak series | unit | `pytest backend/tests/analysis/test_chart_patterns.py -x` | Wave 0 |
| TA-11 | Fibonacci levels 0.236/0.382/0.5/0.618/0.786/1.0/1.618/2.618 computed correctly for given swing high/low | unit | `pytest backend/tests/analysis/test_fibonacci.py -x` | Wave 0 |
| TA-12 | Wave 3 shortest check raises validation flag; Wave 4 overlap check works | unit | `pytest backend/tests/analysis/test_elliott_wave.py -x` | Wave 0 |
| TA-13 | t-test p-value < 0.05 for 70% win rate with n=50; "insufficient data" for n<30 | unit | `pytest backend/tests/analysis/test_patterns.py::test_stat_significance -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/analysis/ -x -q`
- **Per wave merge:** `pytest backend/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/analysis/test_indicators.py` — covers TA-01 through TA-08 grouped tests
- [ ] `backend/tests/analysis/test_patterns.py` — covers TA-09, TA-13 (candlestick patterns + stats)
- [ ] `backend/tests/analysis/test_chart_patterns.py` — covers TA-10 (chart pattern detection)
- [ ] `backend/tests/analysis/test_pivot_points.py` — covers TA-07 (all 5 pivot methods)
- [ ] `backend/tests/analysis/test_fibonacci.py` — covers TA-11 level math
- [ ] `backend/tests/analysis/test_elliott_wave.py` — covers TA-12 validation rules

---

## Project Constraints (from CLAUDE.md)

- **Stack:** FastAPI · React/Vite · TimescaleDB · Redis · Celery · Docker Compose. Do not deviate.
- **Free tier only:** No paid API calls. All indicator computation is internal math on existing OHLCV data — no external API calls. TA-Lib, pandas-ta, arch, scipy are all open-source — compliant.
- **UK/LSE tickers:** `.L` suffix must work everywhere US tickers do. TA-Lib CDL patterns, indicator math, and chart patterns are ticker-agnostic (operate on OHLCV arrays). No special handling needed. Verify in tests.
- **FinBERT local:** Not relevant to Phase 4 (no NLP).
- **TimescaleDB persistence:** Per CLAUDE.md, nothing is cache-only. Pattern stats and pivot points MUST be stored in TimescaleDB (ta_pattern_stats, pivot_points tables). Standard indicator values are computed on-demand and Redis-cached but not persisted — this is compliant because OHLCV data (the source) is already persisted.
- **BRIEF.md:** Read at session start. Phase 4 agents should read 04-CONTEXT.md (this phase) and relevant spec sections only.
- **Bloomberg spec §8:** The authoritative spec for all indicator groups A-H, candlestick patterns (§K), chart patterns (§L), Fibonacci (§M), Elliott Wave (§N), statistical layer (§O). Plans MUST read §8 in full before implementing any backend computation task.

---

## Sources

### Primary (HIGH confidence)
- `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md` §8 — Full math engine spec, indicator groups A-H, §K (candlestick), §L (chart patterns), §M (Fibonacci), §N (Elliott Wave), §O (stats layer)
- `.planning/phases/04-technical-analysis-engine/04-CONTEXT.md` — All locked decisions D-01 through D-19
- Project codebase (CandleChart.tsx, requirements.txt, celery_app.py, black_scholes.py, alembic migrations) — verified integration points
- `pip3 index versions TA-Lib` result — TA-Lib 0.6.8 current (verified 2026-03-29)
- `pip3 index versions arch` result — arch 8.0.0 current (verified 2026-03-29)
- [lightweight-charts Panes tutorial](https://tradingview.github.io/lightweight-charts/tutorials/how_to/panes) — `addSeries(Type, opts, paneIndex)`, `panes()[n].setHeight()`
- [arch GARCH docs](https://arch.readthedocs.io/en/latest/univariate/univariate_volatility_modeling.html) — `arch_model(returns).fit()`

### Secondary (MEDIUM confidence)
- [TA-Lib PyPI page](https://pypi.org/project/TA-Lib/) — 0.6.5+ binary wheels confirmed
- [pandas-ta PyPI](https://pypi.org/project/pandas-ta/) — version 0.4.71b0
- [lightweight-charts IChartApi](https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi) — `addPane()`, `paneIndex` parameter
- [TA-Lib binary wheel confirmation](https://deepwiki.com/TA-Lib/ta-lib-python/1.1-installation) — manylinux_2_28 wheels available from 0.6.5+

### Tertiary (LOW confidence — needs verification at implementation time)
- scipy.signal.find_peaks chart pattern approach — supported by multiple published implementations (see Medium / Analyzing Alpha articles) but exact confidence scoring formula is our own design
- pandas-ta column naming behavior — based on usage patterns, verify at implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — TA-Lib version verified via pip, arch verified via pip, lightweight-charts version in package.json confirmed
- Architecture: HIGH — follows established project patterns exactly (celery_app.py, alembic migrations, analysis/ module, CandleChart.tsx)
- Pitfalls: HIGH — TA-Lib NaN padding, v5 API changes, and GARCH convergence are well-documented; TimescaleDB hypertable pattern verified from existing migrations

**Research date:** 2026-03-29
**Valid until:** 2026-04-29 (stable library versions, 30-day window)
