---
plan: 05-05
phase: 05
subsystem: frontend
tags: [react, recharts, macro, ui-shell]
dependency_graph:
  requires: [05-04]
  provides: [macro-module-shell, useMacroData-hook, macro-sub-tab-nav]
  affects: [frontend/src/App.tsx]
tech_stack:
  added: [recharts@3.8.1]
  patterns: [lazy-import-with-catch-fallback, cancellable-effect-fetch]
key_files:
  created:
    - frontend/src/hooks/useMacroData.ts
    - frontend/src/components/macro/MacroModule.tsx
    - frontend/src/components/macro/MacroSubTabNav.tsx
  modified:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/src/index.css
    - frontend/src/lib/theme.ts
    - frontend/src/App.tsx
decisions:
  - recharts@3.8.1 ships own TypeScript types — no @types/recharts needed
  - MacroModule uses React.lazy + .catch() fallback so plans 05-06 to 05-09 can be run in any order without breaking the shell
  - useMacroData uses cancelled flag pattern to prevent setState on unmounted component
  - App.tsx catch-all stub narrowed to exclude MACRO — EQUITY and MACRO have dedicated renderers, others remain placeholder
metrics:
  duration: 202s
  completed_date: "2026-03-30"
  tasks: 6
  files: 8
---

# Phase 5 Plan 05: recharts Install + MacroModule Container + Sub-Tab Nav + App.tsx Wiring Summary

**One-liner:** React lazy-loaded MacroModule shell with CURVES/INDICATORS/RISK/SENTIMENT sub-tab nav wired into App.tsx, backed by typed useMacroData fetch hook and recharts@3.8.1 install.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 5-05-1 | Install recharts | 70ab63a | frontend/package.json, package-lock.json |
| 5-05-2 | Add colour tokens | a800221 | frontend/src/index.css, frontend/src/lib/theme.ts |
| 5-05-3 | Create useMacroData hook | bd01d54 | frontend/src/hooks/useMacroData.ts |
| 5-05-4 | Create MacroSubTabNav | 671f5ac | frontend/src/components/macro/MacroSubTabNav.tsx |
| 5-05-5 | Create MacroModule container | 0c9db56 | frontend/src/components/macro/MacroModule.tsx |
| 5-05-6 | Wire MacroModule into App.tsx | 3b81c50 | frontend/src/App.tsx |

## What Was Built

- **recharts** installed as frontend dependency (v3.8.1)
- **Colour tokens** `--color-terminal-orange` (#ff6600) and `--color-terminal-bright-green` (#00ff66) added to `index.css` @theme block and `TERMINAL` constant in `theme.ts`
- **useMacroData hook** — fetches `/api/macro/curves`, `/api/macro/indicators`, `/api/macro/risk`, `/api/macro/sentiment` on mount; typed interfaces for all four data shapes; cancellation pattern; single-load (no polling)
- **MacroSubTabNav** — four sub-tabs (CURVES, INDICATORS, RISK, SENTIMENT), amber active style, border hover for inactive, matches App.tsx MODULE_TABS styling
- **MacroModule** — top-level container with header, sub-tab nav, and lazy-loaded sub-tab content area; PlaceholderTab fallback shows tab name while sub-components (05-06 to 05-09) are not yet implemented
- **App.tsx** — imports MacroModule and renders `<MacroModule />` for the MACRO tab; other non-EQUITY tabs retain placeholder div

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed @types/react-dom version constraint preventing npm install**
- **Found during:** Task 1 (npm install recharts)
- **Issue:** `package.json` had `"@types/react-dom": "^19.2.14"` but npm registry only has up to `19.2.3` — npm install failed with ETARGET
- **Fix:** Changed constraint from `^19.2.14` to `^19.2.3` before running npm install
- **Files modified:** frontend/package.json
- **Commit:** 70ab63a

## Known Stubs

- `CurvesTab`, `IndicatorsTab`, `RiskTab`, `SentimentTab` — lazy-imported with `.catch()` fallback to `PlaceholderTab`. These show "{TAB NAME} — LOADING..." until plans 05-06 through 05-09 create the real components. This is intentional — MacroModule is designed to degrade gracefully as each sub-plan lands.

## Self-Check: PASSED

Files exist:
- frontend/src/hooks/useMacroData.ts — FOUND
- frontend/src/components/macro/MacroModule.tsx — FOUND
- frontend/src/components/macro/MacroSubTabNav.tsx — FOUND

Commits exist:
- 70ab63a — FOUND (chore: install recharts)
- a800221 — FOUND (feat: colour tokens)
- bd01d54 — FOUND (feat: useMacroData hook)
- 671f5ac — FOUND (feat: MacroSubTabNav)
- 0c9db56 — FOUND (feat: MacroModule)
- 3b81c50 — FOUND (feat: App.tsx wiring)
