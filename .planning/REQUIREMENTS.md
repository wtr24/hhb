# Requirements: HHBFin — Free Bloomberg Terminal

**Defined:** 2026-03-24
**Core Value:** Unified zero-cost research terminal covering all asset classes — pull up any instrument instantly with live quotes, charts, indicators, macro context, news sentiment, and positioning data

---

## v1 Requirements

### Infrastructure

- [ ] **INFRA-01**: Docker Compose stack starts all 6 services (frontend, api, beat, worker, redis, timescaledb) with `docker compose up -d`
- [ ] **INFRA-02**: FastAPI health endpoint returns 200 and reports status of all service dependencies
- [ ] **INFRA-03**: React/Vite frontend serves Bloomberg dark terminal UI at port 3000
- [ ] **INFRA-04**: Celery beat scheduler runs in its own container and does not share workers
- [x] **INFRA-05**: `.env.example` documents all 7 required free API keys with signup links
- [x] **INFRA-06**: Development docker-compose override enables hot-reload for frontend and backend
- [ ] **INFRA-07**: TimescaleDB hypertables created for all data types on first startup

### Data Ingestion

- [x] **INGEST-01**: Celery workers ingest yfinance OHLCV + fundamentals for any ticker on demand and on schedule
- [x] **INGEST-02**: FRED ingestion worker fetches macro series (CPI, PCE, GDP, unemployment, Fed Funds, yield curve) on 1h schedule
- [x] **INGEST-03**: Redis TTL caching enforced per data type (per spec §5 table)
- [x] **INGEST-04**: Rate limit token buckets in Redis protect all API sources (Finnhub 60/min, FMP 250/day, Alpha Vantage 25/day, CoinGecko 13/hr)
- [x] **INGEST-05**: Fallback chain implemented: Live API → Redis cache → TimescaleDB last-known → stale warning → error
- [x] **INGEST-06**: All ingested data written to TimescaleDB — nothing cache-only
- [x] **INGEST-07**: Frankfurter FX rates ingested on 30s schedule for major pairs + GBP crosses
- [x] **INGEST-08**: US Treasury XML yield curve ingested on 15m schedule
- [x] **INGEST-09**: FastAPI WebSocket broadcaster subscribes to Redis pub/sub and fans out to all connected browser clients

### Equity Overview (Module 1)

- [x] **EQUITY-01**: Live quote (bid/ask/last/volume) displayed with 15s refresh via Finnhub WebSocket
- [ ] **EQUITY-02**: Multi-timeframe chart view — same instrument displayed simultaneously on Weekly / Daily / 4H / 1H
- [ ] **EQUITY-03**: Candlestick chart with timeframe selector (1D / 1W / 1M / 1Y / 5Y) via lightweight-charts
- [x] **EQUITY-04**: Earnings dates plotted as vertical markers on price chart (yfinance + FMP)
- [x] **EQUITY-05**: Dividend ex-dates plotted as markers on price chart
- [x] **EQUITY-06**: Fundamentals panel — P/E, EV/EBITDA, ROE, Debt/Equity, Market Cap (24h cache)
- [ ] **EQUITY-07**: Short interest displayed — % float short, short ratio, days to cover (Finnhub)
- [ ] **EQUITY-08**: Insider transaction clustering — buy/sell ratio, multi-insider detection within 2-week window, 10b5-1 filter
- [x] **EQUITY-09**: Options chain snapshot with Black-Scholes pricer, Greeks (delta/gamma/vega/theta), IV surface, IV percentile rank
- [x] **EQUITY-10**: Company news feed via Finnhub REST (5m refresh)
- [x] **EQUITY-11**: FX-adjusted return view — toggle GBP-adjusted P&L with GBP/USD overlay
- [x] **EQUITY-12**: LSE tickers fully supported via `.L` suffix (e.g. LLOY.L, BARC.L, ^FTSE, ^FTMC)

### Technical Analysis Engine (Math Engine §8)

- [ ] **TA-01**: All Moving Averages implemented — SMA, EMA, DEMA, TEMA, WMA, HMA, LWMA, VWMA + Golden/Death Cross + EMA Ribbon (8 EMAs)
- [ ] **TA-02**: All Momentum/Oscillator indicators — RSI, StochRSI, MACD, Stochastic %K/%D, Williams %R, CCI, ROC, Momentum, DPO, TRIX, Ultimate Oscillator, PPO, KDJ, CMO
- [ ] **TA-03**: All Trend Strength indicators — ADX/+DI/-DI, Aroon, Parabolic SAR, SuperTrend, Vortex, Ichimoku Cloud, Mass Index
- [ ] **TA-04**: All Volatility indicators — Bollinger Bands + %B, Keltner Channel, Donchian Channel, ATR, Historical Vol (3 methods), GARCH(1,1), Chaikin Vol, Ulcer Index
- [ ] **TA-05**: All Volume indicators — OBV, VWAP + Anchored VWAP + VWAP SD Bands, A/D Line, CMF, MFI, Volume Profile, CVD, VROC, Ease of Movement, NVI/PVI, Force Index
- [ ] **TA-06**: All Market Breadth indicators — A/D Line, McClellan Oscillator + Summation, TRIN, New Highs-Lows, Up-Down Volume Ratio, % Above 200/50 SMA, TICK
- [ ] **TA-07**: All 5 Pivot Point methods — Standard, Woodie's, Camarilla, Fibonacci, DeMark — computed nightly, stored in TimescaleDB, displayed as horizontal lines
- [ ] **TA-08**: Intermarket analysis indicators — rolling correlation (30D/90D/1Y) for DXY/Gold, Yields/USD, VIX/SPX, Credit Spreads/Equities, Oil/CPI, Copper/Growth, BTC/SPX
- [ ] **TA-09**: 60+ candlestick patterns detected (TA-Lib) with per-asset historical win rate and p-value (n≥30, out-of-sample only)
- [ ] **TA-10**: Chart pattern detection — Head & Shoulders, Inverse H&S, Cup & Handle, Double Top/Bottom, Ascending/Descending Triangle, Flag/Pennant, Wedge — with confidence scores labelled experimental
- [ ] **TA-11**: Fibonacci retracement and extension tools — interactive drawing on chart with 0.236/0.382/0.5/0.618/0.786/1.0/1.618/2.618 levels
- [ ] **TA-12**: Elliott Wave manual labelling tool with automatic Fibonacci ratio validation (Wave 3 shortest check, Wave 4 overlap check, standard impulse/corrective guidelines)
- [ ] **TA-13**: Statistical significance layer — every signal shows win rate, p-value, sample size, out-of-sample flag; context filter by trend/volume/key level

### Macro Dashboard (Module 2)

- [ ] **MACRO-01**: Full US yield curve (1M–30Y) from US Treasury XML displayed as chart, updated every 15m
- [ ] **MACRO-02**: Full UK gilt curve from Bank of England Statistical Database
- [ ] **MACRO-03**: 2s10s and 5s30s spread as time series charts with recession zone overlay
- [ ] **MACRO-04**: Curve shape classifier — Normal / Flat / Inverted / Humped with historical context
- [ ] **MACRO-05**: Historical curve overlay — today vs 1M ago vs 1Y ago on same chart
- [ ] **MACRO-06**: Real yield curve (nominal minus TIPS breakevens) + breakeven inflation time series (FRED)
- [ ] **MACRO-07**: US macro panels — CPI, Core CPI, PCE (FRED) + UK CPI (ONS API)
- [ ] **MACRO-08**: Labour market — US NFP + unemployment (BLS) + UK employment (ONS)
- [ ] **MACRO-09**: GDP — US (FRED) + UK (ONS) + EU (ECB)
- [ ] **MACRO-10**: Policy rates — Fed Funds + BoE base rate + ECB rate as time series
- [ ] **MACRO-11**: VIX term structure — spot VIX + VIX3M + VIX6M contango/backwardation indicator
- [ ] **MACRO-12**: VIX percentile rank (1Y and 5Y) + market regime classifier (Low Vol / Normal / Elevated / Crisis)
- [ ] **MACRO-13**: DIY Fear & Greed Index — composite of VIX percentile, put/call ratio, market breadth, junk bond spread, SPX momentum, safe haven demand
- [ ] **MACRO-14**: DXY / SPX / FTSE 100 at-a-glance (15s refresh) + seasonality panel (monthly avg returns)

### Forex & Commodities (Module 3)

- [ ] **FX-01**: Major FX pairs + GBP crosses displayed (GBP/USD, EUR/GBP, GBP/JPY prominent), 30s refresh via Frankfurter
- [ ] **FX-02**: COT positioning overlay on FX charts — large speculator net position as % of OI (CFTC weekly)
- [ ] **FX-03**: CFTC COT reports ingested weekly for FX, commodities, and equity indices
- [ ] **FX-04**: WTI crude, Brent crude, natural gas, gold, silver, copper, aluminium prices (FRED + EIA)
- [ ] **FX-05**: COT positioning for crude oil, gold, and key commodities
- [ ] **FX-06**: EIA inventory reports with market impact displayed weekly
- [ ] **FX-07**: Commodity charts with 1M / 1Y / 5Y timeframe selector
- [ ] **FX-08**: Seasonality charts for commodities (crude Q4 pattern, gold Q1 pattern, etc.)

### Crypto Desk (Module 4)

- [ ] **CRYPTO-01**: Top 100 coins by market cap from CoinGecko, 10m refresh
- [ ] **CRYPTO-02**: BTC and ETH real-time OHLCV via persistent Binance WebSocket connection
- [ ] **CRYPTO-03**: Volume Profile — horizontal histogram of volume at each price level (Binance data)
- [ ] **CRYPTO-04**: Cumulative Volume Delta (CVD) — buying vs selling pressure from Binance order flow
- [ ] **CRYPTO-05**: Large trade detection — flag orders above configurable threshold size
- [ ] **CRYPTO-06**: Crypto Fear & Greed index from alternative.me
- [ ] **CRYPTO-07**: BTC on-chain metrics — hash rate, active addresses, transaction volume (Blockchain.info)
- [ ] **CRYPTO-08**: Crypto/equity rolling correlation panel

### News & Sentiment (Module 5)

- [ ] **NEWS-01**: World news timeline from 7 RSS sources polled every 5m with fuzzy deduplication
- [ ] **NEWS-02**: Financial/market news from Finnhub WebSocket (real-time)
- [ ] **NEWS-03**: Company-specific news from Finnhub REST on ticker lookup
- [ ] **NEWS-04**: FinBERT (ProsusAI/finbert) running locally — classifies each headline positive/negative/neutral with confidence score
- [ ] **NEWS-05**: Sentiment time series — rolling 24h sentiment score per ticker, stored in TimescaleDB
- [ ] **NEWS-06**: All news archived to TimescaleDB with full text, source, timestamp, and sentiment scores

### Screener (Module 6)

- [ ] **SCRN-01**: US stock screener via Finviz Playwright scraper (2–5s random delays, 4 user agents)
- [ ] **SCRN-02**: UK stock screener via yfinance bulk scan on FTSE 100/250 constituent lists
- [ ] **SCRN-03**: Filters — sector, P/E, market cap, momentum, earnings date, dividend yield, short interest %, short ratio
- [ ] **SCRN-04**: Advanced filters — Hurst exponent (trending vs mean-reverting) and IV percentile rank
- [ ] **SCRN-05**: Screener results stored to TimescaleDB per run — compare snapshots over time

### Economic Calendar (Module 7)

- [ ] **CAL-01**: Economic calendar scraped from Investing.com via Playwright (1h refresh)
- [ ] **CAL-02**: Forex Factory calendar scraped via Playwright (1h refresh)
- [ ] **CAL-03**: Finnhub earnings calendar integrated (REST API)
- [ ] **CAL-04**: Countdown timer to next high/medium impact release — visible in terminal header at all times
- [ ] **CAL-05**: Consensus vs prior vs actual populated on release, market impact colour coded (high/medium/low)
- [ ] **CAL-06**: Historical release data stored in TimescaleDB — market move analysis on past releases

### Sector Rotation (Module 8)

- [ ] **SECT-01**: US sector ETF table (XLF, XLE, XLK, XLV, XLI, XLB, XLU, XLRE, XLY, XLP, XLC) — 1D/1W/1M/3M/YTD performance rankings
- [ ] **SECT-02**: UK ICB sector performance — FTSE sector indices via yfinance
- [ ] **SECT-03**: Relative strength charts — stock vs sector, sector vs broad index as time series
- [ ] **SECT-04**: Rotation chart — sectors plotted by momentum (x-axis) vs momentum change (y-axis)

### Correlation Dashboard (Module 9)

- [ ] **CORR-01**: Rolling correlation time series (30D/90D/1Y) for all major asset class pairs
- [ ] **CORR-02**: Stress-regime correlation — correlations compared in normal vs drawdown periods
- [ ] **CORR-03**: Lead/lag analysis — cross-correlation function with lag plot (e.g. DXY leads gold by N days)
- [ ] **CORR-04**: Static correlation heatmap across equities, crypto, forex, commodities, bonds with configurable lookback

### Fixed Income (Module 10)

- [ ] **FI-01**: Full US Treasury curve chart (1M–30Y) with daily/weekly/monthly views
- [ ] **FI-02**: Full UK gilt curve from Bank of England Statistical Database
- [ ] **FI-03**: 2s10s and 5s30s spread time series with recession indicator overlay
- [ ] **FI-04**: Corporate bond OAS spreads — investment grade + high yield (FRED)
- [ ] **FI-05**: TIPS breakeven inflation rates (FRED)
- [ ] **FI-06**: SONIA rate (Bank of England) + SOFR rate (FRED) as time series

### Dividend Analysis (Module 11)

- [ ] **DIV-01**: Dividend yield, payout ratio, dividend cover (EPS/DPS) displayed per ticker
- [ ] **DIV-02**: 5Y and 10Y dividend growth CAGR calculated
- [ ] **DIV-03**: Dividend sustainability score — composite of payout ratio, FCF yield, net debt/EBITDA, earnings trend
- [ ] **DIV-04**: Ex-date and payment date calendar
- [ ] **DIV-05**: Dividend history chart — annual DPS over 10Y with growth rate overlay
- [ ] **DIV-06**: ISA income projection — given position size, project forward annual income
- [ ] **DIV-07**: Sector dividend comparison — stock yield vs sector average

### Portfolio Tracker (Module 13)

- [ ] **PORT-01**: Manual position entry (ticker, quantity, purchase price, date, currency) + CSV import
- [ ] **PORT-02**: P&L vs benchmarks — SPX, FTSE 100, FTSE All-Share; all positions normalised to GBP
- [ ] **PORT-03**: Drawdown chart — time series of portfolio drawdown from peak with recovery periods marked
- [ ] **PORT-04**: Risk metrics — Sharpe, Sortino, Information Ratio, Beta (60D + 252D Blume-adjusted), VaR (95% historical), CVaR (95% Basel III), GARCH(1,1) vol, max drawdown, Calmar, Ulcer Index
- [ ] **PORT-05**: Fama-French 3-factor + Carhart 4-factor decomposition via OLS (statsmodels), quantify alpha vs factor exposure
- [ ] **PORT-06**: Portfolio optimisation — Markowitz efficient frontier (min variance + max Sharpe), Risk Parity, Ledoit-Wolf shrinkage covariance
- [ ] **PORT-07**: Seasonality analysis — monthly/quarterly return patterns per position
- [ ] **PORT-08**: Historical P&L snapshots saved to TimescaleDB for replay

### Position Sizing (Module 12)

- [ ] **SIZE-01**: Position sizing calculator — inputs: account size (GBP), risk %, entry price, stop-loss; outputs: shares/units, position value, risk £, R:R ratio
- [ ] **SIZE-02**: Kelly Criterion optimal position size — f* = (p·b - q)/b — requires historical win rate + avg win/loss ratio
- [ ] **SIZE-03**: ISA annual allowance tracker — £20,000 limit, amount used, remaining
- [ ] **SIZE-04**: FX-adjusted sizing for foreign assets (e.g. US stock position in GBP terms)
- [ ] **SIZE-05**: Supports all asset classes — equities, forex (lot sizing), crypto (units)

### Watchlist & Alerts (Module 14)

- [ ] **WATCH-01**: Custom watchlists across all asset classes with keyboard-navigable list
- [ ] **WATCH-02**: Price alerts — above/below threshold with persistent storage
- [ ] **WATCH-03**: Indicator-based alerts — RSI 70/30 crosses, MACD line/signal cross, price/SMA crosses (50/100/200), Bollinger squeeze, volume spike (N × 20d avg), 52-week high/low
- [ ] **WATCH-04**: COT positioning alerts — large speculator net crosses threshold
- [ ] **WATCH-05**: Alert delivery via browser notification (always) + optional SMTP email (self-hosted, configurable per-alert)
- [ ] **WATCH-06**: Earnings and dividend calendar linked to watchlist tickers

### Backtesting Engine (Math Engine §S)

- [ ] **BACK-01**: Event-driven backtester — entry at next open, exit on reversal/N-bar hold/stop
- [ ] **BACK-02**: Transaction costs — UK stamp duty 0.5%, spread 0.1%; US spread 0.05%; crypto 0.1% taker fee
- [ ] **BACK-03**: Slippage model — actual fill = open ± 0.05 × ATR(14)
- [ ] **BACK-04**: Out-of-sample discipline — 70/30 train/test split; UI shows hold-out results only
- [ ] **BACK-05**: Survivorship bias warning — permanent UI notice on all backtest results
- [ ] **BACK-06**: Backtest outputs — win rate, profit factor, Sharpe, Sortino, Calmar, max drawdown, equity curve

---

## v2 Requirements

### Trading 212 Integration

- **T212-01**: T212 ISA portfolio synced automatically via T212 API
- **T212-02**: Real positions replace manual CSV entries in Portfolio Tracker
- **T212-03**: Live P&L pulled directly from T212 account
- **T212-04**: Position sizing calculator pre-filled with current account balance from T212

### UK Companies House Integration

- **CH-01**: UK company filings (10-K equivalent, director RNS) surfaced per LSE ticker
- **CH-02**: Director transaction alerts for watchlisted UK stocks
- **CH-03**: Ownership structure data for UK companies

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bloomberg real-time bond tick data | Proprietary, no free source exists |
| Equity Level 2 order book | Bloomberg-only for stocks; crypto-only via Binance |
| Full analyst consensus estimates | FMP free tier provides limited coverage only |
| Survivorship-bias-free historical equity data | yfinance only covers current constituents; warn users |
| Mobile app | Personal NAS-hosted terminal, keyboard-first |
| Multi-user / team features | Personal tool — no auth system needed |
| Paid API tiers | All sources must work on free tier forever |
| Cloud hosting | Self-hosted NAS only |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 through INFRA-07 | Phase 1 | Pending |
| INGEST-01 through INGEST-09 | Phase 2 | Pending |
| EQUITY-01 through EQUITY-12 | Phase 3 | Pending |
| TA-01 through TA-13 | Phase 4 | Pending |
| MACRO-01 through MACRO-14 | Phase 5 | Pending |
| FX-01 through FX-08 | Phase 6 | Pending |
| CRYPTO-01 through CRYPTO-08 | Phase 6 | Pending |
| NEWS-01 through NEWS-06 | Phase 7 | Pending |
| SCRN-01 through SCRN-05 | Phase 8 | Pending |
| CAL-01 through CAL-06 | Phase 9 | Pending |
| SECT-01 through SECT-04 | Phase 9 | Pending |
| CORR-01 through CORR-04 | Phase 10 | Pending |
| FI-01 through FI-06 | Phase 10 | Pending |
| DIV-01 through DIV-07 | Phase 10 | Pending |
| PORT-01 through PORT-08 | Phase 11 | Pending |
| SIZE-01 through SIZE-05 | Phase 12 | Pending |
| WATCH-01 through WATCH-06 | Phase 12 | Pending |
| BACK-01 through BACK-06 | Phase 12 | Pending |

**Coverage:**
- v1 requirements: 98 total
- Mapped to phases: 98
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after initial definition*
