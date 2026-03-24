# Phase 1: Infrastructure Bootstrap - Research

**Researched:** 2026-03-24
**Domain:** Docker Compose multi-service stack, FastAPI, React/Vite, TimescaleDB, Celery, Redis
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Docker Compose stack starts all 6 services (frontend, api, beat, worker, redis, timescaledb) with `docker compose up -d` | docker-compose.yml structure, healthchecks, depends_on ordering documented below |
| INFRA-02 | FastAPI health endpoint returns 200 and reports status of all service dependencies | FastAPI health route pattern with async Redis ping and TimescaleDB connection check |
| INFRA-03 | React/Vite frontend serves Bloomberg dark terminal UI at port 3000 | Vite project scaffold + Nginx Dockerfile + TailwindCSS dark theme + keyboard nav patterns |
| INFRA-04 | Celery beat scheduler runs in its own container and does not share workers | Beat-only container pattern using `celery beat` command, separate from `celery worker` |
| INFRA-05 | `.env.example` documents all 7 required free API keys with signup links | 7 keys from spec §7: FRED, Finnhub, FMP, Alpha Vantage, EIA, BLS, Companies House |
| INFRA-06 | Development docker-compose override enables hot-reload for frontend and backend | `docker-compose.dev.yml` override with Vite dev server and uvicorn `--reload` flag |
| INFRA-07 | TimescaleDB hypertables created for all data types on first startup | Alembic migrations + `CREATE_HYPERTABLE` in initial migration, triggered on container start |
</phase_requirements>

---

## Summary

Phase 1 establishes the entire infrastructure skeleton: six Docker Compose services wired together, a health-checked FastAPI backend, a Bloomberg-aesthetic React/Vite frontend shell, Celery beat and worker containers separated by design, TimescaleDB hypertables initialised on first boot, and a dev override with hot-reload. This phase produces zero application features — only the skeleton that all subsequent phases build on.

The stack is fully locked by the project spec (FastAPI + React/Vite + TimescaleDB + Redis + Celery). There are no choices to make at infrastructure level — the research task is to identify the exact patterns, versions, and pitfalls for each of the six services and their wiring.

The most consequential pitfall in this phase is startup ordering. TimescaleDB takes 10–20 seconds to become ready on first boot (initialising the extension). All services that depend on it (api, beat, worker) must use `depends_on` with `condition: service_healthy` and a proper `pg_isready` healthcheck, not just `depends_on: timescaledb`. Failing to do this causes api and worker containers to crash-loop until TimescaleDB is ready, which looks like a Docker Compose bug but is a configuration error.

**Primary recommendation:** Use `condition: service_healthy` on all `depends_on` chains, configure a `pg_isready` healthcheck on timescaledb, and use Alembic for all migrations with `alembic upgrade head` run as a startup command in the api container (not a separate migration container for Phase 1).

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| timescale/timescaledb | 2.18.2-pg16 | TimescaleDB with Postgres 16 | Official image; pg16 matches spec; 2.18.x is current stable |
| redis | 7-alpine | Cache + pub/sub broker | Alpine image minimises size; version 7 for all Celery features |
| FastAPI | 0.135.2 | Python async web framework | Spec-locked; latest stable as of 2026-03-24 |
| uvicorn | 0.42.0 | ASGI server for FastAPI | Standard FastAPI ASGI server |
| Celery | 5.6.2 | Distributed task queue + scheduler | Spec-locked; 5.6.x is current stable |
| redis (Python) | 7.4.0 | Python Redis client | Used by Celery broker and FastAPI cache layer |
| SQLAlchemy | 2.0.48 | ORM + raw SQL for TimescaleDB | 2.0 async-native; required for Alembic |
| Alembic | 1.18.4 | Database migrations | Standard SQLAlchemy migration tool |
| psycopg2-binary | 2.9.11 | Postgres driver | Binary wheel; no libpq-dev needed in Docker |
| pydantic | 2.12.5 | Data validation for FastAPI models | FastAPI 0.100+ requires Pydantic v2 |
| python-dotenv | 1.2.2 | .env file loading | Standard 12-factor config loading |
| Vite | 8.0.2 | Frontend build tool + dev server | Spec-locked; 8.x is current major |
| React | 19.2.4 | UI framework | Spec-locked |
| @vitejs/plugin-react | 6.0.1 | Vite React HMR integration | Required for hot-reload in dev |
| TailwindCSS | 4.2.2 | Utility-first CSS | Spec-locked; 4.x uses CSS-first config (no tailwind.config.js by default) |
| lightweight-charts | 5.1.0 | TradingView charting | Spec-locked; Apache 2.0 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| flower | 2.0.1 | Celery monitoring web UI | Optional; useful for dev visibility |
| @types/react | 19.2.14 | TypeScript types for React | Required if using TypeScript in frontend |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg2-binary | asyncpg | asyncpg is faster for async but requires more boilerplate; psycopg2-binary is simpler and compatible with Alembic's sync interface |
| Alembic (sync) | Alembic async | Async migrations add complexity; sync Alembic with a sync engine for migrations is the standard pattern even in async FastAPI apps |
| Nginx serving Vite build | Node serving Vite build | Nginx is more appropriate for NAS deployment; Node should only serve in dev |

**Installation (backend container):**
```bash
pip install fastapi==0.135.2 uvicorn==0.42.0 celery==5.6.2 redis==7.4.0 \
  sqlalchemy==2.0.48 alembic==1.18.4 psycopg2-binary==2.9.11 \
  pydantic==2.12.5 python-dotenv==1.2.2
```

**Installation (frontend):**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss@4.2.2 lightweight-charts@5.1.0
```

---

## Architecture Patterns

### Recommended Project Structure

Per the design spec §6 (locked):

```
hhbfin/
├── frontend/
│   ├── src/
│   │   ├── components/        # Shared terminal UI components
│   │   ├── modules/           # Per-module directories
│   │   ├── hooks/             # useWebSocket, useMarketData, useKeyboard
│   │   └── lib/               # charts.ts, formatters.ts, keybindings.ts, theme.ts
│   ├── Dockerfile             # Multi-stage: build with Node, serve with Nginx
│   └── vite.config.ts
├── backend/
│   ├── api/                   # FastAPI route handlers
│   ├── ingestion/             # Celery tasks (Phase 2+)
│   ├── models/                # SQLAlchemy ORM models + hypertable schemas
│   ├── cache/                 # Redis helpers + TTL config
│   ├── scrapers/              # (Phase 2+)
│   ├── analysis/              # (Phase 4+)
│   ├── alembic/               # Alembic migrations directory
│   │   ├── versions/          # Migration scripts
│   │   └── env.py             # Alembic environment config
│   ├── alembic.ini            # Alembic config file
│   ├── requirements.txt       # Pinned dependencies
│   └── Dockerfile
├── docker-compose.yml         # Production compose
├── docker-compose.dev.yml     # Dev override (hot-reload)
└── .env.example               # All 7 API keys documented
```

### Pattern 1: Docker Compose Service Ordering with Health Checks

**What:** `depends_on` with `condition: service_healthy` ensures services wait for dependencies to be genuinely ready, not just started.

**When to use:** Always, for timescaledb, redis, and any service that depends on them.

```yaml
# docker-compose.yml
services:
  timescaledb:
    image: timescale/timescaledb:2.18.2-pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn api.main:app --host 0.0.0.0 --port 8000"

  beat:
    build: ./backend
    env_file: .env
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A ingestion.celery_app beat --loglevel=info

  worker:
    build: ./backend
    env_file: .env
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A ingestion.celery_app worker --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  timescaledb_data:
```

### Pattern 2: Dev Override for Hot-Reload (INFRA-06)

**What:** `docker-compose.dev.yml` overrides production compose to mount source code and enable hot-reload.

**When to use:** Local development only. Run with `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`.

```yaml
# docker-compose.dev.yml
services:
  api:
    volumes:
      - ./backend:/app
    command: >
      sh -c "alembic upgrade head &&
             uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

  beat:
    volumes:
      - ./backend:/app

  worker:
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      target: dev             # Multi-stage: stop at dev stage
    ports:
      - "3000:5173"           # Vite dev server port
    volumes:
      - ./frontend:/app
      - /app/node_modules     # Named volume prevents host overwrite of node_modules
    command: npm run dev -- --host 0.0.0.0
```

### Pattern 3: FastAPI Health Endpoint (INFRA-02)

**What:** `/health` route checks all dependency connections and returns structured status.

```python
# backend/api/health.py
from fastapi import APIRouter
from sqlalchemy import text
from .database import get_async_db
from .redis_client import get_redis
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check():
    status = {"status": "ok", "services": {}}

    # Redis check
    try:
        r = await get_redis()
        await r.ping()
        status["services"]["redis"] = "ok"
    except Exception as e:
        status["services"]["redis"] = f"error: {e}"
        status["status"] = "degraded"

    # TimescaleDB check
    try:
        async with get_async_db() as db:
            await db.execute(text("SELECT 1"))
        status["services"]["timescaledb"] = "ok"
    except Exception as e:
        status["services"]["timescaledb"] = f"error: {e}"
        status["status"] = "degraded"

    return status
```

### Pattern 4: Celery App Bootstrap (INFRA-04)

**What:** Single Celery app definition shared by both beat and worker containers. Beat is launched with `celery beat`, workers with `celery worker`. They must NEVER share a container to prevent duplicate task scheduling.

```python
# backend/ingestion/celery_app.py
from celery import Celery
import os

app = Celery(
    "hhbfin",
    broker=os.environ["REDIS_URL"],      # redis://redis:6379/0
    backend=os.environ["REDIS_URL"],
    include=["ingestion.tasks"],          # discovered task modules
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={},                     # populated in Phase 2
)
```

### Pattern 5: TimescaleDB Hypertable Migration (INFRA-07)

**What:** Alembic migration creates regular Postgres tables then converts them to TimescaleDB hypertables via `create_hypertable()`. This runs automatically on `alembic upgrade head` at container start.

```python
# backend/alembic/versions/0001_initial_hypertables.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create base table
    op.create_table(
        "ohlcv",
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("open", sa.Numeric(18, 6)),
        sa.Column("high", sa.Numeric(18, 6)),
        sa.Column("low", sa.Numeric(18, 6)),
        sa.Column("close", sa.Numeric(18, 6)),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("source", sa.String(20)),
    )

    # Convert to hypertable — time column is the partitioning key
    op.execute(
        "SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE)"
    )

    # Unique constraint for upserts (ticker + time per source)
    op.create_index("ix_ohlcv_ticker_time", "ohlcv", ["ticker", "time"])

def downgrade():
    op.drop_table("ohlcv")
```

Note: `create_hypertable` requires that no data exists in the table at conversion time. Always call it immediately after `CREATE TABLE` in the same migration.

### Pattern 6: Bloomberg Terminal Dark Theme Shell (INFRA-03)

**What:** Tailwind CSS 4 configuration for Bloomberg aesthetic. TailwindCSS 4 uses CSS-first configuration — there is no `tailwind.config.js` by default. The theme is defined in CSS using `@theme`.

```css
/* frontend/src/index.css */
@import "tailwindcss";

@theme {
  --color-terminal-bg: #0a0a0a;
  --color-terminal-amber: #ff9900;
  --color-terminal-green: #00d084;
  --color-terminal-dim: #404040;
  --color-terminal-border: #1a1a1a;
  --font-family-terminal: "Courier New", "Lucida Console", monospace;
}

body {
  background-color: var(--color-terminal-bg);
  color: var(--color-terminal-amber);
  font-family: var(--font-family-terminal);
  font-size: 12px;
}
```

```tsx
// frontend/src/App.tsx - Bloomberg terminal shell structure
export default function App() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#ff9900] font-mono text-xs">
      {/* Top bar: always-visible header with countdown timer slot */}
      <header className="border-b border-[#1a1a1a] px-2 py-1 flex justify-between">
        <span>HHBFIN TERMINAL</span>
        <span id="event-countdown">--:-- NEXT EVENT</span>
      </header>

      {/* Tab nav — keyboard navigable via number keys */}
      <nav className="border-b border-[#1a1a1a] flex">
        {["EQUITY", "MACRO", "FX", "CRYPTO", "NEWS", "SCREENER"].map((tab, i) => (
          <button
            key={tab}
            className="px-4 py-1 hover:bg-[#1a1a1a] focus:bg-[#ff9900] focus:text-black"
          >
            <span className="text-[#404040]">{i + 1}:</span>{tab}
          </button>
        ))}
      </nav>

      {/* Main module content area */}
      <main className="p-2">
        <p className="text-[#404040]">LOADING TERMINAL...</p>
      </main>
    </div>
  )
}
```

### Pattern 7: Frontend Dockerfile (Multi-Stage)

**What:** Multi-stage Dockerfile builds Vite bundle in a Node stage, then serves with Nginx in production. Dev stage stops at Node.

```dockerfile
# frontend/Dockerfile
FROM node:24-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Dev stage — for docker-compose.dev.yml
FROM base AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM base AS build
COPY . .
RUN npm run build

# Production stage — Nginx
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# frontend/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing — all paths serve index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to FastAPI (avoids CORS in production)
    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Anti-Patterns to Avoid

- **`depends_on` without `condition: service_healthy`:** Container will start before dependency is ready; causes crash-loops on first boot when TimescaleDB is initialising.
- **Running `celery beat` and `celery worker` in the same container:** Causes duplicate task scheduling if workers are ever scaled. INFRA-04 explicitly forbids this.
- **Running migrations outside api container:** A separate migration container or manual migration step is fragile. Run `alembic upgrade head` as the first command in the api container's startup.
- **`COPY . .` before `npm ci` in Dockerfile:** Invalidates npm cache on every source change. Always copy `package*.json` first, run `npm ci`, then copy source.
- **No named volume for `node_modules` in dev:** Mounting host `./frontend` into container overwrites `node_modules` with the empty host directory unless a named volume pins it.
- **Hardcoding credentials in `docker-compose.yml`:** All secrets go in `.env`, loaded via `env_file:`. The `.env.example` documents the keys; `.env` is gitignored.
- **TailwindCSS v4 configured with `tailwind.config.js`:** Tailwind 4 uses CSS-first config via `@theme` in CSS files. A `tailwind.config.js` still works but is the v3 pattern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Database migrations | Custom SQL init scripts | Alembic | Versioned, reversible, handles schema evolution across all phases |
| TimescaleDB hypertable conversion | Inline `CREATE TABLE` + `SELECT create_hypertable()` in a bare SQL file | Alembic migration with `op.execute()` | Alembic tracks whether migration has run; bare SQL files re-run and fail on table-already-exists |
| Service health check wiring | Bash sleep loops | Docker Compose `healthcheck` + `condition: service_healthy` | Docker handles retry logic; sleep loops are fragile and slow |
| Frontend SPA routing | Node server with Express | Nginx with `try_files` | Nginx is stateless, minimal, production-grade |
| Hot-reload in Docker | Custom file-watching scripts | Vite `--host` flag + volume mount; uvicorn `--reload` flag | Both tools have production-quality hot-reload built in |
| Redis connection pooling | Manual socket management | `redis.asyncio.Redis` with connection pool | Thread/coroutine-safe connection pool with automatic reconnect |

**Key insight:** TimescaleDB hypertable bootstrapping is the single most project-specific setup step. Alembic with `op.execute("SELECT create_hypertable(...)")` is the correct pattern — not an init SQL script in the Docker entrypoint, which does not integrate with the migration history.

---

## Common Pitfalls

### Pitfall 1: TimescaleDB Not Ready — Crash-Loop on First Boot
**What goes wrong:** `api`, `beat`, and `worker` containers start while TimescaleDB is still initialising (can take 20–30 seconds on first run). The containers crash with "connection refused", Docker restarts them, and the cycle repeats.
**Why it happens:** `depends_on: timescaledb` without `condition: service_healthy` only waits for the container to start, not for Postgres to be accepting connections.
**How to avoid:** Add a `healthcheck` using `pg_isready` to the timescaledb service, and use `condition: service_healthy` on all dependents. Set `start_period: 30s` to prevent false failures during init.
**Warning signs:** `psycopg2.OperationalError: could not connect to server` in api/worker logs on fresh `docker compose up`.

### Pitfall 2: Duplicate Celery Beat Scheduling
**What goes wrong:** If beat and worker are in the same container and you scale workers (`docker compose up --scale worker=3`), each new instance also runs a beat scheduler, resulting in tasks being enqueued N times.
**Why it happens:** `celery -A app worker -B` runs both beat and worker in the same process.
**How to avoid:** Never use `-B` flag. Beat container runs `celery beat` only. Worker container runs `celery worker` only. This is INFRA-04.
**Warning signs:** Tasks running twice or N times; duplicate database entries.

### Pitfall 3: Alembic Cannot Find Models
**What goes wrong:** `alembic upgrade head` runs but produces empty migrations or fails to import models.
**Why it happens:** `alembic/env.py` must import all SQLAlchemy models so `target_metadata` is populated. If models are not imported, Alembic generates empty migrations.
**How to avoid:** In `env.py`, import `Base` and all model modules before `target_metadata = Base.metadata`.
**Warning signs:** Running `alembic revision --autogenerate` produces a migration with no operations.

### Pitfall 4: `create_hypertable` Fails If Table Has Data
**What goes wrong:** `create_hypertable()` raises `ERROR: table "ohlcv" is not empty` if called after any data has been inserted.
**Why it happens:** TimescaleDB requires the table to be empty to convert it to a hypertable.
**How to avoid:** Always call `create_hypertable` in the same migration that creates the table, before any data is inserted. Use `if_not_exists => TRUE` to make it idempotent.
**Warning signs:** Migration fails with "table is not empty" on re-runs or non-fresh databases.

### Pitfall 5: TailwindCSS v4 Config Mismatch
**What goes wrong:** Styles don't apply, or build fails with "Cannot find module 'tailwindcss/plugin'".
**Why it happens:** TailwindCSS 4 is a breaking change from v3. It no longer uses `tailwind.config.js` for theme configuration by default. Theme is defined via `@theme` in CSS.
**How to avoid:** Use CSS-first config (`@theme` in `index.css`). If you need a config file for advanced use, use `tailwind.config.ts` with v4 API.
**Warning signs:** Terminal styled with defaults instead of custom amber/black theme.

### Pitfall 6: Vite Dev Server Not Accessible in Docker
**What goes wrong:** `npm run dev` inside container starts on `localhost:5173` but is not reachable from the host browser.
**Why it happens:** Vite's dev server binds to `127.0.0.1` by default inside the container.
**How to avoid:** Always pass `--host 0.0.0.0` (or `--host` with no argument) to Vite when running in Docker. In `vite.config.ts`, set `server.host: true` to apply to all environments.
**Warning signs:** Browser at `localhost:3000` (mapped port) gets "connection refused".

### Pitfall 7: Psycopg2 Binary Not Available in Alpine
**What goes wrong:** `psycopg2-binary` installs fine locally but fails with build errors in an Alpine-based Docker image.
**Why it happens:** Alpine uses musl libc; `psycopg2-binary` wheel requires glibc. Alpine needs `libpq-dev` and build tools, or use `python:3.11-slim` (Debian-based).
**How to avoid:** Use `python:3.11-slim` (not Alpine) for the backend Dockerfile, or install `libpq-dev gcc musl-dev` in the Alpine image before pip install.
**Warning signs:** `pip install psycopg2-binary` fails with "pg_config executable not found" in Docker build.

---

## Code Examples

Verified patterns from official sources and ecosystem standards:

### Alembic env.py with async SQLAlchemy

```python
# backend/alembic/env.py
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from alembic import context
import os

# Import all models so Base.metadata is populated
from models.base import Base
import models.ohlcv  # noqa: F401 — side-effect import

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = os.environ["DATABASE_URL"]
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Note: Alembic must use sync engine for migrations.
    # Use psycopg2 URL (postgresql://), not asyncpg (postgresql+asyncpg://)
    from sqlalchemy import create_engine
    url = os.environ["DATABASE_URL"].replace("+asyncpg", "")
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as conn:
        do_run_migrations(conn)
    engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### FastAPI Application Bootstrap

```python
# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .health import router as health_router

app = FastAPI(title="HHBFin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])

@app.get("/")
async def root():
    return {"status": "HHBFIN TERMINAL API"}
```

### .env.example (INFRA-05)

```bash
# Database
POSTGRES_USER=hhbfin
POSTGRES_PASSWORD=changeme
POSTGRES_DB=hhbfin
DATABASE_URL=postgresql://hhbfin:changeme@timescaledb:5432/hhbfin

# Redis
REDIS_URL=redis://redis:6379/0

# Free API Keys — one-time signup, no credit card required
# 1. FRED (Federal Reserve Economic Data) — https://api.stlouisfed.org/ → Register → Get API Key
FRED_API_KEY=

# 2. Finnhub (real-time quotes, news, insider data) — https://finnhub.io → Sign Up Free
FINNHUB_API_KEY=

# 3. Financial Modeling Prep (fundamentals, income statements) — https://financialmodelingprep.com → Free Plan
FMP_API_KEY=

# 4. Alpha Vantage (technical indicators) — https://www.alphavantage.co/support/#api-key → Free Key
ALPHA_VANTAGE_API_KEY=

# 5. EIA (US energy data, oil inventories) — https://www.eia.gov/opendata/register.php
EIA_API_KEY=

# 6. BLS (US Bureau of Labor Statistics — payrolls, CPI) — https://www.bls.gov/developers/api_registration.htm
BLS_API_KEY=

# 7. Companies House (UK company filings) — https://developer.company-information.service.gov.uk → Register
COMPANIES_HOUSE_API_KEY=
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | All 6 services | Yes | 29.2.1 | — |
| Docker Compose | `docker compose up -d` | Yes | v5.0.2 | — |
| Node.js | Frontend build | Yes | 24.14.0 | — |
| npm | Frontend packages | Yes | 11.9.0 | — |
| Python | Backend local dev | Yes | 3.14.3 | — (Docker uses 3.11 image) |
| pip | Python packages | Yes | 25.3 | — |
| timescale/timescaledb image | timescaledb service | Not pulled | 2.18.2-pg16 | Pulled on first `docker compose up` |
| redis image | redis service | Not pulled | 7-alpine | Pulled on first `docker compose up` |

**Missing dependencies with no fallback:** None — all required tools are available.

**Missing dependencies with fallback:** Docker images for TimescaleDB and Redis are not pre-pulled, but `docker compose up` will pull them automatically on first run. No manual action required.

**Note on Python version:** The host has Python 3.14.3, but the Docker container must pin `python:3.11-slim` per the spec ("FastAPI Python 3.11"). psycopg2-binary and TA-Lib have confirmed Python 3.11 wheels. Python 3.14 compatibility for some scientific libraries (TA-Lib in particular) is not guaranteed.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend); Vite built-in (frontend smoke) |
| Config file | `backend/pytest.ini` — Wave 0 |
| Quick run command | `docker compose exec api pytest tests/ -x -q` |
| Full suite command | `docker compose exec api pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | All 6 services start without error | smoke | `docker compose up -d && docker compose ps` (check all "running") | Wave 0 |
| INFRA-02 | `GET /health` returns 200 + redis and timescaledb OK | integration | `docker compose exec api pytest tests/test_health.py -x` | Wave 0 |
| INFRA-03 | Browser at localhost:3000 shows terminal shell | manual smoke | Open browser — verify amber text on black background | manual |
| INFRA-04 | Beat runs separately from workers | smoke | `docker compose ps` — verify "beat" and "worker" are separate services | manual |
| INFRA-05 | `.env.example` lists all 7 keys with URLs | file check | `grep -c "API_KEY=" .env.example` returns 7 | file |
| INFRA-06 | Hot-reload works in dev | manual smoke | Edit backend file → verify reload in container logs | manual |
| INFRA-07 | Hypertables created on first startup | integration | `docker compose exec api pytest tests/test_migrations.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `docker compose exec api pytest tests/ -x -q`
- **Per wave merge:** `docker compose exec api pytest tests/ -v`
- **Phase gate:** All automated tests green + manual smoke checks documented before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/pytest.ini` — pytest configuration
- [ ] `backend/tests/__init__.py` — empty init
- [ ] `backend/tests/test_health.py` — covers INFRA-02 (GET /health returns 200, services ok)
- [ ] `backend/tests/test_migrations.py` — covers INFRA-07 (hypertables exist after alembic upgrade head)
- [ ] `backend/tests/conftest.py` — shared test fixtures (db connection, test app client)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TailwindCSS config in `tailwind.config.js` | CSS-first config via `@theme` in CSS | Tailwind v4 (2025) | Must use `@theme` for custom Bloomberg colors |
| Pydantic v1 models (`class Config:`) | Pydantic v2 (`model_config = ConfigDict(...)`) | FastAPI 0.100+ / Pydantic v2 (2023) | All model config uses v2 API |
| `celery -A app worker --beat` (combined) | Separate `celery beat` container | Celery best practice | INFRA-04 requires explicit separation |
| Docker Compose v2 (`version: "3"` header) | Docker Compose v5, no version header needed | Docker Compose v2.0+ | Remove `version:` key from compose files |

**Deprecated/outdated:**
- `version: "3.8"` in docker-compose.yml: The `version` key is obsolete in Compose v2+. Omit it entirely.
- `celery worker -B` flag: Combining beat and worker. Forbidden by INFRA-04.
- `tailwind.config.js` with `theme.extend.colors`: Still functional but v3 pattern. Use `@theme` in v4.

---

## Open Questions

1. **TimescaleDB hypertable schema completeness for Phase 1**
   - What we know: INFRA-07 says "hypertables created for all data types on first startup"
   - What's unclear: Phase 1 has no data ingestion (Phase 2+), so only a minimal set of hypertable schemas need to exist. Creating placeholder schemas for all future data types now vs creating them in the phases that use them.
   - Recommendation: Create only the `ohlcv` table as a demonstration hypertable in Phase 1 (proves the migration mechanism works). Subsequent phases add their own migrations. This avoids needing to know the complete schema before the data is defined.

2. **Nginx proxy_pass vs CORS for API**
   - What we know: Frontend is at port 3000, API at port 8000. In production (NAS), both behind same Docker network.
   - What's unclear: Whether the frontend should call `/api/...` (proxied through Nginx) or `http://localhost:8000/...` directly.
   - Recommendation: Use Nginx proxy (`location /api/` → `http://api:8000/`) for production. Vite proxy (`server.proxy` in `vite.config.ts`) for dev. This keeps API calls relative and avoids CORS config in production.

---

## Sources

### Primary (HIGH confidence)
- Official Docker Compose docs — `depends_on` with `condition: service_healthy`
- TimescaleDB official docs — `create_hypertable()` syntax and requirements
- Alembic official docs — `env.py` configuration and `op.execute()` pattern
- FastAPI official docs — health endpoint, CORS, router patterns
- Celery official docs — beat scheduler separation pattern
- npm registry — verified package versions: vite@8.0.2, react@19.2.4, tailwindcss@4.2.2, lightweight-charts@5.1.0
- PyPI registry — verified package versions: fastapi@0.135.2, celery@5.6.2, redis@7.4.0, alembic@1.18.4, uvicorn@0.42.0
- TailwindCSS v4 docs — CSS-first `@theme` configuration

### Secondary (MEDIUM confidence)
- Docker Desktop 29.2.1 confirmed available on host machine (verified by Bash probe)
- Docker Compose v5.0.2 confirmed available (verified by Bash probe)
- Node 24.14.0, npm 11.9.0, Python 3.14.3 confirmed available (verified by Bash probe)

### Tertiary (LOW confidence)
- None — all critical claims verified against official docs or package registry

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against npm and PyPI registries
- Architecture: HIGH — Docker Compose patterns from official docs; TimescaleDB from official docs
- Pitfalls: HIGH — startup ordering and hypertable pitfalls are documented in TimescaleDB and Docker Compose official docs

**Research date:** 2026-03-24
**Valid until:** 2026-06-24 (stable ecosystem — 90 days reasonable; check for TimescaleDB image updates before execution)
