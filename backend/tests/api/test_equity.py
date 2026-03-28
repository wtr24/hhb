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
    """Wave 0/3 stub tests: all endpoints now implemented (Wave 3 completed options)."""

    def test_lse_ticker_no_crash(self, client):
        """LSE tickers with .L suffix must not crash any endpoint (no 500 errors)."""
        lse_endpoints = [
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


# --- Wave 2 tests (fundamentals, short interest, insiders) ---

class TestFundamentalsShape:
    """Test fundamentals endpoint shape (Wave 2 implemented in plan 03-04)."""

    def test_fundamentals_shape(self, client):
        """GET /api/equity/fundamentals/AAPL returns 5 metrics including ROE."""
        from unittest.mock import AsyncMock
        from api.main import app
        from api.database import get_async_db

        mock_fund = MagicMock()
        mock_fund.pe_ratio = 28.4
        mock_fund.ev_ebitda = 21.2
        mock_fund.roe = 0.45
        mock_fund.debt_equity = 1.73
        mock_fund.market_cap = 2940000000000

        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = mock_fund

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_scalar)

        async def override_db():
            return mock_db

        with patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis

            app.dependency_overrides[get_async_db] = override_db

            try:
                response = client.get("/api/equity/fundamentals/AAPL")
            finally:
                app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "pe_ratio" in data
        assert "ev_ebitda" in data
        assert "roe" in data
        assert "debt_equity" in data
        assert "market_cap" in data
        assert data["ticker"] == "AAPL"

    def test_fundamentals_no_db_data_falls_back_to_yfinance(self, client):
        """When no DB row exists, fundamentals uses yfinance for ROE."""
        from unittest.mock import AsyncMock
        from api.main import app
        from api.database import get_async_db

        mock_scalar = MagicMock()
        mock_scalar.scalar_one_or_none.return_value = None  # No DB row

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_scalar)

        mock_info = {"returnOnEquity": 0.45}
        mock_ticker_obj = MagicMock()
        mock_ticker_obj.info = mock_info

        async def override_db():
            return mock_db

        with patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch("api.routes.equity.yf.Ticker") as mock_yf:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.return_value = mock_ticker_obj

            app.dependency_overrides[get_async_db] = override_db

            try:
                response = client.get("/api/equity/fundamentals/AAPL")
            finally:
                app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "roe" in data
        assert data["roe"] == pytest.approx(0.45)
        assert data["stale"] is True  # No DB row means stale


class TestShortInterest:
    """Test short interest endpoint (Wave 2 implemented in plan 03-04)."""

    def test_short_interest(self, client):
        """GET /api/equity/short-interest/AAPL returns pct_float ~10.0."""
        mock_si_data = {
            "shortInterest": 100000,
            "sharesOutstanding": 1000000,
            "date": "2026-01-01",
        }
        with patch("api.routes.equity.fetch_short_interest") as mock_fetch, \
             patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"}):
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_fetch.return_value = mock_si_data

            response = client.get("/api/equity/short-interest/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "pct_float" in data
        assert data["pct_float"] == pytest.approx(10.0, rel=1e-3)
        assert data["source"] == "finnhub"

    def test_short_interest_lse_returns_us_only(self, client):
        """LSE ticker LLOY.L returns available=False with US-only message."""
        response = client.get("/api/equity/short-interest/LLOY.L")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "US tickers only" in data.get("message", "")

    def test_short_interest_index_returns_us_only(self, client):
        """Index ticker ^FTSE returns available=False."""
        response = client.get("/api/equity/short-interest/^FTSE")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


class TestLseTicker:
    """Test LSE ticker handling for Wave 2 endpoints (plan 03-04)."""

    def test_short_interest_lse(self, client):
        """GET /api/equity/short-interest/LLOY.L returns available: False."""
        response = client.get("/api/equity/short-interest/LLOY.L")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    def test_insiders_lse(self, client):
        """GET /api/equity/insiders/LLOY.L returns available: False."""
        response = client.get("/api/equity/insiders/LLOY.L")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


class TestInsiders:
    """Test insider clustering endpoint (Wave 2 implemented in plan 03-04)."""

    def test_insiders_structure(self, client):
        """GET /api/equity/insiders/AAPL returns buy/sell counts and clusters."""
        mock_transactions = [
            {
                "name": "Tim Cook",
                "share": 1000,
                "change": 1000,
                "filingDate": "2026-01-05",
                "transactionDate": "2026-01-04",
                "transactionCode": "P",
                "transactionPrice": 185.0,
                "isDerivative": False,
            },
            {
                "name": "Luca Maestri",
                "share": 500,
                "change": 500,
                "filingDate": "2026-01-06",
                "transactionDate": "2026-01-05",
                "transactionCode": "P",
                "transactionPrice": 186.0,
                "isDerivative": False,
            },
            {
                "name": "Jeff Williams",
                "share": 2000,
                "change": -2000,
                "filingDate": "2026-01-10",
                "transactionDate": "2026-01-09",
                "transactionCode": "S",
                "transactionPrice": 190.0,
                "isDerivative": False,
            },
        ]
        with patch("api.routes.equity.fetch_insider_transactions") as mock_fetch, \
             patch("api.routes.equity.get_redis") as mock_get_redis, \
             patch.dict("os.environ", {"FINNHUB_API_KEY": "test_key"}):
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_fetch.return_value = mock_transactions

            response = client.get("/api/equity/insiders/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "buy_count" in data
        assert "sell_count" in data
        assert "clusters" in data
        assert "multi_insider" in data
        assert data["buy_count"] == 2
        assert data["sell_count"] == 1
        assert data["multi_insider"] is True  # 2 buyers in same window
        assert data["source"] == "finnhub"


# --- Wave 3 tests (options chain with Black-Scholes Greeks) ---

class TestOptionsChain:
    """Test options chain endpoint (Wave 3 implemented in plan 03-05)."""

    def _make_option_df(self):
        """Build a minimal 3-row options DataFrame matching yfinance column schema."""
        return pd.DataFrame({
            "contractSymbol": ["AAPL240425C00095000", "AAPL240425C00100000", "AAPL240425C00105000"],
            "strike": [95.0, 100.0, 105.0],
            "lastPrice": [6.10, 2.50, 0.80],
            "bid": [5.90, 2.40, 0.70],
            "ask": [6.20, 2.60, 0.90],
            "volume": [100, 200, 150],
            "openInterest": [500, 800, 300],
            "impliedVolatility": [0.25, 0.22, 0.28],
        })

    def test_options_chain(self, client):
        """GET /api/equity/options/AAPL returns calls/puts with BS Greeks."""
        calls_df = self._make_option_df()
        puts_df = self._make_option_df()
        puts_df["strike"] = [95.0, 100.0, 105.0]

        mock_chain = MagicMock()
        mock_chain.calls = calls_df
        mock_chain.puts = puts_df

        mock_ticker = MagicMock()
        type(mock_ticker).options = PropertyMock(return_value=["2026-04-25", "2026-05-16"])
        mock_ticker.option_chain.return_value = mock_chain
        mock_ticker.info = {"currentPrice": 100.0}

        with patch("api.routes.equity.yf.Ticker") as mock_yf, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.return_value = mock_ticker

            response = client.get("/api/equity/options/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "calls" in data
        assert "puts" in data
        assert len(data["calls"]) == 3
        assert len(data["puts"]) == 3

        # Each row must have BS Greeks
        contract = data["calls"][0]
        assert "delta" in contract
        assert "gamma" in contract
        assert "vega" in contract
        assert "theta" in contract
        assert "strike" in contract
        assert "iv" in contract

    def test_options_chain_greeks_are_numbers(self, client):
        """BS Greeks must be floats (not None) for valid IV and T > 0."""
        calls_df = self._make_option_df()
        puts_df = self._make_option_df()

        mock_chain = MagicMock()
        mock_chain.calls = calls_df
        mock_chain.puts = puts_df

        mock_ticker = MagicMock()
        type(mock_ticker).options = PropertyMock(return_value=["2026-12-19"])
        mock_ticker.option_chain.return_value = mock_chain
        mock_ticker.info = {"currentPrice": 100.0}

        with patch("api.routes.equity.yf.Ticker") as mock_yf, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.return_value = mock_ticker

            response = client.get("/api/equity/options/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        # Delta should be numeric for valid inputs (T>0, sigma>0)
        for contract in data["calls"]:
            if contract["delta"] is not None:
                assert isinstance(contract["delta"], float)
                assert -1.0 <= contract["delta"] <= 1.0

    def test_options_chain_iv_rank(self, client):
        """iv_rank must be between 0 and 100."""
        calls_df = self._make_option_df()
        puts_df = self._make_option_df()

        mock_chain = MagicMock()
        mock_chain.calls = calls_df
        mock_chain.puts = puts_df

        mock_ticker = MagicMock()
        type(mock_ticker).options = PropertyMock(return_value=["2026-06-20"])
        mock_ticker.option_chain.return_value = mock_chain
        mock_ticker.info = {"currentPrice": 100.0}

        with patch("api.routes.equity.yf.Ticker") as mock_yf, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.return_value = mock_ticker

            response = client.get("/api/equity/options/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "iv_rank" in data
        assert 0.0 <= data["iv_rank"] <= 100.0

    def test_options_chain_iv_surface(self, client):
        """iv_surface must contain strikes, expiries, and iv_matrix keys."""
        calls_df = self._make_option_df()
        puts_df = self._make_option_df()

        mock_chain = MagicMock()
        mock_chain.calls = calls_df
        mock_chain.puts = puts_df

        mock_ticker = MagicMock()
        type(mock_ticker).options = PropertyMock(return_value=["2026-06-20", "2026-07-18"])
        mock_ticker.option_chain.return_value = mock_chain
        mock_ticker.info = {"currentPrice": 100.0}

        with patch("api.routes.equity.yf.Ticker") as mock_yf, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.return_value = mock_ticker

            response = client.get("/api/equity/options/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "iv_surface" in data
        surface = data["iv_surface"]
        assert "strikes" in surface
        assert "expiries" in surface
        assert "iv_matrix" in surface

    def test_lse_ticker_returns_not_available(self, client):
        """LSE ticker (.L suffix) returns available=False with message."""
        response = client.get("/api/equity/options/LLOY.L")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "LSE" in data.get("message", "") or "not available" in data.get("message", "").lower()

    def test_options_yfinance_error_returns_unavailable(self, client):
        """On yfinance error, options endpoint returns available=False (not 500)."""
        with patch("api.routes.equity.yf.Ticker") as mock_yf, \
             patch("api.routes.equity.get_redis") as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_get_redis.return_value = mock_redis
            mock_yf.side_effect = Exception("yfinance down")

            response = client.get("/api/equity/options/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
