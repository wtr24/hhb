"""
Tests for Black-Scholes Greeks calculator.

Covers EQUITY-09: options chain with correct Greeks calculations.
Per 03-VALIDATION.md test requirements.
"""
import pytest
from analysis.black_scholes import bs_greeks, iv_percentile_rank


class TestBsGreeks:
    """Tests for bs_greeks() function."""

    def test_call_delta_range(self):
        """Call delta must be in (0, 1) for standard inputs."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        assert result["delta"] is not None
        assert 0 < result["delta"] < 1

    def test_put_delta_range(self):
        """Put delta must be in (-1, 0) for standard inputs."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="put")
        assert result["delta"] is not None
        assert -1 < result["delta"] < 0

    def test_vega_positive(self):
        """Vega must be positive for both call and put."""
        call_result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        put_result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="put")
        assert call_result["vega"] is not None
        assert call_result["vega"] > 0
        assert put_result["vega"] is not None
        assert put_result["vega"] > 0

    def test_theta_negative_call(self):
        """Theta must be negative for a long call (time decay costs the holder)."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        assert result["theta"] is not None
        assert result["theta"] < 0

    def test_zero_time_returns_none(self):
        """T=0 is invalid — all outputs must be None."""
        result = bs_greeks(S=100, K=100, T=0, r=0.05, sigma=0.2, option_type="call")
        assert result["price"] is None
        assert result["delta"] is None
        assert result["gamma"] is None
        assert result["vega"] is None
        assert result["theta"] is None

    def test_zero_sigma_returns_none(self):
        """sigma=0 is invalid — all outputs must be None."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0, option_type="call")
        assert result["price"] is None
        assert result["delta"] is None

    def test_atm_call_delta_near_0_5(self):
        """ATM call (S=K) delta should be approximately 0.5 (within 0.1)."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        assert result["delta"] is not None
        assert abs(result["delta"] - 0.5) < 0.1

    def test_result_keys_present(self):
        """Result dict must contain all five required keys."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        assert "price" in result
        assert "delta" in result
        assert "gamma" in result
        assert "vega" in result
        assert "theta" in result

    def test_gamma_positive(self):
        """Gamma is always positive for both calls and puts."""
        call_result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        put_result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="put")
        assert call_result["gamma"] > 0
        assert put_result["gamma"] > 0

    def test_price_positive(self):
        """Option price must be positive."""
        result = bs_greeks(S=100, K=100, T=0.25, r=0.05, sigma=0.2, option_type="call")
        assert result["price"] > 0


class TestIvPercentileRank:
    """Tests for iv_percentile_rank() function."""

    def test_empty_history_returns_zero(self):
        """Empty IV history returns 0.0."""
        result = iv_percentile_rank(0.25, [])
        assert result == 0.0

    def test_current_above_all_history(self):
        """Current IV above all history returns 100.0."""
        result = iv_percentile_rank(0.50, [0.10, 0.20, 0.30, 0.40])
        assert result == 100.0

    def test_current_below_all_history(self):
        """Current IV below all history returns 0.0."""
        result = iv_percentile_rank(0.05, [0.10, 0.20, 0.30, 0.40])
        assert result == 0.0

    def test_median_iv_returns_50(self):
        """Current IV at the median returns approximately 50.0."""
        history = [0.10, 0.20, 0.30, 0.40]
        result = iv_percentile_rank(0.25, history)
        # 2 values below 0.25, out of 4 total = 50%
        assert result == 50.0
