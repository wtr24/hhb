"""TA-09 candlestick pattern detection + TA-13 statistical significance tests."""
import pytest
import numpy as np

from analysis.candlestick_patterns import (
    detect_all_patterns, compute_pattern_stats, CDL_FUNCTIONS,
)


@pytest.fixture
def ohlcv_200():
    np.random.seed(7)
    closes = 100 + np.cumsum(np.random.randn(200) * 0.5)
    highs = closes + np.abs(np.random.randn(200) * 0.3)
    lows = closes - np.abs(np.random.randn(200) * 0.3)
    opens = closes + np.random.randn(200) * 0.1
    volumes = np.abs(np.random.randn(200) * 1_000_000) + 500_000
    return {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}


def test_cdl_hammer_detection(ohlcv_200):
    result = detect_all_patterns(
        ohlcv_200["open"], ohlcv_200["high"], ohlcv_200["low"], ohlcv_200["close"]
    )
    assert "CDLHAMMER" in result
    assert isinstance(result["CDLHAMMER"], np.ndarray)
    assert len(result["CDLHAMMER"]) == len(ohlcv_200["close"])


def test_cdl_engulfing_detection(ohlcv_200):
    result = detect_all_patterns(
        ohlcv_200["open"], ohlcv_200["high"], ohlcv_200["low"], ohlcv_200["close"]
    )
    assert "CDLENGULFING" in result
    assert isinstance(result["CDLENGULFING"], np.ndarray)
    assert len(result["CDLENGULFING"]) == len(ohlcv_200["close"])


def test_all_60_patterns_return_array(ohlcv_200):
    assert len(CDL_FUNCTIONS) >= 60
    result = detect_all_patterns(
        ohlcv_200["open"], ohlcv_200["high"], ohlcv_200["low"], ohlcv_200["close"]
    )
    for name, arr in result.items():
        assert isinstance(arr, np.ndarray), f"{name} did not return np.ndarray"


def test_pattern_win_rate_computed():
    """Inject 40 occurrences in OOS region (last 20% of 200 bars = last 40 bars)."""
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(200) * 0.5)
    signals = np.zeros(200, dtype=int)
    # Inject 40 bullish signals in last 40 bars (OOS region, exclude last bar)
    signals[159:199] = 100  # bars 159..198 (40 occurrences), bar 199 is excluded by OOS logic

    result = compute_pattern_stats(signals, closes, min_n=30)
    assert result["win_rate"] is not None
    assert isinstance(result["win_rate"], float)
    assert 0.0 <= result["win_rate"] <= 1.0


def test_pattern_p_value_computed():
    """Same synthetic setup — assert p_value is computed and in [0, 1]."""
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(200) * 0.5)
    signals = np.zeros(200, dtype=int)
    signals[159:199] = 100

    result = compute_pattern_stats(signals, closes, min_n=30)
    assert result["p_value"] is not None
    assert isinstance(result["p_value"], float)
    assert 0.0 <= result["p_value"] <= 1.0


def test_pattern_insufficient_data_below_30():
    """Only 10 occurrences in OOS — win_rate and p_value must be None."""
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(200) * 0.5)
    signals = np.zeros(200, dtype=int)
    # Inject only 10 bullish signals in OOS region
    signals[160:170] = 100  # 10 occurrences

    result = compute_pattern_stats(signals, closes, min_n=30)
    assert result["win_rate"] is None
    assert result["p_value"] is None
    assert result["n_occurrences"] == 10


def test_pattern_out_of_sample_split():
    """
    Test that only OOS (last 20%) bars count toward stats.

    Case 1: 40 occurrences in OOS region (bars 159–198) → stats computed.
    Case 2: All occurrences in IS region (bars 0–159) → n_occurrences == 0 → win_rate None.
    """
    np.random.seed(99)
    closes = 100 + np.cumsum(np.random.randn(200) * 0.5)

    # Case 1: occurrences in OOS region
    signals_oos = np.zeros(200, dtype=int)
    signals_oos[159:199] = 100  # 40 occurrences in OOS
    result_oos = compute_pattern_stats(signals_oos, closes, min_n=30)
    assert result_oos["n_occurrences"] >= 30
    assert result_oos["win_rate"] is not None

    # Case 2: occurrences only in IS region (bars 0–158) — zero in OOS
    signals_is = np.zeros(200, dtype=int)
    signals_is[0:40] = 100  # 40 occurrences, all in first 80% (in-sample)
    result_is = compute_pattern_stats(signals_is, closes, min_n=30)
    assert result_is["n_occurrences"] == 0
    assert result_is["win_rate"] is None
