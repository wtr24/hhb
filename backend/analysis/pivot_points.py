"""
Pivot Point computation — TA-07.

All 5 methods: Standard, Woodie's, Camarilla, Fibonacci, DeMark.
Pure functions — accept previous bar OHLC floats, return level dicts.
Called by Celery nightly task which persists results to pivot_points table.
"""


def compute_standard(high: float, low: float, close: float) -> dict:
    """Standard (Classic) pivot points."""
    pp = (high + low + close) / 3
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)
    return {"method": "standard", "pp": pp, "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3}


def compute_woodie(high: float, low: float, close: float, open_: float) -> dict:
    """Woodie's pivot points — uses current open, not previous close."""
    pp = (high + low + 2 * open_) / 4
    r1 = 2 * pp - low
    s1 = 2 * pp - high
    r2 = pp + high - low
    s2 = pp - (high - low)
    r3 = None
    s3 = None
    return {"method": "woodie", "pp": pp, "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3}


def compute_camarilla(high: float, low: float, close: float) -> dict:
    """Camarilla pivot points — 4 levels, close-range based."""
    range_ = high - low
    r1 = close + range_ * 1.1 / 12
    r2 = close + range_ * 1.1 / 6
    r3 = close + range_ * 1.1 / 4
    r4 = close + range_ * 1.1 / 2
    s1 = close - range_ * 1.1 / 12
    s2 = close - range_ * 1.1 / 6
    s3 = close - range_ * 1.1 / 4
    s4 = close - range_ * 1.1 / 2
    pp = (high + low + close) / 3
    return {"method": "camarilla", "pp": pp, "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3, "r4": r4, "s4": s4}


def compute_fibonacci(high: float, low: float, close: float) -> dict:
    """Fibonacci pivot points using Fibonacci ratios 0.382, 0.618, 1.0."""
    pp = (high + low + close) / 3
    range_ = high - low
    r1 = pp + 0.382 * range_
    r2 = pp + 0.618 * range_
    r3 = pp + 1.000 * range_
    s1 = pp - 0.382 * range_
    s2 = pp - 0.618 * range_
    s3 = pp - 1.000 * range_
    return {"method": "fibonacci", "pp": pp, "r1": r1, "r2": r2, "r3": r3,
            "s1": s1, "s2": s2, "s3": s3}


def compute_demark(high: float, low: float, close: float, open_: float) -> dict:
    """
    DeMark pivot points — PP depends on close vs open relationship.
    If close < open: X = H + 2*L + C
    If close > open: X = 2*H + L + C
    If close == open: X = H + L + 2*C
    """
    if close < open_:
        x = high + 2 * low + close
    elif close > open_:
        x = 2 * high + low + close
    else:
        x = high + low + 2 * close
    pp = x / 4
    r1 = x / 2 - low
    s1 = x / 2 - high
    return {"method": "demark", "pp": pp, "r1": r1, "r2": None, "r3": None,
            "s1": s1, "s2": None, "s3": None}


def compute_all_methods(high: float, low: float, close: float, open_: float) -> list[dict]:
    """Run all 5 methods and return list of level dicts."""
    return [
        compute_standard(high, low, close),
        compute_woodie(high, low, close, open_),
        compute_camarilla(high, low, close),
        compute_fibonacci(high, low, close),
        compute_demark(high, low, close, open_),
    ]
