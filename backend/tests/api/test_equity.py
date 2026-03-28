"""
Tests for Phase 3 equity-specific REST endpoints.

Wave 0: all endpoints return 501 Not Implemented.
Stub tests are marked skip until each wave implements the endpoint.
Tests verify response shape once endpoints are implemented.
Per 03-VALIDATION.md test requirements.
"""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


@pytest.fixture
def client():
    """Create test client for equity endpoints."""
    from api.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestEquityStubs:
    """Wave 0 stub tests: fundamentals, short-interest, insiders, options return 501."""

    def test_fundamentals_endpoint_registered(self, client):
        """GET /api/equity/fundamentals/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/fundamentals/AAPL")
        assert response.status_code == 501

    def test_short_interest_endpoint_registered(self, client):
        """GET /api/equity/short-interest/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/short-interest/AAPL")
        assert response.status_code == 501

    def test_insiders_endpoint_registered(self, client):
        """GET /api/equity/insiders/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/insiders/AAPL")
        assert response.status_code == 501

    def test_options_endpoint_registered(self, client):
        """GET /api/equity/options/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/options/AAPL")
        assert response.status_code == 501

    def test_lse_ticker_no_crash(self, client):
        """LSE tickers with .L suffix must not crash any endpoint (no 500 errors)."""
        lse_endpoints = [
            "/api/equity/fundamentals/LLOY.L",
            "/api/equity/short-interest/LLOY.L",
            "/api/equity/insiders/LLOY.L",
            "/api/equity/options/LLOY.L",
        ]
        for url in lse_endpoints:
            response = client.get(url)
            assert response.status_code != 500, f"Server error on {url}"


# --- Wave 1 tests (earnings, dividends, news) ---

class TestEarningsDates:
    """Test earnings calendar endpoint (Wave 1 implemented in plan 03-02)."""

    def test_earnings_dates(self, client):
        """GET /api/equity/earnings/AAPL returns earnings calendar with 3 dates."""
        dates = pd.DatetimeIndex([
            "2024-01-26", "2024-04-26", "2024-07-26"
        ])
        mock_df = pd.DataFrame(
            {"EPS Estimate": [1.5, 1.6, 1.7]},
            index=dates,
        )
        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None  # cache miss
            mock_get_redis.return_value = mock_redis

            mock_ticker = MagicMock()
            mock_ticker.get_earnings_dates.return_value = mock_df
            mock_ticker_cls.return_value = mock_ticker

            response = client.get("/api/equity/earnings/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
        assert data["ticker"] == "AAPL"
        assert "earnings_dates" in data
        assert len(data["earnings_dates"]) == 3
        assert data["source"] == "yfinance"

    def test_earnings_lse_ticker(self, client):
        """LSE ticker LLOY.L earnings dates work without crash (200 or no data)."""
        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            mock_ticker = MagicMock()
            mock_ticker.get_earnings_dates.return_value = pd.DataFrame()
            mock_ticker_cls.return_value = mock_ticker

            response = client.get("/api/equity/earnings/LLOY.L")

        assert response.status_code in (200, 404)

    def test_earnings_yfinance_error_returns_empty(self, client):
        """On yfinance error, earnings endpoint returns empty list not 500."""
        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            mock_ticker_cls.side_effect = Exception("yfinance down")

            response = client.get("/api/equity/earnings/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["earnings_dates"] == []
        assert "error" in data


class TestDividendDates:
    """Test dividend ex-dates endpoint (Wave 1 implemented in plan 03-02)."""

    def test_dividend_dates(self, client):
        """GET /api/equity/dividends/AAPL returns dividend list with 2 entries."""
        dates = pd.DatetimeIndex(["2024-02-09", "2024-05-10"])
        mock_series = pd.Series([0.24, 0.25], index=dates, name="Dividends")

        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            mock_ticker = MagicMock()
            type(mock_ticker).dividends = PropertyMock(return_value=mock_series)
            mock_ticker_cls.return_value = mock_ticker

            response = client.get("/api/equity/dividends/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
        assert data["ticker"] == "AAPL"
        assert "dividends" in data
        assert len(data["dividends"]) == 2
        for entry in data["dividends"]:
            assert "date" in entry
            assert "amount" in entry

    def test_dividend_dates_empty_series(self, client):
        """Ticker with no dividends returns empty list."""
        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            mock_ticker = MagicMock()
            type(mock_ticker).dividends = PropertyMock(
                return_value=pd.Series([], dtype=float)
            )
            mock_ticker_cls.return_value = mock_ticker

            response = client.get("/api/equity/dividends/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["dividends"] == []

    def test_dividend_yfinance_error_returns_empty(self, client):
        """On yfinance error, dividends endpoint returns empty list not 500."""
        with patch("api.routes.equity.yf.Ticker") as mock_ticker_cls, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            mock_ticker_cls.side_effect = Exception("yfinance down")

            response = client.get("/api/equity/dividends/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["dividends"] == []
        assert "error" in data


class TestNews:
    """Test company news endpoint (Wave 1 implemented in plan 03-02)."""

    def test_news(self, client):
        """GET /api/equity/news/AAPL returns 2 news items with headline key."""
        mock_articles = [
            {
                "headline": "Apple beats earnings estimates",
                "source": "Reuters",
                "url": "https://reuters.com/1",
                "datetime": 1700000000,
                "summary": "Apple reported strong quarterly results.",
            },
            {
                "headline": "Apple Vision Pro sales update",
                "source": "Bloomberg",
                "url": "https://bloomberg.com/2",
                "datetime": 1700100000,
                "summary": "Sales exceed analyst forecasts.",
            },
        ]

        with patch("api.routes.equity.fetch_company_news") as mock_news, \
             patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"}):
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_news.return_value = mock_articles

            response = client.get("/api/equity/news/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
        assert data["ticker"] == "AAPL"
        assert "news" in data
        assert len(data["news"]) == 2
        for item in data["news"]:
            assert "headline" in item

    def test_news_no_api_key_returns_empty(self, client):
        """When FINNHUB_API_KEY absent, news endpoint returns empty list with stale=True."""
        with patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch.dict("os.environ", {}, clear=True):
            # Ensure key is not set
            import os
            os.environ.pop("FINNHUB_API_KEY", None)

            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            response = client.get("/api/equity/news/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["news"] == []
        assert data["stale"] is True

    def test_news_finnhub_error_returns_stale(self, client):
        """On Finnhub error, news endpoint returns empty list with stale=True."""
        with patch("api.routes.equity.fetch_company_news") as mock_news, \
             patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"}):
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_news.side_effect = Exception("Finnhub error")

            response = client.get("/api/equity/news/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["news"] == []
        assert data["stale"] is True


# --- Wave 2 tests (implement in Wave 2: short interest, insiders) ---

@pytest.mark.skip(reason="Stub — implement in Wave 2")
class TestFundamentalsShape:
    """Test fundamentals endpoint shape once Wave 2 implements it."""

    def test_fundamentals_shape(self, client):
        """GET /api/equity/fundamentals/AAPL returns expected keys including ROE."""
        response = client.get("/api/equity/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "pe_ratio" in data
        assert "ev_ebitda" in data
        assert "roe" in data
        assert "debt_equity" in data
        assert "market_cap" in data


@pytest.mark.skip(reason="Stub — implement in Wave 2")
class TestShortInterest:
    """Test short interest endpoint once Wave 2 implements it."""

    def test_short_interest(self, client):
        """GET /api/equity/short-interest/AAPL returns structured short interest data."""
        response = client.get("/api/equity/short-interest/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "short_interest" in data or "short_percent_float" in data

    def test_short_interest_lse_note(self, client):
        """LSE tickers return US-only note or 404 for short interest."""
        response = client.get("/api/equity/short-interest/LLOY.L")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "error" in data or "note" in data or "short_interest" in data


@pytest.mark.skip(reason="Stub — implement in Wave 2")
class TestInsiders:
    """Test insider clustering endpoint once Wave 2 implements it."""

    def test_insiders_structure(self, client):
        """GET /api/equity/insiders/AAPL returns buy/sell counts and clusters."""
        response = client.get("/api/equity/insiders/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "buy_count" in data
        assert "sell_count" in data
        assert "clusters" in data
        assert "multi_insider" in data


# --- Wave 3 tests (implement in Wave 3: options chain) ---

@pytest.mark.skip(reason="Stub — implement in Wave 3")
class TestOptionsChain:
    """Test options chain endpoint once Wave 3 implements it."""

    def test_options_chain(self, client):
        """GET /api/equity/options/AAPL returns calls and puts structure."""
        response = client.get("/api/equity/options/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "calls" in data
        assert "puts" in data
        if data["calls"]:
            contract = data["calls"][0]
            assert "strike" in contract
            assert "delta" in contract or "greeks" in contract
