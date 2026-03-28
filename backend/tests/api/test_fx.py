"""
Tests for GET /api/fx/{base}/{quote} endpoint.

Covers EQUITY-11: FX rate returned from fx_rates table.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone


@pytest.fixture
def client():
    """Create test client with mocked DB and Redis."""
    # Import here to avoid circular issues
    from api.main import app
    return TestClient(app)


class TestFXEndpoint:
    """Tests for /api/fx/{base}/{quote}."""

    def test_usdgbp_returns_rate(self, client):
        """GET /api/fx/USD/GBP with DB row returns rate, base, quote, timestamp."""
        from models.fx_rate import FXRate

        mock_row = MagicMock(spec=FXRate)
        mock_row.rate = 0.78954321
        mock_row.time = datetime(2026, 3, 28, 12, 0, 0, tzinfo=timezone.utc)
        mock_row.base = "USD"
        mock_row.quote = "GBP"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value=None)

        with patch("api.routes.fx.get_redis", return_value=mock_redis), \
             patch("api.routes.fx.cache_get", return_value=None), \
             patch("api.routes.fx.cache_set"), \
             patch("api.database.AsyncSessionLocal", return_value=mock_session):
            response = client.get("/api/fx/USD/GBP")

        assert response.status_code == 200
        data = response.json()
        assert "rate" in data
        assert "base" in data
        assert "quote" in data
        assert "timestamp" in data
        assert data["base"] == "USD"
        assert data["quote"] == "GBP"
        assert data["rate"] == pytest.approx(0.78954321, rel=1e-5)

    def test_fx_not_found(self, client):
        """GET /api/fx/USD/GBP with empty DB returns 404 with error key."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_redis = MagicMock()

        with patch("api.routes.fx.get_redis", return_value=mock_redis), \
             patch("api.routes.fx.cache_get", return_value=None), \
             patch("api.database.AsyncSessionLocal", return_value=mock_session):
            response = client.get("/api/fx/USD/GBP")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"] == "fx_rate_not_found"

    def test_fx_cache_hit_returns_cached(self, client):
        """GET /api/fx/USD/GBP with Redis cache hit returns cached data without DB query."""
        cached_data = {
            "base": "USD",
            "quote": "GBP",
            "rate": 0.789,
            "timestamp": "2026-03-28T12:00:00+00:00",
            "stale": True,
        }

        mock_redis = MagicMock()

        with patch("api.routes.fx.get_redis", return_value=mock_redis), \
             patch("api.routes.fx.cache_get", return_value=cached_data):
            response = client.get("/api/fx/USD/GBP")

        # Cache hit — should return 200 with rate
        assert response.status_code == 200
        data = response.json()
        assert "rate" in data
