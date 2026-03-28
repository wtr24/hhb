---
plan: 02-07
phase: 02-data-ingestion-foundation
status: complete
subsystem: ingestion
tags: [rate-limiting, celery, ingestion, gap-closure]
requirements: [INGEST-04]
key-decisions:
  - "yfinance added to RATE_LIMITS at 60/60s (conservative 1 req/s); fetch_ohlcv_batch time.sleep(0.5) retained as secondary per-request throttle"
  - "frankfurter and us_treasury guarded via check_rate_limit even without RATE_LIMITS entries — unknown sources pass through (True), wiring is consistent across all 5 tasks"
  - "Rate limit check fires once per task invocation (not per-series in FRED loop) — avoids consuming tokens for every series iteration"
key-files:
  modified:
    - backend/cache/rate_limiter.py
    - backend/ingestion/tasks.py
metrics:
  duration: ~5min
  completed: "2026-03-28"
  tasks_completed: 3
  files_modified: 2
---

# Phase 02 Plan 07: Wire rate limiter into ingestion tasks — Summary

## One-liner

Token-bucket rate limiter wired into all 5 Celery ingestion tasks via `check_rate_limit` guards, with yfinance added to `RATE_LIMITS` at 60 req/60s.

## What was done

**Task 1 — Added yfinance to RATE_LIMITS (`backend/cache/rate_limiter.py`)**

Added entry after `coingecko` with capacity=60, per_seconds=60. Added explanatory comment noting the unofficial Yahoo Finance API nature and the existing `time.sleep(0.5)` in `fetch_ohlcv_batch` as a secondary throttle.

**Task 2 — Wired 5 rate limit guards (`backend/ingestion/tasks.py`)**

Added import `from cache.rate_limiter import check_rate_limit` and added a consistent guard block before every external API call:

| Task | Source key | RATE_LIMITS entry? | Behaviour |
|---|---|---|---|
| `ingest_ohlcv_batch` | `"yfinance"` | Yes (60/60s) | Token bucket enforced |
| `ingest_ticker` | `"yfinance"` | Yes (60/60s) | Token bucket enforced |
| `ingest_macro_batch` | `"fred"` | No — pass-through | Always True; wired for future |
| `ingest_fx_rates` | `"frankfurter"` | No — pass-through | Always True; wired for future |
| `ingest_treasury_curve` | `"us_treasury"` | No — pass-through | Always True; wired for future |

All guards use the pattern from the plan spec: if throttled, `logger.warning` then `raise self.retry(countdown=RETRY_COUNTDOWNS[0])`.

**Task 3 — Static AST smoke test**

Both files parsed without syntax errors. `check_rate_limit` occurrence count = 6 (1 import + 5 calls). Test output: `Static checks passed`.

## Files changed

- `backend/cache/rate_limiter.py` — yfinance entry + comment added to RATE_LIMITS
- `backend/ingestion/tasks.py` — import + 5 rate limit guard blocks added

## Commits

- `be98852` — `feat(02-07): add yfinance entry to RATE_LIMITS`
- `5dc6749` — `feat(02-07): wire check_rate_limit guards into all 5 ingestion tasks`

## Verification

```
$ grep -n "check_rate_limit" backend/ingestion/tasks.py
16:from cache.rate_limiter import check_rate_limit
34:        if not check_rate_limit(redis_client, "yfinance"):
53:        if not check_rate_limit(redis_client, "yfinance"):
95:        if not check_rate_limit(redis_client, "fred"):
139:        if not check_rate_limit(redis_client, "frankfurter"):
188:        if not check_rate_limit(redis_client, "us_treasury"):

$ python -c "import ast, pathlib; src=pathlib.Path('ingestion/tasks.py').read_text(); ast.parse(src); assert src.count('check_rate_limit') >= 6; print('ok')"
ok
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. `fred`, `frankfurter`, and `us_treasury` pass through `check_rate_limit` because they have no RATE_LIMITS entries (unknown sources always return True per existing logic). This is intentional documented behaviour, not a stub — RATE_LIMITS entries for these sources can be added when rate limits become relevant.

## Self-Check: PASSED

- `backend/cache/rate_limiter.py` contains "yfinance" entry: FOUND
- `backend/ingestion/tasks.py` has 6 occurrences of `check_rate_limit`: FOUND
- Commit `be98852` exists: FOUND
- Commit `5dc6749` exists: FOUND
