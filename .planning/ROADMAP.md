# Roadmap: HHBFin — Free Bloomberg Terminal

## Overview

12 phases building from bare Docker Compose stack to a fully-featured trading research terminal. Each phase delivers a runnable, usable increment. Wave 1 (Phases 1–6) delivers core research capability across all asset classes. Wave 2 (Phases 7–10) adds research depth — news sentiment, screener, economic calendar, correlation, and fixed income. Wave 3 (Phases 11–12) completes the terminal with portfolio tracking, risk analytics, position sizing, alerts, and backtesting.

---

## Phases

- [ ] **Phase 1: Infrastructure Bootstrap** — Docker Compose stack, FastAPI skeleton, React/Vite Bloomberg UI, dev tooling
- [x] **Phase 2: Data Ingestion Foundation** — TimescaleDB schemas, Celery workers, Redis caching, yfinance/FRED/Frankfurter pipelines
- [x] **Phase 3: Equity Overview** — Live quotes, multi-timeframe charts, fundamentals, short interest, insider transactions, options chain (completed 2026-03-28)
- [ ] **Phase 4: Technical Analysis Engine** — 60+ indicators, 60+ candlestick patterns, chart patterns, Fibonacci, Elliott Wave, statistical significance layer
- [ ] **Phase 5: Macro Dashboard** — US+UK yield curves, CPI/GDP/unemployment, VIX regime classifier, DIY Fear & Greed
- [ ] **Phase 6: Forex, Commodities & Crypto** — FX pairs + COT overlay, commodity prices + EIA, Binance WebSocket + CoinGecko crypto desk
- [ ] **Phase 7: News & Sentiment** — RSS + Finnhub news aggregation, local FinBERT scoring, sentiment time series
- [ ] **Phase 8: Screener** — US Finviz + UK FTSE screener, Hurst exponent + IV percentile filters, snapshot history
- [ ] **Phase 9: Economic Calendar & Sector Rotation** — Scraped calendar with countdown timer, US + UK sector rotation charts
- [ ] **Phase 10: Correlation, Fixed Income & Dividends** — Rolling/stress correlation dashboard, full yield curves, OAS spreads, dividend analysis + ISA projection
- [ ] **Phase 11: Portfolio Tracker** — GBP-adjusted P&L, VaR/CVaR/Sharpe/GARCH risk metrics, Fama-French decomposition, Markowitz optimisation
- [ ] **Phase 12: Position Sizing, Watchlist, Alerts & Backtester** — Kelly Criterion calculator, indicator-based alerts, browser/SMTP delivery, event-driven backtester

---

## Phase Details

### Phase 1: Infrastructure Bootstrap
**Goal**: All 6 Docker Compose services running locally; FastAPI health-checked; React/Vite Bloomberg dark terminal renders at localhost:3000; dev hot-reload working
**Depends on**: Nothing
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07
**Success Criteria** (what must be TRUE):
  1. `docker compose up -d` starts all 6 services without error (frontend, api, beat, worker, redis, timescaledb)
  2. `GET /health` returns 200 with redis and timescaledb status OK
  3. Browser at localhost:3000 shows Bloomberg-aesthetic dark terminal shell (amber text, black background, keyboard-navigable nav)
  4. TimescaleDB hypertable migrations run automatically on first startup
  5. `.env.example` lists all 7 API keys with free signup URLs
**Plans**: 5 plans

Plans:
- [x] 01-01: Docker Compose + TimescaleDB + Redis — base infrastructure with health checks
- [x] 01-02: FastAPI skeleton — routing structure, WebSocket broadcaster, Celery app config
- [x] 01-03: React/Vite frontend — Bloomberg dark theme (TailwindCSS), keyboard navigation shell, module routing
- [ ] 01-04: Docker Compose dev override — hot-reload for frontend + backend, volume mounts
- [ ] 01-05: `.env.example` + `docker-compose.prod.yml` + startup migration scripts

---

### Phase 2: Data Ingestion Foundation
**Goal**: Core ingestion pipeline live — Celery workers running on schedule, yfinance/FRED/Frankfurter/US Treasury data flowing into TimescaleDB via Redis rate-limited cache
**Depends on**: Phase 1
**Requirements**: INGEST-01, INGEST-02, INGEST-03, INGEST-04, INGEST-05, INGEST-06, INGEST-07, INGEST-08, INGEST-09
**Success Criteria** (what must be TRUE):
  1. Celery beat fires scheduled tasks without duplication; worker processes tasks from queue
  2. `GET /api/quote/AAPL` returns OHLCV data from TimescaleDB (ingested via yfinance)
  3. `GET /api/quote/LLOY.L` returns data for a UK LSE ticker
  4. Redis TTL caching visible — second request within TTL returns cached response
  5. FRED macro series (CPI, GDP, Fed Funds) accessible via API endpoint
  6. FastAPI WebSocket pushes price update to connected browser client via Redis pub/sub
**Plans**: 6 plans

Plans:
- [x] 02-01-PLAN.md — TimescaleDB hypertable schemas + SQLAlchemy models + async engine + test scaffold
- [x] 02-02-PLAN.md — Redis TTL cache helper + token bucket rate limiter + ingestion config
- [x] 02-03-PLAN.md — yfinance source + Celery ingest tasks + quote REST endpoint with fallback chain
- [x] 02-04-PLAN.md — FRED + Frankfurter + Treasury sources + macro/trigger REST endpoints
- [x] 02-05-PLAN.md — Celery beat schedule wiring (all 4 ingestion tasks)
- [x] 02-06-PLAN.md — WebSocket broadcaster upgrade — Redis pub/sub channel fan-out
- [x] 02-07-PLAN.md — Wire rate limiter into ingestion tasks (gap closure: INGEST-04)

---

### Phase 3: Equity Overview
**Goal**: Full Bloomberg DES/GP equivalent — live quote, multi-timeframe candlestick charts with earnings/dividend markers, fundamentals, short interest, insider transaction clustering, and options chain with Greeks
**Depends on**: Phase 2
**Requirements**: EQUITY-01 through EQUITY-12
**Success Criteria** (what must be TRUE):
  1. Typing a ticker (e.g. `AAPL`, `LLOY.L`) loads the equity overview with live bid/ask/last updating every 15s
  2. Multi-timeframe panel shows same instrument simultaneously on Weekly/Daily/4H/1H charts
  3. Earnings and dividend ex-dates appear as vertical markers on the price chart
  4. Fundamentals panel (P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap) visible with 24h cache badge
  5. Short interest % float and insider buy/sell clustering visible for US tickers
  6. Options chain displays calls/puts with delta/gamma/vega/theta and IV surface heatmap
  7. LSE tickers (LLOY.L, BARC.L) fully supported with GBP-adjusted P&L toggle
**Plans**: 6 plans

Plans:
- [x] 03-01-PLAN.md — Wave 0: scipy + FX endpoint + OHLCV interval column + Black-Scholes + insider analysis + test scaffold
- [x] 03-02-PLAN.md — Wave 1: Finnhub WebSocket live quotes + earnings/dividends/news REST endpoints
- [x] 03-03-PLAN.md — Wave 2: Multi-timeframe candlestick charts (lightweight-charts v5, 4-panel W/D/4H/1H, expand/collapse)
- [x] 03-04-PLAN.md — Wave 2: Fundamentals + short interest + insider clustering panels (backend + frontend)
- [x] 03-05-PLAN.md — Wave 3: Options chain (Black-Scholes Greeks, IV surface heatmap, IV percentile rank)
- [x] 03-06-PLAN.md — Wave 3: EquityModule Bloomberg grid assembly + ticker command bar + GBP toggle + App.tsx wiring

---

### Phase 4: Technical Analysis Engine
**Goal**: Complete math engine — all indicator groups (A–H), 60+ candlestick patterns with win rates/p-values, chart pattern detection, Fibonacci tools, Elliott Wave labelling, and statistical significance layer across all signals
**Depends on**: Phase 3
**Requirements**: TA-01 through TA-13
**Success Criteria** (what must be TRUE):
  1. Any of the 60+ indicators can be overlaid on the price chart from the indicator picker
  2. Candlestick patterns on today's bar are detected and labelled with win rate + p-value badge (e.g. "Hammer: 65% win, n=43, p=0.03")
  3. At least 3 chart patterns (H&S, Double Top, Cup & Handle) detected on historical data and marked with confidence score
  4. Fibonacci retracement tool draws levels interactively on chart click
  5. Elliott Wave labels (1-2-3-4-5 and A-B-C) can be manually placed; Fibonacci ratio validation fires on label placement
  6. All 5 pivot point methods displayed as horizontal lines on chart with method selector
**Plans**: 7 plans

Plans:
- [ ] 04-01: TA-Lib + pandas-ta integration — library setup, wrapper layer, Moving Averages (§A) + EMA Ribbon
- [ ] 04-02: Momentum & oscillator indicators (§B) — RSI, StochRSI, MACD, Stochastic, Williams %R, CCI, etc.
- [ ] 04-03: Trend strength (§C), Volatility (§D), Volume indicators (§E)
- [ ] 04-04: Market breadth (§F), Pivot Points 5 methods (§G), Intermarket indicators (§H)
- [ ] 04-05: Candlestick pattern detection (60+ via TA-Lib) + per-asset win rate + p-value statistical significance layer (§O)
- [x] 04-06: Chart pattern detection (H&S, Cup & Handle, Double Top/Bottom, Triangles, Flags) with confidence scores
- [ ] 04-07: Fibonacci retracement/extension drawing tool + Elliott Wave manual labeller + Fibonacci validation; indicator picker frontend

---

### Phase 5: Macro Dashboard
**Goal**: Bloomberg ECO equivalent — full US+UK yield curves, 2s10s/5s30s spreads, CPI/GDP/unemployment panels, VIX term structure + regime classifier, DIY Fear & Greed composite
**Depends on**: Phase 2
**Requirements**: MACRO-01 through MACRO-14
**Success Criteria** (what must be TRUE):
  1. Macro dashboard shows full US yield curve (1M–30Y) as line chart, refreshing every 15m
  2. Full UK gilt curve displayed alongside US curve
  3. 2s10s spread time series shows grey recession zone overlays (NBER dates)
  4. Curve shape classifier shows current label (Normal/Flat/Inverted/Humped) with historical context
  5. VIX regime classifier shows current label (Low Vol/Normal/Elevated/Crisis) with percentile rank
  6. DIY Fear & Greed composite index (0–100) visible with component breakdown
  7. UK CPI (ONS) alongside US CPI (FRED) in same panel for comparison
**Plans**: 6 plans

Plans:
- [ ] 05-01: US Treasury XML + BoE gilt curve ingestion — full curve (1M–30Y), 15m refresh, TimescaleDB storage
- [ ] 05-02: Yield curve analytics — 2s10s/5s30s spreads, curve shape classifier, historical overlay, real yield (TIPS)
- [ ] 05-03: FRED macro ingestion workers — CPI, Core CPI, PCE, GDP, unemployment, Fed Funds, TIPS breakevens
- [ ] 05-04: ONS UK macro ingestion — UK CPI, employment, GDP; ECB Eurozone GDP; BLS payrolls
- [ ] 05-05: VIX term structure (VIX3M/VIX6M) + regime classifier + percentile rank; CBOE put/call ratio
- [ ] 05-06: DIY Fear & Greed composite + Macro Dashboard frontend (all panels)

---

### Phase 6: Forex, Commodities & Crypto
**Goal**: FX desk with COT positioning overlays, commodity prices with EIA inventory, full crypto desk with Binance WebSocket real-time data, Volume Profile, CVD, and on-chain metrics
**Depends on**: Phase 2
**Requirements**: FX-01 through FX-08, CRYPTO-01 through CRYPTO-08
**Success Criteria** (what must be TRUE):
  1. Major FX pairs + all GBP crosses update every 30s; GBP/USD, EUR/GBP, GBP/JPY displayed prominently
  2. CFTC COT net speculator position chart overlaid on FX chart (updated weekly)
  3. WTI, Brent, gold, silver, copper, aluminium prices displayed with 1M/1Y/5Y chart toggle
  4. BTC and ETH OHLCV updates in real-time from Binance WebSocket
  5. Volume Profile histogram and CVD chart visible for BTC/ETH
  6. CoinGecko top 100 table loads within 10m refresh cycle
  7. Crypto Fear & Greed index and BTC on-chain metrics (hash rate, active addresses) visible
**Plans**: 6 plans

Plans:
- [ ] 06-01: Frankfurter FX ingestion (30s) + FX module frontend with GBP crosses layout
- [ ] 06-02: CFTC COT weekly ingestion — FX, commodities, equity indices; COT chart overlay component
- [ ] 06-03: Commodities ingestion — FRED (gold, copper, aluminium) + EIA (WTI, Brent, natgas, inventories)
- [ ] 06-04: Binance WebSocket worker — persistent connection, BTC/ETH real-time OHLCV → Redis pub/sub
- [ ] 06-05: Volume Profile + CVD calculation engine from Binance tick data; large trade detection
- [ ] 06-06: CoinGecko top 100 + BTC on-chain (Blockchain.info) + Crypto Fear & Greed; Forex/Commodities/Crypto frontend assembly

---

### Phase 7: News & Sentiment
**Goal**: Bloomberg TOP equivalent — live financial + world news from 9 sources, local FinBERT scoring on every headline, sentiment time series per ticker archived to TimescaleDB
**Depends on**: Phase 2
**Requirements**: NEWS-01 through NEWS-06
**Success Criteria** (what must be TRUE):
  1. News feed shows headlines from at least 7 sources, deduplicated, updated within 5m
  2. Every headline has a sentiment badge (Positive/Neutral/Negative) with confidence score
  3. Finnhub WebSocket news appears in real-time without page refresh
  4. Typing a ticker shows company-specific news from Finnhub with sentiment scores
  5. Sentiment time series chart for any ticker shows rolling 24h average score
  6. FinBERT model loads successfully at container startup (no external API calls)
**Plans**: 5 plans

Plans:
- [ ] 07-01: Finnhub WebSocket news consumer + company-specific news REST endpoint
- [ ] 07-02: RSS aggregation worker — 7 sources, 5m polling, fuzzy deduplication (difflib/rapidfuzz)
- [ ] 07-03: FinBERT local inference setup — HuggingFace model download at build, inference pipeline, batch scoring
- [ ] 07-04: Sentiment pipeline — score all incoming headlines, store full text + scores + source to TimescaleDB, rolling 24h time series
- [ ] 07-05: News & Sentiment frontend — timeline view, ticker-specific news, sentiment chart

---

### Phase 8: Screener
**Goal**: Bloomberg EQS equivalent — US stocks via Finviz, UK stocks via FTSE 100/250 bulk scan, full filter set including Hurst exponent and IV percentile, results stored for snapshot comparison
**Depends on**: Phase 4 (for Hurst/IV filters), Phase 2
**Requirements**: SCRN-01 through SCRN-05
**Success Criteria** (what must be TRUE):
  1. Running a US screener returns filtered results from Finviz within 60s
  2. Running a UK screener returns FTSE 100/250 stocks filtered by dividend yield, P/E, momentum
  3. Hurst exponent filter correctly identifies trending (H > 0.6) vs mean-reverting (H < 0.4) stocks
  4. IV percentile filter visible and functional (requires options data from Phase 3)
  5. Two screener snapshots from different dates can be compared side-by-side
**Plans**: 4 plans

Plans:
- [ ] 08-01: Finviz Playwright scraper — rate limiting, user agent rotation, CSS selector parsing, TimescaleDB storage
- [ ] 08-02: FTSE 100/250 constituent list + yfinance bulk scan worker
- [ ] 08-03: Hurst exponent calculation (R/S analysis) + IV percentile filter integration; screener filter engine
- [ ] 08-04: Screener frontend — filter builder, results table, snapshot comparison view

---

### Phase 9: Economic Calendar & Sector Rotation
**Goal**: Full economic calendar with countdown timer always visible; US sector ETF rotation chart and UK ICB sector performance tracking
**Depends on**: Phase 2
**Requirements**: CAL-01 through CAL-06, SECT-01 through SECT-04
**Success Criteria** (what must be TRUE):
  1. Economic calendar shows upcoming events with exact UTC times, consensus, prior, impact colour
  2. Countdown timer to next high-impact event is always visible in the terminal header
  3. When an event releases, actual value appears and market impact is shown
  4. US sector ETF table shows 1D/1W/1M/3M/YTD % rankings — refreshed daily
  5. Rotation chart plots sectors on momentum vs momentum-change axes
  6. Historical release data queryable — what did the market do after last 5 NFP prints?
**Plans**: 5 plans

Plans:
- [ ] 09-01: Investing.com economic calendar Playwright scraper — event times, consensus, prior, impact rating, 1h refresh
- [ ] 09-02: Forex Factory calendar Playwright scraper + Finnhub earnings calendar integration
- [ ] 09-03: Economic Calendar frontend — event list, countdown timer (header component), impact colour coding, historical release view
- [ ] 09-04: Sector ETF ingestion (yfinance, 11 US ETFs + UK ICB indices) + relative strength calculations
- [ ] 09-05: Sector Rotation frontend — performance table, rotation chart (momentum vs rate-of-change), relative strength time series

---

### Phase 10: Correlation, Fixed Income & Dividends
**Goal**: Rolling/stress-regime/lead-lag correlation dashboard; full fixed income view with OAS spreads, TIPS, SONIA/SOFR; dividend sustainability analysis with ISA income projection
**Depends on**: Phase 2, Phase 5 (for yield curve data reuse)
**Requirements**: CORR-01 through CORR-04, FI-01 through FI-06, DIV-01 through DIV-07
**Success Criteria** (what must be TRUE):
  1. Correlation heatmap shows pairwise correlations across equities/crypto/forex/commodities/bonds for selected lookback
  2. Rolling correlation time series (90D window) shows how BTC/SPX correlation has changed over 2 years
  3. Stress-regime correlation panel shows how correlations differ in drawdown vs normal periods
  4. Lead/lag cross-correlation function correctly identifies that DXY leads gold (shows lag in days)
  5. Corporate bond OAS spreads (IG + HY) displayed as time series from FRED
  6. Dividend sustainability score computed for any ticker; ISA annual income projection displayed
**Plans**: 6 plans

Plans:
- [ ] 10-01: Rolling correlation engine — 30D/90D/1Y windows for all asset class pairs, stored in TimescaleDB
- [ ] 10-02: Stress-regime correlation + lead/lag cross-correlation function (cross_corr via scipy)
- [ ] 10-03: Correlation Dashboard frontend — heatmap, rolling time series, stress overlay, lead/lag plot
- [ ] 10-04: Fixed Income ingestion — corporate OAS spreads (FRED), TIPS breakevens, SONIA (BoE), SOFR (FRED)
- [ ] 10-05: Fixed Income frontend — full curve charts, OAS spreads, TIPS, SONIA/SOFR time series
- [ ] 10-06: Dividend analysis engine + Dividend Dashboard frontend (sustainability score, ISA projection, sector comparison)

---

### Phase 11: Portfolio Tracker
**Goal**: Full portfolio tracking with manual entry + CSV import, GBP-adjusted P&L vs benchmarks, complete risk metrics suite, Fama-French factor decomposition, and Markowitz portfolio optimisation
**Depends on**: Phase 4 (GARCH), Phase 2 (price data)
**Requirements**: PORT-01 through PORT-08
**Success Criteria** (what must be TRUE):
  1. Adding a position (AAPL, 10 shares, $150, 2024-01-15) appears in portfolio with live GBP P&L
  2. CSV import successfully loads a portfolio of 10+ positions
  3. Sharpe, Sortino, Max Drawdown, VaR (95%), CVaR (95%) all display correctly with BoE rate as risk-free
  4. Fama-French factor decomposition decomposes portfolio returns into market/SMB/HML/UMD and reports alpha
  5. Markowitz efficient frontier chart generated; minimum variance and max Sharpe portfolios highlighted
  6. Drawdown chart shows time series of portfolio drawdown from peak with recovery periods marked
**Plans**: 6 plans

Plans:
- [ ] 11-01: Portfolio data model + manual position entry UI + CSV import parser
- [ ] 11-02: P&L engine — GBP normalisation (FX adjustment), benchmark comparison (SPX, FTSE 100, FTSE All-Share)
- [ ] 11-03: Risk metrics engine — Sharpe, Sortino, Information Ratio, Blume-adjusted Beta (60D/252D), VaR (historical 95%), CVaR (Basel III), GARCH(1,1) vol, max drawdown, Calmar, Ulcer Index
- [ ] 11-04: Fama-French 3-factor + Carhart 4-factor decomposition — Kenneth French data ingestion + OLS regression (statsmodels)
- [ ] 11-05: Portfolio optimisation — Markowitz (SLSQP), Risk Parity, Ledoit-Wolf shrinkage (scikit-learn)
- [ ] 11-06: Portfolio Tracker frontend — P&L table, drawdown chart, risk panel, factor decomposition, efficient frontier visualisation

---

### Phase 12: Position Sizing, Watchlist, Alerts & Backtester
**Goal**: Full terminal completion — Kelly Criterion position sizing with ISA tracker, watchlist with comprehensive indicator-based alerts, browser + SMTP delivery, and event-driven backtester with proper cost modelling
**Depends on**: Phase 4 (indicators for alert triggers), Phase 3 (options for IV alerts)
**Requirements**: SIZE-01 through SIZE-05, WATCH-01 through WATCH-06, BACK-01 through BACK-06
**Success Criteria** (what must be TRUE):
  1. Position sizing calculator computes correct position size in GBP for a UK stock given account size, risk %, entry, and stop
  2. Kelly Criterion optimal f* calculation requires and accepts historical win rate + avg win/loss
  3. ISA allowance tracker shows £20,000 limit with amount used and remaining
  4. RSI alert fires a browser notification when AAPL RSI crosses 70
  5. Backtester runs a simple SMA crossover strategy on AAPL 5Y data and produces equity curve + Sharpe
  6. Backtest results clearly show out-of-sample (30%) results only, with survivorship bias warning
**Plans**: 6 plans

Plans:
- [ ] 12-01: Position sizing calculator — account size/risk/entry/stop inputs; shares/value/risk/R:R outputs; FX adjustment; lot sizing for FX/crypto
- [ ] 12-02: Kelly Criterion engine + ISA allowance tracker (£20k annual limit, usage tracking)
- [ ] 12-03: Watchlist data model + price alert engine + indicator-based alert triggers (RSI, MACD, SMA cross, Bollinger squeeze, volume spike, 52W high/low, COT threshold)
- [ ] 12-04: Alert delivery — browser Web Notifications API + optional SMTP (self-hosted, per-alert config); COT alerts
- [ ] 12-05: Event-driven backtester — entry/exit logic, cost model (stamp duty, spread, crypto fees), slippage (0.05 × ATR), 70/30 OOS split
- [ ] 12-06: Position Sizer + Watchlist + Backtester frontend; final integration QA pass

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Bootstrap | 3/5 | In Progress|  |
| 2. Data Ingestion Foundation | 7/7 | Complete | 2026-03-28 |
| 3. Equity Overview | 6/6 | Complete   | 2026-03-28 |
| 4. Technical Analysis Engine | 0/7 | Not started | - |
| 5. Macro Dashboard | 0/6 | Not started | - |
| 6. Forex, Commodities & Crypto | 0/6 | Not started | - |
| 7. News & Sentiment | 0/5 | Not started | - |
| 8. Screener | 0/4 | Not started | - |
| 9. Economic Calendar & Sector Rotation | 0/5 | Not started | - |
| 10. Correlation, Fixed Income & Dividends | 0/6 | Not started | - |
| 11. Portfolio Tracker | 0/6 | Not started | - |
| 12. Position Sizing, Watchlist, Alerts & Backtester | 0/6 | Not started | - |
