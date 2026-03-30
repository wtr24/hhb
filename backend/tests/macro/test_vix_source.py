"""Unit tests for vix_source.py — VIX term structure fetch and regime classification."""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from ingestion.sources.vix_source import fetch_vix_term_structure, _classify_regime


def _make_ticker_mock(price: float):
    """Helper: mock yfinance Ticker with fast_info.last_price = price."""
    mock = MagicMock()
    mock.fast_info = {"last_price": price}
    return mock


def test_vix_source_returns_spot():
    mocks = {
        "^VIX": _make_ticker_mock(18.5),
        "^VIX3M": _make_ticker_mock(19.2),
        "^VIX6M": _make_ticker_mock(20.1),
    }
    with patch("ingestion.sources.vix_source.yf.Ticker", side_effect=lambda t: mocks[t]):
        result = fetch_vix_term_structure(history_row_count=300)

    assert result["spot_vix"] == pytest.approx(18.5)
    assert result["vix_3m"] == pytest.approx(19.2)
    assert result["vix_6m"] == pytest.approx(20.1)
    assert "time" in result
    assert "regime" in result


def test_vix_contango_flag_computed():
    mocks = {
        "^VIX": _make_ticker_mock(15.0),
        "^VIX3M": _make_ticker_mock(17.0),  # 3M > spot → contango
        "^VIX6M": _make_ticker_mock(18.0),
    }
    with patch("ingestion.sources.vix_source.yf.Ticker", side_effect=lambda t: mocks[t]):
        result = fetch_vix_term_structure(history_row_count=300)

    assert result["contango"] is True


def test_vix_regime_thresholds():
    assert _classify_regime(12.0) == "LOW_VOL"
    assert _classify_regime(17.5) == "NORMAL"
    assert _classify_regime(25.0) == "ELEVATED"
    assert _classify_regime(35.0) == "CRISIS"
    # Boundary values
    assert _classify_regime(15.0) == "NORMAL"   # >= 15
    assert _classify_regime(20.0) == "ELEVATED"  # >= 20
    assert _classify_regime(30.0) == "CRISIS"    # >= 30


def test_vix_history_depth_flag():
    mocks = {
        "^VIX": _make_ticker_mock(20.0),
        "^VIX3M": _make_ticker_mock(21.0),
        "^VIX6M": _make_ticker_mock(22.0),
    }
    with patch("ingestion.sources.vix_source.yf.Ticker", side_effect=lambda t: mocks[t]):
        result_shallow = fetch_vix_term_structure(history_row_count=100)
        result_deep = fetch_vix_term_structure(history_row_count=300)

    assert result_shallow["history_depth_ok"] is False
    assert result_deep["history_depth_ok"] is True


def test_vix_source_handles_missing_vix6m():
    """VIX6M fetch failure should not abort — vix_6m must be None."""
    def make_mock(ticker):
        if ticker == "^VIX6M":
            m = MagicMock()
            m.fast_info = {"last_price": None}
            m.history.return_value = MagicMock(empty=True)
            return m
        return _make_ticker_mock(18.0 if ticker == "^VIX" else 19.0)

    with patch("ingestion.sources.vix_source.yf.Ticker", side_effect=make_mock):
        result = fetch_vix_term_structure(history_row_count=300)

    assert result["vix_6m"] is None
    assert result["spot_vix"] == pytest.approx(18.0)
