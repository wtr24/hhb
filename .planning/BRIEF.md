# HHBFin BRIEF — auto-generated 2026-03-29T06:57:28Z
> Do not edit. Regenerated every session start by gsd-brief-generator.js.

## Active Phase
**Phase 03: Equity Overview**
Goal: Full Bloomberg DES/GP equivalent — live quote, multi-timeframe candlestick charts with earnings/dividend markers, fundamentals, short interest, insider transaction clustering, and options chain with Greeks
Status: Executing Phase 03
Next: /gsd:plan-phase 3

## Project in One Line
Self-hosted Bloomberg Terminal. FastAPI + React/Vite + TimescaleDB + Redis + Celery.
Docker Compose on NAS. Zero ongoing cost.

## Hard Constraints
- Zero ongoing spend
- Docker Compose on NAS; no Kubernetes, no cloud hosting costs
- FastAPI + React/Vite + TimescaleDB + Redis + Celery
- Must run locally

## Phase Progress
✓ Phase 02: Data Ingestion Foundation
✓ Phase 03: Equity Overview
→ Phase 03: Equity Overview  ← ACTIVE
  Phase 04: Technical Analysis Engine
  Phase 05: Macro Dashboard

## Key Files — Current Phase
- Context:  .planning\phases\03-equity-overview\03-CONTEXT.md
- Requirements: relevant section in .planning/REQUIREMENTS.md
- Prior decisions: check prior phase CONTEXT.md only if conflict arises

## Spec Section Map
docs\superpowers\specs\2026-03-24-bloomberg-terminal-design.md
  §3  → UI aesthetic, colour palette, density rules
  §5  → TTL/caching table, rate limits per API source
  §6  → WebSocket, Redis pub-sub, message format
  §8  → TA math engine, indicator groups A–H
  (Never read the full file — use section offsets)

## Recent Decisions (Phase 03)
- D-01: Bloomberg fixed-height grid layout. Nothing scrolls — all panels visible simultaneously like a real terminal. Layout zones:
- D-02: Stale data indicator — amber ⚠ badge shown inline on any panel that has `stale: true` data (carried forward from Phase 2 fallback chain).
- D-03: Command bar at the top of the EQUITY module (above the grid). Terminal-style: `TICKER> ____` with amber cursor. User types a ticker and presses Enter to load all panels. Auto-uppercases input. Supports `.L` suffix for LSE tickers (LLOY.L, BARC.L) and index notation (^FTSE, ^FTMC).
- D-04: On Enter, all panels refresh simultaneously for the new ticker. Previous ticker data cleared. No history/autocomplete in Phase 3 — plain input only.
- D-05: Default view is 4-panel simultaneous display (Weekly / Daily / 4H / 1H), all showing the same ticker. This satisfies EQUITY-02.
