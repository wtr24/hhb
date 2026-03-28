---
phase: 03-equity-overview
plan: 02
subsystem: api
tags: [finnhub, websocket, live-quotes, earnings, dividends, news, yfinance, redis-pubsub, wave1]

# Dependency graph
requires:
  - phase: 03-01
    provides: equity route stubs, finnhub_source.py REST helpers, test scaffold, cache/ttl helpers
provides:
  - FinnhubWebSocket class in backend/ingestion/sources/finnhub_ws.py
  - is_finnhub_ws_eligible() helper for US/LSE symbol routing
  - FINNHUB_WS_SYMBOLS config list (US-eligible seed tickers only)
  - GET /api/equity/earnings/{ticker} — yfinance earnings dates, 24h cache
  - GET /api/equity/dividends/{ticker} — yfinance dividend history, 24h cache
  - GET /api/equity/news/{ticker} — Finnhub REST news, 5m cache, stale fallback
  - websockets>=12.0 in requirements.txt
affects:
  - 03-03 through 03-06 (live quote strip available; chart markers can use earnings/dividends dates)

# Tech tracking
tech-stack:
  added:
    - websockets>=12.0 (async WebSocket client for Finnhub WS connection)
  patterns:
    - FinnhubWebSocket runs as asyncio background task managed in FastAPI lifespan
    - LSE tickers (.L suffix) and indices (^ prefix) excluded from Finnhub WS — yfinance Celery polling fallback
    - Graceful degradation: finnhub_task=None when FINNHUB_API_KEY absent; warning logged
    - News endpoint uses existing "news" TTL tier (300s) already in cache/ttl.py
    - All Wave 1 endpoints follow cache-then-fetch-then-cache pattern

key-files:
  created:
    - backend/ingestion/sources/finnhub_ws.py
  modified:
    - backend/api/main.py (Finnhub WS task in lifespan)
    - backend/ingestion/config.py (FINNHUB_WS_SYMBOLS list)
    - backend/api/routes/equity.py (earnings/dividends/news implemented, 4 stubs remain)
    - backend/tests/api/test_equity.py (Wave 1 tests: 9 new, skips removed from 3 classes)
    - backend/requirements.txt (websockets>=12.0)

key-decisions:
  - "FinnhubWebSocket uses websockets library (already installed, v16.0) — aiohttp not needed and not a direct dep"
  - "LSE exclusion handled via is_finnhub_ws_eligible() helper — single source of truth for symbol routing"
  - "finnhub_task=None when API key absent — avoids crash, logs warning, Celery polling covers all tickers"
  - "News endpoint uses 'news' TTL tier (300s) already in cache/ttl.py — no new tier needed"
  - "utcnow() replaced with datetime.now(tz=timezone.utc) to eliminate DeprecationWarning"

# Metrics
duration: ~4min
completed: 2026-03-28
---

# Phase 3 Plan 02: Wave 1 — Finnhub WebSocket + Earnings/Dividends/News Summary

**Finnhub WebSocket client publishing US trade ticks to Redis quotes:* pub/sub; earnings/dividends/news REST endpoints implemented from yfinance and Finnhub REST; 9 new Wave 1 tests passing**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-28T21:11:26Z
- **Completed:** 2026-03-28T21:15:34Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- `FinnhubWebSocket` class connects to `wss://ws.finnhub.io`, subscribes to `FINNHUB_WS_SYMBOLS`, publishes trade messages to Redis `quotes:{symbol}` in Phase 2 D-08 format
- `is_finnhub_ws_eligible()` helper: returns False for `.L` suffix (LSE) and `^` prefix (indices) — single routing decision point
- `FINNHUB_WS_SYMBOLS = ["AAPL", "MSFT", "BTC-USD"]` — US/crypto only from seed tickers
- FastAPI lifespan now manages two background tasks: Redis pub/sub listener (existing) + Finnhub WS (new)
- Automatic 5s reconnect loop on disconnect; graceful cancel on FastAPI shutdown
- `GET /api/equity/earnings/{ticker}` — yfinance `get_earnings_dates(limit=12)`, returns list of YYYY-MM-DD strings, 24h cache
- `GET /api/equity/dividends/{ticker}` — yfinance `dividends` Series, returns `[{"date", "amount"}]`, 24h cache
- `GET /api/equity/news/{ticker}` — Finnhub REST `fetch_company_news`, 30-day window, returns `[{"headline","source","url","datetime","summary"}]`, 5m cache
- 9 new Wave 1 tests (3 per endpoint) replacing skips; 14 equity tests pass, 5 still skipped (Wave 2-3)
- Analysis regression: all 26 analysis tests still pass

## Task Commits

1. **Task 1: Finnhub WebSocket client + lifespan wiring** — `fe713b4` (feat)
2. **Task 2: Earnings, dividends, news endpoints + Wave 1 tests** — `293f896` (feat)

## Files Created/Modified

- `backend/ingestion/sources/finnhub_ws.py` — FinnhubWebSocket class + is_finnhub_ws_eligible helper (new)
- `backend/api/main.py` — Finnhub WS task in lifespan (create + cancel pattern matches existing pub/sub task)
- `backend/ingestion/config.py` — FINNHUB_WS_SYMBOLS list derived from SEED_TICKERS
- `backend/api/routes/equity.py` — earnings/dividends/news implemented; 4 stubs (fundamentals/short-interest/insiders/options) remain
- `backend/tests/api/test_equity.py` — 3 Wave 1 test classes unskipped, 9 new tests; 5 Wave 2-3 skips retained
- `backend/requirements.txt` — websockets>=12.0 added

## Decisions Made

- FinnhubWebSocket uses `websockets` library (already installed at v16.0) rather than `aiohttp` — aiohttp is only a transitive dep, not a direct dep; websockets is the idiomatic async WebSocket library
- `is_finnhub_ws_eligible()` is the single source of truth for symbol routing decisions — both the config list derivation and the subscribe() guard use it
- `finnhub_task = None` when `FINNHUB_API_KEY` absent — no crash, warning logged, Celery yfinance polling covers all tickers as fallback
- News endpoint uses existing `"news"` TTL tier (300s) already defined in `cache/ttl.py` — no new tier needed
- `datetime.now(tz=timezone.utc)` used instead of deprecated `datetime.utcnow()` — eliminates DeprecationWarning in test output

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced deprecated datetime.utcnow() with timezone-aware alternative**
- **Found during:** Task 2 test run
- **Issue:** `datetime.utcnow()` produced DeprecationWarning in Python 3.12+; warnings appeared in test output
- **Fix:** Replaced with `datetime.now(tz=timezone.utc)` in equity.py news endpoint
- **Files modified:** `backend/api/routes/equity.py`
- **Commit:** Included in `293f896`

## Known Stubs

- `backend/api/routes/equity.py` — 4 stubs remain intentionally returning 501:
  - `GET /api/equity/fundamentals/{ticker}` — Wave 2 (plan 03-03)
  - `GET /api/equity/short-interest/{ticker}` — Wave 2 (plan 03-03)
  - `GET /api/equity/insiders/{ticker}` — Wave 2 (plan 03-03)
  - `GET /api/equity/options/{ticker}` — Wave 3 (plan 03-05)

## Self-Check: PASSED

All key files confirmed present. Commits fe713b4 (Task 1) and 293f896 (Task 2) verified in git log.
