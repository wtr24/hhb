"""Tests for US Treasury yield curve XML source module."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def _make_xml_response(xml_bytes):
    mock = MagicMock()
    mock.content = xml_bytes
    mock.raise_for_status = MagicMock()
    return mock


# Minimal valid Treasury XML with one entry containing all tenor fields
SAMPLE_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
      xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <content type="application/xml">
      <m:properties>
        <d:NEW_DATE>2026-03-25T00:00:00</d:NEW_DATE>
        <d:BC_1MONTH>5.30</d:BC_1MONTH>
        <d:BC_2MONTH>5.28</d:BC_2MONTH>
        <d:BC_3MONTH>5.25</d:BC_3MONTH>
        <d:BC_6MONTH>5.10</d:BC_6MONTH>
        <d:BC_1YEAR>4.95</d:BC_1YEAR>
        <d:BC_2YEAR>4.60</d:BC_2YEAR>
        <d:BC_3YEAR>4.50</d:BC_3YEAR>
        <d:BC_5YEAR>4.40</d:BC_5YEAR>
        <d:BC_7YEAR>4.45</d:BC_7YEAR>
        <d:BC_10YEAR>4.55</d:BC_10YEAR>
        <d:BC_20YEAR>4.80</d:BC_20YEAR>
        <d:BC_30YEAR>4.75</d:BC_30YEAR>
      </m:properties>
    </content>
  </entry>
</feed>
"""


def test_treasury_fetch_returns_rows():
    """fetch_treasury_yield_curve returns list of dicts with 'date' and bc_* tenor keys."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_xml_response(SAMPLE_XML)
        from ingestion.sources.treasury_source import fetch_treasury_yield_curve
        rows = fetch_treasury_yield_curve()
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert "date" in rows[0]


def test_treasury_parses_tenor_fields():
    """Each row from fetch_treasury_yield_curve has keys bc_1month through bc_30year."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_xml_response(SAMPLE_XML)
        from ingestion.sources.treasury_source import fetch_treasury_yield_curve
        rows = fetch_treasury_yield_curve()
    row = rows[0]
    expected_tenors = [
        "bc_1month", "bc_2month", "bc_3month", "bc_6month",
        "bc_1year", "bc_2year", "bc_3year", "bc_5year",
        "bc_7year", "bc_10year", "bc_20year", "bc_30year",
    ]
    for tenor in expected_tenors:
        assert tenor in row, f"Missing tenor key: {tenor}"
    assert row["bc_10year"] == 4.55


def test_treasury_uses_xml_date_not_now():
    """row['date'] comes from XML NEW_DATE field, not datetime.now()."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_xml_response(SAMPLE_XML)
        from ingestion.sources.treasury_source import fetch_treasury_yield_curve
        rows = fetch_treasury_yield_curve()
    row = rows[0]
    row_date = row["date"]
    # The date must match what's in the XML: 2026-03-25
    assert isinstance(row_date, datetime)
    assert row_date.year == 2026
    assert row_date.month == 3
    assert row_date.day == 25


def test_treasury_date_has_timezone():
    """row['date'] datetime object should have UTC timezone."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_xml_response(SAMPLE_XML)
        from ingestion.sources.treasury_source import fetch_treasury_yield_curve
        rows = fetch_treasury_yield_curve()
    row_date = rows[0]["date"]
    assert row_date.tzinfo is not None


def test_treasury_handles_missing_tenors():
    """Rows with missing tenor values get None, not an error."""
    xml_missing_tenors = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
      xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <content type="application/xml">
      <m:properties>
        <d:NEW_DATE>2026-03-25T00:00:00</d:NEW_DATE>
        <d:BC_1MONTH>5.30</d:BC_1MONTH>
      </m:properties>
    </content>
  </entry>
</feed>
"""
    with patch("requests.get") as mock_get:
        mock_get.return_value = _make_xml_response(xml_missing_tenors)
        from ingestion.sources.treasury_source import fetch_treasury_yield_curve
        rows = fetch_treasury_yield_curve()
    row = rows[0]
    # Missing tenors should be None
    assert row["bc_10year"] is None
    # Present tenor should have value
    assert row["bc_1month"] == 5.30
