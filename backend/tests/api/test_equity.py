"""
Tests for Phase 3 equity-specific REST endpoints.

Wave 0: all endpoints return 501 Not Implemented.
Stub tests are marked skip until each wave implements the endpoint.
Tests verify response shape once endpoints are implemented.
Per 03-VALIDATION.md test requirements.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create test client for equity endpoints."""
    from api.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestEquityStubs:
    """Wave 0 stub tests: all return 501 Not Implemented."""

    def test_earnings_endpoint_registered(self, client):
        """GET /api/equity/earnings/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/earnings/AAPL")
        assert response.status_code == 501
        data = response.json()
        assert data["status"] == "not_implemented"

    def test_dividends_endpoint_registered(self, client):
        """GET /api/equity/dividends/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/dividends/AAPL")
        assert response.status_code == 501
        data = response.json()
        assert data["status"] == "not_implemented"

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

    def test_news_endpoint_registered(self, client):
        """GET /api/equity/news/{ticker} endpoint must exist (returns 501 stub)."""
        response = client.get("/api/equity/news/AAPL")
        assert response.status_code == 501

    def test_lse_ticker_no_crash(self, client):
        """LSE tickers with .L suffix must not crash any endpoint."""
        # All endpoints must accept .L suffix without 500 errors
        lse_endpoints = [
            "/api/equity/earnings/LLOY.L",
            "/api/equity/dividends/LLOY.L",
            "/api/equity/fundamentals/LLOY.L",
            "/api/equity/news/LLOY.L",
        ]
        for url in lse_endpoints:
            response = client.get(url)
            assert response.status_code != 500, f"Server error on {url}"


# --- Wave 1 tests (implement in Wave 1: earnings, dividends, fundamentals) ---

@pytest.mark.skip(reason="Stub — implement in Wave 1")
class TestEarningsDates:
    """Test earnings calendar endpoint once Wave 1 implements it."""

    def test_earnings_dates(self, client):
        """GET /api/equity/earnings/AAPL returns earnings calendar dates."""
        response = client.get("/api/equity/earnings/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
        assert "earnings_dates" in data or "next_earnings" in data

    def test_earnings_lse_ticker(self, client):
        """LSE ticker LLOY.L earnings dates work without crash."""
        response = client.get("/api/equity/earnings/LLOY.L")
        assert response.status_code in (200, 404)  # OK or no data, not 500


@pytest.mark.skip(reason="Stub — implement in Wave 1")
class TestDividendDates:
    """Test dividend ex-dates endpoint once Wave 1 implements it."""

    def test_dividend_dates(self, client):
        """GET /api/equity/dividends/AAPL returns dividend ex-dates."""
        response = client.get("/api/equity/dividends/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
        assert "dividends" in data or "ex_dates" in data


@pytest.mark.skip(reason="Stub — implement in Wave 1")
class TestFundamentalsShape:
    """Test fundamentals endpoint shape once Wave 1 implements it."""

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


# --- Wave 2 tests (implement in Wave 2: short interest, insiders, news) ---

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
            # US-only — may have error note
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


@pytest.mark.skip(reason="Stub — implement in Wave 2")
class TestNews:
    """Test company news endpoint once Wave 2 implements it."""

    def test_news(self, client):
        """GET /api/equity/news/AAPL returns headline list."""
        response = client.get("/api/equity/news/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data or isinstance(data, list)


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
        # Greeks should be present in each contract
        if data["calls"]:
            contract = data["calls"][0]
            assert "strike" in contract
            assert "delta" in contract or "greeks" in contract
