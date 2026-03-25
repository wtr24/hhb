---
phase: 02
slug: data-ingestion-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `backend/pytest.ini` or `backend/pyproject.toml [tool.pytest.ini_options]` |
| **Quick run command** | `docker compose exec api pytest backend/tests/ingestion/ -x -q` |
| **Full suite command** | `docker compose exec api pytest backend/tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec api pytest backend/tests/ingestion/ -x -q`
- **After every plan wave:** Run `docker compose exec api pytest backend/tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | INGEST-01 | unit | `docker compose exec api pytest backend/tests/ingestion/test_schemas.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | INGEST-01 | integration | `docker compose exec api pytest backend/tests/ingestion/test_schemas.py -x -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | INGEST-02 | unit | `docker compose exec api pytest backend/tests/ingestion/test_yfinance.py -x -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | INGEST-03 | unit | `docker compose exec api pytest backend/tests/ingestion/test_yfinance.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 1 | INGEST-04 | unit | `docker compose exec api pytest backend/tests/ingestion/test_fred.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 1 | INGEST-05 | unit | `docker compose exec api pytest backend/tests/ingestion/test_frankfurter.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 1 | INGEST-06 | unit | `docker compose exec api pytest backend/tests/ingestion/test_treasury.py -x -q` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 1 | INGEST-07 | unit | `docker compose exec api pytest backend/tests/ingestion/test_cache.py -x -q` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 2 | INGEST-08 | integration | `docker compose exec api pytest backend/tests/ingestion/test_celery.py -x -q` | ❌ W0 | ⬜ pending |
| 02-05-02 | 05 | 2 | INGEST-09 | integration | `docker compose exec api pytest backend/tests/ingestion/test_celery.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/ingestion/__init__.py` — package init
- [ ] `backend/tests/ingestion/conftest.py` — shared fixtures (mock Redis, TimescaleDB session, Celery test config)
- [ ] `backend/tests/ingestion/test_schemas.py` — stubs for INGEST-01 (hypertable creation, ON CONFLICT upsert)
- [ ] `backend/tests/ingestion/test_yfinance.py` — stubs for INGEST-02, INGEST-03 (mock yfinance responses)
- [ ] `backend/tests/ingestion/test_fred.py` — stubs for INGEST-04 (mock FRED API)
- [ ] `backend/tests/ingestion/test_frankfurter.py` — stubs for INGEST-05 (mock Frankfurter API)
- [ ] `backend/tests/ingestion/test_treasury.py` — stubs for INGEST-06 (mock Treasury XML)
- [ ] `backend/tests/ingestion/test_cache.py` — stubs for INGEST-07 (Redis TTL 60s/300s/900s)
- [ ] `backend/tests/ingestion/test_celery.py` — stubs for INGEST-08, INGEST-09 (Celery beat schedule, retry logic)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `GET /api/quote/LLOY.L` returns LSE data | INGEST-03 | Requires live yfinance call to Yahoo Finance | Run `curl http://localhost:8000/api/quote/LLOY.L` after Celery worker has run |
| `GET /api/macro/fred/GDP` returns FRED data | INGEST-04 | Requires live FRED API key + network | Run `curl http://localhost:8000/api/macro/fred/GDP` with FRED_API_KEY set |
| Celery beat fires without duplication | INGEST-08 | Requires running beat + worker + monitoring logs | Run `docker compose logs beat worker` and confirm single execution per schedule |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
