"""
Technical Analysis indicator computation.

All functions are pure — they accept numpy arrays and return numpy arrays or dicts.
TA-Lib is used as primary source (C speed). pandas-ta is fallback for indicators
TA-Lib does not cover (HMA, VWMA, SuperTrend, Vortex, Ichimoku).

TA-Lib pitfall: all return arrays have NaN for the first (period-1) elements.
Always strip leading NaN before returning: use the valid_mask pattern below.
"""
import numpy as np
import talib


def _strip_nan(times: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Remove leading NaN values. Returns aligned (times, values) pair."""
    mask = ~np.isnan(values)
    return times[mask], values[mask]


# ──────────────────────────────────────────────────────────
# TA-01  Moving Averages
# ──────────────────────────────────────────────────────────

def compute_sma(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """SMA via talib.SMA. Returns {times, values} with NaN stripped."""
    values = talib.SMA(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_ema(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """EMA via talib.EMA."""
    values = talib.EMA(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_dema(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Double EMA via talib.DEMA."""
    values = talib.DEMA(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_tema(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Triple EMA via talib.TEMA."""
    values = talib.TEMA(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_wma(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Weighted MA via talib.WMA."""
    values = talib.WMA(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_lwma(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Linear Weighted MA — identical to WMA formula. Alias for compute_wma."""
    return compute_wma(closes, times, period)


def compute_hma(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Hull MA via pandas_ta (TA-Lib does not include HMA)."""
    import pandas as pd
    import pandas_ta as pta
    series = pd.Series(closes)
    values = pta.hma(series, length=period).to_numpy()
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_vwma(closes: np.ndarray, volumes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Volume Weighted MA via pandas_ta (TA-Lib does not include VWMA)."""
    import pandas as pd
    import pandas_ta as pta
    close_series = pd.Series(closes)
    vol_series = pd.Series(volumes)
    values = pta.vwma(close_series, vol_series, length=period).to_numpy()
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_golden_death_cross(closes: np.ndarray, times: np.ndarray,
                                fast: int = 50, slow: int = 200) -> dict:
    """
    Returns fast MA, slow MA, and cross signal.
    signal: +1 = golden cross (fast crossed above slow), -1 = death cross, 0 = no cross.
    """
    fast_ma = talib.SMA(closes, timeperiod=fast)
    slow_ma = talib.SMA(closes, timeperiod=slow)
    mask = ~(np.isnan(fast_ma) | np.isnan(slow_ma))
    f, s, t = fast_ma[mask], slow_ma[mask], times[mask]
    # Detect cross: previous bar fast was below slow, current bar fast is above (or vice versa)
    signal = np.zeros(len(f), dtype=int)
    if len(f) > 1:
        was_above = f[:-1] > s[:-1]
        is_above = f[1:] > s[1:]
        signal[1:][~was_above & is_above] = 1   # golden cross
        signal[1:][was_above & ~is_above] = -1  # death cross
    return {
        "times": t.tolist(),
        "fast_ma": np.round(f, 4).tolist(),
        "slow_ma": np.round(s, 4).tolist(),
        "signal": signal.tolist(),
    }


def compute_ema_ribbon(closes: np.ndarray, times: np.ndarray,
                       periods: list[int] | None = None) -> dict:
    """
    EMA Ribbon: 8 EMAs with periods [8, 13, 21, 34, 55, 89, 144, 233] by default.
    Returns dict keyed by period. NaN stripped per series individually.
    Slowest period determines the common valid range.
    """
    if periods is None:
        periods = [8, 13, 21, 34, 55, 89, 144, 233]
    result = {}
    for p in periods:
        values = talib.EMA(closes, timeperiod=p)
        t, v = _strip_nan(times, values)
        result[str(p)] = {"times": t.tolist(), "values": np.round(v, 4).tolist()}
    return result


# ──────────────────────────────────────────────────────────
# TA-02  Momentum / Oscillators
# ──────────────────────────────────────────────────────────

def compute_rsi(closes: np.ndarray, times: np.ndarray, period: int = 14) -> dict:
    """RSI via talib.RSI. Values in range 0–100."""
    values = talib.RSI(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_stoch_rsi(closes: np.ndarray, times: np.ndarray,
                      rsi_period: int = 14, stoch_period: int = 14,
                      k_smooth: int = 3, d_smooth: int = 3) -> dict:
    """StochRSI: apply Stochastic formula to RSI values. Returns %K and %D."""
    rsi = talib.RSI(closes, timeperiod=rsi_period)
    k, d = talib.STOCH(rsi, rsi, rsi,
                        fastk_period=stoch_period,
                        slowk_period=k_smooth,
                        slowk_matype=0,
                        slowd_period=d_smooth,
                        slowd_matype=0)
    mask = ~(np.isnan(k) | np.isnan(d))
    return {
        "times": times[mask].tolist(),
        "k": np.round(k[mask], 4).tolist(),
        "d": np.round(d[mask], 4).tolist(),
    }


def compute_macd(closes: np.ndarray, times: np.ndarray,
                 fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD via talib.MACD. Returns macd_line, signal_line, histogram."""
    macd_line, sig_line, histogram = talib.MACD(closes, fastperiod=fast,
                                                 slowperiod=slow, signalperiod=signal)
    mask = ~(np.isnan(macd_line) | np.isnan(sig_line) | np.isnan(histogram))
    return {
        "times": times[mask].tolist(),
        "macd": np.round(macd_line[mask], 4).tolist(),
        "signal": np.round(sig_line[mask], 4).tolist(),
        "histogram": np.round(histogram[mask], 4).tolist(),
    }


def compute_stochastic(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                        times: np.ndarray, k_period: int = 14,
                        k_smooth: int = 3, d_smooth: int = 3) -> dict:
    """Stochastic %K/%D via talib.STOCH."""
    k, d = talib.STOCH(highs, lows, closes,
                        fastk_period=k_period,
                        slowk_period=k_smooth,
                        slowk_matype=0,
                        slowd_period=d_smooth,
                        slowd_matype=0)
    mask = ~(np.isnan(k) | np.isnan(d))
    return {
        "times": times[mask].tolist(),
        "k": np.round(k[mask], 4).tolist(),
        "d": np.round(d[mask], 4).tolist(),
    }


def compute_williams_r(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                        times: np.ndarray, period: int = 14) -> dict:
    """Williams %R via talib.WILLR. Range -100 to 0."""
    values = talib.WILLR(highs, lows, closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_cci(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 times: np.ndarray, period: int = 20) -> dict:
    """Commodity Channel Index via talib.CCI."""
    values = talib.CCI(highs, lows, closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_roc(closes: np.ndarray, times: np.ndarray, period: int = 12) -> dict:
    """Rate of Change via talib.ROC."""
    values = talib.ROC(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_momentum(closes: np.ndarray, times: np.ndarray, period: int = 10) -> dict:
    """Momentum via talib.MOM."""
    values = talib.MOM(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_dpo(closes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """
    Detrended Price Oscillator.
    DPO = Close[i] - SMA(period)[i - period/2 - 1]
    TA-Lib does not include DPO — hand-rolled from the standard formula.
    """
    sma = talib.SMA(closes, timeperiod=period)
    shift = period // 2 + 1
    dpo = np.full(len(closes), np.nan)
    for i in range(shift, len(closes)):
        if not np.isnan(sma[i - shift]):
            dpo[i] = closes[i] - sma[i - shift]
    t, v = _strip_nan(times, dpo)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_trix(closes: np.ndarray, times: np.ndarray, period: int = 15) -> dict:
    """1-day Rate of Change of Triple Smooth EMA via talib.TRIX."""
    values = talib.TRIX(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_ultimate_oscillator(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                                  times: np.ndarray, period1: int = 7,
                                  period2: int = 14, period3: int = 28) -> dict:
    """Ultimate Oscillator via talib.ULTOSC."""
    values = talib.ULTOSC(highs, lows, closes,
                           timeperiod1=period1, timeperiod2=period2, timeperiod3=period3)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_ppo(closes: np.ndarray, times: np.ndarray,
                fast: int = 12, slow: int = 26, ma_type: int = 1) -> dict:
    """Percentage Price Oscillator via talib.PPO."""
    values = talib.PPO(closes, fastperiod=fast, slowperiod=slow, matype=ma_type)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_kdj(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 times: np.ndarray, period: int = 9,
                 signal_k: int = 3, signal_d: int = 3) -> dict:
    """
    KDJ (Stochastic-derived J line) via pandas_ta.
    K = slow stochastic %K, D = %D, J = 3*K - 2*D.
    TA-Lib STOCH produces K/D but not J; pandas_ta.kdj adds the J line.
    """
    import pandas as pd
    import pandas_ta as pta
    high_s = pd.Series(highs)
    low_s = pd.Series(lows)
    close_s = pd.Series(closes)
    result = pta.kdj(high_s, low_s, close_s, length=period,
                     signal=signal_k, signal_d=signal_d)
    # pandas_ta returns DataFrame with columns K_9_3, D_9_3, J_9_3 (suffix varies by period)
    col_k = [c for c in result.columns if c.startswith("K")][0]
    col_d = [c for c in result.columns if c.startswith("D")][0]
    col_j = [c for c in result.columns if c.startswith("J")][0]
    k = result[col_k].to_numpy()
    d = result[col_d].to_numpy()
    j = result[col_j].to_numpy()
    mask = ~(np.isnan(k) | np.isnan(d) | np.isnan(j))
    return {
        "times": times[mask].tolist(),
        "k": np.round(k[mask], 4).tolist(),
        "d": np.round(d[mask], 4).tolist(),
        "j": np.round(j[mask], 4).tolist(),
    }


def compute_cmo(closes: np.ndarray, times: np.ndarray, period: int = 14) -> dict:
    """Chande Momentum Oscillator via talib.CMO. Range -100 to +100."""
    values = talib.CMO(closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}
