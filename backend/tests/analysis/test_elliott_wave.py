"""Tests for TA-12 Elliott Wave Fibonacci ratio validation."""
from analysis.elliott_wave import (
    validate_wave3_not_shortest,
    validate_wave4_no_overlap,
    validate_wave_sequence,
)

# Canonical valid bullish impulse wave sequence
BULLISH_VALID = [
    {"bar_idx": 0, "price": 100.0},   # W1 start
    {"bar_idx": 5, "price": 120.0},   # W1 end (W1 length = 20)
    {"bar_idx": 10, "price": 110.0},  # W2 end / W3 start
    {"bar_idx": 20, "price": 145.0},  # W3 end (W3 length = 35 > W1 length = 20) valid
    {"bar_idx": 25, "price": 130.0},  # W4 end (130 > W1 high of 120) no overlap valid
    {"bar_idx": 35, "price": 160.0},  # W5 end (W5 length = 30 > W3 not shortest check)
]


def test_wave3_not_shortest_check_pass():
    """validate_wave3_not_shortest returns valid=True when W3 > W1 (and W3 > W5)."""
    result = validate_wave3_not_shortest(BULLISH_VALID)
    assert result["valid"] is True, f"Expected valid=True, got: {result}"
    assert result["rule"] == "wave3_not_shortest"


def test_wave3_not_shortest_check_fail():
    """validate_wave3_not_shortest returns valid=False when W3 is shorter than W1."""
    # W1 = 30, W3 = 5 — clearly W3 is shortest
    short_wave3 = [
        {"bar_idx": 0, "price": 100.0},
        {"bar_idx": 5, "price": 130.0},   # W1 length = 30
        {"bar_idx": 10, "price": 125.0},
        {"bar_idx": 15, "price": 130.0},  # W3 length = 5 (shorter than W1) — invalid
    ]
    result = validate_wave3_not_shortest(short_wave3)
    assert result["valid"] is False, f"Expected valid=False, got: {result}"
    assert "shortest" in result["message"].lower() or "shorter" in result["message"].lower()


def test_wave4_no_overlap_check_pass():
    """validate_wave4_no_overlap returns valid=True when W4 stays above W1 high."""
    result = validate_wave4_no_overlap(BULLISH_VALID)
    assert result["valid"] is True, f"Expected valid=True, got: {result}"
    assert result["rule"] == "wave4_no_overlap"
    assert result["overlap_amount"] == 0.0


def test_wave4_no_overlap_check_fail():
    """validate_wave4_no_overlap returns valid=False when W4 goes below W1 end."""
    # W1 ends at 120, W4 ends at 115 — overlap of 5
    overlapping = [
        {"bar_idx": 0, "price": 100.0},   # W1 start
        {"bar_idx": 5, "price": 120.0},   # W1 end
        {"bar_idx": 10, "price": 110.0},  # W2 end / W3 start
        {"bar_idx": 20, "price": 145.0},  # W3 end
        {"bar_idx": 25, "price": 115.0},  # W4 end (115 < 120 = W1 high) — overlap!
    ]
    result = validate_wave4_no_overlap(overlapping)
    assert result["valid"] is False, f"Expected valid=False, got: {result}"
    assert result["overlap_amount"] is not None
    assert result["overlap_amount"] > 0


def test_fibonacci_ratio_between_waves():
    """validate_wave3_not_shortest includes a positive fibonacci_ratio float."""
    result = validate_wave3_not_shortest(BULLISH_VALID)
    assert isinstance(result["fibonacci_ratio"], float), (
        f"Expected float fibonacci_ratio, got {type(result['fibonacci_ratio'])}"
    )
    assert result["fibonacci_ratio"] > 0, (
        f"fibonacci_ratio should be > 0, got {result['fibonacci_ratio']}"
    )


def test_wave_sequence_label_order():
    """validate_wave_sequence with 5 points returns exactly 2 validation results."""
    results = validate_wave_sequence(BULLISH_VALID[:5])
    assert len(results) == 2, f"Expected 2 validation results for 5 points, got {len(results)}"
    rules = [r["rule"] for r in results]
    assert "wave3_not_shortest" in rules
    assert "wave4_no_overlap" in rules
