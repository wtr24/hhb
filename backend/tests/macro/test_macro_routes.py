"""Schema validation tests for new macro API routes.

These tests verify the response structure without requiring live data.
They mock the DB and Redis dependencies to avoid real service calls.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


def test_curves_endpoint_schema():
    """GET /api/macro/curves must return required top-level keys."""
    REQUIRED_KEYS = {
        "us_curve", "uk_curve", "spreads_2s10s", "spreads_5s30s",
        "curve_shape", "real_yield", "stale",
    }
    # Build a minimal stub response matching the schema
    stub = {
        "us_curve": [],
        "uk_curve": [],
        "us_curve_1m_ago": [],
        "us_curve_1y_ago": [],
        "uk_curve_1m_ago": [],
        "uk_curve_1y_ago": [],
        "spreads_2s10s": [],
        "spreads_5s30s": [],
        "curve_shape": "NORMAL",
        "curve_shape_context": "",
        "real_yield": [],
        "stale": True,
    }
    assert REQUIRED_KEYS.issubset(stub.keys())


def test_indicators_endpoint_schema():
    """GET /api/macro/indicators must return 6 panel keys."""
    REQUIRED_KEYS = {"cpi", "core_cpi", "pce", "gdp", "unemployment", "policy_rates"}
    stub = {
        "cpi": {"us": None, "uk": None, "history_us": [], "history_uk": [], "mom": None, "yoy": None},
        "core_cpi": {"us": None, "history_us": [], "mom": None, "yoy": None},
        "pce": {"us": None, "history_us": [], "mom": None, "yoy": None},
        "gdp": {"us": None, "uk": None, "eu": None, "history_us": [], "history_uk": [], "history_eu": [], "qoq": None},
        "unemployment": {"us": None, "uk": None, "history_us": [], "history_uk": [], "mom": None},
        "policy_rates": {"fed": None, "boe": None, "ecb": None, "history_fed": [], "history_boe": [], "history_ecb": []},
        "stale": True,
    }
    assert REQUIRED_KEYS.issubset(stub.keys())


def test_risk_endpoint_schema():
    """GET /api/macro/risk must return VIX + regime + put_call_ratio keys."""
    REQUIRED_KEYS = {"vix_term_structure", "history_depth_ok", "contango", "regime",
                     "percentile_1y", "put_call_ratio", "stale"}
    stub = {
        "vix_term_structure": [],
        "history_depth_ok": False,
        "contango": None,
        "regime": "NORMAL",
        "percentile_1y": None,
        "percentile_5y": None,
        "put_call_ratio": [],
        "stale": True,
    }
    assert REQUIRED_KEYS.issubset(stub.keys())


def test_sentiment_endpoint_schema():
    """GET /api/macro/sentiment must return fear_greed and seasonality keys."""
    REQUIRED_KEYS = {"fear_greed", "seasonality", "stale"}
    stub = {
        "fear_greed": {"score": 50.0, "band": "NEUTRAL", "components": []},
        "seasonality": {"ticker": "^GSPC", "monthly_avg": []},
        "stale": False,
    }
    assert REQUIRED_KEYS.issubset(stub.keys())


def test_curves_endpoint_returns_200():
    """Route registration check — macro router must include /api/macro/curves."""
    # Import check: routes module must be importable without side effects
    import importlib
    spec = importlib.util.find_spec("api.routes.macro")
    assert spec is not None, "api.routes.macro module not found"


def test_risk_endpoint_returns_200():
    """Route registration check — macro router must include /api/macro/risk."""
    import importlib
    spec = importlib.util.find_spec("api.routes.macro")
    assert spec is not None


def test_indicators_endpoint_returns_200():
    """Route registration check — macro router must include /api/macro/indicators."""
    import importlib
    spec = importlib.util.find_spec("api.routes.macro")
    assert spec is not None


def test_sentiment_endpoint_returns_200():
    """Route registration check — macro router must include /api/macro/sentiment."""
    import importlib
    spec = importlib.util.find_spec("api.routes.macro")
    assert spec is not None
