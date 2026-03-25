---
phase: 02-data-ingestion-foundation
plan: "02"
subsystem: cache
tags: [redis, token-bucket, rate-limiter, ttl, caching, celery, ingestion]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: redis_client.py sync Redis client used as pattern for cache helpers

provides:
  - Redis TTL cache helpers (cache_set, cache_get) with per-type expiry constants
  - Atomic token-bucket rate limiter via Lua script (check_rate_limit)
  - RATE_LIMITS constants matching spec (finnhub, fmp, alpha_vantage, coingecko)
  - Ingestion config (SEED_TICKERS, FRED_SERIES_MAP, RETRY_COUNTDOWNS, schedule constants)

affects:
  - 02-data-ingestion-foundation (all other plans use cache/ and ingestion/config.py)
  - All Celery worker tasks that check rate limits before firing API calls
  - FastAPI endpoints that call cache_get/cache_set for hot-path caching

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Token-bucket rate limiting via atomic Redis Lua script — no race conditions under concurrent Celery workers"
    - "TTL keyed by data type string ('quote', 'fx', 'fundamentals', etc.) — single dict drives all cache expiry"
    - "cache_set/cache_get wrap json.dumps/json.loads with default=str for non-JSON-native types"

key-files:
  created:
    - backend/cache/ttl.py
    - backend/cache/rate_limiter.py
    - backend/cache/__init__.py
    - backend/ingestion/config.py
    - backend/tests/ingestion/test_cache.py
    - backend/tests/__init__.py
    - backend/tests/ingestion/__init__.py
  modified: []

key-decisions:
  - "TTL values taken verbatim from spec §5: quote=15s, fx=30s, fundamentals=86400s, macro=3600s, yield_curve=900s"
  - "Token bucket uses Lua eval for atomicity — no Python-level locking needed under concurrent Celery workers"
  - "Unknown rate-limit sources default to True (allow) so new sources never accidentally block"
  - "FRED_SERIES_MAP includes 8 series (cpi, core_cpi, pce, gdp, fed_funds, unemployment, treasury_10y, treasury_2y) per context spec"

patterns-established:
  - "cache_set(redis_client, key, data, ttl_key) — pass client explicitly, no global state"
  - "check_rate_limit(redis_client, source) — returns bool, caller decides whether to proceed or skip"
  - "All Celery worker tasks should call check_rate_limit before any outbound API request"

requirements-completed: [INGEST-03, INGEST-04]

# Metrics
duration: 2min
completed: 2026-03-25
---

# Phase 2 Plan 02: Redis TTL Cache Helper and Token Bucket Rate Limiter Summary

**Redis TTL cache helpers (cache_set/cache_get) and atomic Lua token-bucket rate limiter with spec-compliant constants for all four API sources (Finnhub, FMP, Alpha Vantage, CoinGecko)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T21:05:40Z
- **Completed:** 2026-03-25T21:07:20Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 7

## Accomplishments
- TTL dict with all required data-type keys and spec-correct expiry values
- cache_set/cache_get helpers that wrap JSON serialisation and Redis get/set
- Atomic token-bucket Lua script stored in TOKEN_BUCKET_LUA constant
- RATE_LIMITS dict with all four API sources at correct capacity/window values
- backend.cache package with clean public exports
- SEED_TICKERS (9 assets covering equities, indices, crypto, FX), FRED_SERIES_MAP (8 series), RETRY_COUNTDOWNS, schedule constants
- 37 tests covering all behaviours, all passing

## Task Commits

TDD approach — RED then GREEN:

1. **RED — Failing tests** - `5f389f8` (test)
2. **GREEN — Implementation** - `1f883ef` (feat)

## Files Created/Modified
- `backend/cache/ttl.py` - TTL dict and cache_set/cache_get helpers
- `backend/cache/rate_limiter.py` - TOKEN_BUCKET_LUA Lua script, RATE_LIMITS, check_rate_limit
- `backend/cache/__init__.py` - Package exports (TTL, cache_set, cache_get, check_rate_limit, RATE_LIMITS)
- `backend/ingestion/config.py` - SEED_TICKERS, FRED_SERIES_MAP, RETRY_COUNTDOWNS, schedule constants
- `backend/tests/ingestion/test_cache.py` - 37 unit tests using unittest.mock
- `backend/tests/__init__.py` - Package init
- `backend/tests/ingestion/__init__.py` - Package init

## Decisions Made
- Token bucket implemented with Lua eval for atomicity — no race conditions when multiple Celery workers check limits simultaneously
- Unknown source keys return True (allow) by default in check_rate_limit — prevents silent breakage when new sources are added before rate limits are configured
- TTL dict includes extra keys (news=300, screener=900, crypto_marketcap=600) beyond the five required by the plan, matching the full spec §5 table
- FRED_SERIES_MAP extended to 8 series (context spec called for at minimum CPI, Core CPI, PCE, GDP, Fed Funds, UNRATE, 10Y/2Y Treasury)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- cache/ module fully implemented and tested; all other phase 02 plans can import from backend.cache
- backend/ingestion/config.py provides SEED_TICKERS and FRED_SERIES_MAP needed by Celery task plans
- RETRY_COUNTDOWNS and schedule constants available for Celery beat configuration

---
*Phase: 02-data-ingestion-foundation*
*Completed: 2026-03-25*

## Self-Check: PASSED

Files confirmed on disk:
- FOUND: backend/cache/ttl.py
- FOUND: backend/cache/rate_limiter.py
- FOUND: backend/cache/__init__.py
- FOUND: backend/ingestion/config.py
- FOUND: backend/tests/ingestion/test_cache.py

Commits confirmed:
- FOUND: 1f883ef (feat(02-02))
- FOUND: 5f389f8 (test(02-02))
