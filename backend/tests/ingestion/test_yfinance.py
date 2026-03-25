"""
Unit tests for yfinance source and Celery ingest tasks.
All external dependencies (yfinance, Redis, DB) are mocked.
"""
import time
import json
import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_hist():
    """Return a minimal DataFrame that looks like yfinance history output."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-24", tz="UTC")])
    return pd.DataFrame(
        {
            "Open": [180.0],
            "High": [185.0],
            "Low": [178.0],
            "Close": [183.0],
            "Volume": [1_000_000],
        },
        index=idx,
    )


def _make_fake_ticker(hist=None, fast_info_price=183.0, fast_info_cap=3_000_000_000_000, info=None):
    """Return a mock yf.Ticker object."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _make_fake_hist() if hist is None else hist
    # fast_info
    fi = MagicMock()
    fi.last_price = fast_info_price
    fi.market_cap = fast_info_cap
    mock_ticker.fast_info = fi
    # info dict
    default_info = {
        "forwardPE": 28.4,
        "enterpriseToEbitda": 21.2,
        "marketCap": 3_000_000_000_000,
        "debtToEquity": 1.73,
    }
    mock_ticker.info = info if info is not None else default_info
    return mock_ticker


# ---------------------------------------------------------------------------
# Tests for fetch_ohlcv_and_fundamentals
# ---------------------------------------------------------------------------

class TestFetchOhlcvAndFundamentals:
    def test_fetch_ohlcv_returns_correct_structure(self):
        """fetch_ohlcv_and_fundamentals returns expected keys and row structure."""
        with patch("ingestion.sources.yfinance_source.yf") as mock_yf:
            mock_yf.Ticker.return_value = _make_fake_ticker()
            from ingestion.sources.yfinance_source import fetch_ohlcv_and_fundamentals

            result = fetch_ohlcv_and_fundamentals("AAPL")

        assert "ohlcv" in result
        assert "price" in result
        assert "fundamentals" in result
        assert "fetched_at" in result

        # OHLCV row structure
        assert len(result["ohlcv"]) == 1
        row = result["ohlcv"][0]
        for key in ("time", "ticker", "open", "high", "low", "close", "volume", "source"):
            assert key in row, f"Missing OHLCV key: {key}"
        assert row["ticker"] == "AAPL"
        assert row["open"] == 180.0
        assert row["source"] == "yfinance"

        # Fundamentals structure
        fund = result["fundamentals"]
        for key in ("pe_ratio", "ev_ebitda", "market_cap", "debt_equity"):
            assert key in fund, f"Missing fundamentals key: {key}"

    def test_fetch_ohlcv_price_from_fast_info(self):
        """Price should come from fast_info.last_price when available."""
        with patch("ingestion.sources.yfinance_source.yf") as mock_yf:
            mock_yf.Ticker.return_value = _make_fake_ticker(fast_info_price=190.0)
            from ingestion.sources.yfinance_source import fetch_ohlcv_and_fundamentals

            result = fetch_ohlcv_and_fundamentals("AAPL")

        assert result["price"] == 190.0

    def test_fetch_ohlcv_fallback_price_when_fast_info_fails(self):
        """Price falls back to last OHLCV close when fast_info raises."""
        with patch("ingestion.sources.yfinance_source.yf") as mock_yf:
            ticker = _make_fake_ticker()
            # Make fast_info raise
            type(ticker).fast_info = property(lambda self: (_ for _ in ()).throw(Exception("no fast_info")))
            mock_yf.Ticker.return_value = ticker
            from ingestion.sources.yfinance_source import fetch_ohlcv_and_fundamentals

            result = fetch_ohlcv_and_fundamentals("AAPL")

        assert result["price"] == 183.0  # last close from fake hist

    def test_fetch_ohlcv_fundamentals_from_info(self):
        """Fundamentals values should be pulled from ticker.info."""
        custom_info = {
            "forwardPE": 30.0,
            "enterpriseToEbitda": 15.5,
            "marketCap": 2_000_000_000_000,
            "debtToEquity": 0.5,
        }
        with patch("ingestion.sources.yfinance_source.yf") as mock_yf:
            mock_yf.Ticker.return_value = _make_fake_ticker(info=custom_info)
            from ingestion.sources.yfinance_source import fetch_ohlcv_and_fundamentals

            result = fetch_ohlcv_and_fundamentals("AAPL")

        assert result["fundamentals"]["pe_ratio"] == 30.0
        assert result["fundamentals"]["ev_ebitda"] == 15.5
        assert result["fundamentals"]["market_cap"] == 2_000_000_000_000
        assert result["fundamentals"]["debt_equity"] == 0.5


# ---------------------------------------------------------------------------
# Tests for fetch_ohlcv_batch
# ---------------------------------------------------------------------------

class TestFetchOhlcvBatch:
    def test_fetch_ohlcv_batch_sleeps_between_tickers(self):
        """fetch_ohlcv_batch should call time.sleep(0.5) between each ticker."""
        tickers = ["AAPL", "MSFT", "LLOY.L"]
        with (
            patch("ingestion.sources.yfinance_source.yf") as mock_yf,
            patch("ingestion.sources.yfinance_source.time") as mock_time,
        ):
            mock_yf.Ticker.return_value = _make_fake_ticker()
            mock_time.sleep = MagicMock()
            from ingestion.sources.yfinance_source import fetch_ohlcv_batch

            results = fetch_ohlcv_batch(tickers)

        # sleep called once per ticker
        assert mock_time.sleep.call_count == len(tickers)
        for c in mock_time.sleep.call_args_list:
            assert c == call(0.5)

    def test_fetch_ohlcv_batch_continues_on_error(self):
        """batch fetch should skip failed tickers and continue."""
        with (
            patch("ingestion.sources.yfinance_source.yf") as mock_yf,
            patch("ingestion.sources.yfinance_source.time"),
        ):
            good_ticker = _make_fake_ticker()
            bad_ticker = MagicMock()
            bad_ticker.history.side_effect = Exception("network error")
            mock_yf.Ticker.side_effect = [bad_ticker, good_ticker]
            from ingestion.sources.yfinance_source import fetch_ohlcv_batch

            results = fetch_ohlcv_batch(["BAD", "GOOD"])

        # Only the good ticker result should be in the list
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Tests for Celery tasks
# ---------------------------------------------------------------------------

class TestIngestTicker:
    def test_ingest_ticker_calls_fetch(self):
        """ingest_ticker task should call fetch_ohlcv_and_fundamentals for the given ticker."""
        with (
            patch("ingestion.tasks.fetch_ohlcv_and_fundamentals") as mock_fetch,
            patch("ingestion.tasks.SessionLocal") as mock_session_cls,
            patch("ingestion.tasks.redis_client") as mock_redis,
        ):
            mock_fetch.return_value = {
                "ohlcv": [
                    {
                        "time": datetime(2026, 3, 24, tzinfo=timezone.utc),
                        "ticker": "AAPL",
                        "open": 180.0,
                        "high": 185.0,
                        "low": 178.0,
                        "close": 183.0,
                        "volume": 1_000_000,
                        "source": "yfinance",
                    }
                ],
                "price": 183.0,
                "fundamentals": {
                    "pe_ratio": 28.4,
                    "ev_ebitda": 21.2,
                    "market_cap": 3_000_000_000_000,
                    "debt_equity": 1.73,
                },
                "fetched_at": "2026-03-24T00:00:00+00:00",
            }
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session_cls.return_value = mock_session
            mock_session.execute = MagicMock()
            mock_redis.publish = MagicMock()
            mock_redis.set = MagicMock()

            from ingestion.tasks import ingest_ticker
            # Call the underlying function directly (bypasses Celery task wrapping)
            ingest_ticker("AAPL")

        mock_fetch.assert_called_once_with("AAPL")

    def test_ingest_ticker_retries_on_exception(self):
        """ingest_ticker task body should call self.retry with countdown from RETRY_COUNTDOWNS."""
        from ingestion.config import RETRY_COUNTDOWNS

        # Build a minimal self-like mock that mimics what Celery passes as `self`
        # when bind=True is used.
        retry_mock = MagicMock(side_effect=Exception("retry triggered"))
        self_mock = MagicMock()
        self_mock.request.retries = 0
        self_mock.retry = retry_mock

        # The actual task function body is registered on the celery app; we can
        # access the original unwrapped callable via the `run` attribute that
        # Celery stores on task instances.
        import ingestion.tasks as task_module

        with (
            patch.object(task_module, "fetch_ohlcv_and_fundamentals", side_effect=RuntimeError("yf error")),
            patch.object(task_module, "SessionLocal"),
        ):
            with pytest.raises(Exception):
                # Call the task body directly — passing self_mock as `self`
                task_module.ingest_ticker.run.__func__(self_mock, "AAPL")

        retry_mock.assert_called_once()
        retry_kwargs = retry_mock.call_args[1]
        assert retry_kwargs.get("countdown") == RETRY_COUNTDOWNS[0]

    def test_publish_to_redis_channel(self):
        """After ingest, redis_client.publish must be called with 'quotes:{ticker}'."""
        with (
            patch("ingestion.tasks.fetch_ohlcv_and_fundamentals") as mock_fetch,
            patch("ingestion.tasks.SessionLocal") as mock_session_cls,
            patch("ingestion.tasks.redis_client") as mock_redis,
        ):
            mock_fetch.return_value = {
                "ohlcv": [],
                "price": 183.0,
                "fundamentals": {
                    "pe_ratio": None,
                    "ev_ebitda": None,
                    "market_cap": None,
                    "debt_equity": None,
                },
                "fetched_at": "2026-03-24T00:00:00+00:00",
            }
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session_cls.return_value = mock_session
            mock_session.execute = MagicMock()
            mock_redis.publish = MagicMock()
            mock_redis.set = MagicMock()

            from ingestion.tasks import ingest_ticker
            ingest_ticker("AAPL")

        # Verify publish was called with the correct channel
        publish_calls = mock_redis.publish.call_args_list
        assert any(c[0][0] == "quotes:AAPL" for c in publish_calls), (
            f"Expected redis.publish('quotes:AAPL', ...) but got: {publish_calls}"
        )
