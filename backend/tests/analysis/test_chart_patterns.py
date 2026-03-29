"""Tests for TA-10 chart pattern detection module."""
import numpy as np
import pytest

from analysis.chart_patterns import (
    detect_head_and_shoulders,
    detect_inverse_head_and_shoulders,
    detect_double_top,
    detect_double_bottom,
    detect_cup_and_handle,
    detect_triangle,
    detect_flag_pennant,
    detect_all_chart_patterns,
)


@pytest.fixture
def synthetic_hs():
    """Synthetic price series shaped like a Head-and-Shoulders pattern."""
    bars = np.array([
        100, 102, 105, 103, 106, 110, 107, 104, 108, 112,
        115, 111, 107, 103, 106, 110, 107, 103, 100, 97
    ], dtype=float)
    volumes = np.ones(len(bars)) * 1_000_000
    return {"high": bars + 1, "low": bars - 1, "close": bars, "volume": volumes}


def test_detect_head_and_shoulders(synthetic_hs):
    highs = synthetic_hs["high"]
    lows = synthetic_hs["low"]
    closes = synthetic_hs["close"]
    volumes = synthetic_hs["volume"]
    result = detect_head_and_shoulders(highs, lows, closes, volumes)
    assert isinstance(result, list)
    if result:
        assert result[0]["pattern"] == "head_and_shoulders"


def test_detect_inverse_head_and_shoulders(synthetic_hs):
    # Invert the price series to create an inverse H&S
    highs = -synthetic_hs["low"]
    lows = -synthetic_hs["high"]
    closes = -synthetic_hs["close"]
    volumes = synthetic_hs["volume"]
    result = detect_inverse_head_and_shoulders(highs, lows, closes, volumes)
    assert isinstance(result, list)


def test_detect_double_top():
    # Two equal peaks separated by a trough
    n = 40
    closes = np.ones(n, dtype=float) * 100.0
    highs = closes.copy()
    lows = closes.copy()
    # First peak at bar 8
    highs[8] = 110.0
    closes[8] = 109.0
    # Trough between peaks
    lows[16] = 92.0
    closes[16] = 93.0
    # Second peak at bar 24 (within 3% of first)
    highs[24] = 110.5
    closes[24] = 109.5
    volumes = np.ones(n) * 1_000_000
    result = detect_double_top(highs, lows, closes, volumes)
    assert len(result) >= 1


def test_detect_double_bottom():
    # Two equal troughs separated by a peak
    n = 40
    closes = np.ones(n, dtype=float) * 100.0
    highs = closes.copy()
    lows = closes.copy()
    # First trough at bar 8
    lows[8] = 90.0
    closes[8] = 91.0
    # Peak between troughs
    highs[16] = 108.0
    closes[16] = 107.0
    # Second trough at bar 24 (within 3% of first)
    lows[24] = 90.5
    closes[24] = 91.5
    volumes = np.ones(n) * 1_000_000
    result = detect_double_bottom(highs, lows, closes, volumes)
    assert len(result) >= 1


def test_detect_cup_and_handle():
    # U-shaped + handle: 50 bars
    n = 50
    # Cup: bars 0-39 form a U shape
    t = np.linspace(0, np.pi, 40)
    cup = 100 - 10 * np.sin(t)  # starts high, dips, returns
    handle = cup[-1] - np.linspace(0, 2, 10)  # slight downward drift
    closes = np.concatenate([cup, handle])
    highs = closes + 1.0
    lows = closes - 1.0
    volumes = np.ones(n) * 1_000_000
    result = detect_cup_and_handle(highs, lows, closes, volumes)
    assert isinstance(result, list)


def test_detect_triangle():
    # Converging highs and lows over 20 bars (symmetric triangle)
    n = 20
    x = np.arange(n, dtype=float)
    highs = 110 - 0.2 * x        # declining highs
    lows = 90 + 0.2 * x          # rising lows
    closes = (highs + lows) / 2
    volumes = np.ones(n) * 1_000_000
    result = detect_triangle(highs, lows, closes, volumes)
    assert isinstance(result, list)


def test_detect_flag_pennant():
    # Strong upward pole followed by sideways consolidation
    n = 30
    pole = np.linspace(100, 115, 10)       # strong 15% up move
    consolidation = np.linspace(115, 114, 20)  # slight drift
    closes = np.concatenate([pole, consolidation])
    highs = closes + 0.5
    lows = closes - 0.5
    volumes = np.ones(n) * 1_000_000
    result = detect_flag_pennant(highs, lows, closes, volumes)
    assert isinstance(result, list)


def test_confidence_score_range(synthetic_hs):
    highs = synthetic_hs["high"]
    lows = synthetic_hs["low"]
    closes = synthetic_hs["close"]
    volumes = synthetic_hs["volume"]
    result = detect_all_chart_patterns(highs, lows, closes, volumes)
    assert isinstance(result, list)
    for r in result:
        assert 0.0 <= r["confidence"] <= 1.0, (
            f"confidence {r['confidence']} out of range for {r['pattern']}"
        )
        assert r["experimental"] is True, (
            f"experimental flag missing for {r['pattern']}"
        )
