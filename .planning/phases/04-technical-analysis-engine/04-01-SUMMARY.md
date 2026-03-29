---
plan: 04-01
phase: 04
subsystem: analysis
tags: [indicators, ta-lib, pandas-ta, moving-averages, momentum, oscillators]
dependency_graph:
  requires: [04-00]
  provides: [TA-01, TA-02]
  affects: [backend/analysis/indicators.py]
tech_stack:
  added: [TA-Lib 0.6.8, pandas-ta 0.4.71b0]
  patterns: [pure-function computation module, _strip_nan helper, NaN-stripped dict returns]
key_files:
  created:
    - backend/analysis/indicators.py
  modified:
    - backend/tests/analysis/test_indicators.py
decisions:
  - TA-Lib 0.6.8 binary wheels install correctly via pip on both local Windows and Docker Linux containers
  - pandas-ta (with numba) used for HMA, VWMA, KDJ — TA-Lib does not cover these
  - DPO hand-rolled (no TA-Lib support): DPO = Close[i] - SMA[i - period/2 - 1]
  - LWMA is an alias for WMA (identical formula)
  - EMA Ribbon uses 8 Fibonacci-derived periods [8,13,21,34,55,89,144,233] by default
metrics:
  duration: 270s
  completed: 2026-03-29
  tasks: 2
  files: 2
---

# Phase 4 Plan 1: Moving Averages and Momentum Indicators Summary

## One-liner

Pure-function TA-Lib + pandas-ta indicators module covering 10 moving averages and 14 momentum/oscillator functions, all NaN-stripped and returning typed dicts.

## What Was Built

### Task 4-01-1: Moving Averages (TA-01)

Created `backend/analysis/indicators.py` with all moving average variants:

- **SMA, EMA, DEMA, TEMA, WMA, LWMA** — via `talib` (C-speed bindings)
- **HMA** (Hull MA) — via `pandas_ta.hma()` (talib does not implement HMA)
- **VWMA** (Volume Weighted MA) — via `pandas_ta.vwma()` with volume input
- **Golden/Death Cross** — SMA(fast) vs SMA(slow), returns signal array {-1, 0, +1}
- **EMA Ribbon** — 8 EMAs at Fibonacci periods [8, 13, 21, 34, 55, 89, 144, 233]
- `_strip_nan(times, values)` helper — removes leading NaN from all TA-Lib output

### Task 4-01-2: Momentum / Oscillators (TA-02) + Test Updates

Appended 14 momentum/oscillator functions to `indicators.py`:

- **RSI** (Relative Strength Index) — talib, range 0–100
- **StochRSI** — RSI values fed into STOCH, returns %K and %D
- **MACD** — returns macd_line, signal_line, histogram
- **Stochastic** — talib.STOCH, %K and %D
- **Williams %R** — talib.WILLR, range -100 to 0
- **CCI** (Commodity Channel Index) — talib.CCI
- **ROC** (Rate of Change) — talib.ROC
- **Momentum** — talib.MOM
- **DPO** (Detrended Price Oscillator) — hand-rolled (talib lacks DPO)
- **TRIX** — talib.TRIX (1-day ROC of triple smooth EMA)
- **Ultimate Oscillator** — talib.ULTOSC, 3 time periods
- **PPO** (Percentage Price Oscillator) — talib.PPO
- **KDJ** — pandas_ta.kdj (adds J line = 3K - 2D; talib STOCH lacks J)
- **CMO** (Chande Momentum Oscillator) — talib.CMO, range -100 to +100

Updated `backend/tests/analysis/test_indicators.py`:
- Replaced all 11 Wave 0 `pytest.skip()` stubs with real assertions
- Added imports for all tested functions
- TA-03 through TA-08 stubs remain correctly SKIPPED

## Verification Results

```
pytest backend/tests/analysis/test_indicators.py -k "moving_averages or momentum" -q
9 passed, 18 deselected in 2.50s

pytest backend/tests/analysis/test_indicators.py -x -q
11 passed, 16 skipped in 3.36s
```

All TA-01/TA-02 tests pass. TA-03 through TA-08 remain SKIPPED (correct Wave 0 behavior).

## Commits

| Task | Hash | Message |
|------|------|---------|
| 4-01-1 | 2c0be27 | feat(04-01): create indicators.py with moving averages (TA-01) |
| 4-01-2 | e9f7bf0 | feat(04-01): implement TA-01/TA-02 tests and momentum indicators (TA-02) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all TA-01 and TA-02 functions are fully implemented and tested.

## Self-Check: PASSED
