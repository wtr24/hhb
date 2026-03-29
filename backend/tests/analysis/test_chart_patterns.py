"""Wave 0 stubs — TA-10 chart pattern detection."""
import pytest
import numpy as np

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
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_inverse_head_and_shoulders(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_double_top(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_double_bottom(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_cup_and_handle(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_triangle(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_detect_flag_pennant(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")

def test_confidence_score_range(synthetic_hs):
    pytest.skip("Wave 0 stub — TA-10")
