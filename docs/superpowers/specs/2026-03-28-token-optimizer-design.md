# Token Optimizer — Design Spec

**Date:** 2026-03-28
**Project:** HHBFin — Free Bloomberg Terminal
**Status:** Ready for planning

---

## Problem

Each Claude Code session for this project burns significant tokens on context that is largely static and already known:

| Source | Approx tokens | Frequency |
|--------|--------------|-----------|
| ROADMAP.md (317 lines) | ~5,500 | Every session / phase start |
| REQUIREMENTS.md (262 lines) | ~4,500 | Every session / phase start |
| PROJECT.md (106 lines) | ~1,800 | Every session / phase start |
| Bloomberg design spec (60KB) | ~15,000 | Every sub-agent that reads canonical refs |
| Prior phase CONTEXT.md files | ~1,000+ (growing) | discuss-phase loads all |
| **Total per session** | **~28K+** | — |

With 5–7 sub-agents per phase execution, the spec alone costs ~75–105K tokens per phase. The project has 14+ remaining phases.

---

## Goals

1. Reduce session-start context load from ~28K tokens to ~3K tokens automatically
2. Eliminate full Bloomberg spec reads — route agents to specific sections only
3. Require zero manual maintenance — system self-updates as phases progress
4. Work with existing files as-is — no restructuring of docs or planning files
5. Apply to sub-agents automatically via CLAUDE.md inheritance

---

## Non-Goals

- LLM-based summarisation (adds cost, defeats the purpose)
- Modifying or splitting the Bloomberg design spec
- Changing GSD workflow files or existing hooks
- Per-user or multi-project generalisation (this is project-specific)

---

## Architecture

Three components working together:

```
SessionStart
    │
    ▼
[1] gsd-brief-generator.js  (new hook)
    │  Pure Node.js, ~50ms
    │  Reads: STATE.md, ROADMAP.md, PROJECT.md, active phase CONTEXT.md
    │  Writes: .planning/BRIEF.md
    │  Returns: additionalContext nudge to read BRIEF.md
    ▼
[2] CLAUDE.md  (new file, project root)
    │  Loaded by Claude Code automatically every session
    │  Contains: loading rules + spec section map
    │  Inherited by all sub-agents
    ▼
[3] .planning/BRIEF.md  (auto-generated, never manually edited)
    │  ~150 lines, replaces 685 lines of planning files
    │  Always fresh — overwritten every SessionStart
    └─ Contains: active phase, constraints, completed phases, spec section map,
                 key files for current phase
```

---

## Component 1: `gsd-brief-generator.js`

**Location:** `C:\Users\Surface-Pro-1\.claude\hooks\gsd-brief-generator.js`

**Trigger:** `SessionStart` hook in `settings.json`

**Behaviour:**

1. Determine project root by walking up from `cwd` looking for `.planning/ROADMAP.md`
2. If no `.planning/` directory found → exit with code 0, no output (safe for non-GSD projects)
3. Read `.planning/STATE.md` → extract active phase number, name, status
4. Read `.planning/ROADMAP.md` → extract active phase goal + next 2 upcoming phases + list of completed phases
5. Read `.planning/PROJECT.md` → extract stack line + hard constraints (first 40 lines sufficient)
6. Read active phase `CONTEXT.md` if it exists → extract up to 5 most recent `D-NN` decisions
7. Read `docs/superpowers/specs/` directory listing → build spec section map from known filename
8. Write `.planning/BRIEF.md` with structured content (see BRIEF.md spec below)
9. Return `additionalContext`: `"Project brief updated. Read .planning/BRIEF.md for orientation before proceeding."`

**Implementation constraints:**
- Pure Node.js — no npm dependencies beyond `fs`, `path`, `os`
- Must not throw — wrap all file reads in try/catch, degrade gracefully if files missing
- Must exit cleanly within 10s (matches existing hook timeout pattern)
- Follows the same stdin/stdout pattern as `gsd-context-monitor.js`

---

## Component 2: `CLAUDE.md`

**Location:** `C:\hhbfin\CLAUDE.md`

**Contents:**

```markdown
# HHBFin — Claude Code Instructions

## Session Start Protocol

Read `.planning/BRIEF.md` at the start of every session. It is auto-generated
and always current. Do NOT read PROJECT.md, REQUIREMENTS.md, or ROADMAP.md
unless the user explicitly asks or a task requires the full file.

## Bloomberg Design Spec — Section Routing

The spec at `docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md`
is 60KB. Never read it whole. Use the section map in BRIEF.md:

- UI aesthetic / colour palette / density rules → §3
- Data layer / TTL caching table / rate limits  → §5
- WebSocket / pub-sub / message formats         → §6
- TA math engine / indicator groups             → §8

Read only the section relevant to your task.

## File Loading Rules

1. For quick tasks (questions, small fixes): BRIEF.md is sufficient. Load nothing else.
2. For planning/execution: read current phase CONTEXT.md + PLAN files only.
3. Do not load prior phase directories (01, 02, 03...) unless debugging a
   prior-phase issue — treat them as archive.
4. When dispatching sub-agents: pass only the files they specifically need.

## Stack (never deviate)

FastAPI · React/Vite · TimescaleDB · Redis · Celery · Docker Compose on NAS

## Hard Constraints

- All data sources must be free tier — no paid APIs
- UK/LSE tickers (.L suffix) must work everywhere US tickers do
- FinBERT runs locally — no cloud NLP calls
```

---

## Component 3: `.planning/BRIEF.md` Structure

Auto-generated by the hook. Example output for Phase 4:

```markdown
# HHBFin BRIEF — auto-generated 2026-03-28T09:00:00Z
> Do not edit. Regenerated every session start by gsd-brief-generator.js

## Active Phase
**Phase 4: Technical Analysis Engine**
Goal: Complete math engine — all indicator groups, 60+ candlestick patterns with
win rates/p-values, chart pattern detection, Fibonacci tools, Elliott Wave labelling
Status: Context gathered — ready for planning
Next: /gsd:plan-phase 4

## Project in One Line
Self-hosted Bloomberg Terminal. FastAPI + React/Vite + TimescaleDB + Redis + Celery.
Docker Compose on NAS. Zero ongoing cost.

## Hard Constraints
- Stack FIXED: FastAPI · React/Vite · TimescaleDB · Redis · Celery
- Free tier only — no paid APIs ever
- UK/LSE tickers (.L suffix) supported everywhere
- FinBERT local only

## Phase Progress
✓ Phase 1: Infrastructure Bootstrap
✓ Phase 2: Data Ingestion Foundation
✓ Phase 3: Equity Overview
→ Phase 4: Technical Analysis Engine  ← ACTIVE
  Phase 5: Macro Dashboard
  Phase 6: Forex & Commodities

## Key Files — Current Phase
- Context:      .planning/phases/04-technical-analysis-engine/04-CONTEXT.md
- Requirements: TA-01 through TA-13 in .planning/REQUIREMENTS.md
- Prior chart decisions: .planning/phases/03-equity-overview/03-CONTEXT.md §D-05/D-06

## Spec Section Map
docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md
  §3  → UI aesthetic, colour palette, density rules
  §5  → TTL/caching table, rate limits per API source
  §6  → WebSocket, Redis pub-sub, message format
  §8  → TA math engine, indicator groups A–H, candlestick patterns
  (Never read the full file — use section offsets)

## Recent Decisions (Phase 4)
- D-01: [Indicators ▾] button in expanded chart panel header
- D-07: Win rates pre-computed nightly via Celery → ta_pattern_stats table
- D-11: [Fib] button → click-click drawing mode
- D-15: Chart patterns: heuristic algorithms (scipy.signal.find_peaks)
- D-18: Patterns shown as shaded region + confidence % badge on chart
```

---

## Registration

Add to `C:\Users\Surface-Pro-1\.claude\settings.json` SessionStart hooks array:

```json
{
  "type": "command",
  "command": "node \"C:/Users/Surface-Pro-1/.claude/hooks/gsd-brief-generator.js\""
}
```

Placed after `gsd-check-update.js`, before any other SessionStart hooks.

---

## Estimated Token Savings

| Scenario | Before | After | Saved |
|----------|--------|-------|-------|
| Session start (Claude reads) | ~11.8K | ~1.5K | ~10K |
| Sub-agent with spec access | ~15K (spec) | ~2K (one section) | ~13K |
| Phase execution (5 agents) | ~75K spec alone | ~10K | ~65K |
| Full project (14 phases) | ~1M+ | ~140K | **~860K** |

---

## Testing

1. Open a new Claude Code session in `C:\hhbfin`
2. Verify `BRIEF.md` exists at `.planning/BRIEF.md` with current phase info
3. Verify `additionalContext` nudge appears in session start
4. Ask Claude "what phase are we on?" — it should answer from BRIEF.md without reading other files
5. Simulate a sub-agent task — verify it doesn't read the full Bloomberg spec
6. Complete a phase, start new session — verify BRIEF.md reflects updated state

---

*Spec written: 2026-03-28*
