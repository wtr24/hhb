"""TA-01 through TA-05 indicator tests — Wave 1 implementation."""
import pytest
import numpy as np

from analysis.indicators import (
    compute_sma, compute_ema, compute_hma, compute_vwma,
    compute_golden_death_cross, compute_ema_ribbon,
    compute_rsi, compute_macd, compute_stoch_rsi,
    compute_williams_r, compute_kdj,
    compute_adx, compute_aroon, compute_parabolic_sar, compute_supertrend, compute_ichimoku,
    compute_bollinger_bands, compute_atr, compute_historical_vol, compute_ulcer_index,
    compute_obv, compute_vwap, compute_volume_profile, compute_cmf, compute_mfi,
)
from analysis.garch import compute_garch_volatility

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
    times = np.arange(100, dtype=float)
    result = compute_sma(ohlcv_100["close"], times, period=20)
    assert len(result["values"]) > 0
    assert all(isinstance(v, float) for v in result["values"])
    assert not any(np.isnan(v) for v in result["values"])


def test_moving_averages_ema(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_ema(ohlcv_100["close"], times, period=20)
    assert len(result["values"]) > 0
    assert all(isinstance(v, float) for v in result["values"])
    assert not any(np.isnan(v) for v in result["values"])


def test_moving_averages_hma(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_hma(ohlcv_100["close"], times, period=20)
    assert len(result["values"]) > 0
    assert not any(np.isnan(v) for v in result["values"])


def test_moving_averages_vwma(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_vwma(ohlcv_100["close"], ohlcv_100["volume"], times, period=20)
    assert len(result["values"]) > 0
    assert not any(np.isnan(v) for v in result["values"])


def test_golden_death_cross(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_golden_death_cross(ohlcv_100["close"], times, fast=10, slow=20)
    assert "signal" in result
    assert all(v in {-1, 0, 1} for v in result["signal"])


def test_ema_ribbon(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_ema_ribbon(ohlcv_100["close"], times)
    assert len(result) == 8


# TA-02 Momentum / Oscillators

def test_momentum_rsi(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_rsi(ohlcv_100["close"], times, period=14)
    assert len(result["values"]) > 0
    assert all(0.0 <= v <= 100.0 for v in result["values"])


def test_momentum_macd(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_macd(ohlcv_100["close"], times)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result


def test_momentum_stoch_rsi(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_stoch_rsi(ohlcv_100["close"], times)
    assert "k" in result
    assert "d" in result


def test_momentum_williams_r(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_williams_r(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times, period=14
    )
    assert len(result["values"]) > 0
    assert all(-100.0 <= v <= 0.0 for v in result["values"])


def test_momentum_kdj(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_kdj(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times
    )
    assert "k" in result
    assert "d" in result
    assert "j" in result


# TA-03 Trend Strength

def test_trend_strength_adx(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_adx(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times, period=14
    )
    assert "adx" in result
    assert "plus_di" in result
    assert "minus_di" in result
    assert len(result["adx"]) > 0
    assert all(0.0 <= v <= 100.0 for v in result["adx"])


def test_trend_strength_supertrend(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_supertrend(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times
    )
    assert "values" in result
    assert "direction" in result
    assert len(result["values"]) > 0
    assert all(d in {1, -1} for d in result["direction"])


def test_trend_strength_ichimoku(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_ichimoku(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times
    )
    assert "tenkan_sen" in result
    assert "kijun_sen" in result
    assert "senkou_a" in result
    assert "senkou_b" in result
    assert "chikou_span" in result


def test_trend_strength_parabolic_sar(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_parabolic_sar(ohlcv_100["high"], ohlcv_100["low"], times)
    assert "values" in result
    assert len(result["values"]) > 0


# TA-04 Volatility

def test_volatility_bollinger_bands(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_bollinger_bands(ohlcv_100["close"], times, period=20)
    assert "upper" in result
    assert "middle" in result
    assert "lower" in result
    assert len(result["upper"]) > 0
    assert all(u > m > l for u, m, l in zip(result["upper"], result["middle"], result["lower"]))


def test_volatility_atr(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_atr(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], times, period=14
    )
    assert len(result["values"]) > 0
    assert all(v >= 0 for v in result["values"])


def test_volatility_garch(ohlcv_100):
    np.random.seed(99)
    closes_100 = 100 + np.cumsum(np.random.randn(100) * 0.5)
    result = compute_garch_volatility(closes_100)
    assert "vol_1d_forward" in result

    closes_50 = 100 + np.cumsum(np.random.randn(50) * 0.5)
    result_short = compute_garch_volatility(closes_50)
    assert "error" in result_short


def test_volatility_historical_vol(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_historical_vol(ohlcv_100["close"], times, period=20)
    assert len(result["values"]) > 0
    assert all(v > 0 for v in result["values"])


# TA-05 Volume

def test_volume_obv(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_obv(ohlcv_100["close"], ohlcv_100["volume"], times)
    assert "values" in result
    assert len(result["values"]) > 0


def test_volume_vwap(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_vwap(
        ohlcv_100["close"], ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["volume"], times
    )
    assert "values" in result
    assert len(result["values"]) > 0
    assert all(v > 0 for v in result["values"])


def test_volume_profile(ohlcv_100):
    result = compute_volume_profile(ohlcv_100["close"], ohlcv_100["volume"])
    assert "bins" in result
    assert "volumes" in result
    assert "poc" in result
    assert isinstance(result["poc"], float)


def test_volume_cmf(ohlcv_100):
    times = np.arange(100, dtype=float)
    result = compute_cmf(
        ohlcv_100["high"], ohlcv_100["low"], ohlcv_100["close"], ohlcv_100["volume"], times
    )
    assert "values" in result
    assert len(result["values"]) > 0
    assert all(-1.0 <= v <= 1.0 for v in result["values"])


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
