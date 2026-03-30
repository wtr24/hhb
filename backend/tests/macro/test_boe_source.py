"""Unit tests for boe_source.py — BoE IADB gilt curve fetch and parse."""
import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from ingestion.sources.boe_source import fetch_boe_gilt_curve, HEADERS, TENOR_MAP

# Minimal tab-delimited CSV response matching BoE CSVF=TT format
SAMPLE_CSV = (
    "Date\tIUDMNZC.A6\tIUDMNZC.A12\tIUDMNZC.A24\tIUDMNZC.A60\tIUDMNZC.A120\n"
    "27 Mar 2026\t4.82\t4.75\t4.61\t4.43\t4.38\n"
    "26 Mar 2026\t\t4.76\t4.62\t4.44\t4.39\n"  # 6M missing on this date
)


@pytest.fixture
def mock_boe_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_CSV
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_boe_fetch_returns_list(mock_boe_response):
    with patch("ingestion.sources.boe_source.requests.get", return_value=mock_boe_response):
        result = fetch_boe_gilt_curve()
    assert isinstance(result, list)
    assert len(result) == 2


def test_boe_csv_parses_tenors(mock_boe_response):
    with patch("ingestion.sources.boe_source.requests.get", return_value=mock_boe_response):
        result = fetch_boe_gilt_curve()
    first = result[0]
    assert "date" in first
    assert "tenor_6m" in first
    assert "tenor_10y" in first
    assert first["tenor_6m"] == pytest.approx(4.82)
    assert first["tenor_10y"] == pytest.approx(4.38)


def test_boe_handles_missing_short_tenors(mock_boe_response):
    """BoE does not publish 6M on some dates — must be None, not error."""
    with patch("ingestion.sources.boe_source.requests.get", return_value=mock_boe_response):
        result = fetch_boe_gilt_curve()
    second = result[1]
    assert second["tenor_6m"] is None
    assert second["tenor_1y"] == pytest.approx(4.76)


def test_boe_returns_403_without_user_agent():
    """Verify that a 403 response raises a descriptive HTTPError."""
    import requests as req
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.url = "https://www.bankofengland.co.uk/..."
    mock_resp.raise_for_status.side_effect = req.HTTPError(response=mock_resp)
    with patch("ingestion.sources.boe_source.requests.get", return_value=mock_resp):
        with pytest.raises(req.HTTPError, match="403"):
            fetch_boe_gilt_curve()


def test_boe_date_format_parses_correctly(mock_boe_response):
    """Date column '27 Mar 2026' must parse to UTC datetime."""
    with patch("ingestion.sources.boe_source.requests.get", return_value=mock_boe_response):
        result = fetch_boe_gilt_curve()
    assert result[0]["date"] == datetime(2026, 3, 27, tzinfo=timezone.utc)


def test_boe_user_agent_header_present():
    """Verify the HEADERS constant includes a User-Agent to avoid 403."""
    assert "User-Agent" in HEADERS
    assert "Mozilla" in HEADERS["User-Agent"]
