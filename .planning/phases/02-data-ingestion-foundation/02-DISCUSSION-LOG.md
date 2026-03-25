# Phase 2: Data Ingestion Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 02-data-ingestion-foundation
**Areas discussed:** Market hours awareness, WebSocket channel design, On-demand quote trigger, Phase 2 API surface

---

## Market Hours Awareness

| Option | Description | Selected |
|--------|-------------|----------|
| Always-on | Tasks fire 24/7; stale data outside market hours handled by fallback chain | ✓ |
| Market-hours-aware | Beat tasks check calendar; skips weekends/after-hours per UK+US exchange | |
| Configurable per data type | Macro always-on; equity quotes market-hours-aware only | |

**User's choice:** Always-on
**Notes:** Personal NAS tool with generous free-tier rate limits — timezone complexity not worth it.

---

## Task Failure Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Retry with exponential backoff | 3 attempts at 60s/300s/900s; beat retries on next natural cycle | ✓ |
| Fail silently, let beat retry | No autoretry; next cycle fires on schedule | |
| Retry + dead letter queue | After 3 retries, push to Redis dead-letter list | |

**User's choice:** Retry with exponential backoff

---

## yfinance Scheduled Refresh Interval

| Option | Description | Selected |
|--------|-------------|----------|
| Every 5 minutes | Frequent enough for intraday; within rate limits | ✓ |
| Every 1 minute | Near real-time; may trigger rate limits | |
| Every 15 minutes | Conservative; matches many free API limits | |

**User's choice:** Every 5 minutes

---

## Ticker Universe for Beat Schedule

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded seed list | Fixed list in config; sufficient for Phase 2 | ✓ |
| Query TimescaleDB for known tickers | Dynamic but needs prior on-demand call | |
| Redis-backed active ticker set | Most flexible; adds state management complexity | |

**User's choice:** Hardcoded seed list

---

## WebSocket Channel Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Per-ticker channels | quotes:AAPL, macro:CPI, fx:GBPUSD; clients subscribe selectively | ✓ |
| Single broadcast channel | All data on hhbfin:live; all clients receive all updates | |

**User's choice:** Per-ticker channels

---

## WebSocket Message Format

| Option | Description | Selected |
|--------|-------------|----------|
| Flat structure | All fields at top level with channel, ticker, price, stale | ✓ |
| Envelope with data payload | type + metadata wrapper with nested data object | |

**User's choice:** Flat structure with `stale` boolean field

---

## WebSocket Subscribe with No Data

| Option | Description | Selected |
|--------|-------------|----------|
| Send last-known from DB on subscribe | Server reads latest TimescaleDB row immediately on connect | ✓ |
| Send nothing, wait for next pub/sub event | Client waits until next Celery publish | |
| Send last Redis cache value | Fast but may miss DB-only data | |

**User's choice:** Send last-known from DB on subscribe

---

## WebSocket Subscriber Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Single background task on startup | One asyncio task, one Redis connection, fan-out by channel | ✓ |
| Per-connection subscriber | Each WebSocket gets its own Redis pubsub | |

**User's choice:** Single background task on FastAPI lifespan startup

---

## On-Demand Quote Trigger (Empty DB)

| Option | Description | Selected |
|--------|-------------|----------|
| Trigger + wait with timeout | Fire Celery task, poll DB for 10s, return 200 or 503 | ✓ |
| Fire async, return 202 | Dispatch and return immediately; frontend polls | |
| Return 404, beat handles it | Simplest but worst UX | |

**User's choice:** Trigger + wait with 10s timeout; 503 with retry_after on timeout

---

## Phase 2 Endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| /api/quote/{ticker} | OHLCV + price + fundamentals | ✓ |
| /api/macro/{series} | Macro time series | ✓ |
| /api/fx/{pair} | Frankfurter FX rates | |
| /api/ingest/trigger/{ticker} | Manual ingest trigger | ✓ |

**User's choice:** quote + macro + ingest/trigger; FX deferred to Forex module phase

---

## Quote Response Scope

| Option | Description | Selected |
|--------|-------------|----------|
| OHLCV + latest price only | Price + change; fundamentals deferred to Phase 3 | |
| OHLCV + fundamentals combined | P/E, EV/EBITDA, market cap included in one response | ✓ |

**User's choice:** Combined OHLCV + fundamentals in one response

---

## /api/ingest/trigger Auth

| Option | Description | Selected |
|--------|-------------|----------|
| Open in dev, protected in prod | No auth for now; add header/IP restriction later if needed | ✓ |
| Always open | Personal NAS tool; no protection ever needed | |
| Protected now | API key in .env + middleware | |

**User's choice:** Open in dev, protected in prod

---

## Macro Endpoint Series Names

| Option | Description | Selected |
|--------|-------------|----------|
| Friendly names mapped internally | /api/macro/cpi → CPIAUCSL; mapping table in code | ✓ |
| Raw FRED series ID | /api/macro/CPIAUCSL; transparent but frontend must know IDs | |

**User's choice:** Friendly names with internal FRED ID mapping

---

## Macro Response Format

| Option | Description | Selected |
|--------|-------------|----------|
| Time series array | Last 24 months of observations; frontend can chart immediately | ✓ |
| Latest value only | Single reading; history needs separate endpoint | |

**User's choice:** Time series array (default 24 months)

---

## Yield Curve Endpoint

| Option | Description | Selected |
|--------|-------------|----------|
| Defer to Macro Dashboard phase | Phase 2 ingests only; endpoint built with macro module | ✓ |
| Expose now via /api/macro/yield_curve | One extra endpoint alongside ingest work | |

**User's choice:** Defer to Macro Dashboard phase

---

## FX Rate Endpoint

| Option | Description | Selected |
|--------|-------------|----------|
| Defer to Forex module phase | Phase 2 ingests only; endpoint built with forex module | ✓ |
| Expose now via /api/fx/{base}/{quote} | Phase 3 might need it for GBP-adjusted returns | |

**User's choice:** Defer — but flagged that Phase 3 (EQUITY-11) may need this pulled forward

---

## Claude's Discretion

- Async Redis client choice for WebSocket listener (redis.asyncio vs aioredis)
- Hypertable column schemas for fundamentals, macro, news, screener, factors, dividends, COT tables
- FRED macro series mapping table column completeness beyond the minimum set

## Deferred Ideas

- `/api/fx/{base}/{quote}` — flagged for Phase 3 planner (EQUITY-11 dependency)
- `/api/macro/yield_curve` — Macro Dashboard phase
- Dynamic Redis-backed ticker set — Phase 3
- Market hours-aware scheduling — indefinitely deferred
- Dead letter queue — indefinitely deferred
