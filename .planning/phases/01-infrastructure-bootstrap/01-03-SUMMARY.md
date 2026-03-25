---
phase: 1
plan: "01-03"
title: "React/Vite frontend — Bloomberg dark terminal shell with keyboard navigation"
subsystem: frontend
tags: [react, vite, tailwindcss-v4, bloomberg-ui, keyboard-nav, docker, nginx]
completed: 2026-03-24T21:57:35Z
duration_seconds: 113
tasks_completed: 2
files_created: 15

dependency_graph:
  requires: [01-01]
  provides: [frontend-shell, bloomberg-theme, keyboard-nav, frontend-dockerfile]
  affects: [01-04, all-frontend-plans]

tech_stack:
  added:
    - react@19.2.4
    - react-dom@19.2.4
    - vite@8.0.2
    - "@vitejs/plugin-react@6.0.1"
    - tailwindcss@4.2.2
    - lightweight-charts@5.1.0
    - typescript@5.8.0
    - node:24-alpine (Dockerfile base)
    - nginx:alpine (Dockerfile production)
  patterns:
    - TailwindCSS v4 CSS-first @theme (no tailwind.config.js)
    - Multi-stage Dockerfile (base/dev/build/production)
    - React useEffect keyboard hook with input guard
    - Nginx SPA fallback + API proxy pattern

key_files:
  created:
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/index.html
    - frontend/tsconfig.json
    - frontend/tsconfig.app.json
    - frontend/tsconfig.node.json
    - frontend/.gitignore
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/index.css
    - frontend/src/vite-env.d.ts
    - frontend/src/lib/theme.ts
    - frontend/src/hooks/useKeyboard.ts
    - frontend/Dockerfile
    - frontend/nginx.conf

decisions:
  - TailwindCSS v4 CSS-first @theme used — no tailwind.config.js/ts exists; all theme tokens defined in index.css
  - node:24-alpine chosen for base stage (LTS current as of research)
  - 4-stage Dockerfile: base (deps), dev (Vite HMR), build (tsc+vite), production (nginx:alpine)
  - useKeyboard hook guards INPUT/TEXTAREA/contentEditable to prevent nav interference while typing

metrics:
  duration: 113s
  completed: 2026-03-24
  tasks: 2
  files: 15
---

# Phase 1 Plan 03: React/Vite Frontend — Bloomberg Terminal Shell Summary

**One-liner:** React 19 + Vite 8 + TailwindCSS v4 CSS-first terminal shell with amber-on-black Bloomberg aesthetic, 6 keyboard-navigable module tabs, and a 4-stage Dockerfile serving dev (Vite HMR) and production (Nginx with API proxy).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Vite project scaffold, TailwindCSS v4 theme, Bloomberg terminal shell | 77fbb33 | frontend/package.json, tsconfig*.json, vite.config.ts, index.html, src/index.css, src/main.tsx, src/App.tsx, src/vite-env.d.ts, src/lib/theme.ts, .gitignore |
| 2 | useKeyboard hook + Dockerfile (multi-stage) + Nginx config | 432a066 | frontend/src/hooks/useKeyboard.ts, frontend/Dockerfile, frontend/nginx.conf |

## What Was Built

**Bloomberg Terminal Shell**
- `frontend/src/App.tsx`: Full terminal layout — HHBFIN TERMINAL header, 6 module tabs (EQUITY, MACRO, FX, CRYPTO, NEWS, SCREENER), active tab highlighted with `bg-terminal-amber text-black`, footer status bar
- `frontend/src/index.css`: TailwindCSS v4 `@import "tailwindcss"` + `@theme` block defining `--color-terminal-amber: #ff9900`, `--color-terminal-bg: #0a0a0a`, and all terminal colors; body defaults to monospace font
- `frontend/src/lib/theme.ts`: Typed `TERMINAL` color constants, `MODULE_TABS` tuple, `ModuleTab` union type

**Keyboard Navigation**
- `frontend/src/hooks/useKeyboard.ts`: `useEffect`-based keydown listener; skips events when focused on INPUT/TEXTAREA/contentEditable; App wires keys 1-6 to module tab switching

**Docker Infrastructure**
- `frontend/Dockerfile`: 4 named stages — `base` (node:24-alpine, npm ci), `dev` (exposes 5173, runs Vite), `build` (tsc + vite build), `production` (nginx:alpine serving /usr/share/nginx/html)
- `frontend/nginx.conf`: `try_files $uri $uri/ /index.html` for SPA routing; `/api/` proxied to `http://api:8000/`; `/ws` WebSocket proxy with Upgrade/Connection headers

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

- `[{activeTab}] MODULE READY` — each module tab renders a placeholder. This is intentional for Phase 1; each module (EQUITY, MACRO, FX, CRYPTO, NEWS, SCREENER) will be wired with real components in Phases 2–12.
- `--:-- NEXT EVENT` in the header — economic calendar countdown is a Phase 4 deliverable.
- `HHBFin v0.1.0` in footer — version is static; no dynamic version wiring needed until release tagging.

## Self-Check: PASSED

Files verified present:
- frontend/package.json: FOUND
- frontend/src/index.css: FOUND
- frontend/src/App.tsx: FOUND
- frontend/src/hooks/useKeyboard.ts: FOUND
- frontend/Dockerfile: FOUND
- frontend/nginx.conf: FOUND

Commits verified:
- 77fbb33: FOUND (Task 1)
- 432a066: FOUND (Task 2)
