---
phase: 05-macro-dashboard
plan: "10"
subsystem: testing
tags: [react, fastapi, celery, barrel-exports, integration-tests, typescript]

requires:
  - phase: 05-macro-dashboard
    provides: all macro components (05-05 to 05-09), API routes (05-04), ingestion tasks (05-01 to 05-03)

provides:
  - Barrel export index.ts for all 18 macro components
  - Confirmed macro router registration in main.py
  - 19 integration smoke tests covering MACRO-01 through MACRO-14
  - TypeScript clean build (tsc --noEmit exit 0)

affects: [future phase consumers of macro components, CI test suite]

tech-stack:
  added: []
  patterns:
    - "Barrel export index.ts pattern for component directories"
    - "Import ingestion.tasks before checking Celery app task registry to trigger @app.task registration"

key-files:
  created:
    - frontend/src/components/macro/index.ts
    - backend/tests/macro/test_macro_integration.py
  modified: []

key-decisions:
  - "Celery task registration test helper imports ingestion.tasks explicitly before querying app.tasks — without this side-effect import the @app.task-decorated functions are not yet registered and the registry only shows built-in celery.* tasks"
  - "Task 5-10-2 required no file changes — macro router was already imported and registered in main.py from Phase 05-04 work"

patterns-established:
  - "Integration smoke tests: import side-effect pattern for Celery task registry checks"

requirements-completed: [MACRO-01, MACRO-02, MACRO-03, MACRO-04, MACRO-05, MACRO-06, MACRO-07, MACRO-08, MACRO-09, MACRO-10, MACRO-11, MACRO-12, MACRO-13, MACRO-14]

duration: 8min
completed: 2026-03-30
---

# Phase 5 Plan 10: Integration Wiring Summary

**Barrel export for all 18 macro components, confirmed router registration, and 19 integration smoke tests verifying MACRO-01 through MACRO-14 end-to-end with clean TypeScript build**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-30T20:35:00Z
- **Completed:** 2026-03-30T20:43:00Z
- **Tasks:** 4 (3 with file changes + 1 verification)
- **Files modified:** 2

## Accomplishments

- Created `frontend/src/components/macro/index.ts` re-exporting all 18 macro components built in plans 05-05 through 05-09
- Confirmed `macro_router` already imported and registered in `backend/api/main.py` (no changes required)
- Created 19 integration smoke tests in `backend/tests/macro/test_macro_integration.py` — all pass — covering importability of all 6 ingestion source modules, Celery task registration for BoE/VIX/CBOE/breadth tasks, FRED series map coverage (TIPS breakeven, HY spread, DXY), DB model importability (GiltCurve, VixTermStructure), and TTL cache key coverage
- TypeScript compiler (`npx tsc --noEmit`) exits 0 — all 18 macro components type-check cleanly

## Task Commits

1. **Task 5-10-1: Macro component barrel export** - `475200f` (feat)
2. **Task 5-10-2: Verify macro router registration** - no commit (already present, no file changes)
3. **Task 5-10-3: Integration smoke tests** - `72efa53` (test)
4. **Task 5-10-4: TypeScript build verification** - no commit (verification only, exit 0)

## Files Created/Modified

- `frontend/src/components/macro/index.ts` - Barrel export re-exporting all 18 macro components
- `backend/tests/macro/test_macro_integration.py` - 19 integration smoke tests for MACRO-01 through MACRO-14

## Decisions Made

- Celery task registration checks require explicit `import ingestion.tasks` before querying `app.tasks` — without this import the `@app.task` decorators have not fired and only Celery built-in tasks appear in the registry. Added `_get_registered_task_names()` helper to ensure this side-effect import happens before each task-registry assertion.
- No changes were needed to `backend/api/main.py` — the macro router was already registered from Phase 05-04 work.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Celery task registration test by importing tasks module first**
- **Found during:** Task 5-10-3 (integration smoke tests)
- **Issue:** Tests checking `app.tasks.keys()` after `from ingestion.celery_app import app` found only built-in `celery.*` tasks — the `@app.task`-decorated functions in `ingestion/tasks.py` were not registered because that module had never been imported
- **Fix:** Added `_get_registered_task_names()` helper that imports `ingestion.tasks` first (triggering all `@app.task` registrations) then returns task names; all four Celery task tests use this helper
- **Files modified:** `backend/tests/macro/test_macro_integration.py`
- **Verification:** All 19 tests pass: `19 passed in 2.87s`
- **Committed in:** `72efa53`

---

**Total deviations:** 1 auto-fixed (Rule 1 bug)
**Impact on plan:** Required fix ensured the Celery task registration tests were actually testing the right state. No scope creep.

## Issues Encountered

None beyond the Celery registry import order issue documented above.

## Known Stubs

None — this plan creates an index barrel and test suite. No UI-rendering stubs.

## Next Phase Readiness

- Phase 05 macro dashboard is fully integrated: all 18 components exported, macro router registered, 19 smoke tests passing, TypeScript clean
- All 14 MACRO requirements (MACRO-01 through MACRO-14) are traceable through the requirement traceability matrix in the plan
- Ready for Phase 06 or next milestone

---
*Phase: 05-macro-dashboard*
*Completed: 2026-03-30*
