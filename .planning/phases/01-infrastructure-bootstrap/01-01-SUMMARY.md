---
phase: 1
plan: "01-01"
subsystem: infrastructure
tags: [docker, timescaledb, redis, celery, alembic, sqlalchemy, fastapi]
dependency_graph:
  requires: []
  provides: [docker-compose-stack, backend-dockerfile, alembic-migrations, sqlalchemy-models]
  affects: [01-02, 01-03, 01-04, 01-05]
tech_stack:
  added:
    - timescale/timescaledb:2.18.2-pg16
    - redis:7-alpine
    - python:3.11-slim
    - fastapi==0.135.2
    - uvicorn==0.42.0
    - celery==5.6.2
    - redis==7.4.0
    - sqlalchemy==2.0.48
    - alembic==1.18.4
    - psycopg2-binary==2.9.11
    - pydantic==2.12.5
    - python-dotenv==1.2.2
  patterns:
    - condition:service_healthy depends_on for all TimescaleDB/Redis dependents
    - Alembic sync engine for migrations (psycopg2), not asyncpg
    - create_hypertable called immediately after CREATE TABLE in same migration
    - DeclarativeBase (SQLAlchemy 2.0) over legacy declarative_base()
key_files:
  created:
    - docker-compose.yml
    - backend/Dockerfile
    - backend/requirements.txt
    - backend/models/base.py
    - backend/models/ohlcv.py
    - backend/models/__init__.py
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/alembic/versions/0001_initial_hypertables.py
    - backend/alembic/versions/__init__.py
    - .gitignore
  modified: []
decisions:
  - "Used condition:service_healthy (not just depends_on) on timescaledb and redis for all 3 dependent services (api, beat, worker) to prevent crash-loops on first boot"
  - "Alembic configured with sync engine (psycopg2) even though app is async; async Alembic adds complexity for no benefit in this project"
  - "create_hypertable called immediately after op.create_table with if_not_exists=>TRUE guard for idempotent migrations"
  - "Beat and worker containers have distinct commands (celery beat vs celery worker) to prevent duplicate scheduling if workers are scaled"
metrics:
  duration: 118s
  completed_date: "2026-03-24"
  tasks_completed: 2
  tasks_total: 2
  files_created: 11
  files_modified: 0
---

# Phase 1 Plan 01: Docker Compose + TimescaleDB + Redis + Backend Dockerfile Summary

**One-liner:** Six-service Docker Compose stack with pg_isready/redis-cli healthchecks, python:3.11-slim backend Dockerfile, and Alembic migration creating ohlcv hypertable on first boot.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Docker Compose stack with healthchecks + backend Dockerfile + .gitignore | 999b1cf | docker-compose.yml, backend/Dockerfile, backend/requirements.txt, .gitignore |
| 2 | SQLAlchemy models + Alembic config + initial ohlcv hypertable migration | 0769fe7 | backend/models/*.py, backend/alembic.ini, backend/alembic/env.py, backend/alembic/versions/0001_initial_hypertables.py |

## What Was Built

### docker-compose.yml
Six services with proper startup ordering:
- **timescaledb**: `timescale/timescaledb:2.18.2-pg16` with `pg_isready` healthcheck (`start_period: 30s` to handle init)
- **redis**: `redis:7-alpine` with `redis-cli ping` healthcheck
- **api**: builds `./backend`, runs `alembic upgrade head && uvicorn`, depends on both with `condition: service_healthy`
- **beat**: `celery -A ingestion.celery_app beat --loglevel=info` (beat-only, never worker)
- **worker**: `celery -A ingestion.celery_app worker --loglevel=info` (worker-only, never beat)
- **frontend**: builds `./frontend`, serves at `3000:80`

### backend/Dockerfile
`python:3.11-slim` base, installs `gcc libpq-dev`, copies `requirements.txt` before source (Docker layer caching), exposes port 8000.

### backend/requirements.txt
Nine pinned packages: fastapi, uvicorn, celery, redis, sqlalchemy, alembic, psycopg2-binary, pydantic, python-dotenv.

### SQLAlchemy Models
- `models/base.py`: `DeclarativeBase` (SQLAlchemy 2.0 style)
- `models/ohlcv.py`: `OHLCV` model with composite PK `(time, ticker)`, 8 columns, `ix_ohlcv_ticker_time` index
- `models/__init__.py`: exports `Base` and `OHLCV`

### Alembic Infrastructure
- `alembic.ini`: `script_location = alembic`, `sqlalchemy.url` left empty (overridden by env.py)
- `alembic/env.py`: reads `DATABASE_URL` from `os.environ`, strips `+asyncpg` driver for psycopg2 compatibility, uses `engine_from_config` (sync), imports all models before `target_metadata = Base.metadata`
- `alembic/versions/0001_initial_hypertables.py`: creates `ohlcv` table, immediately converts to hypertable with `if_not_exists => TRUE`, creates composite index

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan creates infrastructure configuration files only, no data-rendering UI components.

## Verification Results

- docker-compose.yml: no `version:` header (Compose v2+ format)
- `grep -c "service_healthy" docker-compose.yml` returns 6 (2 per api/beat/worker)
- timescaledb healthcheck uses `pg_isready` with `start_period: 30s`
- redis healthcheck uses `redis-cli ping`
- beat command: `celery -A ingestion.celery_app beat --loglevel=info`
- worker command: `celery -A ingestion.celery_app worker --loglevel=info`
- api command: `alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000`
- frontend ports: `3000:80`
- Dockerfile FROM: `python:3.11-slim AS base`
- `COPY requirements.txt .` before `COPY . .`
- All 9 packages pinned in requirements.txt
- `class Base(DeclarativeBase)` in models/base.py
- `class OHLCV(Base)` with `__tablename__ = "ohlcv"` in models/ohlcv.py
- `target_metadata = Base.metadata` in alembic/env.py
- `engine_from_config` (sync) used, no `create_async_engine`
- `SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE)` after `op.create_table` in migration 0001
- `down_revision = None` in migration 0001

## Self-Check: PASSED
