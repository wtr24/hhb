# Token Optimizer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce per-session token consumption by ~10–13K tokens via a SessionStart hook that generates a compact BRIEF.md, plus a CLAUDE.md with file-loading rules.

**Architecture:** Three components — (1) `gsd-brief-generator.js` hook reads planning files and writes `.planning/BRIEF.md` on every session start; (2) `CLAUDE.md` at project root contains static loading rules and spec section routing, inherited by sub-agents; (3) `settings.json` registration wires the hook into the existing SessionStart array.

**Tech Stack:** Node.js (no dependencies beyond `fs`, `path`, `os`, `glob` via `fs.readdirSync`), Claude Code hooks system, Markdown.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `C:\Users\Surface-Pro-1\.claude\hooks\gsd-brief-generator.js` | SessionStart hook — parses planning files, writes BRIEF.md, returns additionalContext |
| Create | `C:\Users\Surface-Pro-1\.claude\hooks\tests\gsd-brief-generator.test.js` | Unit tests for all parsing functions |
| Create | `C:\hhbfin\CLAUDE.md` | Static loading rules + spec section map, auto-loaded every session |
| Modify | `C:\Users\Surface-Pro-1\.claude\settings.json` | Register hook in existing SessionStart[0].hooks array |
| Auto-generated | `C:\hhbfin\.planning\BRIEF.md` | Written by hook — never manually edited |

---

## Task 1: Hook scaffolding + stdin/stdout wrapper

**Files:**
- Create: `C:\Users\Surface-Pro-1\.claude\hooks\gsd-brief-generator.js`
- Create: `C:\Users\Surface-Pro-1\.claude\hooks\tests\gsd-brief-generator.test.js`

- [ ] **Step 1: Create the test file with a scaffolding test**

Create `C:\Users\Surface-Pro-1\.claude\hooks\tests\gsd-brief-generator.test.js`:

```javascript
#!/usr/bin/env node
// Tests for gsd-brief-generator.js parsing functions
// Run: node tests/gsd-brief-generator.test.js

const assert = require('assert');
const path = require('path');
const fs = require('fs');
const os = require('os');

// We'll import the module under test once it exists.
// For now, just verify the test runner itself works.

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

// Scaffold: will be replaced with real tests in Task 2
test('test runner works', () => {
  assert.strictEqual(1 + 1, 2);
});

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
```

- [ ] **Step 2: Run scaffold test to confirm it works**

```bash
node "C:/Users/Surface-Pro-1/.claude/hooks/tests/gsd-brief-generator.test.js"
```

Expected output: `1 passed, 0 failed`

- [ ] **Step 3: Create the hook file with stdin/stdout wrapper only (no logic yet)**

Create `C:\Users\Surface-Pro-1\.claude\hooks\gsd-brief-generator.js`:

```javascript
#!/usr/bin/env node
// gsd-hook-version: 1.0.0
// Brief Generator - SessionStart hook
// Reads .planning/ files and writes a compact BRIEF.md to reduce
// per-session token load. Returns additionalContext nudge to read it.

'use strict';
const fs   = require('fs');
const path = require('path');
const os   = require('os');

// ── Exports (for unit testing) ────────────────────────────────────────────
function findPlanningRoot(cwd) {
  // Walk up from cwd looking for .planning/ROADMAP.md
  let dir = cwd;
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, '.planning', 'ROADMAP.md'))) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) return null; // reached filesystem root
    dir = parent;
  }
  return null;
}

function parseStateYaml(content) {
  // Extract YAML frontmatter fields from STATE.md
  // Returns { status, last_updated, completed_phases, total_phases }
  const frontmatter = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatter) return {};
  const yaml = frontmatter[1];
  const get = (key) => {
    const m = yaml.match(new RegExp(`^${key}:\\s*["']?([^"'\\n]+)["']?`, 'm'));
    return m ? m[1].trim() : null;
  };
  return {
    status:            get('status'),
    last_updated:      get('last_updated'),
    completed_phases:  parseInt(get('completed_phases') || '0', 10),
    total_phases:      parseInt(get('total_phases') || '0', 10),
  };
}

function parseActivePhase(stateMd) {
  // Extract active phase number and name from STATE.md body
  // Looks for: **Phase**: 04 — Technical Analysis Engine
  const m = stateMd.match(/\*\*Phase\*\*:\s*(\d+)\s*[—-]+\s*([^\n(]+)/i);
  if (!m) return null;
  return { number: m[1].padStart(2, '0'), name: m[2].trim() };
}

function parseRoadmap(content, activePhaseNum) {
  // Extract: completed phases, active phase goal, next 2 upcoming phases
  const lines = content.split('\n');
  const completed = [];
  let activeGoal = null;
  const upcoming = [];
  let inActiveDetails = false;
  let inPhaseDetails = false;

  // Phase summary lines: "- [x] **Phase N: Name** — description"
  for (const line of lines) {
    const completedMatch = line.match(/^-\s+\[x\]\s+\*\*Phase\s+(\d+):\s+([^*]+)\*\*/i);
    const pendingMatch   = line.match(/^-\s+\[\s*\]\s+\*\*Phase\s+(\d+):\s+([^*]+)\*\*/i);
    if (completedMatch) {
      completed.push({ number: completedMatch[1].padStart(2, '0'), name: completedMatch[2].trim() });
    } else if (pendingMatch) {
      const num = pendingMatch[1].padStart(2, '0');
      if (num !== activePhaseNum && upcoming.length < 2 && completed.length > 0) {
        upcoming.push({ number: num, name: pendingMatch[2].trim() });
      }
    }
    // Goal line inside ### Phase N details block
    const detailHeader = line.match(/^###\s+Phase\s+(\d+):/i);
    if (detailHeader) {
      inPhaseDetails = true;
      inActiveDetails = detailHeader[1].padStart(2, '0') === activePhaseNum;
    }
    if (inActiveDetails && line.startsWith('**Goal**:')) {
      activeGoal = line.replace('**Goal**:', '').trim();
      inActiveDetails = false;
    }
  }
  return { completed, activeGoal, upcoming };
}

function parseConstraints(projectMd) {
  // Extract the 4 hard constraints from the Constraints section
  const section = projectMd.match(/## Constraints\n([\s\S]*?)(?=\n##|$)/);
  if (!section) return [];
  return section[1]
    .split('\n')
    .filter(l => l.startsWith('- **'))
    .slice(0, 4)
    .map(l => l.replace(/^- \*\*[^*]+\*\*:\s*/, '').split('—')[0].trim());
}

function parseContextDecisions(contextMd) {
  // Extract up to 5 D-NN decisions from a CONTEXT.md file
  const decisions = [];
  const re = /- \*\*(D-\d+):\*\*\s+([^\n]+)/g;
  let m;
  while ((m = re.exec(contextMd)) !== null && decisions.length < 5) {
    decisions.push(`${m[1]}: ${m[2].trim()}`);
  }
  return decisions;
}

function findSpecFile(projectRoot) {
  // Glob for bloomberg spec by pattern — guards against date-prefix changes
  const specsDir = path.join(projectRoot, 'docs', 'superpowers', 'specs');
  if (!fs.existsSync(specsDir)) return null;
  const files = fs.readdirSync(specsDir);
  const match = files.find(f => f.includes('bloomberg-terminal-design') && f.endsWith('.md'));
  return match ? path.join('docs', 'superpowers', 'specs', match) : null;
}

function generateBrief({ activePhase, activeGoal, stateYaml, completed, upcoming,
                         constraints, decisions, specFile, phaseDir, nextCommand }) {
  const ts = new Date().toISOString().slice(0, 19) + 'Z';
  const completedList = completed.map(p => `✓ Phase ${p.number}: ${p.name}`).join('\n');
  const upcomingList  = upcoming.map(p  => `  Phase ${p.number}: ${p.name}`).join('\n');
  const constraintList = constraints.map(c => `- ${c}`).join('\n');
  const decisionList  = decisions.length
    ? decisions.map(d => `- ${d}`).join('\n')
    : '- (no context file yet)';

  const specSection = specFile
    ? `## Spec Section Map\n${specFile}\n  §3  → UI aesthetic, colour palette, density rules\n  §5  → TTL/caching table, rate limits per API source\n  §6  → WebSocket, Redis pub-sub, message format\n  §8  → TA math engine, indicator groups A–H\n  (Never read the full file — use section offsets)`
    : '## Spec Section Map\n(spec file not found in docs/superpowers/specs/)';

  const contextLine = phaseDir
    ? `- Context:  ${phaseDir}`
    : '- Context:  (not yet created)';

  return `# HHBFin BRIEF — auto-generated ${ts}
> Do not edit. Regenerated every session start by gsd-brief-generator.js.

## Active Phase
**Phase ${activePhase.number}: ${activePhase.name}**
Goal: ${activeGoal || '(see ROADMAP.md)'}
Status: ${stateYaml.status || 'unknown'}
Next: ${nextCommand}

## Project in One Line
Self-hosted Bloomberg Terminal. FastAPI + React/Vite + TimescaleDB + Redis + Celery.
Docker Compose on NAS. Zero ongoing cost.

## Hard Constraints
${constraintList}

## Phase Progress
${completedList}
→ Phase ${activePhase.number}: ${activePhase.name}  ← ACTIVE
${upcomingList}

## Key Files — Current Phase
${contextLine}
- Requirements: relevant section in .planning/REQUIREMENTS.md
- Prior decisions: check prior phase CONTEXT.md only if conflict arises

${specSection}

## Recent Decisions (Phase ${activePhase.number})
${decisionList}
`;
}

module.exports = {
  findPlanningRoot, parseStateYaml, parseActivePhase,
  parseRoadmap, parseConstraints, parseContextDecisions,
  findSpecFile, generateBrief,
};

// ── Main (stdin/stdout hook entrypoint) ───────────────────────────────────
if (require.main === module) {
  let input = '';
  const stdinTimeout = setTimeout(() => process.exit(0), 10000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    clearTimeout(stdinTimeout);
    try {
      const data   = JSON.parse(input || '{}');
      const cwd    = data.cwd || process.cwd();
      const root   = findPlanningRoot(cwd);

      // Not a GSD project — exit silently
      if (!root) { process.exit(0); }

      const read = (rel) => {
        try { return fs.readFileSync(path.join(root, rel), 'utf8'); }
        catch (_) { return ''; }
      };

      const stateMd    = read('.planning/STATE.md');
      const roadmapMd  = read('.planning/ROADMAP.md');
      const projectMd  = read('.planning/PROJECT.md');
      const stateYaml  = parseStateYaml(stateMd);
      const activePhase = parseActivePhase(stateMd);

      if (!activePhase) { process.exit(0); }

      const { completed, activeGoal, upcoming } = parseRoadmap(roadmapMd, activePhase.number);
      const constraints = parseConstraints(projectMd);
      const specFile    = findSpecFile(root);

      // Read active phase CONTEXT.md
      const phaseGlob = fs.readdirSync(path.join(root, '.planning', 'phases'))
        .find(d => d.startsWith(activePhase.number));
      const phaseDir  = phaseGlob
        ? path.join('.planning', 'phases', phaseGlob, `${activePhase.number}-CONTEXT.md`)
        : null;
      const contextMd = phaseDir ? read(phaseDir) : '';
      const decisions = parseContextDecisions(contextMd);
      const nextCommand = `/gsd:plan-phase ${parseInt(activePhase.number, 10)}`;

      const brief = generateBrief({
        activePhase, activeGoal, stateYaml, completed, upcoming,
        constraints, decisions, specFile, phaseDir, nextCommand,
      });

      fs.writeFileSync(path.join(root, '.planning', 'BRIEF.md'), brief, 'utf8');

      const output = {
        hookSpecificOutput: {
          hookEventName: 'SessionStart',
          additionalContext:
            'Project brief updated. Read .planning/BRIEF.md for project orientation ' +
            'before loading any other planning files.',
        },
      };
      process.stdout.write(JSON.stringify(output));
    } catch (_) {
      process.exit(0); // Silent fail — never block session start
    }
  });
}
```

- [ ] **Step 4: Verify the file was created**

```bash
ls "C:/Users/Surface-Pro-1/.claude/hooks/gsd-brief-generator.js"
```

Expected: file listed with no error

- [ ] **Step 5: Commit scaffold**

```bash
cd "C:/Users/Surface-Pro-1/.claude" && git add hooks/gsd-brief-generator.js hooks/tests/gsd-brief-generator.test.js && git commit -m "feat: add gsd-brief-generator hook scaffold with stdin/stdout wrapper"
```

---

## Task 2: Unit tests for all parsing functions

**Files:**
- Modify: `C:\Users\Surface-Pro-1\.claude\hooks\tests\gsd-brief-generator.test.js`

- [ ] **Step 1: Write failing tests for all parsing functions**

Replace the scaffold test file content with:

```javascript
#!/usr/bin/env node
// Tests for gsd-brief-generator.js parsing functions
// Run: node "C:/Users/Surface-Pro-1/.claude/hooks/tests/gsd-brief-generator.test.js"

'use strict';
const assert = require('assert');
const path   = require('path');
const fs     = require('fs');
const os     = require('os');
const {
  parseStateYaml, parseActivePhase, parseRoadmap,
  parseConstraints, parseContextDecisions, findSpecFile, generateBrief,
} = require('../gsd-brief-generator.js');

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); console.log(`  ✓ ${name}`); passed++; }
  catch (e) { console.error(`  ✗ ${name}\n    ${e.message}`); failed++; }
}

// ── parseStateYaml ────────────────────────────────────────────────────────
const SAMPLE_STATE = `---
gsd_state_version: 1.0
milestone: v1.0
status: Executing Phase 04
last_updated: "2026-03-28T09:00:00Z"
progress:
  total_phases: 12
  completed_phases: 3
---

# Project State

**Phase**: 04 — Technical Analysis Engine (in progress)
`;

test('parseStateYaml: extracts status', () => {
  const r = parseStateYaml(SAMPLE_STATE);
  assert.strictEqual(r.status, 'Executing Phase 04');
});

test('parseStateYaml: extracts completed_phases', () => {
  const r = parseStateYaml(SAMPLE_STATE);
  assert.strictEqual(r.completed_phases, 3);
});

test('parseStateYaml: returns empty object when no frontmatter', () => {
  const r = parseStateYaml('# No frontmatter here');
  assert.deepStrictEqual(r, {});
});

// ── parseActivePhase ──────────────────────────────────────────────────────
test('parseActivePhase: extracts phase number and name', () => {
  const r = parseActivePhase(SAMPLE_STATE);
  assert.deepStrictEqual(r, { number: '04', name: 'Technical Analysis Engine' });
});

test('parseActivePhase: returns null when no phase line', () => {
  const r = parseActivePhase('# No phase here');
  assert.strictEqual(r, null);
});

test('parseActivePhase: pads single-digit phase numbers', () => {
  const r = parseActivePhase('**Phase**: 4 — Some Phase');
  assert.strictEqual(r.number, '04');
});

// ── parseRoadmap ──────────────────────────────────────────────────────────
const SAMPLE_ROADMAP = `## Phases

- [x] **Phase 1: Infrastructure Bootstrap** — Docker stuff
- [x] **Phase 2: Data Ingestion Foundation** — Celery workers
- [x] **Phase 3: Equity Overview** — Live quotes
- [ ] **Phase 4: Technical Analysis Engine** — Indicators
- [ ] **Phase 5: Macro Dashboard** — Yield curves
- [ ] **Phase 6: Forex & Commodities** — FX pairs

## Phase Details

### Phase 4: Technical Analysis Engine
**Goal**: Complete math engine — all indicator groups
**Depends on**: Phase 3
`;

test('parseRoadmap: extracts completed phases', () => {
  const { completed } = parseRoadmap(SAMPLE_ROADMAP, '04');
  assert.strictEqual(completed.length, 3);
  assert.strictEqual(completed[0].name, 'Infrastructure Bootstrap');
});

test('parseRoadmap: extracts active phase goal', () => {
  const { activeGoal } = parseRoadmap(SAMPLE_ROADMAP, '04');
  assert.strictEqual(activeGoal, 'Complete math engine — all indicator groups');
});

test('parseRoadmap: extracts next 2 upcoming phases', () => {
  const { upcoming } = parseRoadmap(SAMPLE_ROADMAP, '04');
  assert.strictEqual(upcoming.length, 2);
  assert.strictEqual(upcoming[0].name, 'Macro Dashboard');
  assert.strictEqual(upcoming[1].name, 'Forex & Commodities');
});

// ── parseConstraints ──────────────────────────────────────────────────────
const SAMPLE_PROJECT = `## Constraints

- **Cost**: Zero ongoing spend — all data sources free tier
- **Deployment**: Docker Compose on NAS; no Kubernetes
- **Stack**: FastAPI + React/Vite + TimescaleDB — no deviations
- **FinBERT**: Must run locally — no cloud NLP API calls

## Other Section
`;

test('parseConstraints: extracts up to 4 constraints', () => {
  const r = parseConstraints(SAMPLE_PROJECT);
  assert.strictEqual(r.length, 4);
  assert.ok(r[0].includes('Zero ongoing'));
});

test('parseConstraints: returns empty array when no Constraints section', () => {
  const r = parseConstraints('# No constraints here');
  assert.deepStrictEqual(r, []);
});

// ── parseContextDecisions ─────────────────────────────────────────────────
const SAMPLE_CONTEXT = `## Implementation Decisions

### Indicator UX

- **D-01:** Indicators button in chart panel header
- **D-02:** Expanded chart only
- **D-03:** Grouped by category

### Win Rate

- **D-07:** Pre-computed nightly via Celery
- **D-08:** Next-bar close-to-close
- **D-09:** Candlestick patterns only
`;

test('parseContextDecisions: extracts up to 5 decisions', () => {
  const r = parseContextDecisions(SAMPLE_CONTEXT);
  assert.strictEqual(r.length, 5);
  assert.ok(r[0].startsWith('D-01:'));
});

test('parseContextDecisions: returns empty array for empty content', () => {
  assert.deepStrictEqual(parseContextDecisions(''), []);
});

// ── findSpecFile ──────────────────────────────────────────────────────────
test('findSpecFile: finds bloomberg spec by pattern in temp dir', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'brief-test-'));
  const specsDir = path.join(tmp, 'docs', 'superpowers', 'specs');
  fs.mkdirSync(specsDir, { recursive: true });
  fs.writeFileSync(path.join(specsDir, '2026-03-24-bloomberg-terminal-design.md'), '');
  const result = findSpecFile(tmp);
  assert.ok(result.includes('bloomberg-terminal-design'));
  fs.rmSync(tmp, { recursive: true });
});

test('findSpecFile: returns null when specs dir missing', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'brief-test-'));
  assert.strictEqual(findSpecFile(tmp), null);
  fs.rmSync(tmp, { recursive: true });
});

// ── generateBrief ─────────────────────────────────────────────────────────
test('generateBrief: output includes active phase name', () => {
  const brief = generateBrief({
    activePhase: { number: '04', name: 'Technical Analysis Engine' },
    activeGoal: 'Complete math engine',
    stateYaml: { status: 'Executing Phase 04' },
    completed: [{ number: '01', name: 'Infrastructure Bootstrap' }],
    upcoming: [{ number: '05', name: 'Macro Dashboard' }],
    constraints: ['Zero ongoing spend'],
    decisions: ['D-01: Some decision'],
    specFile: 'docs/superpowers/specs/2026-03-24-bloomberg-terminal-design.md',
    phaseDir: '.planning/phases/04-technical-analysis-engine/04-CONTEXT.md',
    nextCommand: '/gsd:plan-phase 4',
  });
  assert.ok(brief.includes('Technical Analysis Engine'));
  assert.ok(brief.includes('Complete math engine'));
  assert.ok(brief.includes('D-01: Some decision'));
  assert.ok(brief.includes('§3'));  // spec section map present
});

test('generateBrief: handles missing spec file gracefully', () => {
  const brief = generateBrief({
    activePhase: { number: '04', name: 'Test' },
    activeGoal: 'goal', stateYaml: {}, completed: [], upcoming: [],
    constraints: [], decisions: [], specFile: null,
    phaseDir: null, nextCommand: '/gsd:plan-phase 4',
  });
  assert.ok(brief.includes('spec file not found'));
});

// ── Summary ───────────────────────────────────────────────────────────────
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
```

- [ ] **Step 2: Run tests — expect them to pass (logic already implemented in hook)**

```bash
node "C:/Users/Surface-Pro-1/.claude/hooks/tests/gsd-brief-generator.test.js"
```

Expected: all tests pass (`N passed, 0 failed`). If any fail, fix the corresponding function in `gsd-brief-generator.js` before continuing.

- [ ] **Step 3: Commit tests**

```bash
cd "C:/Users/Surface-Pro-1/.claude" && git add hooks/tests/gsd-brief-generator.test.js && git commit -m "test: unit tests for gsd-brief-generator parsing functions"
```

---

## Task 3: Integration test — run hook against real project

**Files:** No new files — testing existing hook against `C:\hhbfin`

- [ ] **Step 1: Create a minimal test harness that simulates hook invocation**

Run this directly in bash to simulate what Claude Code does when it triggers the SessionStart hook:

```bash
echo '{"cwd":"C:/hhbfin","session_id":"test-123"}' | node "C:/Users/Surface-Pro-1/.claude/hooks/gsd-brief-generator.js"
```

Expected output (stdout):
```json
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Project brief updated. Read .planning/BRIEF.md for project orientation before loading any other planning files."}}
```

- [ ] **Step 2: Verify BRIEF.md was written**

```bash
cat C:/hhbfin/.planning/BRIEF.md
```

Expected: file contains active phase (Phase 4: Technical Analysis Engine), constraints, spec section map with §3/§5/§6/§8, and recent D-NN decisions from 04-CONTEXT.md.

- [ ] **Step 3: Verify silent exit for non-GSD directory**

```bash
echo '{"cwd":"C:/Users","session_id":"test-456"}' | node "C:/Users/Surface-Pro-1/.claude/hooks/gsd-brief-generator.js"
echo "Exit code: $?"
```

Expected: no stdout output, exit code 0.

- [ ] **Step 4: Commit BRIEF.md to repo**

```bash
cd C:/hhbfin && git add .planning/BRIEF.md && git commit -m "feat: add auto-generated BRIEF.md (written by gsd-brief-generator hook)"
```

---

## Task 4: Register hook in settings.json

**Files:**
- Modify: `C:\Users\Surface-Pro-1\.claude\settings.json`

- [ ] **Step 1: Add hook to existing SessionStart[0].hooks array**

Edit `C:\Users\Surface-Pro-1\.claude\settings.json`. Find the `"SessionStart"` array. The existing structure is:

```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "node \"C:/Users/Surface-Pro-1/.claude/hooks/gsd-check-update.js\""
      }
    ]
  }
]
```

Add the new entry **after** `gsd-check-update.js` in the same inner `hooks` array:

```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "node \"C:/Users/Surface-Pro-1/.claude/hooks/gsd-check-update.js\""
      },
      {
        "type": "command",
        "command": "node \"C:/Users/Surface-Pro-1/.claude/hooks/gsd-brief-generator.js\""
      }
    ]
  }
]
```

- [ ] **Step 2: Validate settings.json is valid JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('C:/Users/Surface-Pro-1/.claude/settings.json','utf8')); console.log('valid JSON')"
```

Expected: `valid JSON`

- [ ] **Step 3: Commit settings change**

```bash
cd "C:/Users/Surface-Pro-1/.claude" && git add settings.json && git commit -m "feat: register gsd-brief-generator in SessionStart hooks"
```

---

## Task 5: Write CLAUDE.md

**Files:**
- Create: `C:\hhbfin\CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

Create `C:\hhbfin\CLAUDE.md` with this exact content:

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
```

- [ ] **Step 2: Verify CLAUDE.md is readable by Claude Code (plain text check)**

```bash
wc -l C:/hhbfin/CLAUDE.md
```

Expected: ~40 lines

- [ ] **Step 3: Commit CLAUDE.md**

```bash
cd C:/hhbfin && git add CLAUDE.md && git commit -m "feat: add CLAUDE.md with session loading rules and spec section routing"
```

---

## Task 6: End-to-end verification

**Files:** No changes — verification only

- [ ] **Step 1: Start a new Claude Code session in C:\hhbfin**

Open a fresh session (or `/clear`). Observe that:
- `gsd-brief-generator.js` runs on session start (no error in session output)
- The additionalContext nudge appears: "Project brief updated. Read .planning/BRIEF.md..."

- [ ] **Step 2: Ask Claude "what phase are we on?" without loading other files**

Expected: Claude answers "Phase 4: Technical Analysis Engine" sourced from BRIEF.md, without reading ROADMAP.md or PROJECT.md.

- [ ] **Step 3: Verify BRIEF.md contains correct data**

```bash
cat C:/hhbfin/.planning/BRIEF.md
```

Checklist:
- [ ] Active phase shows Phase 4: Technical Analysis Engine
- [ ] Goal line populated from ROADMAP.md
- [ ] 3 completed phases listed (1, 2, 3)
- [ ] Next 2 phases listed (5, 6)
- [ ] Hard constraints section present (4 items)
- [ ] Spec section map present with §3/§5/§6/§8
- [ ] Recent decisions from 04-CONTEXT.md present (D-01 through D-09 range) — **Note:** Phase 4 context exists but planning hasn't run yet, so this row may show "(no context file yet)" — that's correct and expected at this stage

- [ ] **Step 4: Add BRIEF.md to .gitignore (it's auto-generated)**

```bash
echo ".planning/BRIEF.md" >> C:/hhbfin/.gitignore
cd C:/hhbfin && git add .gitignore && git commit -m "chore: gitignore auto-generated BRIEF.md"
```

If BRIEF.md was previously committed (Task 3 Step 4 committed it), untrack it in a second commit:

```bash
cd C:/hhbfin && git rm --cached .planning/BRIEF.md && git commit -m "chore: untrack auto-generated BRIEF.md"
```

---

*Plan written: 2026-03-29*
