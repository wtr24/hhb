"""
Candlestick pattern detection and win rate computation — TA-09, TA-13.

detect_all_patterns: runs all 60+ TA-Lib CDL* functions on OHLCV arrays.
compute_pattern_stats: computes win rate + p-value for a single pattern across history.
build_pattern_stats_for_ticker: computes stats for all patterns (called by Celery nightly).
"""
import numpy as np
import talib
from scipy import stats


# All 61 TA-Lib CDL functions
CDL_FUNCTIONS = {
    "CDL2CROWS": talib.CDL2CROWS,
    "CDL3BLACKCROWS": talib.CDL3BLACKCROWS,
    "CDL3INSIDE": talib.CDL3INSIDE,
    "CDL3LINESTRIKE": talib.CDL3LINESTRIKE,
    "CDL3OUTSIDE": talib.CDL3OUTSIDE,
    "CDL3STARSINSOUTH": talib.CDL3STARSINSOUTH,
    "CDL3WHITESOLDIERS": talib.CDL3WHITESOLDIERS,
    "CDLABANDONEDBABY": talib.CDLABANDONEDBABY,
    "CDLADVANCEBLOCK": talib.CDLADVANCEBLOCK,
    "CDLBELTHOLD": talib.CDLBELTHOLD,
    "CDLBREAKAWAY": talib.CDLBREAKAWAY,
    "CDLCLOSINGMARUBOZU": talib.CDLCLOSINGMARUBOZU,
    "CDLCONCEALBABYSWALL": talib.CDLCONCEALBABYSWALL,
    "CDLCOUNTERATTACK": talib.CDLCOUNTERATTACK,
    "CDLDARKCLOUDCOVER": talib.CDLDARKCLOUDCOVER,
    "CDLDOJI": talib.CDLDOJI,
    "CDLDOJISTAR": talib.CDLDOJISTAR,
    "CDLDRAGONFLYDOJI": talib.CDLDRAGONFLYDOJI,
    "CDLENGULFING": talib.CDLENGULFING,
    "CDLEVENINGDOJISTAR": talib.CDLEVENINGDOJISTAR,
    "CDLEVENINGSTAR": talib.CDLEVENINGSTAR,
    "CDLGAPSIDESIDEWHITE": talib.CDLGAPSIDESIDEWHITE,
    "CDLGRAVESTONEDOJI": talib.CDLGRAVESTONEDOJI,
    "CDLHAMMER": talib.CDLHAMMER,
    "CDLHANGINGMAN": talib.CDLHANGINGMAN,
    "CDLHARAMI": talib.CDLHARAMI,
    "CDLHARAMICROSS": talib.CDLHARAMICROSS,
    "CDLHIGHWAVE": talib.CDLHIGHWAVE,
    "CDLHIKKAKE": talib.CDLHIKKAKE,
    "CDLHIKKAKEMOD": talib.CDLHIKKAKEMOD,
    "CDLHOMINGPIGEON": talib.CDLHOMINGPIGEON,
    "CDLIDENTICAL3CROWS": talib.CDLIDENTICAL3CROWS,
    "CDLINNECK": talib.CDLINNECK,
    "CDLINVERTEDHAMMER": talib.CDLINVERTEDHAMMER,
    "CDLKICKING": talib.CDLKICKING,
    "CDLKICKINGBYLENGTH": talib.CDLKICKINGBYLENGTH,
    "CDLLADDERBOTTOM": talib.CDLLADDERBOTTOM,
    "CDLLONGLEGGEDDOJI": talib.CDLLONGLEGGEDDOJI,
    "CDLLONGLINE": talib.CDLLONGLINE,
    "CDLMARUBOZU": talib.CDLMARUBOZU,
    "CDLMATCHINGLOW": talib.CDLMATCHINGLOW,
    "CDLMATHOLD": talib.CDLMATHOLD,
    "CDLMORNINGDOJISTAR": talib.CDLMORNINGDOJISTAR,
    "CDLMORNINGSTAR": talib.CDLMORNINGSTAR,
    "CDLONNECK": talib.CDLONNECK,
    "CDLPIERCING": talib.CDLPIERCING,
    "CDLRICKSHAWMAN": talib.CDLRICKSHAWMAN,
    "CDLRISEFALL3METHODS": talib.CDLRISEFALL3METHODS,
    "CDLSEPARATINGLINES": talib.CDLSEPARATINGLINES,
    "CDLSHOOTINGSTAR": talib.CDLSHOOTINGSTAR,
    "CDLSHORTLINE": talib.CDLSHORTLINE,
    "CDLSPINNINGTOP": talib.CDLSPINNINGTOP,
    "CDLSTALLEDPATTERN": talib.CDLSTALLEDPATTERN,
    "CDLSTICKSANDWICH": talib.CDLSTICKSANDWICH,
    "CDLTAKURI": talib.CDLTAKURI,
    "CDLTASUKIGAP": talib.CDLTASUKIGAP,
    "CDLTHRUSTING": talib.CDLTHRUSTING,
    "CDLTRISTAR": talib.CDLTRISTAR,
    "CDLUNIQUE3RIVER": talib.CDLUNIQUE3RIVER,
    "CDLUPSIDEGAP2CROWS": talib.CDLUPSIDEGAP2CROWS,
    "CDLXSIDEGAP3METHODS": talib.CDLXSIDEGAP3METHODS,
}


def detect_all_patterns(opens: np.ndarray, highs: np.ndarray,
                         lows: np.ndarray, closes: np.ndarray) -> dict[str, np.ndarray]:
    """
    Run all CDL* functions. Returns dict {pattern_name: signal_array}.
    signal_array values: +100 = bullish, -100 = bearish, 0 = no pattern.
    """
    results = {}
    for name, fn in CDL_FUNCTIONS.items():
        try:
            results[name] = fn(opens, highs, lows, closes)
        except Exception:
            results[name] = np.zeros(len(closes), dtype=int)
    return results


def compute_pattern_stats(pattern_signals: np.ndarray, closes: np.ndarray,
                            min_n: int = 30) -> dict:
    """
    Compute win rate + p-value for a single pattern signal array.

    Win definition (D-08): price closes higher on the bar immediately following detection.
    Out-of-sample only: use last 20% of bars as test set (D-10).

    Returns:
    - n_occurrences, n_wins, win_rate, p_value (all None if n < min_n)
    - is_bullish: True if majority of signals are +100, False if -100
    """
    n_total = len(closes)
    split_idx = int(n_total * 0.8)  # first 80% in-sample (discarded), last 20% out-of-sample

    oos_signals = pattern_signals[split_idx:-1]  # exclude last bar (no next bar)
    oos_closes = closes[split_idx:]

    bullish_count = np.sum(oos_signals == 100)
    bearish_count = np.sum(oos_signals == -100)
    is_bullish = bullish_count >= bearish_count

    # For bullish patterns: win = next bar close > this bar close
    # For bearish patterns: win = next bar close < this bar close
    active_mask = oos_signals == (100 if is_bullish else -100)
    n_occurrences = int(np.sum(active_mask))

    if n_occurrences < min_n:
        return {
            "n_occurrences": n_occurrences,
            "n_wins": None,
            "win_rate": None,
            "p_value": None,
            "is_bullish": bool(is_bullish),
        }

    active_indices = np.where(active_mask)[0]
    wins = 0
    for idx in active_indices:
        next_close = oos_closes[idx + 1]
        curr_close = oos_closes[idx]
        if is_bullish and next_close > curr_close:
            wins += 1
        elif not is_bullish and next_close < curr_close:
            wins += 1

    win_rate = wins / n_occurrences
    # t-test against 0.5 (random baseline)
    outcomes = np.array([1.0 if (
        (is_bullish and oos_closes[i + 1] > oos_closes[i]) or
        (not is_bullish and oos_closes[i + 1] < oos_closes[i])
    ) else 0.0 for i in active_indices])
    t_stat, p_value = stats.ttest_1samp(outcomes, 0.5)

    return {
        "n_occurrences": n_occurrences,
        "n_wins": wins,
        "win_rate": round(win_rate, 4),
        "p_value": round(float(p_value), 4),
        "is_bullish": bool(is_bullish),
    }


def build_pattern_stats_for_ticker(opens: np.ndarray, highs: np.ndarray,
                                    lows: np.ndarray, closes: np.ndarray) -> list[dict]:
    """
    Compute stats for all CDL patterns for a single ticker.
    Returns list of dicts ready for insertion into ta_pattern_stats table.
    Each dict has: pattern_name, n_occurrences, n_wins, win_rate, p_value, is_bullish.
    """
    all_signals = detect_all_patterns(opens, highs, lows, closes)
    results = []
    for pattern_name, signals in all_signals.items():
        stats_dict = compute_pattern_stats(signals, closes)
        stats_dict["pattern_name"] = pattern_name
        results.append(stats_dict)
    return results
