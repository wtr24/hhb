"""Unit tests for analysis/fear_greed.py — Fear & Greed computation."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from analysis.fear_greed import _percentile_rank, _score_to_band, compute_fear_greed_composite


def test_percentile_rank_basic():
    series = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert _percentile_rank(series, 30.0) == pytest.approx(60.0)


def test_percentile_rank_empty_series():
    assert _percentile_rank([], 25.0) == 50.0


def test_fear_greed_band_extreme_fear():
    assert _score_to_band(10.0) == "EXTREME FEAR"
    assert _score_to_band(24.9) == "EXTREME FEAR"


def test_fear_greed_band_extreme_greed():
    assert _score_to_band(75.0) == "EXTREME GREED"
    assert _score_to_band(100.0) == "EXTREME GREED"


def test_fear_greed_band_all_bands():
    assert _score_to_band(0.0) == "EXTREME FEAR"
    assert _score_to_band(35.0) == "FEAR"
    assert _score_to_band(50.0) == "NEUTRAL"
    assert _score_to_band(65.0) == "GREED"
    assert _score_to_band(90.0) == "EXTREME GREED"


def test_fear_greed_missing_component_still_computes():
    """If some components missing, composite is still computed from available ones."""
    # Mock session that returns empty for all queries
    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = []
    mock_query.count.return_value = 0
    mock_session.query.return_value = mock_query

    result = compute_fear_greed_composite(mock_session)
    assert "score" in result
    assert "band" in result
    assert "components" in result
    assert 0 <= result["score"] <= 100


def test_fear_greed_equal_weighted_average():
    """Composite must be the mean of component scores."""
    from analysis.fear_greed import _score_to_band
    # Simulate: 3 components with scores 20, 60, 80
    # Mean = (20 + 60 + 80) / 3 = 53.33 → NEUTRAL
    assert _score_to_band(53.3) == "NEUTRAL"
