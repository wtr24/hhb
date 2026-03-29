---
phase: "04"
plan: "04-02"
subsystem: technical-analysis-engine
tags: [indicators, trend-strength, volatility, volume, garch, ta-lib, pandas-ta]
dependency_graph:
  requires: [04-01]
  provides: [TA-03, TA-04, TA-05]
  affects: [backend/analysis/indicators.py, backend/analysis/garch.py]
tech_stack:
  added: [arch>=8.0.0 (GARCH), pandas-ta (SuperTrend/Vortex/Ichimoku/Keltner)]
  patterns: [pure-function indicators, numpy array I/O, NaN strip helper]
key_files:
  created: [backend/analysis/garch.py]
  modified: [backend/analysis/indicators.py, backend/tests/analysis/test_indicators.py]
decisions:
  - "arch library isolated to garch.py — heavyweight imports kept out of indicators.py"
  - "GARCH returns error dict on <100 bars — no exception raised (caller-safe)"
  - "compute_vwap hand-rolled — no TA-Lib equivalent exists"
  - "CMF hand-rolled with numpy rolling window — more accurate than ADOSC approximation"
  - "Volume Profile returns histogram dict (not time-series) — used as chart overlay"
metrics:
  duration: 301s
  completed: "2026-03-29"
  tasks: 2
  files: 3
---

# Phase 4 Plan 2: Trend Strength, Volatility, and Volume Indicators Summary

## One-liner

Added 26 indicator functions covering ADX/Aroon/SAR/SuperTrend/Ichimoku (TA-03), Bollinger/Keltner/Donchian/ATR/HV/GARCH/Ulcer (TA-04), and OBV/VWAP variants/A-D/CMF/MFI/VolumeProfile/CVD/NVI-PVI/ForceIndex (TA-05) to `indicators.py` plus isolated GARCH(1,1) in `garch.py`.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 4-02-1 | Trend strength (TA-03) + volatility (TA-04) indicators, garch.py created | 02dbbf8 |
| 4-02-2 | Volume indicators (TA-05) appended + test stubs replaced with real assertions | 31bbe06 |

## Test Results

`pytest backend/tests/analysis/test_indicators.py -x -q` — 23 passed, 4 skipped (TA-06 and TA-08 Wave 0 stubs remain).

Filter `pytest -k "trend_strength or volatility or volume"` — 12 passed, 0 failed.

## Functions Added

### TA-03 Trend Strength (indicators.py)
- `compute_adx` — ADX + +DI + -DI via talib
- `compute_aroon` — Aroon Up/Down + Oscillator via talib
- `compute_parabolic_sar` — SAR via talib
- `compute_supertrend` — via pandas_ta (TA-Lib has no SuperTrend)
- `compute_vortex` — +VI/-VI via pandas_ta
- `compute_ichimoku` — 5-line cloud via pandas_ta (tenkan, kijun, senkou_a, senkou_b, chikou)
- `compute_mass_index` — hand-rolled EMA-ratio rolling sum

### TA-04 Volatility (indicators.py + garch.py)
- `compute_bollinger_bands` — upper/middle/lower + %B via talib.BBANDS
- `compute_keltner_channel` — via pandas_ta
- `compute_donchian_channel` — hand-rolled rolling max/min
- `compute_atr` — via talib.ATR
- `compute_historical_vol` — close-to-close method
- `compute_historical_vol_parkinson` — high-low Parkinson method
- `compute_chaikin_volatility` — ROC of EMA(HL) via talib
- `compute_ulcer_index` — RMS drawdown from N-bar high
- `compute_garch_volatility` (garch.py) — GARCH(1,1) via arch library, returns params + 1-day forecast

### TA-05 Volume (indicators.py)
- `compute_obv` — via talib.OBV
- `compute_vwap` — cumulative session VWAP, hand-rolled
- `compute_anchored_vwap` — from user-selected anchor bar
- `compute_vwap_sd_bands` — VWAP ± 1σ/2σ bands
- `compute_ad_line` — via talib.AD
- `compute_cmf` — Chaikin Money Flow, hand-rolled rolling window
- `compute_mfi` — via talib.MFI
- `compute_volume_profile` — histogram of volume-at-price, returns bins/volumes/poc
- `compute_cvd` — Cumulative Volume Delta (up/down bar splitting)
- `compute_vroc` — Volume ROC via talib.ROC on volume array
- `compute_ease_of_movement` — mid-move / box-ratio smoothed by SMA
- `compute_nvi_pvi` — Negative/Positive Volume Index starting at 1000
- `compute_force_index` — EMA of (close delta * volume)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing `arch` library in local Python environment**
- **Found during:** Task 4-02-2 test run
- **Issue:** `ModuleNotFoundError: No module named 'arch'` when running test_volatility_garch locally
- **Fix:** Installed `arch` via pip. Library was already in `backend/requirements.txt` (>=8.0.0), so Docker production is unaffected.
- **Files modified:** none (pip install only)
- **Commit:** N/A (environment fix)

## Known Stubs

None — all TA-03/TA-04/TA-05 tests are wired with real data. TA-06 (Market Breadth) and TA-08 (Intermarket) remain as Wave 0 pytest.skip() stubs per plan design.

## Self-Check: PASSED
