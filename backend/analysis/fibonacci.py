"""
Fibonacci retracement and extension level computation — TA-11.

Pure functions. Called by /api/ta/fibonacci endpoint when user provides
swing high and swing low bar indices. Returns price levels as horizontal
line data for the frontend to render via lightweight-charts LineSeries.
"""

# The 8 required Fibonacci ratios (D-12 from CONTEXT.md)
FIB_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.618, 2.618]

# Display labels: key levels (amber in UI), minor levels (dim)
KEY_LEVELS = {0.382, 0.5, 0.618, 1.0}
MINOR_LEVELS = {0.236, 0.786, 1.618, 2.618}


def compute_fibonacci_levels(swing_high: float, swing_low: float) -> list[dict]:
    """
    Compute Fibonacci retracement levels between swing_high and swing_low.

    For retracement (uptrend: high > low):
      level_price = swing_high - ratio * (swing_high - swing_low)
    For retracement (downtrend: low > high):
      level_price = swing_low + ratio * (swing_low - swing_high)
      (same formula, just swap high/low — the formula is symmetric)

    Returns list of 9 level dicts ordered from highest to lowest price
    (0.0 prepended + 8 ratio levels).
    Each dict: {ratio, price, label, is_key_level}
    """
    if swing_high == swing_low:
        raise ValueError("swing_high and swing_low must be different prices")

    range_ = abs(swing_high - swing_low)
    # Retracement levels measured from the higher price down
    high = max(swing_high, swing_low)
    low = min(swing_high, swing_low)
    levels = []
    for ratio in FIB_LEVELS:
        price = high - ratio * range_
        levels.append({
            "ratio": ratio,
            "price": round(price, 4),
            "label": str(ratio),
            "is_key_level": ratio in KEY_LEVELS,
        })
    # Add 0.0 (swing high) and include in return for completeness
    levels.insert(0, {
        "ratio": 0.0,
        "price": round(high, 4),
        "label": "0.0",
        "is_key_level": True,
    })
    return levels


def compute_fibonacci_extensions(swing_high: float, swing_low: float,
                                  pullback: float) -> list[dict]:
    """
    Compute Fibonacci extension levels for price projection.
    pullback: the price at which the retracement ended (the start of the new move).

    Extension levels project BEYOND the original swing high (for bullish moves).
    extension_price = pullback + ratio * abs(swing_high - swing_low)

    Extension ratios used: 0.618, 1.0, 1.618, 2.618.
    """
    range_ = abs(swing_high - swing_low)
    extension_ratios = [0.618, 1.0, 1.618, 2.618]
    levels = []
    for ratio in extension_ratios:
        price = pullback + ratio * range_
        levels.append({
            "ratio": ratio,
            "price": round(price, 4),
            "label": f"{ratio} ext",
            "is_key_level": ratio in KEY_LEVELS,
        })
    return levels
