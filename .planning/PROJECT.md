# HHBFin — Free Bloomberg Terminal

## What This Is

A self-hosted personal trading research terminal — a zero-cost Bloomberg Terminal equivalent — covering all asset classes (UK/EU equities, US equities, crypto, forex, commodities, options). Built for daily ISA investment decision-making via Trading 212, deployed on a home NAS via Docker Compose with a dense dark terminal aesthetic.

## Core Value

A unified research dashboard where any instrument — LLOY.L, BTC, GBP/USD, WTI crude — can be pulled up instantly with live quotes, multi-timeframe charts, all key indicators, macro context, news with FinBERT sentiment, and positioning data, without paying Bloomberg £2,000/month.

## Requirements

### Validated

- [x] Full-stack Docker Compose deployment (frontend + api + beat + worker + redis + timescaledb) runnable with a single `docker compose up -d` — *Validated in Phase 1: Infrastructure Bootstrap*

### Active
- [ ] Equity overview with live quotes, multi-timeframe charts, fundamentals, short interest, insider transactions, options chain
- [ ] 60+ technical indicators with historical win rates and statistical significance (p-values)
- [ ] 60+ candlestick patterns + chart pattern detection + Fibonacci + Elliott Wave labelling
- [ ] Full macro dashboard — US+UK yield curves, CPI/PCE/GDP/unemployment, VIX regime, DIY Fear & Greed
- [ ] Forex major/minor pairs with COT positioning overlay, GBP crosses prominent
- [ ] Commodities (WTI, Brent, gold, copper) with EIA inventory data
- [ ] Crypto desk — Binance WebSocket real-time + CoinGecko top 100 + on-chain + Volume Profile + CVD
- [ ] News aggregation from 9 sources (RSS + Finnhub) with local FinBERT sentiment scoring
- [ ] US (Finviz) + UK (FTSE 100/250) stock screener with Hurst exponent + IV percentile filters
- [ ] Economic calendar — Investing.com + Forex Factory scraped, countdown timer, market impact ratings
- [ ] US sector rotation (11 ETFs) + UK ICB sector performance + rotation chart
- [ ] Rolling/stress-regime/lead-lag correlation dashboard across all asset classes
- [ ] Full fixed income view — US+UK yield curves, OAS spreads, TIPS breakevens, SONIA/SOFR
- [ ] Dividend analysis — sustainability score, 5Y/10Y CAGR, ISA income projection
- [ ] Portfolio tracker — GBP-adjusted P&L, VaR/CVaR/Sharpe/Sortino/GARCH, Fama-French, Markowitz
- [ ] Position sizing calculator with Kelly Criterion + ISA allowance tracker
- [ ] Watchlist with indicator-based alerts + browser/SMTP delivery
- [ ] Event-driven backtester with transaction costs, slippage, out-of-sample discipline
- [ ] All data zero-cost (no credit card, no expiring free tiers)
- [ ] UK/LSE equities fully supported via `.L` suffix (LLOY.L, BARC.L, ^FTSE, ^FTMC)

### Out of Scope

- T212 ISA API integration — deferred to Phase 2 milestone after core terminal is stable
- Proprietary bond tick data / real-time corporate bond pricing — Bloomberg-only, no free source
- Equity Level 2 order book for stocks — crypto only (Binance)
- Analyst consensus estimates — limited via FMP free tier only
- Survivorship-bias-free equity universe — yfinance only covers current constituents (warn in UI)
- Mobile app — web terminal, keyboard-navigable, NAS-hosted
- Multi-user / team features — personal tool only
- Paid API tiers — all sources must work on free tier forever

## Context

- **Stack**: React (Vite + TailwindCSS + lightweight-charts) + FastAPI (Python 3.11) + TimescaleDB + Redis + Celery
- **UI aesthetic**: Bloomberg dark terminal — dense, keyboard-navigable, information-dense, amber/green on black
- **Data persistence**: Every OHLCV bar, macro reading, news headline, screener result, COT report, and factor return is timestamped and stored permanently in TimescaleDB
- **Rate limit strategy**: Redis token bucket per API source; fallback chain: Live API → Redis cache → TimescaleDB → stale cache (⚠ warning) → error state
- **Scrapers**: Playwright for JS-rendered pages (Finviz, Investing.com), BeautifulSoup for static pages; 2–5s random delays, 4 rotating user agents, `robots.txt` respected
- **FinBERT**: ProsusAI/finbert (~440MB) downloaded once at container build time — finance-specific NLP, runs locally, no API cost
- **Build rule**: Every scraper and API integration tested locally with real keys before pipeline integration; API keys explicitly prompted before each test
- **NAS deployment**: Docker Compose on Synology/home NAS; single `docker compose up -d`
- **Free API keys required**: FRED, Finnhub, FMP, Alpha Vantage, EIA, BLS, Companies House

## Constraints

- **Cost**: Zero ongoing spend — all data sources free tier, no credit card required
- **Deployment**: Docker Compose on NAS; no Kubernetes, no cloud hosting costs
- **Stack**: FastAPI + React/Vite + TimescaleDB + Redis + Celery — no deviations
- **FinBERT**: Must run locally — no cloud NLP API calls
- **Data**: Everything persisted to TimescaleDB — no cache-only data
- **UK focus**: LSE/FTSE data parity with US data throughout all modules

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| TimescaleDB over plain Postgres | Hypertable compression + time-series queries for OHLCV data; partitioned by time automatically | — Phase 1 wired, hypertable migration confirmed |
| Redis dual role (cache + pub/sub) | Single service covers both TTL caching for rate limits and WebSocket fan-out to browsers | — Phase 1 wired, Phase 2 activates pub/sub |
| Celery beat as separate container | Prevents duplicate scheduling if workers are scaled | — Confirmed in Phase 1; distinct commands prevent duplicate scheduling |
| FinBERT local inference | Zero ongoing cost; finance-specific model outperforms general NLP on financial text | — Pending |
| lightweight-charts (TradingView) | Apache 2.0, performant canvas rendering, supports all chart types needed | — Pending |
| TA-Lib + pandas-ta dual library | TA-Lib for speed (C bindings), pandas-ta as Python fallback; 200+ indicators combined | — Pending |
| yfinance `.L` suffix for LSE | Covers FTSE 100/250 with full OHLCV + fundamentals + dividends at no cost | — Pending |
| Playwright for Finviz/calendar scrapers | JS-rendered pages require browser execution; BeautifulSoup insufficient | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

## Current State

Phase 1 complete — full Docker Compose stack bootstrapped (6 services), FastAPI skeleton with health/WebSocket, React/Vite Bloomberg terminal shell, dev hot-reload override, production restart policies, and .env.example with all 7 API keys documented.

---
*Last updated: 2026-03-25 after Phase 1: Infrastructure Bootstrap*
