"""Tests for FRED API source module."""
import os
from unittest.mock import patch, MagicMock
import pytest


def _make_mock_response(json_data=None, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_OBSERVATIONS = {
    "observations": [
        {"date": "2026-01-01", "value": "314.7"},
        {"date": "2025-12-01", "value": "313.2"},
        {"date": "2025-11-01", "value": "."},  # missing value — should be filtered
    ]
}


def test_fred_fetch_returns_observations():
    """fetch_fred_series returns list of dicts with 'date' and 'value' keys."""
    with patch.dict(os.environ, {"FRED_API_KEY": "testkey"}):
        with patch("requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(SAMPLE_OBSERVATIONS)
            from ingestion.sources.fred_source import fetch_fred_series
            result = fetch_fred_series("CPIAUCSL")
    assert isinstance(result, list)
    assert len(result) == 2  # missing value "." filtered out
    assert "date" in result[0]
    assert "value" in result[0]
    assert result[0]["value"] == 314.7


def test_fred_fetch_uses_api_key():
    """fetch_fred_series reads FRED_API_KEY from os.environ."""
    with patch.dict(os.environ, {"FRED_API_KEY": "my_secret_key"}):
        with patch("requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(SAMPLE_OBSERVATIONS)
            from ingestion.sources.fred_source import fetch_fred_series
            fetch_fred_series("CPIAUCSL")
    call_kwargs = mock_get.call_args
    params = call_kwargs[1].get("params") or call_kwargs[0][1] if len(call_kwargs[0]) > 1 else call_kwargs.kwargs.get("params", {})
    assert params.get("api_key") == "my_secret_key"


def test_fred_fetch_raises_without_api_key():
    """fetch_fred_series raises ValueError when FRED_API_KEY is not set."""
    env = {k: v for k, v in os.environ.items() if k != "FRED_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        from ingestion.sources.fred_source import fetch_fred_series
        with pytest.raises(ValueError, match="FRED_API_KEY"):
            fetch_fred_series("CPIAUCSL")


def test_fred_fetch_filters_missing_values():
    """Observations with value='.' are filtered out."""
    data = {
        "observations": [
            {"date": "2026-01-01", "value": "100.0"},
            {"date": "2025-12-01", "value": "."},
            {"date": "2025-11-01", "value": ""},
        ]
    }
    with patch.dict(os.environ, {"FRED_API_KEY": "testkey"}):
        with patch("requests.get") as mock_get:
            mock_get.return_value = _make_mock_response(data)
            from ingestion.sources.fred_source import fetch_fred_series
            result = fetch_fred_series("GDP")
    assert len(result) == 1
    assert result[0]["date"] == "2026-01-01"
