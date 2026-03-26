---
phase: 02-data-ingestion-foundation
plan: "06"
subsystem: api/websocket
tags: [websocket, redis, pubsub, realtime, fan-out]
dependency_graph:
  requires: ["02-01", "02-04"]
  provides: ["realtime-websocket-fan-out", "channel-subscriptions"]
  affects: ["frontend-websocket-client"]
tech_stack:
  added: ["redis.asyncio (pub/sub)", "asynccontextmanager lifespan"]
  patterns: ["per-channel fan-out", "asyncio background task", "psubscribe pattern matching"]
key_files:
  created: []
  modified:
    - backend/api/websocket.py
    - backend/api/redis_client.py
    - backend/api/main.py
decisions:
  - "psubscribe used (not subscribe) so all quotes:*, macro:*, fx:* channels matched with one call per D-10"
  - "pmessage type filter prevents subscription confirmation messages reaching clients per Research Pitfall 4"
  - "task.cancel() + pubsub.aclose() + redis.aclose() shutdown sequence prevents task leaks per Research Pitfall 8"
  - "send_initial_snapshot() imports AsyncSessionLocal lazily to avoid circular import"
  - "Legacy broadcast() method kept for backward compatibility with any existing callers"
metrics:
  duration: 73s
  completed: "2026-03-26"
  tasks: 2
  files: 3
---

# Phase 02 Plan 06: WebSocket Channel-Based Redis Pub/Sub Fan-Out Summary

Channel-based WebSocket fan-out wired to Redis pub/sub — ConnectionManager upgraded from broadcast-all echo stub to per-channel subscriber tracking with initial DB snapshot on subscribe, and FastAPI lifespan manages a single async Redis pub/sub listener that distributes messages to subscribed clients.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Upgrade ConnectionManager + WebSocket endpoint | 862891a | backend/api/websocket.py |
| 2 | Async Redis client + lifespan pub/sub listener | 1a06f60 | backend/api/redis_client.py, backend/api/main.py |

## What Was Built

### Task 1: ConnectionManager Upgrade (websocket.py)

Replaced the Phase 1 broadcast-all echo stub with a full channel-based subscription system:

- `channel_subscriptions: dict[str, set[WebSocket]]` — per-channel subscriber sets
- `subscribe(websocket, channel)` — registers a client to a channel (D-07)
- `unsubscribe_all(websocket)` — removes client from all channels on disconnect
- `broadcast_to_channel(channel, message)` — fans out only to subscribed clients (D-10), dead connection pruning included
- `send_initial_snapshot(websocket, channel)` — on subscribe, fetches latest TimescaleDB row and pushes it flagged `"stale": True` (D-09)
- `_fetch_latest_for_channel()` — handles quotes (OHLCV), macro (MacroSeries via FRED_SERIES_MAP), and fx (FXRate) channel types
- WebSocket endpoint parses JSON messages with `subscribe`/`unsubscribe` actions; unknown actions return error

### Task 2: Async Redis Client + Lifespan (redis_client.py, main.py)

- `get_async_redis_url()` added to redis_client.py — returns REDIS_URL for async client initialization while preserving sync redis_client unchanged
- `lifespan(app)` asynccontextmanager added to main.py — creates single `asyncio.create_task(_redis_pubsub_listener)` on startup, cancels and cleans up on shutdown
- `_redis_pubsub_listener()` — psubscribes to `quotes:*`, `macro:*`, `fx:*`; filters `message["type"] == "pmessage"` to skip subscription confirmations; deserializes JSON data; calls `manager.broadcast_to_channel(channel, data)`
- FastAPI app constructed with `lifespan=lifespan`

## Decisions Made

- Used `psubscribe` (pattern subscribe) rather than individual `subscribe` calls — one call covers all channel prefixes per D-10
- Filter `message["type"] == "pmessage"` prevents subscription confirmation messages (`psubscribe` type) from being forwarded to clients (Research Pitfall 4)
- Shutdown sequence: `task.cancel()` → `await task` (catches CancelledError) → `pubsub.punsubscribe()` → `pubsub.aclose()` → `async_redis.aclose()` — prevents task leaks and dangling connections (Research Pitfall 8)
- `send_initial_snapshot()` uses lazy import of `AsyncSessionLocal` inside the method body to avoid circular import between api and ingestion packages
- Legacy `broadcast()` method preserved for any backward compatibility needs

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all channel types (quotes, macro, fx) are wired to real TimescaleDB models. The initial snapshot returns `None` gracefully if no data exists yet in the DB, which is expected before ingestion runs.

## Self-Check

Files exist:
- backend/api/websocket.py — modified
- backend/api/redis_client.py — modified
- backend/api/main.py — modified

Commits:
- 862891a — feat(02-06): upgrade ConnectionManager to channel-based fan-out
- 1a06f60 — feat(02-06): add async Redis pub/sub lifespan listener in main.py
