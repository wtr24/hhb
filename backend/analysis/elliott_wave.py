"""
Elliott Wave Fibonacci ratio validation — TA-12.

Pure functions called by /api/ta/elliott-wave/validate endpoint.
Validates:
  1. Wave 3 is not the shortest impulse wave (checked after Wave 4 label placed)
  2. Wave 4 does not overlap Wave 1 territory (overlap check)
  3. Fibonacci relationships between wave lengths

All functions accept wave_points: list of {bar_idx, price} dicts in sequence order.
"""


def _wave_length(point_a: dict, point_b: dict) -> float:
    """Absolute price length of a wave."""
    return abs(point_b["price"] - point_a["price"])


def validate_wave3_not_shortest(wave_points: list[dict]) -> dict:
    """
    Elliott Wave Rule: Wave 3 is never the shortest impulse wave.
    Wave 3 = points[2] to points[3] (index 2->3, 0-indexed from Wave 1 start)
    Wave 1 = points[0] to points[1]
    Wave 5 = points[4] to points[5] (only checked if 6 points provided)

    Called after Wave 4 label (4th click) to check Wave 1/3/5 relationships.
    If only 4 points provided (Wave 4 just placed), can only compare Wave 1 vs Wave 3.

    Returns: {valid: bool, rule: str, message: str, fibonacci_ratio: float|None}
    """
    if len(wave_points) < 4:
        return {
            "valid": True,
            "rule": "wave3_not_shortest",
            "message": "Insufficient points to check (need at least 4)",
            "fibonacci_ratio": None,
        }
    w1 = _wave_length(wave_points[0], wave_points[1])
    w3 = _wave_length(wave_points[2], wave_points[3])
    fib_ratio = round(w3 / w1, 3) if w1 > 0 else None

    if len(wave_points) >= 6:
        w5 = _wave_length(wave_points[4], wave_points[5])
        is_shortest = w3 < w1 and w3 < w5
    else:
        # With only 4 points: Wave 3 must be longer than Wave 1 (strict check deferred until W5)
        is_shortest = w3 < w1

    if is_shortest:
        return {
            "valid": False,
            "rule": "wave3_not_shortest",
            "message": f"Wave 3 ({w3:.2f}) is shorter than Wave 1 ({w1:.2f}) — violates Elliott Wave rules",
            "fibonacci_ratio": fib_ratio,
        }
    return {
        "valid": True,
        "rule": "wave3_not_shortest",
        "message": f"Wave 3 ratio to Wave 1: {fib_ratio}x (valid)",
        "fibonacci_ratio": fib_ratio,
    }


def validate_wave4_no_overlap(wave_points: list[dict]) -> dict:
    """
    Elliott Wave Rule: Wave 4 must not overlap Wave 1 territory.
    For a bullish impulse: Wave 4 low must NOT go below Wave 1 high.
    For a bearish impulse: Wave 4 high must NOT go above Wave 1 low.

    wave_points[0] = Wave 1 start, wave_points[1] = Wave 1 end (= Wave 2 start)
    wave_points[3] = Wave 3 end (= Wave 4 start), wave_points[4] = Wave 4 end

    Called after Wave 4 label is placed (5 points: W1-start, W1-end/W2-start,
    W2-end/W3-start, W3-end/W4-start, W4-end).
    """
    if len(wave_points) < 5:
        return {
            "valid": True,
            "rule": "wave4_no_overlap",
            "message": "Insufficient points to check Wave 4 overlap (need 5)",
            "overlap_amount": None,
        }
    wave1_start = wave_points[0]["price"]
    wave1_end = wave_points[1]["price"]
    wave4_end = wave_points[4]["price"]

    bullish = wave1_end > wave1_start
    if bullish:
        # Wave 4 low must stay above Wave 1 high (= wave1_end)
        overlap = wave1_end - wave4_end  # positive if overlap
        if overlap > 0:
            return {
                "valid": False,
                "rule": "wave4_no_overlap",
                "message": f"Wave 4 overlaps Wave 1 by {overlap:.2f} — violates Elliott Wave rules",
                "overlap_amount": round(overlap, 4),
            }
    else:
        # Bearish: Wave 4 high must stay below Wave 1 low (= wave1_end)
        overlap = wave4_end - wave1_end
        if overlap > 0:
            return {
                "valid": False,
                "rule": "wave4_no_overlap",
                "message": f"Wave 4 overlaps Wave 1 by {overlap:.2f} — violates Elliott Wave rules",
                "overlap_amount": round(overlap, 4),
            }

    return {
        "valid": True,
        "rule": "wave4_no_overlap",
        "message": "Wave 4 does not overlap Wave 1 territory (valid)",
        "overlap_amount": 0.0,
    }


def validate_wave_sequence(wave_points: list[dict]) -> list[dict]:
    """
    Run all applicable validations given the current number of wave points.
    Returns list of validation results — one per applicable rule.

    Called after each wave label is placed:
    - 4 points (after W3 end label): check wave3_not_shortest
    - 5 points (after W4 end label): check wave4_no_overlap
    - 6 points (after W5 end): re-check wave3_not_shortest with full W5 data
    """
    results = []
    n = len(wave_points)
    if n >= 4:
        results.append(validate_wave3_not_shortest(wave_points))
    if n >= 5:
        results.append(validate_wave4_no_overlap(wave_points))
    return results
