---
plan: 05-07
phase: 05
subsystem: frontend/macro
tags: [react, macro, indicators, sparkline, svg]
dependency_graph:
  requires: [05-05]
  provides: [MacroPanel, PolicyRatesPanel, IndicatorsTab]
  affects: [MacroModule sub-tab INDICATORS]
tech_stack:
  added: []
  patterns: [CSS grid 3x2, SVG sparklines, conditional UK/EU data rendering]
key_files:
  created:
    - frontend/src/components/macro/MacroPanel.tsx
    - frontend/src/components/macro/PolicyRatesPanel.tsx
    - frontend/src/components/macro/IndicatorsTab.tsx
  modified: []
decisions:
  - buildSparklinePath duplicated in PolicyRatesPanel rather than shared — keeps components self-contained per plan spec
  - PolicyRatesPanel overlays Fed+BoE in single SVG (Fed solid amber, BoE dashed green) for visual density
  - euData in MacroPanel is current-only (no history array) — EU GDP history not in IndicatorPanel type
metrics:
  duration: 91s
  completed: "2026-03-30T20:29:01Z"
  tasks: 3
  files: 3
---

# Phase 05 Plan 07: INDICATORS Sub-Tab — MacroPanel Component + 3x2 Grid Summary

## One-liner

Reusable MacroPanel with SVG sparkline + delta badges and IndicatorsTab 3x2 CSS grid wiring CPI/Core CPI/PCE/GDP/Unemployment/PolicyRates panels.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 5-07-1 | Create MacroPanel component | a7bca95 | MacroPanel.tsx |
| 5-07-2 | Create PolicyRatesPanel component | 99f862e | PolicyRatesPanel.tsx |
| 5-07-3 | Create IndicatorsTab layout | 350abf1 | IndicatorsTab.tsx |

## What Was Built

**MacroPanel** (`MacroPanel.tsx`): Reusable panel component with title bar (amber, bold), SVG sparkline for US history (amber), optional UK sparkline (green), current value display for US/UK/EU, and MoM/YoY delta badges with colour-coded sign (green positive, red negative).

**PolicyRatesPanel** (`PolicyRatesPanel.tsx`): Specialised panel for the POLICY RATES cell — overlays Fed (amber solid 1.5px) and BoE (green dashed 1px) sparklines in a single SVG, then lists FED/BOE/ECB current rates with 2dp precision.

**IndicatorsTab** (`IndicatorsTab.tsx`): 3x2 CSS grid (`gridTemplateColumns: repeat(3,1fr)`, `gridTemplateRows: repeat(2,1fr)`) that fills 100% height. Row 1: CPI (US+UK), CORE CPI (US), PCE (US). Row 2: GDP (US+UK+EU), UNEMPLOYMENT (US+UK), PolicyRatesPanel.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — components render real data from `IndicatorsData` / `PolicyRatesPanel` types in `useMacroData.ts`. Loading state shows "LOADING..." when data is null.

## Self-Check: PASSED

- frontend/src/components/macro/MacroPanel.tsx: EXISTS
- frontend/src/components/macro/PolicyRatesPanel.tsx: EXISTS
- frontend/src/components/macro/IndicatorsTab.tsx: EXISTS
- buildSparklinePath in MacroPanel.tsx: FOUND
- gridTemplateColumns/Rows in IndicatorsTab.tsx: FOUND
- Commits a7bca95, 99f862e, 350abf1: VERIFIED
