"""Unit tests for cboe_source.py — CBOE equity put/call ratio fetch and parse."""
import io
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from ingestion.sources.cboe_source import fetch_cboe_pcr

SAMPLE_CSV = "DATE,P/C Ratio\n03/27/2026,0.68\n03/28/2026,0.71\n"


@pytest.fixture
def mock_cboe_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_CSV
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def test_cboe_fetch_returns_dict(mock_cboe_response):
    with patch("ingestion.sources.cboe_source.requests.get", return_value=mock_cboe_response):
        result = fetch_cboe_pcr()
    assert isinstance(result, dict)
    assert "date" in result
    assert "value" in result
    assert result["source"] == "cboe"


def test_cboe_parses_latest_date_row(mock_cboe_response):
    """Must return the LAST row (most recent date), not the first."""
    with patch("ingestion.sources.cboe_source.requests.get", return_value=mock_cboe_response):
        result = fetch_cboe_pcr()
    # 03/28/2026 is the latest row
    assert result["date"] == datetime(2026, 3, 28, tzinfo=timezone.utc)


def test_cboe_value_is_float(mock_cboe_response):
    with patch("ingestion.sources.cboe_source.requests.get", return_value=mock_cboe_response):
        result = fetch_cboe_pcr()
    assert isinstance(result["value"], float)
    assert result["value"] == pytest.approx(0.71)
