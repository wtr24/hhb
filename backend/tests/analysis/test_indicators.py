"""Wave 0 stubs — replaced by Wave 1 implementation tests."""
import pytest
import numpy as np

# Synthetic OHLCV data used across all indicator tests (100 bars)
@pytest.fixture
def ohlcv_100():
    np.random.seed(42)
    closes = 100 + np.cumsum(np.random.randn(100) * 0.5)
    highs = closes + np.abs(np.random.randn(100) * 0.3)
    lows = closes - np.abs(np.random.randn(100) * 0.3)
    opens = closes + np.random.randn(100) * 0.1
    volumes = np.abs(np.random.randn(100) * 1_000_000) + 500_000
    return {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}


# TA-01 Moving Averages
def test_moving_averages_sma(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")

def test_moving_averages_ema(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")

def test_moving_averages_hma(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")

def test_moving_averages_vwma(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")

def test_golden_death_cross(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")

def test_ema_ribbon(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-01")


# TA-02 Momentum / Oscillators
def test_momentum_rsi(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-02")

def test_momentum_macd(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-02")

def test_momentum_stoch_rsi(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-02")

def test_momentum_williams_r(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-02")

def test_momentum_kdj(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-02")


# TA-03 Trend Strength
def test_trend_strength_adx(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-03")

def test_trend_strength_supertrend(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-03")

def test_trend_strength_ichimoku(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-03")

def test_trend_strength_parabolic_sar(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-03")


# TA-04 Volatility
def test_volatility_bollinger_bands(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-04")

def test_volatility_atr(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-04")

def test_volatility_garch(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-04")

def test_volatility_historical_vol(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-04")


# TA-05 Volume
def test_volume_obv(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-05")

def test_volume_vwap(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-05")

def test_volume_profile(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-05")

def test_volume_cmf(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-05")


# TA-06 Market Breadth
def test_breadth_mcclellan(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-06")

def test_breadth_trin(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-06")

def test_breadth_pct_above_sma(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-06")


# TA-08 Intermarket
def test_intermarket_correlation(ohlcv_100):
    pytest.skip("Wave 0 stub — TA-08")
