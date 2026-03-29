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


# ──────────────────────────────────────────────────────────
# TA-03  Trend Strength
# ──────────────────────────────────────────────────────────

def compute_adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                times: np.ndarray, period: int = 14) -> dict:
    """ADX + +DI + -DI via talib.ADX / PLUS_DI / MINUS_DI."""
    adx = talib.ADX(highs, lows, closes, timeperiod=period)
    plus_di = talib.PLUS_DI(highs, lows, closes, timeperiod=period)
    minus_di = talib.MINUS_DI(highs, lows, closes, timeperiod=period)
    mask = ~(np.isnan(adx) | np.isnan(plus_di) | np.isnan(minus_di))
    return {
        "times": times[mask].tolist(),
        "adx": np.round(adx[mask], 4).tolist(),
        "plus_di": np.round(plus_di[mask], 4).tolist(),
        "minus_di": np.round(minus_di[mask], 4).tolist(),
    }


def compute_aroon(highs: np.ndarray, lows: np.ndarray, times: np.ndarray,
                   period: int = 25) -> dict:
    """Aroon Up/Down via talib.AROON. Aroon Oscillator via talib.AROONOSC."""
    aroon_down, aroon_up = talib.AROON(highs, lows, timeperiod=period)
    osc = talib.AROONOSC(highs, lows, timeperiod=period)
    mask = ~(np.isnan(aroon_up) | np.isnan(aroon_down))
    return {
        "times": times[mask].tolist(),
        "aroon_up": np.round(aroon_up[mask], 4).tolist(),
        "aroon_down": np.round(aroon_down[mask], 4).tolist(),
        "oscillator": np.round(osc[mask], 4).tolist(),
    }


def compute_parabolic_sar(highs: np.ndarray, lows: np.ndarray, times: np.ndarray,
                           acceleration: float = 0.02, maximum: float = 0.2) -> dict:
    """Parabolic SAR via talib.SAR. Returns dot prices and position (above/below)."""
    sar = talib.SAR(highs, lows, acceleration=acceleration, maximum=maximum)
    t, v = _strip_nan(times, sar)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_supertrend(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                        times: np.ndarray, period: int = 7, multiplier: float = 3.0) -> dict:
    """
    SuperTrend via pandas_ta (TA-Lib does not include SuperTrend).
    Returns supertrend values and direction (+1 bullish, -1 bearish).
    """
    import pandas as pd
    import pandas_ta as pta
    df = pd.DataFrame({"high": highs, "low": lows, "close": closes})
    result = pta.supertrend(df["high"], df["low"], df["close"],
                             length=period, multiplier=multiplier)
    # pandas_ta returns DataFrame: SUPERT_7_3.0, SUPERTd_7_3.0, SUPERTl_7_3.0, SUPERTs_7_3.0
    col_st = [c for c in result.columns if c.startswith("SUPERT_")][0]
    col_dir = [c for c in result.columns if c.startswith("SUPERTd_")][0]
    st_vals = result[col_st].to_numpy()
    dir_vals = result[col_dir].to_numpy()
    mask = ~np.isnan(st_vals)
    return {
        "times": times[mask].tolist(),
        "values": np.round(st_vals[mask], 4).tolist(),
        "direction": dir_vals[mask].astype(int).tolist(),
    }


def compute_vortex(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                    times: np.ndarray, period: int = 14) -> dict:
    """Vortex Indicator +VI and -VI via pandas_ta (not in TA-Lib)."""
    import pandas as pd
    import pandas_ta as pta
    result = pta.vortex(pd.Series(highs), pd.Series(lows), pd.Series(closes), length=period)
    col_plus = [c for c in result.columns if "VTXP" in c or "VI+" in c][0]
    col_minus = [c for c in result.columns if "VTXM" in c or "VI-" in c][0]
    vp = result[col_plus].to_numpy()
    vm = result[col_minus].to_numpy()
    mask = ~(np.isnan(vp) | np.isnan(vm))
    return {
        "times": times[mask].tolist(),
        "vi_plus": np.round(vp[mask], 4).tolist(),
        "vi_minus": np.round(vm[mask], 4).tolist(),
    }


def compute_ichimoku(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                      times: np.ndarray,
                      tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> dict:
    """
    Ichimoku Cloud via pandas_ta (TA-Lib does not include Ichimoku).
    Returns: tenkan_sen, kijun_sen, senkou_a, senkou_b, chikou_span.
    """
    import pandas as pd
    import pandas_ta as pta
    df = pd.DataFrame({"high": highs, "low": lows, "close": closes})
    result = pta.ichimoku(df["high"], df["low"], df["close"],
                           tenkan=tenkan, kijun=kijun, senkou=senkou_b)
    # pandas_ta.ichimoku returns a tuple (span_df, cloud_df)
    span_df = result[0]
    # Column names: ISA_9, ISB_26, ITS_9, IKS_26, ICS_26 (vary by period params)
    def _col(prefix):
        return [c for c in span_df.columns if c.startswith(prefix)][0]
    tenkan_col = _col("ITS")
    kijun_col = _col("IKS")
    senkou_a_col = _col("ISA")
    senkou_b_col = _col("ISB")
    chikou_col = _col("ICS")
    mask = ~np.isnan(span_df[tenkan_col].to_numpy())
    t = times[mask]
    return {
        "times": t.tolist(),
        "tenkan_sen": np.round(span_df[tenkan_col].to_numpy()[mask], 4).tolist(),
        "kijun_sen": np.round(span_df[kijun_col].to_numpy()[mask], 4).tolist(),
        "senkou_a": np.round(span_df[senkou_a_col].to_numpy()[mask], 4).tolist(),
        "senkou_b": np.round(span_df[senkou_b_col].to_numpy()[mask], 4).tolist(),
        "chikou_span": np.round(span_df[chikou_col].to_numpy()[mask], 4).tolist(),
    }


def compute_mass_index(highs: np.ndarray, lows: np.ndarray, times: np.ndarray,
                        fast: int = 9, slow: int = 25) -> dict:
    """Mass Index via talib (uses EMA of high-low range). No direct talib.MASS — hand-rolled."""
    hl_range = highs - lows
    ema1 = talib.EMA(hl_range, timeperiod=fast)
    ema2 = talib.EMA(ema1, timeperiod=fast)
    ratio = np.where(ema2 != 0, ema1 / ema2, np.nan)
    # Rolling sum of ratio over slow period
    mass = np.full(len(highs), np.nan)
    for i in range(slow - 1, len(ratio)):
        window = ratio[i - slow + 1:i + 1]
        if not np.any(np.isnan(window)):
            mass[i] = np.sum(window)
    t, v = _strip_nan(times, mass)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


# ──────────────────────────────────────────────────────────
# TA-04  Volatility
# ──────────────────────────────────────────────────────────

def compute_bollinger_bands(closes: np.ndarray, times: np.ndarray,
                             period: int = 20, std_dev: float = 2.0) -> dict:
    """Bollinger Bands (upper, middle, lower) + %B via talib.BBANDS."""
    upper, middle, lower = talib.BBANDS(closes, timeperiod=period,
                                          nbdevup=std_dev, nbdevdn=std_dev, matype=0)
    mask = ~(np.isnan(upper) | np.isnan(middle) | np.isnan(lower))
    u, m, l, t = upper[mask], middle[mask], lower[mask], times[mask]
    pct_b = np.where((u - l) != 0, (closes[mask] - l) / (u - l), 0.5)
    return {
        "times": t.tolist(),
        "upper": np.round(u, 4).tolist(),
        "middle": np.round(m, 4).tolist(),
        "lower": np.round(l, 4).tolist(),
        "pct_b": np.round(pct_b, 4).tolist(),
    }


def compute_keltner_channel(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                              times: np.ndarray, ema_period: int = 20,
                              atr_period: int = 10, multiplier: float = 2.0) -> dict:
    """Keltner Channel via pandas_ta (TA-Lib has no direct Keltner)."""
    import pandas as pd
    import pandas_ta as pta
    result = pta.kc(pd.Series(highs), pd.Series(lows), pd.Series(closes),
                    length=ema_period, scalar=multiplier, mamode="ema")
    col_u = [c for c in result.columns if "KCUe" in c or "U_" in c.upper()][0]
    col_m = [c for c in result.columns if "KCBe" in c or "B_" in c.upper()][0]
    col_l = [c for c in result.columns if "KCLe" in c or "L_" in c.upper()][0]
    u = result[col_u].to_numpy()
    m = result[col_m].to_numpy()
    l = result[col_l].to_numpy()
    mask = ~(np.isnan(u) | np.isnan(m) | np.isnan(l))
    return {
        "times": times[mask].tolist(),
        "upper": np.round(u[mask], 4).tolist(),
        "middle": np.round(m[mask], 4).tolist(),
        "lower": np.round(l[mask], 4).tolist(),
    }


def compute_donchian_channel(highs: np.ndarray, lows: np.ndarray, times: np.ndarray,
                              period: int = 20) -> dict:
    """Donchian Channel (highest high / lowest low over N bars) — hand-rolled with numpy."""
    upper = np.full(len(highs), np.nan)
    lower = np.full(len(lows), np.nan)
    for i in range(period - 1, len(highs)):
        upper[i] = np.max(highs[i - period + 1:i + 1])
        lower[i] = np.min(lows[i - period + 1:i + 1])
    middle = (upper + lower) / 2
    mask = ~(np.isnan(upper) | np.isnan(lower))
    return {
        "times": times[mask].tolist(),
        "upper": np.round(upper[mask], 4).tolist(),
        "middle": np.round(middle[mask], 4).tolist(),
        "lower": np.round(lower[mask], 4).tolist(),
    }


def compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 times: np.ndarray, period: int = 14) -> dict:
    """Average True Range via talib.ATR."""
    values = talib.ATR(highs, lows, closes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_historical_vol(closes: np.ndarray, times: np.ndarray,
                            period: int = 20) -> dict:
    """
    Historical Volatility — 3 methods:
    1. Close-to-close (standard deviation of log returns * sqrt(252))
    2. Parkinson (using High-Low) — requires highs/lows; falls back to close-to-close if not provided
    3. Yang-Zhang — most accurate; requires OHLC
    Only close-to-close is computed here (close array only). For Parkinson/Yang-Zhang
    use compute_historical_vol_parkinson and compute_historical_vol_yang_zhang.
    """
    log_returns = np.diff(np.log(closes))
    hv = np.full(len(closes), np.nan)
    for i in range(period, len(log_returns) + 1):
        window = log_returns[i - period:i]
        hv[i] = np.std(window, ddof=1) * np.sqrt(252)
    t, v = _strip_nan(times, hv)
    return {"times": t.tolist(), "values": np.round(v, 6).tolist(), "method": "close_to_close"}


def compute_historical_vol_parkinson(highs: np.ndarray, lows: np.ndarray,
                                      times: np.ndarray, period: int = 20) -> dict:
    """Parkinson Historical Volatility using High-Low range."""
    log_hl = np.log(highs / lows) ** 2
    factor = 1.0 / (4 * np.log(2))
    hv = np.full(len(highs), np.nan)
    for i in range(period - 1, len(highs)):
        window = log_hl[i - period + 1:i + 1]
        hv[i] = np.sqrt(factor * np.mean(window) * 252)
    t, v = _strip_nan(times, hv)
    return {"times": t.tolist(), "values": np.round(v, 6).tolist(), "method": "parkinson"}


def compute_chaikin_volatility(highs: np.ndarray, lows: np.ndarray, times: np.ndarray,
                                ema_period: int = 10, roc_period: int = 10) -> dict:
    """Chaikin Volatility: ROC of EMA of (High - Low)."""
    hl = highs - lows
    ema_hl = talib.EMA(hl, timeperiod=ema_period)
    cv = talib.ROC(ema_hl, timeperiod=roc_period)
    t, v = _strip_nan(times, cv)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_ulcer_index(closes: np.ndarray, times: np.ndarray, period: int = 14) -> dict:
    """Ulcer Index: RMS of percentage drawdown from recent N-bar high."""
    ui = np.full(len(closes), np.nan)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1:i + 1]
        peak = np.max(window)
        drawdowns = ((window - peak) / peak * 100) ** 2
        ui[i] = np.sqrt(np.mean(drawdowns))
    t, v = _strip_nan(times, ui)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


# ──────────────────────────────────────────────────────────
# TA-05  Volume
# ──────────────────────────────────────────────────────────

def compute_obv(closes: np.ndarray, volumes: np.ndarray, times: np.ndarray) -> dict:
    """On-Balance Volume via talib.OBV."""
    values = talib.OBV(closes, volumes)
    t, v = _strip_nan(times, values.astype(float))
    return {"times": t.tolist(), "values": np.round(v, 0).tolist()}


def compute_vwap(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray,
                  volumes: np.ndarray, times: np.ndarray) -> dict:
    """
    Session VWAP (intraday cumulative from bar 0 of the array).
    VWAP = cumulative(typical_price * volume) / cumulative(volume).
    typical_price = (H + L + C) / 3.
    No TA-Lib function for VWAP — hand-rolled from standard formula.
    Note: for daily timeframes, each bar IS the session, so VWAP equals typical price.
    """
    typical = (highs + lows + closes) / 3
    cum_tp_vol = np.cumsum(typical * volumes)
    cum_vol = np.cumsum(volumes)
    vwap = np.where(cum_vol != 0, cum_tp_vol / cum_vol, np.nan)
    t, v = _strip_nan(times, vwap)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_anchored_vwap(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray,
                           volumes: np.ndarray, times: np.ndarray,
                           anchor_idx: int = 0) -> dict:
    """
    Anchored VWAP from a specific bar index (anchor_idx).
    Frontend provides anchor_idx when user selects an anchor bar.
    """
    if anchor_idx >= len(closes) or anchor_idx < 0:
        return {"times": [], "values": [], "error": "anchor_idx out of range"}
    typical = (highs[anchor_idx:] + lows[anchor_idx:] + closes[anchor_idx:]) / 3
    vols = volumes[anchor_idx:]
    cum_tp_vol = np.cumsum(typical * vols)
    cum_vol = np.cumsum(vols)
    vwap = np.where(cum_vol != 0, cum_tp_vol / cum_vol, np.nan)
    t, v = _strip_nan(times[anchor_idx:], vwap)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_vwap_sd_bands(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray,
                           volumes: np.ndarray, times: np.ndarray,
                           std_devs: list[float] | None = None) -> dict:
    """
    VWAP with Standard Deviation bands (±1σ, ±2σ).
    SD is rolling population std dev of (typical_price - VWAP) weighted by volume.
    """
    if std_devs is None:
        std_devs = [1.0, 2.0]
    typical = (highs + lows + closes) / 3
    cum_tp_vol = np.cumsum(typical * volumes)
    cum_vol = np.cumsum(volumes)
    vwap = np.where(cum_vol != 0, cum_tp_vol / cum_vol, np.nan)
    variance = np.where(cum_vol != 0,
                        np.cumsum((typical - vwap) ** 2 * volumes) / cum_vol,
                        np.nan)
    sd = np.sqrt(np.maximum(variance, 0))
    result = {"times": times.tolist(), "vwap": np.round(vwap, 4).tolist()}
    for s in std_devs:
        result[f"upper_{s}"] = np.round(vwap + s * sd, 4).tolist()
        result[f"lower_{s}"] = np.round(vwap - s * sd, 4).tolist()
    return result


def compute_ad_line(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                     volumes: np.ndarray, times: np.ndarray) -> dict:
    """Accumulation/Distribution Line via talib.AD."""
    values = talib.AD(highs, lows, closes, volumes)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 2).tolist()}


def compute_cmf(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 volumes: np.ndarray, times: np.ndarray, period: int = 20) -> dict:
    """Chaikin Money Flow via talib.ADOSC (ratio of A/D oscillator)."""
    # CMF = sum(MFV * volume, N) / sum(volume, N)
    # MFV = ((C - L) - (H - C)) / (H - L)  when H != L, else 0
    hl = highs - lows
    mfv = np.where(hl != 0, ((closes - lows) - (highs - closes)) / hl, 0.0) * volumes
    cmf = np.full(len(closes), np.nan)
    for i in range(period - 1, len(closes)):
        vol_sum = np.sum(volumes[i - period + 1:i + 1])
        cmf[i] = np.sum(mfv[i - period + 1:i + 1]) / vol_sum if vol_sum != 0 else 0.0
    t, v = _strip_nan(times, cmf)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_mfi(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                 volumes: np.ndarray, times: np.ndarray, period: int = 14) -> dict:
    """Money Flow Index via talib.MFI. Range 0–100."""
    values = talib.MFI(highs, lows, closes, volumes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_volume_profile(closes: np.ndarray, volumes: np.ndarray,
                            n_bins: int = 24) -> dict:
    """
    Volume Profile: price level -> total volume traded at that level.
    Returns histogram of volume-at-price. Not time-series — used as chart overlay.
    n_bins controls price granularity (24 bins is standard terminal density).
    """
    price_min, price_max = np.min(closes), np.max(closes)
    if price_min == price_max:
        return {"bins": [], "volumes": [], "poc": None}
    bin_edges = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    hist_vol = np.zeros(n_bins)
    for i, c in enumerate(closes):
        bin_idx = np.searchsorted(bin_edges[1:], c)
        bin_idx = min(bin_idx, n_bins - 1)
        hist_vol[bin_idx] += volumes[i]
    poc_idx = int(np.argmax(hist_vol))
    return {
        "bins": np.round(bin_centers, 4).tolist(),
        "volumes": hist_vol.tolist(),
        "poc": round(float(bin_centers[poc_idx]), 4),
    }


def compute_cvd(closes: np.ndarray, volumes: np.ndarray, times: np.ndarray) -> dict:
    """
    Cumulative Volume Delta: up-bar volume minus down-bar volume, cumulated.
    up-bar = close >= close[i-1]; down-bar = close < close[i-1].
    """
    delta = np.zeros(len(closes))
    for i in range(1, len(closes)):
        if closes[i] >= closes[i - 1]:
            delta[i] = volumes[i]
        else:
            delta[i] = -volumes[i]
    cvd = np.cumsum(delta)
    t, v = _strip_nan(times, cvd)
    return {"times": t.tolist(), "values": np.round(v, 0).tolist()}


def compute_vroc(volumes: np.ndarray, times: np.ndarray, period: int = 14) -> dict:
    """Volume Rate of Change via talib.ROC applied to volume array."""
    values = talib.ROC(volumes, timeperiod=period)
    t, v = _strip_nan(times, values)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_ease_of_movement(highs: np.ndarray, lows: np.ndarray, volumes: np.ndarray,
                               times: np.ndarray, period: int = 14) -> dict:
    """Ease of Movement (EOM): combines price change and volume."""
    hl2 = (highs + lows) / 2
    mid_move = np.diff(hl2, prepend=hl2[0])
    box_ratio = np.where(highs != lows,
                          volumes / 1e6 / (highs - lows),
                          np.nan)
    eom_raw = np.where(box_ratio != 0, mid_move / box_ratio, np.nan)
    eom_sma = talib.SMA(eom_raw, timeperiod=period)
    t, v = _strip_nan(times, eom_sma)
    return {"times": t.tolist(), "values": np.round(v, 4).tolist()}


def compute_nvi_pvi(closes: np.ndarray, volumes: np.ndarray, times: np.ndarray) -> dict:
    """
    Negative Volume Index (NVI) and Positive Volume Index (PVI).
    NVI: only updates on days when volume decreases from previous bar.
    PVI: only updates on days when volume increases from previous bar.
    Both start at 1000.
    """
    nvi = np.full(len(closes), np.nan)
    pvi = np.full(len(closes), np.nan)
    nvi[0] = pvi[0] = 1000.0
    for i in range(1, len(closes)):
        pct_chg = (closes[i] - closes[i - 1]) / closes[i - 1] if closes[i - 1] != 0 else 0
        if volumes[i] < volumes[i - 1]:
            nvi[i] = nvi[i - 1] * (1 + pct_chg)
            pvi[i] = pvi[i - 1]
        else:
            pvi[i] = pvi[i - 1] * (1 + pct_chg)
            nvi[i] = nvi[i - 1]
    return {
        "times": times.tolist(),
        "nvi": np.round(nvi, 4).tolist(),
        "pvi": np.round(pvi, 4).tolist(),
    }


def compute_force_index(closes: np.ndarray, volumes: np.ndarray, times: np.ndarray,
                         period: int = 13) -> dict:
    """Force Index = EMA(period) of (Close - Close[prev]) * Volume."""
    raw = np.full(len(closes), np.nan)
    for i in range(1, len(closes)):
        raw[i] = (closes[i] - closes[i - 1]) * volumes[i]
    fi_ema = talib.EMA(np.nan_to_num(raw, nan=0.0), timeperiod=period)
    fi_ema[np.isnan(raw)] = np.nan
    t, v = _strip_nan(times, fi_ema)
    return {"times": t.tolist(), "values": np.round(v, 2).tolist()}
