---
phase: 4
slug: technical-analysis-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.0+ |
| **Config file** | `backend/conftest.py` (exists) |
| **Quick run command** | `pytest backend/tests/analysis/ -x -q` |
| **Full suite command** | `pytest backend/tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest backend/tests/analysis/ -x -q`
- **After every plan wave:** Run `pytest backend/tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-* | 01 | 1 | TA-01 | unit | `pytest backend/tests/analysis/test_indicators.py::test_moving_averages -x` | ❌ W0 | ⬜ pending |
| 4-02-* | 02 | 1 | TA-02 | unit | `pytest backend/tests/analysis/test_indicators.py::test_momentum -x` | ❌ W0 | ⬜ pending |
| 4-03-* | 03 | 1 | TA-03, TA-04, TA-05 | unit | `pytest backend/tests/analysis/test_indicators.py::test_trend_strength -x` | ❌ W0 | ⬜ pending |
| 4-04-* | 04 | 1 | TA-06, TA-07, TA-08 | unit | `pytest backend/tests/analysis/test_indicators.py::test_breadth -x` | ❌ W0 | ⬜ pending |
| 4-05-* | 05 | 2 | TA-09, TA-13 | unit | `pytest backend/tests/analysis/test_patterns.py -x` | ❌ W0 | ⬜ pending |
| 4-06-* | 06 | 2 | TA-10 | unit | `pytest backend/tests/analysis/test_chart_patterns.py -x` | ❌ W0 | ⬜ pending |
| 4-07-* | 07 | 3 | TA-11, TA-12 | unit | `pytest backend/tests/analysis/test_fibonacci.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/analysis/test_indicators.py` — stubs for TA-01 through TA-08 (grouped tests: moving averages, momentum, trend strength, volatility, volume, breadth, intermarket)
- [ ] `backend/tests/analysis/test_patterns.py` — stubs for TA-09, TA-13 (candlestick patterns + statistical significance)
- [ ] `backend/tests/analysis/test_chart_patterns.py` — stubs for TA-10 (chart pattern detection: H&S, Double Top, Cup & Handle)
- [ ] `backend/tests/analysis/test_pivot_points.py` — stubs for TA-07 (all 5 pivot point methods)
- [ ] `backend/tests/analysis/test_fibonacci.py` — stubs for TA-11 (level math: 0.236/0.382/0.5/0.618/0.786/1.0/1.618/2.618)
- [ ] `backend/tests/analysis/test_elliott_wave.py` — stubs for TA-12 (Wave 3 shortest check, Wave 4 overlap validation)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fibonacci levels drawn interactively on chart click | TA-11 | Requires browser interaction — click drag on chart | Open equity view, click chart at swing high, drag to swing low, verify 7 levels appear as price lines |
| Elliott Wave labels manually placed on chart | TA-12 | Requires browser interaction | Open equity view, right-click chart, place Wave 1–5 labels, verify Fibonacci ratio validation fires on each placement |
| Indicator picker opens and overlays indicator on chart | TA-01 through TA-08 | Requires browser rendering | Open equity view, click indicator picker, select SMA(20), verify overlay appears on chart with correct colour |
| Candlestick pattern badge renders on today's bar | TA-09 | Requires live/recent OHLCV data matching a pattern | Run with real ticker data, verify badge shows "PatternName: XX% win, n=YY, p=0.ZZ" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
