"""
Tests for Redis TTL cache helper, token bucket rate limiter, and ingestion config.
Covers all behaviors specified in plan 02-02.
"""
import json
import unittest
from unittest.mock import MagicMock, patch


class TestTTLConstants(unittest.TestCase):
    """TTL dict contains the required keys with correct values."""

    def test_ttl_quote(self):
        from backend.cache.ttl import TTL
        self.assertEqual(TTL["quote"], 15)

    def test_ttl_fx(self):
        from backend.cache.ttl import TTL
        self.assertEqual(TTL["fx"], 30)

    def test_ttl_fundamentals(self):
        from backend.cache.ttl import TTL
        self.assertEqual(TTL["fundamentals"], 86400)

    def test_ttl_macro(self):
        from backend.cache.ttl import TTL
        self.assertEqual(TTL["macro"], 3600)

    def test_ttl_yield_curve(self):
        from backend.cache.ttl import TTL
        self.assertEqual(TTL["yield_curve"], 900)


class TestCacheSet(unittest.TestCase):
    """cache_set calls redis.set with correct key, serialised JSON, and TTL expiry."""

    def setUp(self):
        self.redis = MagicMock()

    def test_cache_set_calls_set_with_ex(self):
        from backend.cache.ttl import cache_set, TTL
        data = {"price": 189.50}
        cache_set(self.redis, "quote:AAPL", data, "quote")
        self.redis.set.assert_called_once_with(
            "quote:AAPL",
            json.dumps(data, default=str),
            ex=TTL["quote"],
        )

    def test_cache_set_uses_correct_ttl_for_fundamentals(self):
        from backend.cache.ttl import cache_set, TTL
        data = {"pe_ratio": 28.4}
        cache_set(self.redis, "fundamentals:AAPL", data, "fundamentals")
        _, kwargs = self.redis.set.call_args
        self.assertEqual(kwargs["ex"], TTL["fundamentals"])

    def test_cache_set_serialises_non_serialisable_values(self):
        """default=str should handle non-JSON-native types."""
        from backend.cache.ttl import cache_set
        import decimal
        data = {"value": decimal.Decimal("3.14")}
        # Should not raise
        cache_set(self.redis, "test:key", data, "macro")
        self.assertTrue(self.redis.set.called)


class TestCacheGet(unittest.TestCase):
    """cache_get returns parsed dict on hit and None on miss."""

    def setUp(self):
        self.redis = MagicMock()

    def test_cache_get_hit_returns_dict(self):
        from backend.cache.ttl import cache_get
        payload = {"price": 189.50, "change": 1.23}
        self.redis.get.return_value = json.dumps(payload)
        result = cache_get(self.redis, "quote:AAPL")
        self.assertEqual(result, payload)

    def test_cache_get_miss_returns_none(self):
        from backend.cache.ttl import cache_get
        self.redis.get.return_value = None
        result = cache_get(self.redis, "quote:MISSING")
        self.assertIsNone(result)

    def test_cache_get_calls_redis_get_with_key(self):
        from backend.cache.ttl import cache_get
        self.redis.get.return_value = None
        cache_get(self.redis, "quote:AAPL")
        self.redis.get.assert_called_once_with("quote:AAPL")


class TestRateLimits(unittest.TestCase):
    """RATE_LIMITS constants match the spec values."""

    def test_finnhub_capacity_and_window(self):
        from backend.cache.rate_limiter import RATE_LIMITS
        self.assertEqual(RATE_LIMITS["finnhub"]["capacity"], 60)
        self.assertEqual(RATE_LIMITS["finnhub"]["per_seconds"], 60)

    def test_fmp_capacity_and_window(self):
        from backend.cache.rate_limiter import RATE_LIMITS
        self.assertEqual(RATE_LIMITS["fmp"]["capacity"], 250)
        self.assertEqual(RATE_LIMITS["fmp"]["per_seconds"], 86400)

    def test_alpha_vantage_capacity_and_window(self):
        from backend.cache.rate_limiter import RATE_LIMITS
        self.assertEqual(RATE_LIMITS["alpha_vantage"]["capacity"], 25)
        self.assertEqual(RATE_LIMITS["alpha_vantage"]["per_seconds"], 86400)

    def test_coingecko_capacity_and_window(self):
        from backend.cache.rate_limiter import RATE_LIMITS
        self.assertEqual(RATE_LIMITS["coingecko"]["capacity"], 13)
        self.assertEqual(RATE_LIMITS["coingecko"]["per_seconds"], 3600)


class TestCheckRateLimit(unittest.TestCase):
    """check_rate_limit returns True when Lua script returns 1, False when 0."""

    def setUp(self):
        self.redis = MagicMock()

    def test_returns_true_when_lua_returns_1(self):
        from backend.cache.rate_limiter import check_rate_limit
        self.redis.eval.return_value = 1
        result = check_rate_limit(self.redis, "finnhub")
        self.assertTrue(result)

    def test_returns_false_when_lua_returns_0(self):
        from backend.cache.rate_limiter import check_rate_limit
        self.redis.eval.return_value = 0
        result = check_rate_limit(self.redis, "finnhub")
        self.assertFalse(result)

    def test_unknown_source_returns_true(self):
        """Unknown API source should not block — default allow."""
        from backend.cache.rate_limiter import check_rate_limit
        result = check_rate_limit(self.redis, "unknown_api")
        self.assertTrue(result)
        self.redis.eval.assert_not_called()

    def test_eval_called_with_correct_key_prefix(self):
        from backend.cache.rate_limiter import check_rate_limit
        self.redis.eval.return_value = 1
        check_rate_limit(self.redis, "coingecko")
        args = self.redis.eval.call_args[0]
        # args[1] = numkeys, args[2] = key
        self.assertEqual(args[2], "ratelimit:coingecko")

    def test_eval_passes_capacity_as_argv1(self):
        from backend.cache.rate_limiter import check_rate_limit, RATE_LIMITS
        self.redis.eval.return_value = 1
        check_rate_limit(self.redis, "fmp")
        args = self.redis.eval.call_args[0]
        # args[3] = capacity
        self.assertEqual(args[3], RATE_LIMITS["fmp"]["capacity"])


class TestCachePackageInit(unittest.TestCase):
    """backend.cache package exports expected names."""

    def test_ttl_exported(self):
        from backend.cache import TTL
        self.assertIsInstance(TTL, dict)

    def test_cache_set_exported(self):
        from backend.cache import cache_set
        self.assertTrue(callable(cache_set))

    def test_cache_get_exported(self):
        from backend.cache import cache_get
        self.assertTrue(callable(cache_get))

    def test_check_rate_limit_exported(self):
        from backend.cache import check_rate_limit
        self.assertTrue(callable(check_rate_limit))

    def test_rate_limits_exported(self):
        from backend.cache import RATE_LIMITS
        self.assertIsInstance(RATE_LIMITS, dict)


class TestIngestionConfig(unittest.TestCase):
    """backend.ingestion.config contains required constants."""

    def test_seed_tickers_contains_aapl(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("AAPL", SEED_TICKERS)

    def test_seed_tickers_contains_msft(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("MSFT", SEED_TICKERS)

    def test_seed_tickers_contains_lloy(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("LLOY.L", SEED_TICKERS)

    def test_seed_tickers_contains_barc(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("BARC.L", SEED_TICKERS)

    def test_seed_tickers_contains_ftse(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("^FTSE", SEED_TICKERS)

    def test_seed_tickers_contains_btc(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("BTC-USD", SEED_TICKERS)

    def test_seed_tickers_contains_gbpusd(self):
        from backend.ingestion.config import SEED_TICKERS
        self.assertIn("GBP=X", SEED_TICKERS)

    def test_fred_series_cpi(self):
        from backend.ingestion.config import FRED_SERIES_MAP
        self.assertEqual(FRED_SERIES_MAP["cpi"], "CPIAUCSL")

    def test_fred_series_gdp(self):
        from backend.ingestion.config import FRED_SERIES_MAP
        self.assertEqual(FRED_SERIES_MAP["gdp"], "GDP")

    def test_fred_series_fed_funds(self):
        from backend.ingestion.config import FRED_SERIES_MAP
        self.assertEqual(FRED_SERIES_MAP["fed_funds"], "FEDFUNDS")

    def test_fred_series_unemployment(self):
        from backend.ingestion.config import FRED_SERIES_MAP
        self.assertEqual(FRED_SERIES_MAP["unemployment"], "UNRATE")

    def test_retry_countdowns(self):
        from backend.ingestion.config import RETRY_COUNTDOWNS
        self.assertEqual(RETRY_COUNTDOWNS, [60, 300, 900])


if __name__ == "__main__":
    unittest.main()
