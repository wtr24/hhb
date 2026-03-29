---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Executing Phase 04
last_updated: "2026-03-29T20:37:43.341Z"
progress:
  total_phases: 12
  completed_phases: 3
  total_plans: 18
  completed_plans: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Unified zero-cost research terminal — pull up any instrument instantly with live quotes, charts, indicators, macro context, news sentiment, and positioning data
**Current focus:** Phase 04 — technical-analysis-engine

## Current Status

- **Phase**: 03 — Equity Overview (complete — 6/6 plans complete; user visual verification approved)
- **Last action**: 03-06 Task 3 complete — user visually approved full Equity Bloomberg module in browser
- **Next action**: Phase 04 planning or execution

## Milestone

**v1.0 — Full Terminal**: Phases 1–12

- 12 phases total
- 68 plans total
- 98 v1 requirements

## Progress

Phase 2: [██████████] 100% — 12/12 plans complete

## Gap Closure

- **02-07** — INGEST-04: Rate limiter wired into ingestion tasks — **complete** (2026-03-28)
  - Files: `backend/cache/rate_limiter.py`, `backend/ingestion/tasks.py`

## Decisions

- Used `condition: service_healthy` (not bare `depends_on`) on timescaledb and redis for api/beat/worker to prevent crash-loops on first boot
- Alembic configured with sync engine (psycopg2) for migrations even though app is async — avoids complexity
- `create_hypertable` called immediately after `op.create_table` with `if_not_exists => TRUE` for idempotent migrations
- Beat and worker containers have distinct commands to prevent duplicate scheduling if workers are scaled
- Sync SQLAlchemy and sync Redis used for Phase 1 FastAPI health checks — async upgrade deferred to later phase
- beat_schedule left empty dict in celery_app.py — Phase 2 populates with ingestion schedules
- WebSocket stub echoes messages; Phase 2 wires Redis pub/sub fan-out into ConnectionManager
- [Phase 01]: Frontend dev port remapped to 3000:5173 (Vite) not 3000:80 (Nginx) in docker-compose.dev.yml
- [Phase 01]: Anonymous volume /app/node_modules protects container npm install from host directory overwrite in dev
- [Phase 01]: docker-compose.prod.yml intentionally minimal for Phase 1 — resource limits deferred to later phases
- [Phase 01]: .env committed with empty API keys — Phase 1 does not use live data; keys populated before Phase 2 ingestion
- [Phase 02-01]: Added async engine (postgresql+asyncpg://) alongside sync engine in database.py — sync preserved for Alembic/Celery
- [Phase 02-01]: Compression policies for all 5 hypertables added in migration 0002 (30-day interval)
- [Phase 02-01]: YieldCurve PK is time-only — one canonical US Treasury snapshot per day
- [Phase 02-03]: Relative imports used in api/routes/quote.py (..database, ..redis_client) — consistent with health.py pattern, works inside api package namespace
- [Phase 02-03]: ingest_ticker lazy-imported inside get_quote function body to avoid circular import between api and ingestion packages
- [Phase 02]: SessionLocal context-manager pattern used for Celery tasks instead of plan-suggested _get_sync_session() helper — consistent with existing tasks.py
- [Phase 02]: Lazy model imports inside Celery tasks (from models.X import Y) used in 02-04 to avoid circular imports at module load time
- [Phase 02]: beat_schedule uses timedelta intervals (not crontab) — required for sub-minute FX 30s interval
- [Phase 02-06]: psubscribe used for all quotes:*/macro:*/fx:* channels with pmessage filter per D-10 and Pitfall 4
- [Phase 02-06]: lifespan manages single async Redis pub/sub task with task.cancel()+aclose() shutdown per Pitfall 8
- [Phase 02-07]: Rate limit check in tasks.py fires once per task invocation (not per-series in FRED loop) — avoids consuming tokens for every series iteration
- [Phase 02-07]: frankfurter and us_treasury guarded via check_rate_limit even without RATE_LIMITS entries — unknown sources pass through (returns True), wiring is consistent
- [Phase 02-07]: yfinance added to RATE_LIMITS at 60/60s (conservative); fetch_ohlcv_batch time.sleep(0.5) retained as secondary per-request throttle
- [Phase 03-01]: Equity stub routes return 501 JSON so tests have concrete assertion target before wave implementation lands
- [Phase 03-01]: cluster_insiders filters F/A/D codes (10b5-1, award, disposition), keeps only P/S open-market transactions
- [Phase 03-01]: bs_greeks vega divided by 100 to express per 1% IV move (industry convention for options analytics)
- [Phase 03-02]: FinnhubWebSocket uses websockets library (v16.0) — already installed, idiomatic async WS library
- [Phase 03-02]: is_finnhub_ws_eligible() is single source of truth for LSE/index exclusion from Finnhub WS
- [Phase 03-02]: finnhub_task=None when FINNHUB_API_KEY absent — graceful degradation, Celery yfinance polling covers all tickers
- [Phase 03]: lightweight-charts v5 addSeries(CandlestickSeries) used — addCandlestickSeries() removed in v5
- [Phase 03]: createSeriesMarkers() used for earnings/dividend markers — series.setMarkers() removed in v5
- [Phase 03]: Intraday time format is Unix seconds — lightweight-charts v5 requirement for sub-day intervals
- [Phase 03]: On-demand yfinance ingest for 1h/4h when no DB rows exist — avoids empty charts on first load
- [Phase 03-04]: Fundamentals endpoint supplements DB roe with yfinance returnOnEquity when null — single source of truth
- [Phase 03-04]: Short interest and insiders use macro TTL (1h) — corporate data updates infrequently, cache hit rate more important than freshness
- [Phase 03-04]: FundamentalsPanel multiplies ROE by 100 only when absolute value <= 5 — handles both decimal (0.45) and percentage (45) input from API
- [Phase 03-05]: Risk-free rate hardcoded at 0.045 with TODO comment — yield_curve table query deferred to Phase 8
- [Phase 03-05]: IV rank uses cross-strike median IV percentile (not 52-week history) — 52-week rank requires historical option data storage (Phase 8 screener)
- [Phase 03-05]: IVSurface uses HTML Canvas (not charting library) — compact heatmap strip above options table, no D3/recharts dependency
- [Phase 03-06]: App outer div changed from min-h-screen to h-screen flex flex-col — Bloomberg layout requires fixed viewport height (D-01: nothing scrolls)
- [Phase 03-06]: GBP rate fetched once on gbpMode=true, cached in gbpRate state — avoids re-fetch on every render, rate stable within session
- [Phase 04]: TA-Lib 0.6.8 ships manylinux_2_28 binary wheels — no Dockerfile changes needed for C library
- [Phase 04]: ta_pattern_stats win_rate and p_value nullable when n_occurrences < 30 (insufficient sample size)
- [Phase 04]: Wave 0 stubs use pytest.skip() to ensure pytest reports SKIPPED not ERROR for not-yet-implemented tests
- [Phase 04]: TA-Lib 0.6.8 binary wheels install via pip on both local Windows and Docker Linux containers — no Dockerfile changes needed
- [Phase 04]: pandas-ta (numba) used for HMA, VWMA, KDJ — TA-Lib does not cover these three
- [Phase 04]: DPO hand-rolled: DPO[i] = Close[i] - SMA(period)[i - period/2 - 1] — no TA-Lib support
- [Phase 04]: arch library isolated to garch.py to keep heavyweight imports out of indicators.py
- [Phase 04]: compute_garch_volatility returns error dict on <100 bars — no exception raised, caller-safe pattern
- [Phase 04]: CMF hand-rolled with numpy rolling window — ADOSC approximation less accurate than direct formula
- [Phase 04]: [Phase 04-03]: Celery task compute_nightly_pivot_points placed in tasks.py (not celery_app.py) for consistency with existing task function placement pattern
- [Phase 04]: [Phase 04-03]: pivot_points nightly task uses delete+insert pattern (not upsert) — PivotPoints composite PK has 4 columns, simplest correctness path
- [Phase 04]: deps.py does not exist — used ..database.get_async_db and ..redis_client.get_redis to match equity.py pattern (plan had wrong import path)
- [Phase 04]: TA dispatch dict uses _build_dispatch() closures per request — binds numpy arrays in scope, avoids global state leakage
- [Phase 04]: OOS split is last 20% of bars for pattern stats (not a fixed date) — consistent with plan spec D-10
- [Phase 04]: Candlestick task function in tasks.py (not celery_app.py); beat schedule in celery_app.py — avoids circular import
- [Phase 04-06]: detect_all_chart_patterns wraps each detector with try/except — one failing detector does not abort the aggregator
- [Phase 04-06]: TTL imported from cache.ttl.TTL dict directly in route handler (not via cache_set helper) — consistent with other ta.py route patterns
- [Phase 04]: Fibonacci route uses POST (not GET) — user-provided swing points are request body data, not path/query params
- [Phase 04]: Fibonacci levels include 0.0 prepended making total 9 levels (0.0 + 8 ratios) for frontend completeness
- [Phase 04]: No Redis caching on Fibonacci or EW routes — computations are instant and inputs unique per interaction

## Performance Metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01 | 01-01 | 118s | 2 | 11 |
| 01 | 01-02 | 53s | 2 | 10 |
| 01 | 01-03 | 113s | 2 | 15 |
| 01 | 01-04 | 26s | 1 | 1 |
| 01 | 01-05 | 45s | 2 | 3 |
| 02 | 02-01 | 3min | 2 | 11 |
| 02 | 02-02 | 2min | 1 | 7 |
| 02 | 02-03 | 2min | 2 | 7 |
| Phase 02 P04 | 216 | 2 tasks | 10 files |
| Phase 02 P02-05 | 58s | 1 tasks | 2 files |
| Phase 02 P06 | 73 | 2 tasks | 3 files |
| Phase 03 P03-01 | 25 | 2 tasks | 16 files |
| Phase 03 P03-02 | 248 | 2 tasks | 6 files |
| Phase 03 P03-03 | 199 | 2 tasks | 7 files |
| Phase 03 P03-04 | 290s | 2 tasks | 6 files |
| Phase 03 P05 | 412 | 2 tasks | 4 files |
| Phase 03 P03-06 | 148 | 2 tasks | 5 files |
| Phase 04 P04-00 | 240 | 3 tasks | 11 files |
| Phase 04 P04-01 | 270 | 2 tasks | 2 files |
| Phase 04 P04-02 | 301 | 2 tasks | 3 files |
| Phase 04 P04-03 | 267 | 4 tasks | 6 files |
| Phase 04 P04-04 | 264 | 2 tasks | 2 files |
| Phase 04 P04-05 | 234 | 3 tasks | 5 files |
| Phase 04 P04-06 | 90s | 2 tasks | 3 files |
| Phase 04 P04-07 | 185 | 3 tasks | 5 files |

## Notes

- All data sources zero-cost; API keys prompted before each test (see spec §9)
- T212 integration deferred to v2 milestone
- FinBERT model downloaded at container build time (~440MB)
- UK/LSE tickers tested with same priority as US tickers throughout

## Last Session

- **Stopped at**: Completed 04-07 (Fibonacci levels + Elliott Wave validation — TA-11, TA-12)
- **Timestamp**: 2026-03-29T21:04:00Z
