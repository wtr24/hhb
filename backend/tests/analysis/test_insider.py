"""
Tests for insider transaction clustering logic.

Covers EQUITY-08: insider clustering filter excludes 10b5-1 codes,
groups by time window, detects multi-insider buying.
Per 03-VALIDATION.md test requirements.
"""
import pytest
from analysis.insider import cluster_insiders


def _make_transaction(name="Alice", code="P", date="2026-01-01", share=100, price=50.0):
    """Helper to build a minimal insider transaction dict."""
    return {
        "name": name,
        "share": share,
        "change": share,
        "filingDate": date,
        "transactionDate": date,
        "transactionCode": code,
        "transactionPrice": price,
        "isDerivative": False,
    }


class TestClusterInsiders:
    """Tests for cluster_insiders() function."""

    def test_filter_10b5_1(self):
        """Transaction with code 'F' (10b5-1) must be excluded from counts."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),  # included
            _make_transaction(name="Bob", code="F", date="2026-01-01"),    # excluded
        ]
        result = cluster_insiders(transactions)
        assert result["buy_count"] == 1
        assert result["sell_count"] == 0

    def test_filter_award_code(self):
        """Transaction with code 'A' (award) must be excluded."""
        transactions = [
            _make_transaction(name="Alice", code="S", date="2026-01-01"),  # included
            _make_transaction(name="Bob", code="A", date="2026-01-01"),    # excluded
        ]
        result = cluster_insiders(transactions)
        assert result["sell_count"] == 1
        assert result["buy_count"] == 0

    def test_filter_disposition_code(self):
        """Transaction with code 'D' (disposition) must be excluded."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-05"),  # included
            _make_transaction(name="Bob", code="D", date="2026-01-05"),    # excluded
        ]
        result = cluster_insiders(transactions)
        assert result["buy_count"] == 1

    def test_buy_sell_ratio(self):
        """3 buys + 1 sell = buy_sell_ratio of 3.0."""
        transactions = [
            _make_transaction(name="A", code="P", date="2026-01-01"),
            _make_transaction(name="B", code="P", date="2026-01-02"),
            _make_transaction(name="C", code="P", date="2026-01-03"),
            _make_transaction(name="D", code="S", date="2026-01-04"),
        ]
        result = cluster_insiders(transactions)
        assert result["buy_count"] == 3
        assert result["sell_count"] == 1
        assert result["buy_sell_ratio"] == pytest.approx(3.0, rel=1e-4)

    def test_buy_sell_ratio_none_when_no_sells(self):
        """buy_sell_ratio is None when there are no sell transactions."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),
        ]
        result = cluster_insiders(transactions)
        assert result["buy_sell_ratio"] is None

    def test_multi_insider_detection(self):
        """2 different names buying within 14 days = multi_insider True."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),
            _make_transaction(name="Bob", code="P", date="2026-01-10"),  # within 14 days
        ]
        result = cluster_insiders(transactions, window_days=14)
        assert result["multi_insider"] is True

    def test_multi_insider_false_when_same_person(self):
        """Same person buying multiple times is not multi_insider."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),
            _make_transaction(name="Alice", code="P", date="2026-01-05"),
        ]
        result = cluster_insiders(transactions, window_days=14)
        assert result["multi_insider"] is False

    def test_multi_insider_false_when_outside_window(self):
        """2 different buyers more than window_days apart = multi_insider False."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),
            _make_transaction(name="Bob", code="P", date="2026-02-01"),  # 31 days apart
        ]
        result = cluster_insiders(transactions, window_days=14)
        assert result["multi_insider"] is False

    def test_empty_input(self):
        """Empty list returns all zeros, no clusters."""
        result = cluster_insiders([])
        assert result["buy_count"] == 0
        assert result["sell_count"] == 0
        assert result["buy_sell_ratio"] is None
        assert result["clusters"] == []
        assert result["multi_insider"] is False

    def test_result_keys_present(self):
        """Result dict must contain all required keys."""
        result = cluster_insiders([])
        assert "buy_count" in result
        assert "sell_count" in result
        assert "buy_sell_ratio" in result
        assert "clusters" in result
        assert "multi_insider" in result

    def test_only_excluded_codes_returns_empty(self):
        """Input of only F/A/D codes returns zero counts."""
        transactions = [
            _make_transaction(code="F"),
            _make_transaction(code="A"),
            _make_transaction(code="D"),
        ]
        result = cluster_insiders(transactions)
        assert result["buy_count"] == 0
        assert result["sell_count"] == 0
        assert result["clusters"] == []

    def test_cluster_groups_nearby_transactions(self):
        """Transactions within window_days are grouped into a single cluster."""
        transactions = [
            _make_transaction(name="Alice", code="P", date="2026-01-01"),
            _make_transaction(name="Bob", code="P", date="2026-01-07"),   # 6 days apart
            _make_transaction(name="Carol", code="P", date="2026-02-01"), # 31 days from Alice
        ]
        result = cluster_insiders(transactions, window_days=14)
        # Alice + Bob should be in one cluster, Carol in another
        assert len(result["clusters"]) == 2
