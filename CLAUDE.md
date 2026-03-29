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
- TA math engine / indicator groups A–H         → §8

Read only the section relevant to your task. If unsure which section, check
BRIEF.md first — it will tell you.

## File Loading Rules

1. **Quick tasks** (questions, small fixes, config changes): BRIEF.md is
   sufficient. Load nothing else.
2. **Planning / execution tasks**: read current phase CONTEXT.md and PLAN
   files only. Do not load prior phase CONTEXT.md files unless resolving a
   specific conflict.
3. **Prior phase directories** (01, 02, 03...): treat as archive. Do not
   load unless explicitly debugging a prior-phase issue.
4. **Dispatching sub-agents**: pass only the files they specifically need —
   not the full .planning/ directory.

## Stack (never deviate)

FastAPI · React/Vite · TimescaleDB · Redis · Celery · Docker Compose on NAS

## Hard Constraints

- All data sources must be free tier — no paid APIs, no credit card required
- UK/LSE tickers (.L suffix) must work everywhere US tickers do
- FinBERT runs locally — no cloud NLP calls
- Everything persisted to TimescaleDB — nothing cache-only
