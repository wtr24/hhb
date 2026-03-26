"""Tests for Frankfurter FX source module."""
from unittest.mock import patch, MagicMock


def _make_mock_response(json_data=None, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_FX_RESPONSE = {
    "amount": 1.0,
    "base": "USD",
    "date": "2026-03-26",
    "rates": {
        "GBP": 0.7892,
        "EUR": 0.9154,
        "JPY": 151.23,
        "CHF": 0.9001,
        "AUD": 1.5432,
        "CAD": 1.3512,
        "NZD": 1.6800,
        "NOK": 10.54,
        "SEK": 10.32,
    }
}


def test_frankfurter_fetch_returns_rates():
    """fetch_fx_rates returns dict with 'base', 'date', 'rates' keys."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(SAMPLE_FX_RESPONSE)
        from ingestion.sources.frankfurter_source import fetch_fx_rates
        result = fetch_fx_rates("USD")
    assert isinstance(result, dict)
    assert "base" in result
    assert "date" in result
    assert "rates" in result
    assert result["base"] == "USD"


def test_frankfurter_rates_include_gbp():
    """fetch_fx_rates("USD") response includes GBP in rates."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(SAMPLE_FX_RESPONSE)
        from ingestion.sources.frankfurter_source import fetch_fx_rates
        result = fetch_fx_rates("USD")
    assert "GBP" in result["rates"]
    assert result["rates"]["GBP"] == 0.7892


def test_frankfurter_calls_correct_url():
    """fetch_fx_rates calls Frankfurter latest endpoint."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(SAMPLE_FX_RESPONSE)
        from ingestion.sources.frankfurter_source import fetch_fx_rates
        fetch_fx_rates("USD")
    call_args = mock_get.call_args
    url = call_args[0][0] if call_args[0] else call_args.args[0]
    assert "frankfurter" in url
    assert "latest" in url


def test_frankfurter_passes_base_and_symbols():
    """fetch_fx_rates passes base and symbols params to the request."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_mock_response(SAMPLE_FX_RESPONSE)
        from ingestion.sources.frankfurter_source import fetch_fx_rates
        fetch_fx_rates("USD")
    call_kwargs = mock_get.call_args
    params = call_kwargs[1].get("params") or {}
    assert params.get("base") == "USD"
    assert "GBP" in params.get("symbols", "")
