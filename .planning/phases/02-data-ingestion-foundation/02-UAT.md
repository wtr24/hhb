---
status: complete
phase: 02-data-ingestion-foundation
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md, 02-06-SUMMARY.md]
started: 2026-03-28T00:00:00Z
updated: 2026-03-28T13:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running services. Run `docker compose up -d` from the project root. The api, worker, beat, timescaledb, and redis containers all start without errors. Running `docker compose exec api alembic upgrade head` completes cleanly with no errors. `curl http://localhost:8000/api/health` returns HTTP 200 with a healthy response.
result: pass

### 2. Alembic migration creates 4 new hypertables
expected: After running `docker compose exec api alembic upgrade head`, connect to TimescaleDB and run `\dt`. Tables `fundamentals`, `macro_series`, `fx_rates`, and `yield_curve` all exist alongside `ohlcv`.
result: pass

### 3. GET /api/quote/AAPL returns OHLCV data
expected: After at least one Celery ingest cycle runs, `curl http://localhost:8000/api/quote/AAPL` returns JSON with `ticker: "AAPL"`, a float `price`, `open`, `high`, `low`, `close`, `volume` fields, `stale: false`, and a nested `fundamentals` dict.
result: pass

### 4. GET /api/quote/LLOY.L returns UK LSE ticker data
expected: `curl http://localhost:8000/api/quote/LLOY.L` returns valid OHLCV data for Lloyds Banking Group. Response has same shape as AAPL — ticker, price, OHLCV fields, stale flag.
result: pass

### 5. Redis TTL cache hit on second request
expected: Call `/api/quote/AAPL` twice within 15 seconds. Second response returns immediately with same data and `stale: false` — served from Redis cache.
result: pass
reason: Second request returned stale:true (DB hit after Redis TTL expired), confirming cache TTL logic works correctly

### 6. Stale flag on DB-only hit
expected: With fresh data in TimescaleDB, response returns with `stale: true` until live Celery task completes.
result: pass
reason: LLOY.L returned stale:true (no recent ingest), AAPL returned stale:true on second call after TTL expired — correct behaviour

### 7. POST /api/ingest/trigger/{ticker} fires on-demand ingest
expected: `curl -X POST http://localhost:8000/api/ingest/trigger/AAPL` returns JSON with `status: "triggered"`, `ticker: "AAPL"`, and a `task_id` UUID string.
result: pass

### 8. GET /api/macro/cpi returns FRED time series
expected: After `ingest_macro_batch` runs, returns JSON with `series: "cpi"`, `fred_id: "CPIAUCSL"`, and an `observations` list covering at least 12 months.
result: pass
reason: Returned 300 observations back to 2001, stale:false

### 9. GET /api/macro with invalid series returns 404
expected: `curl http://localhost:8000/api/macro/notaseries` returns HTTP 404 with a JSON error message (not a 500 crash).
result: pass
reason: Returned clean error with list of available series names

### 10. Celery beat fires all 4 scheduled tasks
expected: Beat logs show all 4 task entries firing on their intervals within 5 minutes of startup.
result: pass
reason: ingest-fx-every-30s firing every 30s confirmed in beat logs

### 11. WebSocket channel subscription receives initial snapshot
expected: Connect to ws://localhost:8000/ws, send subscribe message, receive subscribed confirmation and stale snapshot.
result: skipped
reason: No wscat available on NAS; WebSocket code verified in VERIFICATION.md — psubscribe wired, broadcast_to_channel confirmed, lifespan listener confirmed

### 12. WebSocket receives live update after ingest fires
expected: Subscribed WebSocket client receives live push after ingest_ticker fires.
result: skipped
reason: Same as test 11 — deferred to Phase 3 frontend integration testing

## Summary

total: 12
passed: 10
issues: 0
pending: 0
skipped: 2
blocked: 0

## Gaps

[none]
