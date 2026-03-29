"""
Chart pattern detection — TA-10.

Heuristic algorithms using scipy.signal.find_peaks + geometric constraints.
One detection function per pattern type. All return a list of PatternResult dicts.

PatternResult schema:
{
    "pattern": str,           # e.g. "head_and_shoulders"
    "start_bar": int,         # index into input arrays
    "end_bar": int,           # index into input arrays
    "breakout_bar": int,      # bar where breakout is expected
    "confidence": float,      # 0.0–1.0 (geometric symmetry + volume)
    "label": str,             # display label e.g. "H&S 72%"
    "experimental": True,     # always True per TA-10
}
"""
import numpy as np
from scipy.signal import find_peaks


def _volume_confirmation(volumes: np.ndarray, start: int, end: int,
                          breakout: int) -> float:
    """
    Volume confirmation score: 0.0–0.5.
    Score 0.5 if volume at breakout bar is above mean volume in [start, end].
    Score 0.0 otherwise.
    """
    if breakout >= len(volumes):
        return 0.0
    mean_vol = np.mean(volumes[start:end + 1]) if end > start else volumes[start]
    return 0.5 if volumes[breakout] > mean_vol else 0.0


def _symmetry_score(left_height: float, right_height: float,
                     peak_height: float) -> float:
    """
    Symmetry score 0.0–0.5 based on how balanced left and right shoulders/legs are.
    Perfect symmetry = 0.5; asymmetry proportional to height difference.
    """
    if peak_height == 0:
        return 0.0
    diff = abs(left_height - right_height) / peak_height
    return max(0.0, 0.5 - diff)


def detect_head_and_shoulders(highs: np.ndarray, lows: np.ndarray,
                               closes: np.ndarray, volumes: np.ndarray,
                               prominence: float = 0.02) -> list[dict]:
    """
    Head-and-Shoulders: 3 peaks with middle peak (head) tallest.
    Neckline: line through the two troughs between peaks.
    Confidence = symmetry score + volume confirmation.
    prominence is relative (fraction of price range).
    """
    price_range = np.max(highs) - np.min(lows)
    abs_prominence = prominence * price_range
    peaks, props = find_peaks(highs, prominence=abs_prominence, distance=5)

    results = []
    for i in range(len(peaks) - 2):
        left_idx, head_idx, right_idx = peaks[i], peaks[i + 1], peaks[i + 2]
        lh, hh, rh = highs[left_idx], highs[head_idx], highs[right_idx]
        # Head must be tallest
        if not (hh > lh and hh > rh):
            continue
        # Shoulders should be roughly equal height (within 15% of each other)
        if abs(lh - rh) / hh > 0.15:
            continue
        # Find neckline — trough between left shoulder and head, and head and right shoulder
        trough1_idx = left_idx + np.argmin(lows[left_idx:head_idx + 1])
        trough2_idx = head_idx + np.argmin(lows[head_idx:right_idx + 1])
        neckline = (lows[trough1_idx] + lows[trough2_idx]) / 2
        # Breakout bar: first bar after right shoulder where close crosses below neckline
        breakout = right_idx
        for j in range(right_idx, min(right_idx + 20, len(closes))):
            if closes[j] < neckline:
                breakout = j
                break
        sym = _symmetry_score(lh, rh, hh)
        vol = _volume_confirmation(volumes, left_idx, right_idx, breakout)
        confidence = round(min(1.0, sym + vol), 2)
        results.append({
            "pattern": "head_and_shoulders",
            "start_bar": int(left_idx),
            "end_bar": int(right_idx),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"H&S {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_inverse_head_and_shoulders(highs: np.ndarray, lows: np.ndarray,
                                       closes: np.ndarray, volumes: np.ndarray,
                                       prominence: float = 0.02) -> list[dict]:
    """Inverse H&S: 3 troughs with middle trough (head) lowest."""
    price_range = np.max(highs) - np.min(lows)
    abs_prominence = prominence * price_range
    # Invert lows to find troughs as peaks
    troughs, _ = find_peaks(-lows, prominence=abs_prominence, distance=5)

    results = []
    for i in range(len(troughs) - 2):
        left_idx, head_idx, right_idx = troughs[i], troughs[i + 1], troughs[i + 2]
        ll, hl, rl = lows[left_idx], lows[head_idx], lows[right_idx]
        if not (hl < ll and hl < rl):
            continue
        if abs(ll - rl) / max(abs(hl), 1e-10) > 0.15:
            continue
        neckline = (highs[left_idx + np.argmax(highs[left_idx:head_idx + 1])] +
                    highs[head_idx + np.argmax(highs[head_idx:right_idx + 1])]) / 2
        breakout = right_idx
        for j in range(right_idx, min(right_idx + 20, len(closes))):
            if closes[j] > neckline:
                breakout = j
                break
        sym = _symmetry_score(abs(ll - hl), abs(rl - hl), abs(hl))
        vol = _volume_confirmation(volumes, left_idx, right_idx, breakout)
        confidence = round(min(1.0, sym + vol), 2)
        results.append({
            "pattern": "inverse_head_and_shoulders",
            "start_bar": int(left_idx),
            "end_bar": int(right_idx),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"Inv H&S {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_double_top(highs: np.ndarray, lows: np.ndarray,
                       closes: np.ndarray, volumes: np.ndarray,
                       prominence: float = 0.02, max_diff: float = 0.03) -> list[dict]:
    """Double Top: 2 peaks at similar price levels (within max_diff fraction)."""
    price_range = np.max(highs) - np.min(lows)
    peaks, _ = find_peaks(highs, prominence=prominence * price_range, distance=8)

    results = []
    for i in range(len(peaks) - 1):
        l_idx, r_idx = peaks[i], peaks[i + 1]
        if abs(highs[l_idx] - highs[r_idx]) / highs[l_idx] > max_diff:
            continue
        trough_idx = l_idx + np.argmin(lows[l_idx:r_idx + 1])
        neckline = lows[trough_idx]
        breakout = r_idx
        for j in range(r_idx, min(r_idx + 15, len(closes))):
            if closes[j] < neckline:
                breakout = j
                break
        vol = _volume_confirmation(volumes, l_idx, r_idx, breakout)
        confidence = round(min(1.0, 0.5 + vol), 2)
        results.append({
            "pattern": "double_top",
            "start_bar": int(l_idx),
            "end_bar": int(r_idx),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"Dbl Top {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_double_bottom(highs: np.ndarray, lows: np.ndarray,
                          closes: np.ndarray, volumes: np.ndarray,
                          prominence: float = 0.02, max_diff: float = 0.03) -> list[dict]:
    """Double Bottom: 2 troughs at similar price levels."""
    price_range = np.max(highs) - np.min(lows)
    troughs, _ = find_peaks(-lows, prominence=prominence * price_range, distance=8)

    results = []
    for i in range(len(troughs) - 1):
        l_idx, r_idx = troughs[i], troughs[i + 1]
        if abs(lows[l_idx] - lows[r_idx]) / max(abs(lows[l_idx]), 1e-10) > max_diff:
            continue
        neckline = highs[l_idx + np.argmax(highs[l_idx:r_idx + 1])]
        breakout = r_idx
        for j in range(r_idx, min(r_idx + 15, len(closes))):
            if closes[j] > neckline:
                breakout = j
                break
        vol = _volume_confirmation(volumes, l_idx, r_idx, breakout)
        confidence = round(min(1.0, 0.5 + vol), 2)
        results.append({
            "pattern": "double_bottom",
            "start_bar": int(l_idx),
            "end_bar": int(r_idx),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"Dbl Bot {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_cup_and_handle(highs: np.ndarray, lows: np.ndarray,
                           closes: np.ndarray, volumes: np.ndarray,
                           min_cup_bars: int = 15) -> list[dict]:
    """
    Cup and Handle: U-shaped price decline + recovery + small consolidation.
    Cup: price falls then rises to original level over min_cup_bars.
    Handle: small downward drift (< 50% cup depth) after cup completes.
    """
    results = []
    n = len(closes)
    for start in range(0, n - min_cup_bars - 5, min_cup_bars // 2):
        end = min(start + min_cup_bars * 2, n - 6)
        if end - start < min_cup_bars:
            continue
        rim_l = closes[start]
        cup_low_idx = start + np.argmin(lows[start:end + 1])
        rim_r_end = min(cup_low_idx + (cup_low_idx - start), n - 1)
        if rim_r_end >= n:
            continue
        rim_r = closes[rim_r_end]
        # Rim levels must be roughly equal
        if abs(rim_l - rim_r) / max(rim_l, 1e-10) > 0.05:
            continue
        cup_depth = rim_l - lows[cup_low_idx]
        if cup_depth <= 0:
            continue
        # Handle: small decline, max 50% of cup depth
        handle_end = min(rim_r_end + 10, n - 2)
        handle_low = np.min(lows[rim_r_end:handle_end + 1])
        if rim_r - handle_low > 0.5 * cup_depth:
            continue
        breakout = handle_end
        vol = _volume_confirmation(volumes, start, handle_end, breakout)
        confidence = round(min(1.0, 0.5 + vol), 2)
        results.append({
            "pattern": "cup_and_handle",
            "start_bar": int(start),
            "end_bar": int(handle_end),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"C&H {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_triangle(highs: np.ndarray, lows: np.ndarray,
                     closes: np.ndarray, volumes: np.ndarray,
                     min_bars: int = 10) -> list[dict]:
    """
    Triangle patterns: Ascending, Descending, Symmetric.
    Uses OLS regression on swing highs and swing lows to classify.
    Returns the dominant triangle type found in the lookback window.
    """
    from scipy import stats as scipy_stats
    results = []
    n = len(closes)
    step = min_bars
    for start in range(0, n - min_bars, step):
        end = min(start + min_bars * 2, n - 2)
        if end - start < min_bars:
            continue
        x = np.arange(end - start + 1, dtype=float)
        h = highs[start:end + 1]
        l = lows[start:end + 1]
        # OLS slopes for highs and lows
        slope_h, _, _, _, _ = scipy_stats.linregress(x, h)
        slope_l, _, _, _, _ = scipy_stats.linregress(x, l)
        tol = 0.001  # near-zero slope threshold
        if abs(slope_h) < tol and slope_l > tol:
            ptype = "ascending_triangle"
            label = "Asc Tri"
        elif slope_h < -tol and abs(slope_l) < tol:
            ptype = "descending_triangle"
            label = "Desc Tri"
        elif slope_h < -tol and slope_l > tol:
            ptype = "symmetric_triangle"
            label = "Sym Tri"
        else:
            continue
        breakout = min(end + 2, n - 1)
        vol = _volume_confirmation(volumes, start, end, breakout)
        confidence = round(min(1.0, 0.4 + vol), 2)
        results.append({
            "pattern": ptype,
            "start_bar": int(start),
            "end_bar": int(end),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"{label} {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_flag_pennant(highs: np.ndarray, lows: np.ndarray,
                         closes: np.ndarray, volumes: np.ndarray,
                         pole_bars: int = 8, flag_bars: int = 8) -> list[dict]:
    """
    Flag: strong directional move (pole) followed by tight sideways consolidation.
    Pennant: strong move followed by converging consolidation (mini symmetric triangle).
    """
    from scipy import stats as scipy_stats
    results = []
    n = len(closes)
    for pole_start in range(0, n - pole_bars - flag_bars, pole_bars):
        pole_end = pole_start + pole_bars
        if pole_end + flag_bars >= n:
            break
        # Pole: significant price move (> 3% change)
        pole_change = (closes[pole_end] - closes[pole_start]) / closes[pole_start]
        if abs(pole_change) < 0.03:
            continue
        flag_end = pole_end + flag_bars
        flag_highs = highs[pole_end:flag_end + 1]
        flag_lows = lows[pole_end:flag_end + 1]
        x = np.arange(len(flag_highs), dtype=float)
        slope_h, _, _, _, _ = scipy_stats.linregress(x, flag_highs)
        slope_l, _, _, _, _ = scipy_stats.linregress(x, flag_lows)
        h_range = np.max(flag_highs) - np.min(flag_lows)
        # Flag: parallel channel (both slopes similar direction, small range)
        if abs(slope_h - slope_l) < 0.2 * h_range / len(x):
            ptype = "flag"
            label = "Flag"
        # Pennant: converging (slopes diverge toward each other)
        elif slope_h < 0 and slope_l > 0:
            ptype = "pennant"
            label = "Pennant"
        else:
            continue
        breakout = flag_end
        vol = _volume_confirmation(volumes, pole_end, flag_end, breakout)
        confidence = round(min(1.0, 0.4 + vol + min(abs(pole_change) * 5, 0.1)), 2)
        results.append({
            "pattern": ptype,
            "start_bar": int(pole_start),
            "end_bar": int(flag_end),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"{label} {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_wedge(highs: np.ndarray, lows: np.ndarray,
                  closes: np.ndarray, volumes: np.ndarray,
                  min_bars: int = 12) -> list[dict]:
    """
    Wedge: both high and low trendlines slope in same direction but converge.
    Rising wedge (bearish reversal): both slope up, upper slope < lower slope.
    Falling wedge (bullish reversal): both slope down, lower slope steeper.
    """
    from scipy import stats as scipy_stats
    results = []
    n = len(closes)
    for start in range(0, n - min_bars, min_bars // 2):
        end = min(start + min_bars * 2, n - 2)
        if end - start < min_bars:
            continue
        x = np.arange(end - start + 1, dtype=float)
        slope_h, _, _, _, _ = scipy_stats.linregress(x, highs[start:end + 1])
        slope_l, _, _, _, _ = scipy_stats.linregress(x, lows[start:end + 1])
        # Both sloping same direction
        same_direction = (slope_h > 0 and slope_l > 0) or (slope_h < 0 and slope_l < 0)
        if not same_direction:
            continue
        # Converging: distance between lines decreasing
        start_width = highs[start] - lows[start]
        end_width = highs[end] - lows[end]
        if end_width >= start_width:
            continue
        ptype = "rising_wedge" if slope_h > 0 else "falling_wedge"
        label = "Rise Wedge" if slope_h > 0 else "Fall Wedge"
        breakout = min(end + 2, n - 1)
        vol = _volume_confirmation(volumes, start, end, breakout)
        confidence = round(min(1.0, 0.4 + vol), 2)
        results.append({
            "pattern": ptype,
            "start_bar": int(start),
            "end_bar": int(end),
            "breakout_bar": int(breakout),
            "confidence": confidence,
            "label": f"{label} {int(confidence * 100)}%",
            "experimental": True,
        })
    return results


def detect_all_chart_patterns(highs: np.ndarray, lows: np.ndarray,
                               closes: np.ndarray, volumes: np.ndarray) -> list[dict]:
    """Run all 7 detectors and return combined list, sorted by confidence desc."""
    all_results = []
    detectors = [
        detect_head_and_shoulders,
        detect_inverse_head_and_shoulders,
        detect_double_top,
        detect_double_bottom,
        detect_cup_and_handle,
        detect_triangle,
        detect_flag_pennant,
        detect_wedge,
    ]
    for fn in detectors:
        try:
            all_results.extend(fn(highs, lows, closes, volumes))
        except Exception:
            pass  # skip failed detector, don't abort
    return sorted(all_results, key=lambda x: x["confidence"], reverse=True)
