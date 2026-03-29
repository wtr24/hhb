"""Tests for TA-11 Fibonacci retracement/extension level math."""
from analysis.fibonacci import compute_fibonacci_levels, compute_fibonacci_extensions, FIB_LEVELS


def test_fibonacci_retracement_levels():
    """compute_fibonacci_levels returns 9 levels (0.0 + 8 ratios), correct endpoint prices."""
    levels = compute_fibonacci_levels(100.0, 80.0)
    assert len(levels) == 9, f"Expected 9 levels, got {len(levels)}"
    # Level at ratio 0.0 should be the swing high
    level_0 = next(l for l in levels if l["ratio"] == 0.0)
    assert level_0["price"] == 100.0, f"Expected 100.0 at ratio 0.0, got {level_0['price']}"
    # Level at ratio 1.0 should be the swing low
    level_1 = next(l for l in levels if l["ratio"] == 1.0)
    assert level_1["price"] == 80.0, f"Expected 80.0 at ratio 1.0, got {level_1['price']}"


def test_fibonacci_extension_levels():
    """compute_fibonacci_extensions returns 4 levels all above the pullback price."""
    extensions = compute_fibonacci_extensions(100.0, 80.0, 90.0)
    assert len(extensions) == 4, f"Expected 4 extension levels, got {len(extensions)}"
    for ext in extensions:
        assert ext["price"] > 90.0, f"Extension price {ext['price']} should be > pullback 90.0"


def test_fibonacci_returns_eight_levels():
    """FIB_LEVELS constant contains exactly 8 ratios."""
    assert len(FIB_LEVELS) == 8, f"Expected 8 FIB_LEVELS, got {len(FIB_LEVELS)}"


def test_fibonacci_swing_high_greater_than_low():
    """When swing_high > swing_low, returned prices are ordered highest to lowest."""
    levels = compute_fibonacci_levels(100.0, 80.0)
    prices = [l["price"] for l in levels]
    assert prices == sorted(prices, reverse=True), "Prices should be ordered from highest to lowest"


def test_fibonacci_inverted_range_same_levels():
    """compute_fibonacci_levels is symmetric — swapping high/low returns same price set."""
    levels_normal = compute_fibonacci_levels(100.0, 80.0)
    levels_inverted = compute_fibonacci_levels(80.0, 100.0)
    prices_normal = sorted(l["price"] for l in levels_normal)
    prices_inverted = sorted(l["price"] for l in levels_inverted)
    assert prices_normal == prices_inverted, (
        "Swapping swing_high and swing_low should return same set of prices"
    )
