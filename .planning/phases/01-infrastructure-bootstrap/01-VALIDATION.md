---
phase: 1
slug: infrastructure-bootstrap
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend); Vite built-in smoke (frontend) |
| **Config file** | `backend/pytest.ini` — Wave 0 creates this |
| **Quick run command** | `docker compose exec api pytest tests/ -x -q` |
| **Full suite command** | `docker compose exec api pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec api pytest tests/ -x -q`
- **After every plan wave:** Run `docker compose exec api pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + manual smoke checks documented
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | INFRA-01 | smoke | `docker compose up -d && docker compose ps` (all "running") | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-04 | smoke | `docker compose ps \| grep -E "beat\|worker"` (separate services) | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 2 | INFRA-02 | integration | `docker compose exec api pytest tests/test_health.py -x` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 2 | INFRA-07 | integration | `docker compose exec api pytest tests/test_migrations.py -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | INFRA-02 | integration | `docker compose exec api pytest tests/test_health.py -x` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 1 | INFRA-03 | manual | Open browser at localhost:3000 — verify amber text on black | manual | ⬜ pending |
| 1-04-01 | 04 | 1 | INFRA-06 | manual | Edit backend file → verify reload in container logs within 2s | manual | ⬜ pending |
| 1-05-01 | 05 | 1 | INFRA-05 | file | `grep -c "API_KEY=" .env.example` returns 7 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/pytest.ini` — pytest configuration with testpaths = tests
- [ ] `backend/tests/__init__.py` — empty init
- [ ] `backend/tests/conftest.py` — shared test fixtures (db connection, async test app client)
- [ ] `backend/tests/test_health.py` — stubs for INFRA-02 (GET /health returns 200, redis OK, timescaledb OK)
- [ ] `backend/tests/test_migrations.py` — stubs for INFRA-07 (verify hypertable exists in timescaledb after alembic upgrade)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bloomberg dark terminal renders at localhost:3000 | INFRA-03 | Browser visual check — amber text, black background, keyboard nav | `docker compose up -d` → open http://localhost:3000 → verify amber/black terminal aesthetic |
| Beat and worker are separate containers | INFRA-04 | Docker compose structural check | `docker compose ps` → verify "beat" and "worker" are distinct entries |
| Hot-reload works for backend in dev | INFRA-06 | Live filesystem watch — requires runtime verification | `docker compose -f docker-compose.dev.yml up` → edit `backend/api/main.py` → verify uvicorn reload in logs within 2s |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
