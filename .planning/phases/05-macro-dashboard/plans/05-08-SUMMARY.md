---
plan: 05-08
phase: 05
subsystem: frontend/macro
tags: [react, recharts, risk, vix, regime, put-call]
dependency_graph:
  requires: [05-05]
  provides: [RiskTab, VixTermChart, RegimeClassifier, PutCallChart]
  affects: [MacroModule]
tech_stack:
  added: []
  patterns: [recharts LineChart, recharts ReferenceLine, CSS grid 60/40 layout]
key_files:
  created:
    - frontend/src/components/macro/VixTermChart.tsx
    - frontend/src/components/macro/RegimeClassifier.tsx
    - frontend/src/components/macro/PutCallChart.tsx
    - frontend/src/components/macro/RiskTab.tsx
  modified: []
decisions:
  - BACKWARDATION uses Unicode escape \u26a0 (warning sign) to avoid emoji in source — consistent with CLAUDE.md no-emoji convention
  - VIX6M line conditionally rendered (not just styled invisible) — eliminates recharts rendering overhead when not applicable
  - PutCallChart empty-state guard uses optional chaining (put_call_ratio?.length) — handles both null data and empty array
key-decisions:
  - BACKWARDATION warning sign uses Unicode escape rather than emoji literal
  - VIX6M line gated behind historyDepthOk conditional render
metrics:
  duration: 83s
  completed_date: "2026-03-30"
  tasks_completed: 4
  files_created: 4
  files_modified: 0
requirements: [MACRO-11, MACRO-12]
---

# Phase 05 Plan 08: RISK Sub-Tab — VIX Term Structure Chart, Regime Classifier, Put/Call Chart Summary

**One-liner:** Four RISK sub-tab components — VIX term structure 3-line chart with accumulating-history guard, regime badge with ordinal percentile ranks, CBOE put/call ratio chart with 0.70 neutral reference line, and 60/40 layout container.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 5-08-1 | Create VixTermChart | 22e2018 | VixTermChart.tsx |
| 5-08-2 | Create RegimeClassifier | ed75a96 | RegimeClassifier.tsx |
| 5-08-3 | Create PutCallChart | c01b035 | PutCallChart.tsx |
| 5-08-4 | Create RiskTab layout | b691801 | RiskTab.tsx |

## What Was Built

### VixTermChart (`VixTermChart.tsx`)
- Recharts LineChart with three series: spot VIX (amber, strokeWidth 2), VIX3M (green, strokeWidth 1.5), VIX6M (dim dashed)
- VIX6M line only rendered when `history_depth_ok` is true — eliminates unnecessary recharts overhead
- "ACCUMULATING HISTORY" badge displayed in header when `history_depth_ok` is false
- Colour legend strip at bottom matching line colours
- Loading skeleton with LOADING... centred text

### RegimeClassifier (`RegimeClassifier.tsx`)
- Regime badge with D-20 colours: LOW VOL=green, NORMAL=amber, ELEVATED=orange (#ff6600 CSS var), CRISIS=red
- `ordinalSuffix()` utility formats percentile ranks (1st, 2nd, 3rd, 4th...)
- 1Y and 5Y percentile ranks rendered when non-null
- CONTANGO/BACKWARDATION indicator badge pinned to bottom via `marginTop: auto`
- BACKWARDATION uses Unicode escape \u26a0 (warning sign) per CLAUDE.md no-emoji convention

### PutCallChart (`PutCallChart.tsx`)
- Recharts LineChart with CBOE put/call ratio series (amber)
- ReferenceLine at y=0.7 with "NEUTRAL 0.70" label (dim, dashed) per D-06/UI-SPEC
- NO DATA state when put_call_ratio array absent or empty
- borderTop on main container creates visual separator from RegimeClassifier above

### RiskTab (`RiskTab.tsx`)
- CSS grid layout: 60% left (VixTermChart) / 40% right column
- Right column split 50/50 rows: RegimeClassifier top, PutCallChart bottom
- All `overflow: hidden` and `minHeight: 0` for Bloomberg fixed-height layout compliance

## Deviations from Plan

None — plan executed exactly as written. One minor adjustment:

**BACKWARDATION emoji → Unicode escape:** The plan used `'BACKWARDATION ⚠'` with a literal emoji character. Per CLAUDE.md "avoid writing emojis to files unless asked", replaced with Unicode escape `\u26a0`. Functionally identical rendered output.

## Known Stubs

None — all four components are fully wired to `RiskData` props from `useMacroData`. No placeholder data or hardcoded values.

## Self-Check

### Files exist:
- frontend/src/components/macro/VixTermChart.tsx — FOUND
- frontend/src/components/macro/RegimeClassifier.tsx — FOUND
- frontend/src/components/macro/PutCallChart.tsx — FOUND
- frontend/src/components/macro/RiskTab.tsx — FOUND

### Commits exist:
- 22e2018 — FOUND (VixTermChart)
- ed75a96 — FOUND (RegimeClassifier)
- c01b035 — FOUND (PutCallChart)
- b691801 — FOUND (RiskTab)

## Self-Check: PASSED
