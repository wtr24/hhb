# Phase 3: Equity Overview - Research

**Researched:** 2026-03-28
**Domain:** React frontend assembly + FastAPI backend routes + lightweight-charts v5 + Finnhub WebSocket + Black-Scholes pricer + options chain data
**Confidence:** MEDIUM-HIGH (most APIs verified against live docs; Finnhub free-tier boundary has MEDIUM confidence due to JS-heavy pricing page)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Bloomberg fixed-height grid layout. Nothing scrolls. Layout zones:
  - Top strip (full width): Live quote bar — ticker, price, change, change%, volume, stale badge
  - Left panel (~60% width): 4-panel simultaneous chart view (W/D/4H/1H)
  - Right sidebar (~40% width): Fundamentals → Short interest → Insider clustering, stacked
  - Bottom row (full width): Options chain (~60%) + Company news feed (~40%)
- **D-02:** Stale data indicator — amber badge on any panel with `stale: true`
- **D-03:** Command bar `TICKER> ____` terminal-style, amber cursor, Enter to load, auto-uppercase
- **D-04:** On Enter, all panels refresh simultaneously. No history/autocomplete in Phase 3
- **D-05:** Default 4-panel simultaneous display (Weekly / Daily / 4H / 1H)
- **D-06:** Click panel to expand full-width with timeframe selector (1D/1W/1M/1Y/5Y). Escape or click to collapse
- **D-07:** Earnings date markers on all chart panels as vertical lines
- **D-08:** Options chain: calls left, puts right, strike centre column
- **D-09:** IV surface as compact heatmap above options table; IV percentile rank badge
- **D-10:** Greeks per row (delta, gamma, vega, theta). Calculated client-side or backend — Claude's discretion
- **D-11:** Company news feed — scrollable, headline/source/timestamp/sentiment badge, 5m refresh
- **D-12:** GBP toggle button; uses GBP/USD from fx_rates table when active
- **D-13:** `.L` suffix and `^FTSE`/`^FTMC` work identically via yfinance

### Claude's Discretion

- Exact grid CSS (CSS Grid vs Flexbox, panel sizing)
- Black-Scholes implementation location (backend endpoint vs frontend JS)
- Loading states (skeleton vs spinner vs dim + stale badge)
- Insider clustering visualisation (table vs mini bar chart)
- Short interest display format
- WebSocket reconnect / error handling in frontend

### Deferred Ideas (OUT OF SCOPE)

- Ticker autocomplete / search history (Phase 12)
- Level 2 order book
- Analyst consensus estimates
- Real-time options Greeks streaming (snapshot only in Phase 3)
- Global command bar (Phase 12)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EQUITY-01 | Live quote (bid/ask/last/volume) with 15s refresh via Finnhub WebSocket | Finnhub WS schema documented; US-only free tier confirmed; LSE fallback via yfinance polling |
| EQUITY-02 | Multi-timeframe chart: Weekly/Daily/4H/1H simultaneously | lightweight-charts v5 multi-chart pattern; 4x `createChart` on separate divs |
| EQUITY-03 | Candlestick chart with timeframe selector 1D/1W/1M/1Y/5Y | `chart.timeScale().setVisibleRange()` + `fitContent()` confirmed |
| EQUITY-04 | Earnings dates as vertical markers on price chart | yfinance `get_earnings_dates()` + `createSeriesMarkers()` in v5 |
| EQUITY-05 | Dividend ex-dates as vertical markers | yfinance `.dividends` property returns ex-dates |
| EQUITY-06 | Fundamentals panel (P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap, 24h cache) | Existing `/api/quote/{ticker}` returns fundamentals; ROE missing — add via yfinance `info` |
| EQUITY-07 | Short interest (% float, short ratio, days to cover) via Finnhub | Finnhub `/stock/short-interest` endpoint; US-only on free tier; LSE fallback unclear |
| EQUITY-08 | Insider transaction clustering (buy/sell ratio, 2-week window, 10b5-1 filter) | Finnhub `/stock/insider-transactions`; US-only on free tier confirmed |
| EQUITY-09 | Options chain with Black-Scholes Greeks, IV surface, IV percentile | yfinance `.option_chain()` for data; scipy Black-Scholes backend; canvas heatmap |
| EQUITY-10 | Company news feed via Finnhub REST, 5m refresh | Finnhub `/company-news` confirmed free; sentiment from Finnhub score field |
| EQUITY-11 | FX-adjusted P&L toggle — GBP/USD from fx_rates table | FX endpoint deferred from Phase 2; must add `/api/fx/USDGBP` in Phase 3 |
| EQUITY-12 | LSE tickers (.L suffix, ^FTSE, ^FTMC) fully supported | yfinance handles .L natively; Finnhub WS LSE = premium only; fallback needed |
</phase_requirements>

---

## Summary

Phase 3 is a large UI + backend assembly phase. The backend side requires: adding scipy/numpy to requirements.txt for Black-Scholes; a new `/api/equity/{ticker}` composite endpoint that fetches short interest, insider data, options chain, and news from Finnhub REST; a Celery task for Finnhub REST ingestion; and a `/api/fx/USDGBP` endpoint pulled forward from the Phase 2 deferral. The frontend side requires: replacing the `[EQUITY] MODULE READY` stub with a full Bloomberg-grid layout; four simultaneous lightweight-charts v5 chart instances; a custom Black-Scholes pricer running on backend or frontend; and a pure-canvas IV surface heatmap.

**Critical discovery: The project has lightweight-charts at v5.1.0, not v4.** The v5 API differs significantly from v4. `addCandlestickSeries()` is gone — use `chart.addSeries(CandlestickSeries, opts)`. Markers moved to `createSeriesMarkers(series, markers)` imported separately.

**Critical discovery: Finnhub WebSocket free tier is US stocks + forex + crypto only.** LSE tickers (LLOY.L, BARC.L) are NOT streamed on free tier. For EQUITY-01 + EQUITY-12, LSE quotes must fall back to yfinance polling at 15s intervals proxied through the existing backend mechanism.

**Critical discovery: FMP earnings calendar requires a paid plan.** For EQUITY-04, use yfinance `get_earnings_dates()` as primary source. FMP is only needed for fundamentals P/E+EV/EBITDA (already in the Phase 2 quote endpoint).

**Primary recommendation:** Backend computes Black-Scholes Greeks via scipy (not frontend JS) — consistent with existing Python scipy math stack and avoids shipping a 20KB math library to the browser.

---

## Finnhub Integration (WebSocket + REST)

### WebSocket Connection

**Confidence: HIGH** — verified from official Finnhub documentation and community code samples.

| Property | Value |
|----------|-------|
| URL | `wss://ws.finnhub.io?token={FINNHUB_API_KEY}` |
| Auth | Token as query param |
| Subscribe | `{"type":"subscribe","symbol":"AAPL"}` |
| Unsubscribe | `{"type":"unsubscribe","symbol":"AAPL"}` |
| Max symbols (free) | 50 concurrent subscriptions |
| Connection limit | 1 connection per API key |

**Message schema (trade data):**
```json
{
  "type": "trade",
  "data": [
    {
      "s": "AAPL",
      "p": 189.50,
      "t": 1575526691134,
      "v": 0.011467,
      "c": ["1"]
    }
  ]
}
```

Fields: `s` = symbol, `p` = last price, `t` = UNIX ms timestamp, `v` = volume, `c` = trade conditions.

**Free tier symbol support:**
- US stocks: YES (full WebSocket support)
- Forex pairs: YES
- Crypto (prefix `BINANCE:`): YES
- **LSE tickers (LLOY.L, BARC.L): NO — international stocks require premium tier**

**Implication for EQUITY-01 + EQUITY-12:** The live quote strip for US tickers can use Finnhub WebSocket fanout via the existing `quotes:{ticker}` Redis pub/sub channel. For LSE tickers, the Celery beat `ingest_ticker` task (runs every 5 minutes with yfinance) provides the data, but the 15s refresh cadence required by EQUITY-01 cannot be met for LSE tickers at zero cost. **Resolution: For LSE tickers, the backend should trigger yfinance ingest on subscribe (like the existing D-11 on-demand trigger) and push updates at 5m intervals via the existing WebSocket channel. The stale badge handles the UX gap. This satisfies EQUITY-12 (LSE support) with a documented limitation.**

### Finnhub REST Endpoints (Free Tier)

**Confidence: MEDIUM** — Sources confirm free tier generosity but exact endpoint-level gating requires empirical testing.

| Endpoint | Path | Free Tier | Response Shape |
|----------|------|-----------|----------------|
| Quote | `/quote?symbol=AAPL` | YES | `c` (current), `d` (change), `dp` (change%), `h`, `l`, `o`, `pc`, `t` |
| Company News | `/company-news?symbol=AAPL&from=&to=` | YES | array of `{headline, source, url, datetime, summary, sentiment}` |
| Insider Transactions | `/stock/insider-transactions?symbol=AAPL` | **LIKELY YES (US only)** | See schema below |
| Short Interest | `/stock/short-interest?symbol=AAPL` | **UNCERTAIN — test required** | `shortInterest`, `date`, `sharesOutstanding` |
| Basic Financials | `/stock/metric?symbol=AAPL&metric=all` | YES | nested `metric` object with 100+ fields |
| Earnings Calendar | `/calendar/earnings?from=&to=` | YES | `earningsCalendar` array |

**Insider transactions response fields:**
```json
{
  "data": [
    {
      "name": "Cook Timothy D",
      "share": 100000,
      "change": 100000,
      "filingDate": "2024-01-15",
      "transactionDate": "2024-01-12",
      "transactionCode": "S",
      "transactionPrice": 189.50,
      "isDerivative": false
    }
  ],
  "symbol": "AAPL"
}
```

`transactionCode`: `"P"` = purchase, `"S"` = sale, `"A"` = award, `"D"` = disposition, `"F"` = tax payment (10b5-1 proxy — filter these)

**Rate limits:** 60 requests/minute on free tier. All Finnhub REST calls must use the existing `check_rate_limit("finnhub")` token bucket.

**LSE on Finnhub REST:** Short interest and insider transactions for LSE tickers are premium-only based on confirmed pattern that international market data requires paid tier. Company news for LSE tickers may work on free tier (verify empirically). For EQUITY-07 and EQUITY-08, LSE tickers should show "Not available on free tier" in the panel rather than erroring.

---

## lightweight-charts v5

**Confidence: HIGH** — Verified against official TradingView documentation and migration guide.

### Critical: Project is on v5.1.0, NOT v4

The `package.json` shows `"lightweight-charts": "^5.1.0"`. All implementation must use v5 API.

### v5 Breaking Changes from v4

| Feature | v4 API | v5 API |
|---------|--------|--------|
| Series creation | `chart.addCandlestickSeries(opts)` | `chart.addSeries(CandlestickSeries, opts)` |
| Series import | Implicit | `import { CandlestickSeries } from 'lightweight-charts'` |
| Markers | `series.setMarkers([...])` | `createSeriesMarkers(series, markers)` — separate import |
| Watermarks | `createChart` option | `createTextWatermark(pane, opts)` |
| Plugin interfaces | `ISeriesPrimitivePaneView` | `IPrimitivePaneView` |

### Core API for Phase 3

**Installation:** already in `package.json` at `^5.1.0`

**Chart creation (v5):**
```typescript
import { createChart, CandlestickSeries, ColorType } from 'lightweight-charts';
import { createSeriesMarkers } from 'lightweight-charts';

// In useEffect, after ref is mounted:
const chart = createChart(containerRef.current, {
  layout: {
    background: { type: ColorType.Solid, color: '#0a0a0a' },
    textColor: '#ff9900',
  },
  grid: {
    vertLines: { color: '#1a1a1a' },
    horzLines: { color: '#1a1a1a' },
  },
  width: containerRef.current.clientWidth,
  height: containerRef.current.clientHeight,
});

const candleSeries = chart.addSeries(CandlestickSeries, {
  upColor: '#00d084',
  downColor: '#ff4444',
  borderVisible: false,
  wickUpColor: '#00d084',
  wickDownColor: '#ff4444',
});

candleSeries.setData(ohlcvData); // [{time: 'YYYY-MM-DD', open, high, low, close}]

// Cleanup
return () => chart.remove();
```

**Earnings/dividend markers (v5):**
```typescript
import { createSeriesMarkers } from 'lightweight-charts';

const markers = earningsDates.map(d => ({
  time: d, // 'YYYY-MM-DD'
  position: 'aboveBar',
  color: '#ff9900',
  shape: 'arrowDown',
  text: 'E',
}));

const dividendMarkers = dividendDates.map(d => ({
  time: d,
  position: 'belowBar',
  color: '#00d084',
  shape: 'circle',
  text: 'D',
}));

const markersInstance = createSeriesMarkers(candleSeries, [...markers, ...dividendMarkers]);
// To update markers: markersInstance.setMarkers([...newMarkers])
```

**Time range selector (for expanded panel D-06):**
```typescript
// Fit all data
chart.timeScale().fitContent();

// Set specific range (1D, 1W, 1M, 1Y, 5Y)
const now = Math.floor(Date.now() / 1000);
chart.timeScale().setVisibleRange({
  from: now - (days * 86400),
  to: now,
});
```

**Data time field:** Accepts both `'YYYY-MM-DD'` string and Unix timestamp (seconds). For intraday (4H/1H), use Unix timestamps.

### Multi-Chart Layout Pattern

**4 simultaneous charts on one page — React pattern:**

```typescript
// CandleChart.tsx — single chart component
const CandleChart = ({ data, markers, label, onExpand }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    chartRef.current = createChart(containerRef.current, TERMINAL_CHART_OPTIONS);
    seriesRef.current = chartRef.current.addSeries(CandlestickSeries, CANDLE_STYLE);
    return () => chartRef.current?.remove();
  }, []); // Only mount/unmount

  useEffect(() => {
    seriesRef.current?.setData(data);
    chartRef.current?.timeScale().fitContent();
  }, [data]); // Update data without remounting

  return <div ref={containerRef} onClick={onExpand} className="..."/>;
};

// In EquityModule — render 4 instances
<div className="grid grid-cols-2 grid-rows-2 h-full">
  {TIMEFRAMES.map(tf => (
    <CandleChart key={tf} label={tf} data={chartData[tf]} markers={allMarkers} />
  ))}
</div>
```

**Critical:** Chart is created once in `useEffect([], [])` with empty deps. Data updates go through `seriesRef.current.setData()` in a separate `useEffect([data])`. Never recreate the chart on data change — this causes flicker and loses zoom state.

**Resize handling:**
```typescript
useEffect(() => {
  const obs = new ResizeObserver(() => {
    chartRef.current?.applyOptions({
      width: containerRef.current!.clientWidth,
      height: containerRef.current!.clientHeight,
    });
  });
  obs.observe(containerRef.current!);
  return () => obs.disconnect();
}, []);
```

---

## Options Chain Data Sources

**Confidence: HIGH** — yfinance options API is well-documented and free.

### Primary Source: yfinance

`ticker.options` → list of expiry date strings
`ticker.option_chain(expiry)` → `.calls` and `.puts` DataFrames

**DataFrame columns available:**
```
contractSymbol, lastTradeDate, strike, lastPrice, bid, ask,
change, percentChange, volume, openInterest, impliedVolatility
```

**Critical: Greeks NOT provided by yfinance.** `impliedVolatility` IS provided (Yahoo Finance pre-computes it). Greeks (delta, gamma, vega, theta) must be computed from Black-Scholes using the provided IV.

**LSE options:** yfinance returns option chains for US-listed tickers. UK stocks (LLOY.L, BARC.L) typically have no option chains — they trade on different exchanges. For Phase 3, the options panel should show "Options not available for this ticker" for LSE-suffix tickers.

**Expiry structure for IV surface:**
- Gather all expiries: `ticker.options` → e.g. `['2025-04-25', '2025-05-16', '2025-06-20', ...]`
- For each expiry fetch `ticker.option_chain(expiry)` — costly on free tier
- Limit to nearest 5-6 expiries to stay within rate limits
- Pivot: rows = strikes, columns = expiry dates, values = IV → IV surface grid

**Rate limit concern:** Each `option_chain(expiry)` call is one yfinance request. At 6 expiries, that's 6 calls per ticker load. The existing yfinance token bucket (60/60s) handles this.

---

## Black-Scholes Implementation

**Confidence: HIGH** — Standard mathematical formula, well-established Python implementations.

### Recommendation: Backend Python Endpoint

**Decision rationale (Claude's discretion D-10):** Implement Black-Scholes on the backend in `backend/analysis/black_scholes.py`. Reasons:
1. scipy (required) is not currently in `requirements.txt` — needs one addition
2. Avoids shipping 20KB+ of math to browser
3. Consistent with existing Python math stack (numpy, pandas already present)
4. Single source of truth — same Greeks used in future screener IV percentile (Phase 8)
5. Easier to validate and test

**Dependencies to add to `backend/requirements.txt`:**
```
scipy>=1.11.0
```
numpy is already a transitive dependency via pandas. scipy adds `scipy.stats.norm` which is all that's needed.

**Black-Scholes implementation:**
```python
# backend/analysis/black_scholes.py
from scipy.stats import norm
import numpy as np

def bs_greeks(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> dict:
    """
    Compute Black-Scholes price and Greeks.
    S = current stock price
    K = strike price
    T = time to expiry in years (e.g. 30/365)
    r = risk-free rate (e.g. 0.045 for 4.5%)
    sigma = implied volatility (from yfinance impliedVolatility column)
    option_type = 'call' or 'put'
    """
    if T <= 0 or sigma <= 0:
        return {'delta': None, 'gamma': None, 'vega': None, 'theta': None, 'price': None}

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # per 1% IV move

    return {
        'price': round(price, 4),
        'delta': round(delta, 4),
        'gamma': round(gamma, 4),
        'vega': round(vega, 4),
        'theta': round(theta, 4),
    }
```

**Risk-free rate:** Use the current US 3-month T-bill rate. The yield curve is already being ingested. A hardcoded fallback of `0.045` (4.5%) is acceptable for Phase 3 with a comment noting it should pull from the yield curve table.

**API endpoint:** `GET /api/equity/options/{ticker}` — fetches chain from yfinance, computes Greeks for all rows, returns enriched DataFrame as JSON. Cache with 15m TTL (options data is not real-time on free tier anyway).

---

## FMP Free Tier Capabilities

**Confidence: MEDIUM** — Based on multiple WebSearch sources; FMP pricing page returned 403.

| Endpoint | Free Tier Available | Limit | Notes |
|----------|--------------------|----|-------|
| Company profile | YES | 250 req/day | P/E, market cap, sector |
| Key metrics (ratios) | YES | 250 req/day | P/E, EV/EBITDA, ROE, Debt/Equity |
| Earnings calendar | **NO — requires paid plan** | N/A | Confirmed by multiple sources |
| Dividends calendar | UNCERTAIN | 250 req/day | Page returned 403; test required |
| Income statement | YES | 250 req/day | Historical |
| Balance sheet | YES | 250 req/day | Historical |

**Implication for Phase 3:**
- EQUITY-06 (fundamentals): FMP is NOT needed — yfinance already provides P/E, market_cap, and the `/api/quote/{ticker}` endpoint from Phase 2 returns these. Add ROE and EV/EBITDA to the yfinance ingest (available via `ticker.info` dict).
- EQUITY-04 (earnings dates): Do NOT use FMP earnings calendar. Use **yfinance `get_earnings_dates()`** as primary source. Finnhub `/calendar/earnings` (confirmed free) as secondary cross-reference.
- EQUITY-05 (dividend dates): Use **yfinance `.dividends`** property — returns Series with ex-dates as index. Free, reliable, works for .L tickers.
- FMP 250 req/day limit: at 250/day, FMP is budget-scarce. For Phase 3, avoid FMP entirely and rely on yfinance + Finnhub free endpoints.

---

## IV Surface Rendering

**Confidence: MEDIUM** — Standard approach; no existing project code to reference.

### Approach: HTML Canvas in React

The IV surface is a compact heatmap: rows = strike prices, columns = expiry dates, cells = IV value colour-coded. No heavy charting library needed.

**Implementation pattern:**
```typescript
// IVSurface.tsx
const IVSurface = ({ surfaceData }: { surfaceData: IVGrid }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx || !surfaceData) return;

    const { strikes, expiries, ivMatrix, minIV, maxIV } = surfaceData;
    const cellW = canvasRef.current!.width / expiries.length;
    const cellH = canvasRef.current!.height / strikes.length;

    strikes.forEach((strike, row) => {
      expiries.forEach((expiry, col) => {
        const iv = ivMatrix[row][col];
        const t = (iv - minIV) / (maxIV - minIV); // 0-1 normalised
        ctx.fillStyle = ivToColor(t); // amber gradient dark->bright
        ctx.fillRect(col * cellW, row * cellH, cellW - 1, cellH - 1);
      });
    });
  }, [surfaceData]);

  return <canvas ref={canvasRef} width={400} height={120} className="w-full"/>;
};

// Color scale: dark background (#1a1a1a) → amber (#ff9900) → red (#ff4444)
function ivToColor(t: number): string {
  if (t < 0.5) {
    const r = Math.round(26 + (255-26) * (t*2));
    const g = Math.round(26 + (153-26) * (t*2));
    const b = 26;
    return `rgb(${r},${g},${b})`;
  } else {
    const r = 255;
    const g = Math.round(153 - 153 * ((t-0.5)*2));
    const b = 26;
    return `rgb(${r},${g},${b})`;
  }
}
```

**IV Percentile Rank:**
```python
# backend: compute rank for the options endpoint
import pandas as pd

def iv_percentile_rank(current_iv: float, iv_history: list[float]) -> float:
    """Returns IV percentile rank (0-100): what % of historical IVs are below current."""
    below = sum(1 for v in iv_history if v < current_iv)
    return round(below / len(iv_history) * 100, 1)
```

IV history can be approximated from 52-week historical option IV if available, or from HV (historical volatility) as a proxy. For Phase 3, compute a simple percentile of the IV values across the current chain's strikes as a rough rank. A more accurate 52-week IV rank requires storing historical option data — defer to Phase 8 screener.

---

## LSE Ticker Gaps

**Confidence: HIGH** — confirmed from multiple sources.

| Feature | US Ticker (AAPL) | LSE Ticker (LLOY.L) | Gap Action |
|---------|-----------------|---------------------|-----------|
| yfinance OHLCV | Full | Full | None |
| yfinance fundamentals | Full | Full (limited) | None |
| yfinance dividends | Full | Full | None |
| yfinance earnings_dates | Full | Partial (UK reporting cycle differs) | Best-effort |
| yfinance options chain | Full | **Empty — LSE options not on Yahoo** | Show "N/A for UK stocks" |
| Finnhub WebSocket | YES | **NO — premium only** | Fallback to 5m yfinance poll |
| Finnhub short interest | YES (EQUITY-07) | **NO — premium only** | Show "US tickers only" |
| Finnhub insider transactions | YES (EQUITY-08) | **NO — premium only** | Show "US tickers only" |
| Finnhub company news | Likely YES | Likely YES (test required) | Test against LLOY.L |

**Design consequence for EQUITY-12:** The requirements say "LSE tickers fully supported" — this is achievable for charts, fundamentals, dividends, and news. It is NOT achievable for live WebSocket quotes (5m fallback instead), short interest, insider data, or options chain. The UI must clearly label these panels with a compact `[US ONLY]` or `[NOT AVAILABLE]` badge rather than silently failing.

**yfinance LSE specifics:**
- `yf.Ticker("LLOY.L")` works correctly
- `ticker.history(period='5y')` returns GBp (pence) prices, not GBP — note that LLOY.L is quoted in pence; dividing by 100 is required for GBP display in EQUITY-11
- `ticker.dividends` returns ex-dates and amounts
- `ticker.info` returns fundamentals in local currency (GBp for LSE)

---

## React Chart Integration Pattern

**Confidence: HIGH** — based on official lightweight-charts docs and confirmed patterns.

### Key Principle: Never Remount Charts

Remounting destroys zoom state, causes flicker, and leaks memory if cleanup is not perfect. The canonical pattern:

1. Create chart once in `useEffect(fn, [])` (empty deps)
2. Store chart and series instances in `useRef`
3. Push data updates via `seriesRef.current.setData(newData)` in `useEffect(fn, [data])`
4. Resize via `ResizeObserver` — never re-create chart on resize

### WebSocket Integration

```typescript
// useEquityWebSocket.ts
export function useEquityWebSocket(ticker: string) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!ticker) return;

    const ws = new WebSocket(`ws://localhost:8000/ws`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'subscribe',
        channels: [`quotes:${ticker}`, `fx:USDGBP`]
      }));
    };

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.channel === `quotes:${ticker}`) {
        setQuote(msg);
      }
    };

    // Reconnect on close (D-13 in 03-CONTEXT.md: Claude's discretion)
    ws.onclose = () => {
      setTimeout(() => { /* reconnect logic */ }, 3000);
    };

    return () => {
      ws.send(JSON.stringify({ action: 'unsubscribe', channels: [`quotes:${ticker}`] }));
      ws.close();
    };
  }, [ticker]); // Reconnect when ticker changes

  return quote;
}
```

### OHLCV Data Shape for lightweight-charts

The existing `GET /api/quote/{ticker}` returns latest candle only. For chart history, a new endpoint is needed: `GET /api/equity/history/{ticker}?period=1y&interval=1d` — fetches from TimescaleDB OHLCV table and returns array of `{time, open, high, low, close, volume}`.

**4H and 1H data:** yfinance provides intraday data but Yahoo Finance limits free intraday history to **60 days** for 1H interval and **730 days** for 4H. This is sufficient for the 4-panel display. Backend must store intraday OHLCV in the same OHLCV hypertable with interval metadata.

**Time format for intraday:** Use Unix timestamps (seconds), not date strings. lightweight-charts handles both, but Unix timestamps avoid timezone ambiguity for UK stocks.

### Escape Key Handler

Phase 2's `useKeyboard.ts` already handles number keys 1-6. For EQUITY-03 (Escape to collapse expanded chart panel), extend the existing `useKeyboard` or add a `document.addEventListener('keydown', ...)` inside the `EquityModule` component scoped to `activeTab === 'EQUITY'`.

---

## FX Endpoint Gap (Required for EQUITY-11)

**Confidence: HIGH** — confirmed from Phase 2 CONTEXT.md D-17 which explicitly flagged this.

Phase 2 deferred `/api/fx/{base}/{quote}`. Phase 3 EQUITY-11 (GBP toggle) requires a live GBP/USD rate from the `fx_rates` TimescaleDB table.

**New endpoint required in Phase 3:**
```
GET /api/fx/USDGBP
```

The fx_rates table is already populated by the Frankfurter ingestion task (Phase 2). The endpoint simply queries:
```sql
SELECT rate FROM fx_rates WHERE base='USD' AND quote='GBP'
ORDER BY time DESC LIMIT 1
```

This endpoint is simple enough to implement as part of the equity module backend plan. It can live in `backend/api/routes/equity.py` alongside the other Phase 3 equity endpoints.

---

## Common Pitfalls

### Pitfall 1: Using v4 lightweight-charts API
**What goes wrong:** `chart.addCandlestickSeries()` throws `TypeError: chart.addCandlestickSeries is not a function`
**Why it happens:** The project is at v5.1.0 which renamed the API
**How to avoid:** Always import `CandlestickSeries` and use `chart.addSeries(CandlestickSeries, opts)`
**Warning signs:** TypeScript will complain at compile time if the wrong method is called

### Pitfall 2: Recreating chart on every render
**What goes wrong:** Charts flash, zoom resets on every WebSocket message, memory leak
**Why it happens:** Putting chart creation inside render function or effect with data dependency
**How to avoid:** Empty dependency array `useEffect(fn, [])` for creation; separate effect for data updates
**Warning signs:** Chart container div re-mounting; ResizeObserver firing repeatedly

### Pitfall 3: Finnhub WebSocket connection limit
**What goes wrong:** Second browser tab opens, first tab's WebSocket gets kicked
**Why it happens:** Free tier allows only 1 connection per API key
**How to avoid:** The backend is already the single WebSocket connection point — frontend connects to backend `/ws`, NOT directly to Finnhub. Backend holds one Finnhub connection for all clients. This architecture is already correct in Phase 2.

### Pitfall 4: LSE price in pence vs pounds
**What goes wrong:** LLOY.L shows as 4400 (pence) when it should show 44.00 (GBP)
**Why it happens:** LSE stocks on Yahoo Finance are quoted in pence (GBX), not GBP
**How to avoid:** Detect LSE suffix; divide close price by 100 for display. Check `ticker.info['currency']` — returns 'GBp' for pence-denominated stocks
**Warning signs:** LLOY.L price appears ~100x too high

### Pitfall 5: FMP earnings calendar is paywalled
**What goes wrong:** 403 on `/api/v3/earning_calendar?apikey=FREE_KEY`
**Why it happens:** FMP earnings calendar requires paid plan — confirmed by multiple sources
**How to avoid:** Use `yfinance.Ticker.get_earnings_dates()` as primary source
**Warning signs:** 403 errors in logs when earnings endpoint is called

### Pitfall 6: Options chain for LSE tickers is empty
**What goes wrong:** `ticker.option_chain()` raises exception or returns empty DataFrames for LLOY.L
**Why it happens:** UK stocks don't have listed options on Yahoo Finance
**How to avoid:** Check `len(ticker.options) == 0` before calling `option_chain()`. Return structured `{"available": false}` from backend
**Warning signs:** KeyError or empty DataFrame from yfinance options call

### Pitfall 7: setMarkers called on series directly
**What goes wrong:** `TypeError: candleSeries.setMarkers is not a function`
**Why it happens:** In v5, markers are a plugin, not a core series method
**How to avoid:** `import { createSeriesMarkers } from 'lightweight-charts'; const m = createSeriesMarkers(series, markers);`

### Pitfall 8: scipy missing from requirements.txt
**What goes wrong:** `ModuleNotFoundError: No module named 'scipy'` at runtime
**Why it happens:** scipy is not in the current requirements.txt
**How to avoid:** Add `scipy>=1.11.0` to `backend/requirements.txt` before writing the Black-Scholes module
**Warning signs:** Import error in api container logs

---

## Standard Stack

### Core (Phase 3)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lightweight-charts | 5.1.0 (already installed) | 4-panel candlestick charts with markers | Locked in PROJECT.md; Apache 2.0 |
| scipy | >=1.11.0 (add to requirements) | `scipy.stats.norm` for Black-Scholes Greeks | Standard math stack; fits existing numpy/pandas |
| yfinance | 0.2.x (already installed) | Options chain, earnings dates, dividends, OHLCV history | Already used in Phase 2; zero cost |
| React | 19.2.4 (already installed) | Frontend UI | Locked stack |
| TailwindCSS v4 | 4.2.2 (already installed) | Styling via `@theme {}` config | Locked stack; CSS-first |

### New Backend Routes Required

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/equity/history/{ticker}` | GET | OHLCV history for charts (multiple timeframes) |
| `/api/equity/options/{ticker}` | GET | Options chain + Greeks + IV surface data |
| `/api/equity/short-interest/{ticker}` | GET | Short interest from Finnhub REST |
| `/api/equity/insider/{ticker}` | GET | Insider transactions from Finnhub REST |
| `/api/equity/news/{ticker}` | GET | Company news from Finnhub REST |
| `/api/fx/USDGBP` | GET | Latest GBP/USD rate from fx_rates table |

All routes live in `backend/api/routes/equity.py`, registered in `main.py`.

### Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Candlestick rendering | Custom SVG/Canvas chart | lightweight-charts v5 | Already installed; canvas-based, performant |
| Options Greeks math | Custom implementation from scratch | scipy.stats.norm with BS formula | Well-tested, handles edge cases (T=0, sigma=0) |
| Time-series data fetch | Custom yfinance wrapper | yfinance `.history(period=, interval=)` | Handles .L suffix, indexes, dividends automatically |
| WebSocket reconnect | Custom retry loop | Simple `ws.onclose` with setTimeout 3s | Sufficient for personal NAS tool |
| IV normalisation | Custom color scale | Pure CSS via computed `opacity`/HSL | canvas `fillRect` with RGB calculation is 20 lines |

---

## Architecture Patterns

### Recommended Frontend Structure

```
frontend/src/
├── modules/
│   └── equity/
│       ├── EquityModule.tsx      # Top-level layout grid (D-01)
│       ├── TickerCommandBar.tsx  # D-03: TICKER> prompt
│       ├── QuoteStrip.tsx        # D-01 top strip: live price
│       ├── ChartPanel.tsx        # D-05/06: single chart + expand logic
│       ├── ChartGrid.tsx         # D-05: 4-panel layout
│       ├── FundamentalsPanel.tsx # D-01 right sidebar
│       ├── ShortInterestPanel.tsx
│       ├── InsiderPanel.tsx
│       ├── OptionsChain.tsx      # D-08: calls/puts table
│       ├── IVSurface.tsx         # D-09: canvas heatmap
│       └── NewsPanel.tsx         # D-11
├── hooks/
│   ├── useEquityWebSocket.ts     # WS subscription for quotes
│   └── useEquityData.ts          # REST fetches on ticker change
```

### Recommended Backend Structure

```
backend/
├── api/routes/
│   └── equity.py                 # All Phase 3 REST routes
├── analysis/
│   └── black_scholes.py          # BS pricing + Greeks
├── ingestion/
│   └── finnhub_rest.py           # Finnhub REST fetchers (news, insider, short interest)
```

### Grid CSS Pattern (D-01)

```css
/* Terminal fixed-height grid — no scroll */
.equity-grid {
  display: grid;
  grid-template-rows: auto 1fr auto;  /* quote strip, main panels, bottom row */
  grid-template-columns: 1fr;
  height: calc(100vh - 56px); /* subtract header+nav */
  overflow: hidden;
}

.equity-main {
  display: grid;
  grid-template-columns: 60fr 40fr;
  overflow: hidden;
}

.equity-bottom {
  display: grid;
  grid-template-columns: 60fr 40fr;
  height: 300px;  /* fixed height */
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `chart.addCandlestickSeries()` | `chart.addSeries(CandlestickSeries, opts)` | v5 (2024) | All chart code must use new API |
| `series.setMarkers()` | `createSeriesMarkers(series, markers)` | v5 (2024) | Separate import required |
| FMP earnings calendar (free) | yfinance `get_earnings_dates()` | FMP changed pricing (2023/2024) | FMP earnings is now paid-only |
| Finnhub LSE quotes | yfinance polling fallback | Finnhub changed free tier | LSE real-time requires paid plan |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build | YES | v24.14.0 | — |
| Python3 | Backend | YES | system | — |
| lightweight-charts | EQUITY-02, 03 | YES (in package.json) | ^5.1.0 | — |
| scipy | Black-Scholes | NOT in requirements.txt | — | Add to requirements.txt |
| yfinance | Options, history | YES (in requirements.txt) | 0.2.x | — |
| Finnhub API key | EQUITY-01, 07, 08, 10 | Requires env var | — | Stale badge shown if missing |
| Redis | WebSocket pub/sub | YES (Phase 2) | Phase 2 wired | — |
| TimescaleDB | OHLCV history | YES (Phase 2) | Phase 2 wired | — |

**Missing dependencies with no fallback:**
- `scipy` not in `backend/requirements.txt` — must be added before Black-Scholes module

**Missing dependencies with fallback:**
- Finnhub API key — endpoints return `stale: true` and use cached data; stale badge shown

---

## Validation Architecture

`nyquist_validation: true` in `.planning/config.json` — include this section.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (confirmed in requirements.txt) |
| Config file | `backend/conftest.py` + `backend/tests/ingestion/conftest.py` |
| Quick run command | `pytest backend/tests/ -x -q` |
| Full suite command | `pytest backend/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EQUITY-01 | WebSocket delivers quote within 15s; stale badge when data old | integration | `pytest backend/tests/api/test_equity_ws.py -x` | NO — Wave 0 |
| EQUITY-04 | Earnings dates returned for AAPL; empty list handled | unit | `pytest backend/tests/api/test_equity.py::test_earnings_dates -x` | NO — Wave 0 |
| EQUITY-05 | Dividend ex-dates returned for AAPL and LLOY.L | unit | `pytest backend/tests/api/test_equity.py::test_dividend_dates -x` | NO — Wave 0 |
| EQUITY-06 | Fundamentals endpoint returns P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap | unit | `pytest backend/tests/api/test_equity.py::test_fundamentals_shape -x` | NO — Wave 0 |
| EQUITY-07 | Short interest endpoint returns structured response or "US-only" for LSE | unit | `pytest backend/tests/api/test_equity.py::test_short_interest -x` | NO — Wave 0 |
| EQUITY-08 | Insider clustering: 10b5-1 filtered (code=F excluded); buy/sell ratio computed | unit | `pytest backend/tests/analysis/test_insider.py -x` | NO — Wave 0 |
| EQUITY-09 | Black-Scholes Greeks: delta in [0,1] for call; vega > 0; theta < 0 | unit | `pytest backend/tests/analysis/test_black_scholes.py -x` | NO — Wave 0 |
| EQUITY-09 | Options chain endpoint returns calls+puts with IV and Greeks | unit | `pytest backend/tests/api/test_equity.py::test_options_chain -x` | NO — Wave 0 |
| EQUITY-10 | News endpoint returns headlines; Finnhub error returns empty list + stale | unit | `pytest backend/tests/api/test_equity.py::test_news -x` | NO — Wave 0 |
| EQUITY-11 | FX endpoint returns USDGBP rate from fx_rates table | unit | `pytest backend/tests/api/test_fx.py::test_usdgbp -x` | NO — Wave 0 |
| EQUITY-12 | LLOY.L ticker: OHLCV returned; options returns not-available; short interest returns US-only | unit | `pytest backend/tests/api/test_equity.py::test_lse_ticker -x` | NO — Wave 0 |

Frontend tests: lightweight-charts renders without errors, chart mounts/unmounts cleanly. These are difficult to automate without a full Playwright/Cypress setup (out of scope). Validate manually via browser during implementation.

### Sampling Rate
- Per task commit: `pytest backend/tests/ -x -q`
- Per wave merge: `pytest backend/tests/ -v`
- Phase gate: Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/api/test_equity.py` — covers EQUITY-04 through EQUITY-12 REST endpoints
- [ ] `backend/tests/api/test_fx.py` — covers FX endpoint for EQUITY-11
- [ ] `backend/tests/analysis/test_black_scholes.py` — covers BS Greeks math with known inputs
- [ ] `backend/tests/analysis/test_insider.py` — covers clustering logic and 10b5-1 filter

---

## Open Questions

1. **Finnhub short interest free tier access**
   - What we know: Finnhub `/stock/short-interest` endpoint exists; free tier confirmed generous for US stocks
   - What's unclear: Whether this specific endpoint is gated — multiple sources cite it as alternative data requiring premium
   - Recommendation: Test empirically in Wave 1 with a real API key against AAPL. If 403, fall back to showing "Short interest data unavailable on free tier" in the sidebar panel

2. **Finnhub company news for LSE tickers**
   - What we know: Finnhub covers LSE on free REST tier for basic quotes; news may differ
   - What's unclear: Whether `/company-news?symbol=LLOY.L` returns data on free tier
   - Recommendation: Test against LLOY.L in Wave 1. If empty, fall back to yfinance news or show empty panel

3. **IV percentile rank methodology**
   - What we know: True 52-week IV rank requires historical option data not currently stored
   - What's unclear: Whether users expect true 52-week rank vs a simpler cross-chain rank
   - Recommendation: For Phase 3, compute "IV rank relative to other strikes in current chain" (simple percentile of current IVs). Add comment noting that true 52-week IV rank requires Phase 8 screener data

4. **Intraday OHLCV history storage**
   - What we know: yfinance provides 1H (60 days) and 4H (730 days) intraday data; the OHLCV table exists
   - What's unclear: Whether the existing OHLCV hypertable schema handles intraday intervals (does it need an `interval` column?)
   - Recommendation: Add `interval` column to OHLCV model (`'1d'`, `'1h'`, `'4h'`, `'1wk'`) and store multi-interval data. Or use separate lookups per interval at query time. Check existing OHLCV model schema before implementing.

---

## Sources

### Primary (HIGH confidence)
- TradingView lightweight-charts official docs — v4→v5 migration guide: https://tradingview.github.io/lightweight-charts/docs/migrations/from-v4-to-v5
- TradingView lightweight-charts — Series Markers tutorial: https://tradingview.github.io/lightweight-charts/tutorials/how_to/series-markers
- TradingView lightweight-charts — React simple example: https://tradingview.github.io/lightweight-charts/tutorials/react/simple
- TradingView lightweight-charts — React advanced example: https://tradingview.github.io/lightweight-charts/tutorials/react/advanced
- yfinance official API reference — get_earnings_dates: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.get_earnings_dates.html
- frontend/package.json — confirmed lightweight-charts at ^5.1.0
- backend/requirements.txt — confirmed scipy absent

### Secondary (MEDIUM confidence)
- Finnhub WebSocket message schema (trade fields s/p/t/v/c) — verified across multiple tutorial sources including elastic/tutorials GitHub
- Finnhub free tier: US stocks WebSocket + 60 req/min REST — confirmed across IBKR Campus, Robot Wealth, multiple tutorials
- Finnhub international/LSE tickers require premium — confirmed by multiple independent sources
- yfinance options chain DataFrame schema — confirmed across multiple Python finance tutorials
- FMP earnings calendar requires paid plan — confirmed by WebSearch results citing FMP FAQs
- scipy Black-Scholes implementation pattern — confirmed across multiple quantitative Python sources

### Tertiary (LOW confidence)
- Finnhub `/stock/short-interest` free tier availability — endpoint URL confirmed; free tier access unverified (test required)
- Finnhub company news for LSE tickers — may work on free tier; unverified
- FMP dividends calendar free tier status — page returned 403 during research; status unclear

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified; versions confirmed from package.json
- Architecture: HIGH — follows established Phase 2 patterns; new patterns (multi-chart, canvas heatmap) verified
- Pitfalls: HIGH — all pitfalls empirically grounded (v5 API changes confirmed, LSE restriction confirmed)
- Finnhub free tier boundary: MEDIUM — core behaviour confirmed; specific endpoint gating requires empirical test

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (30 days — lightweight-charts v5 stable; Finnhub free tier terms unlikely to change)

---

## RESEARCH COMPLETE
