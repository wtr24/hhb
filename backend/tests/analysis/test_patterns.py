"""Wave 0 stubs — TA-09 candlestick patterns + TA-13 statistical significance."""
import pytest
import numpy as np

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
    pytest.skip("Wave 0 stub — TA-09")

def test_cdl_engulfing_detection(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-09")

def test_all_60_patterns_return_array(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-09")

def test_pattern_win_rate_computed(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-13")

def test_pattern_p_value_computed(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-13")

def test_pattern_insufficient_data_below_30(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-13")

def test_pattern_out_of_sample_split(ohlcv_200):
    pytest.skip("Wave 0 stub — TA-13")
