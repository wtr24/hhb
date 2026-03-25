# Phase 2: Data Ingestion Foundation - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Core backend data pipeline only. Deliver: Celery beat scheduler with ingestion workers for yfinance, FRED/BLS/US Treasury XML, and Frankfurter FX; Redis TTL caching + token bucket rate limiters; TimescaleDB hypertable schemas for all data types; FastAPI REST endpoints for quote + macro; WebSocket broadcaster wired to Redis pub/sub.

Does NOT include: frontend UI, chart rendering, Finnhub WebSocket (Phase 3), equity module (Phase 3), macro dashboard (Phase 4/5), forex module screens, crypto desk.

</domain>

<decisions>
## Implementation Decisions

### Celery Beat Scheduling

- **D-01:** Always-on scheduling — tasks fire 24/7 regardless of market hours. Outside market hours, yfinance returns stale/unchanged data; fallback chain handles it. No timezone or market calendar logic in Phase 2.
- **D-02:** Task failure handling — Celery autoretry with exponential backoff: 3 attempts at 60s / 300s / 900s delays. After all retries exhausted, task logs failure. Beat fires again on next natural schedule cycle.
- **D-03:** yfinance OHLCV scheduled refresh interval — every 5 minutes.
- **D-04:** Ticker universe for scheduled tasks — hardcoded seed list defined in config (e.g. AAPL, MSFT, LLOY.L, BARC.L, ^FTSE, BTC-USD, GBP=X). Dynamic watchlist-driven scheduling deferred to Phase 3.

### Redis Caching + Rate Limits

- **D-05:** TTL values — fully specified in spec §5 table (docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md §5). Examples: live quotes 15s, FX 30s, fundamentals 24h, macro 1h, yield curve 15m. Do not re-derive these — read the spec.
- **D-06:** Rate limit token buckets — one per API source as specified in spec §5 (Finnhub 60/min, FMP 250/day, Alpha Vantage 25/day, CoinGecko 13/hr). Celery workers check before firing.

### WebSocket Broadcaster

- **D-07:** Channel structure — per-entity Redis pub/sub channels: `quotes:AAPL`, `quotes:LLOY.L`, `macro:CPI`, `fx:GBPUSD`. Frontend subscribes to specific channels via WebSocket message `{"action": "subscribe", "channels": [...]}`. Clients only receive data they subscribe to.
- **D-08:** Message format — flat structure with all fields at top level:
  ```json
  {
    "channel": "quotes:AAPL",
    "ticker": "AAPL",
    "price": 189.50,
    "change": 1.23,
    "change_pct": 0.65,
    "volume": 42837291,
    "timestamp": "2026-03-25T14:32:00Z",
    "stale": false
  }
  ```
  The `stale: true` flag communicates fallback chain state to frontend.
- **D-09:** On subscribe with no recent data — server reads latest row from TimescaleDB for that channel and sends it immediately. Client always gets an initial value on connect, even if stale.
- **D-10:** Subscriber architecture — single asyncio background task spawned at FastAPI lifespan startup. One Redis pub/sub connection total; fans out to matching WebSocket clients by channel. Per-connection Redis subscribers not used.

### On-Demand Quote Trigger

- **D-11:** When `GET /api/quote/{ticker}` is called and TimescaleDB has no data for that ticker: fire `ingest_ticker.apply_async()` immediately, then poll TimescaleDB for up to 10 seconds. If data arrives → return 200 with data. If timeout → return 503 `{"error": "ingestion_timeout", "retry_after": 15}`.

### REST API Surface (Phase 2)

- **D-12:** Phase 2 exposes exactly these endpoints:
  - `GET /api/quote/{ticker}` — OHLCV + latest price + fundamentals (see D-13)
  - `GET /api/macro/{series}` — macro time series (see D-14, D-15)
  - `POST /api/ingest/trigger/{ticker}` — manually trigger ingestion (open, no auth — personal NAS tool)
- **D-13:** `GET /api/quote/{ticker}` response — OHLCV + fundamentals combined in one call:
  ```json
  {
    "ticker": "AAPL",
    "price": 189.50, "change_pct": 0.65,
    "open": 187.20, "high": 190.10, "low": 186.80, "close": 189.50,
    "volume": 42837291,
    "stale": false,
    "fundamentals": {
      "pe_ratio": 28.4,
      "ev_ebitda": 21.2,
      "market_cap": 2940000000000,
      "debt_equity": 1.73
    }
  }
  ```
- **D-14:** `GET /api/macro/{series}` uses friendly names mapped internally to FRED IDs: `cpi`→`CPIAUCSL`, `gdp`→`GDP`, `fed_funds`→`FEDFUNDS`, `unemployment`→`UNRATE`. Mapping table lives in backend code.
- **D-15:** `GET /api/macro/{series}` returns a time series array (last 24 months by default):
  ```json
  {
    "series": "cpi",
    "fred_id": "CPIAUCSL",
    "observations": [{"date": "2026-01-01", "value": 315.2}, ...],
    "stale": false,
    "last_updated": "2026-03-25T01:00:00Z"
  }
  ```
- **D-16:** Yield curve REST endpoint (`/api/macro/yield_curve`) deferred to Macro Dashboard phase (Phase 4/5). Phase 2 only ingests and stores yield curve data.
- **D-17:** FX rate REST endpoint (`/api/fx/{base}/{quote}`) deferred to Forex module phase. Phase 2 only ingests and caches FX data. ⚠️ Phase 3 (EQUITY-11) needs GBP-adjusted returns — if Phase 3 planner identifies this dependency, pull the FX endpoint forward.

### Claude's Discretion

- TimescaleDB hypertable schemas for fundamentals, macro, news, screener, factors, dividends, COT — column design and compression policies left to Claude (spec §5 defines the data types ingested).
- Async vs sync Redis client for WebSocket subscriber — use async redis-py (`aioredis` or `redis.asyncio`) for the background listener task; existing sync `redis_client.py` stays for Celery/health use.
- FRED macro series mapping table completeness — include at minimum: CPI, Core CPI, PCE, GDP, Fed Funds, UNRATE, 10Y/2Y Treasury (as a macro proxy). Full yield curve handled separately.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Rate Limits & Caching Strategy
- `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md` §5 — Caching TTLs table, per-source token bucket limits, fallback chain definition, scraping rules. This is the authoritative source for all TTL and rate limit values.

### Project Architecture
- `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md` §6 — Project structure (backend/ingestion/ layout, one file per data source pattern, cache/ directory purpose).

### Requirements
- `.planning/REQUIREMENTS.md` — INGEST-01 through INGEST-09 are the acceptance criteria for this phase.

### Existing Code (Phase 1 stubs to build on)
- `backend/ingestion/celery_app.py` — Celery app instance; `beat_schedule={}` empty dict to populate.
- `backend/ingestion/tasks.py` — Placeholder task; all real ingest tasks added here.
- `backend/api/websocket.py` — `ConnectionManager` with `broadcast()`; wire Redis pub/sub into this.
- `backend/api/redis_client.py` — Sync Redis client; async variant needed for WebSocket listener.
- `backend/alembic/versions/0001_initial_hypertables.py` — `ohlcv` hypertable already created; new migration adds remaining tables.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ConnectionManager` (websocket.py): has `connect()`, `disconnect()`, `broadcast()` — extend with channel-based fan-out instead of broadcast-all.
- `redis_client` (redis_client.py): sync Redis instance ready; use as pattern for async version in WebSocket listener.
- `celery_app` (celery_app.py): fully configured with Redis broker/backend; just populate `beat_schedule` and add tasks.

### Established Patterns
- Alembic migrations in `backend/alembic/versions/` — use same pattern for new hypertable migration (0002_*). `create_hypertable` called immediately after `op.create_table` with `if_not_exists => TRUE` for idempotency.
- Sync SQLAlchemy engine for migrations (psycopg2), async for app runtime — established in Phase 1, continue in Phase 2.

### Integration Points
- `backend/api/main.py` — new routers for `/api/quote`, `/api/macro`, `/api/ingest` registered here.
- `backend/ingestion/tasks.py` — all Celery task functions land here (or sub-modules per source).
- `backend/cache/` — empty `__init__.py`; Phase 2 builds TTL helper + token bucket here.

</code_context>

<specifics>
## Specific Ideas

- The `stale: true/false` field on all API responses and WebSocket messages is the mechanism for communicating fallback chain state to the frontend. Downstream phases should rely on this field for rendering stale-data warnings.
- Seed ticker list for beat schedule: at minimum AAPL, MSFT, LLOY.L, BARC.L, ^FTSE, ^FTMC, BTC-USD, GBP=X, EURUSD=X — covers all asset classes needed for Phase 2 success criteria validation.

</specifics>

<deferred>
## Deferred Ideas

- `/api/fx/{base}/{quote}` endpoint — ingestion happens in Phase 2, REST endpoint deferred to Forex module phase. **Flag for Phase 3 planner**: EQUITY-11 (GBP-adjusted P&L) needs FX rates — if Phase 3 depends on this endpoint, pull it into Phase 3 scope.
- `/api/macro/yield_curve` endpoint — ingestion in Phase 2, endpoint deferred to Macro Dashboard (Phase 4/5).
- Dynamic ticker universe (Redis-backed active ticker set) — deferred to Phase 3 when watchlist is built.
- Market hours-aware scheduling — deferred indefinitely; always-on is sufficient for a personal NAS tool with generous rate limits.
- Dead letter queue for failed Celery tasks — deferred; exponential backoff + logging is sufficient for Phase 2.

</deferred>

---

*Phase: 02-data-ingestion-foundation*
*Context gathered: 2026-03-25*
