"""
Market Breadth indicator computation — TA-06.

All functions accept numpy arrays of constituent-level data
(advance count, decline count, or price arrays for an index).
Pure functions — no DB calls. Caller fetches data from TimescaleDB.
"""
import numpy as np


def compute_advance_decline_line(advances: np.ndarray, declines: np.ndarray,
                                  times: np.ndarray) -> dict:
    """
    Cumulative A/D Line: cumsum(advances - declines).
    advances: count of rising stocks per bar (from yfinance constituent snapshot).
    declines: count of falling stocks per bar.
    """
    net = advances - declines
    ad_line = np.cumsum(net)
    return {"times": times.tolist(), "values": ad_line.tolist()}


def compute_mcclellan(advances: np.ndarray, declines: np.ndarray,
                       times: np.ndarray,
                       fast: int = 19, slow: int = 39) -> dict:
    """
    McClellan Oscillator: EMA(fast) - EMA(slow) of (A - D) breadth.
    McClellan Summation Index: cumsum of oscillator values.
    """
    import talib
    net = (advances - declines).astype(float)
    ema_fast = talib.EMA(net, timeperiod=fast)
    ema_slow = talib.EMA(net, timeperiod=slow)
    mask = ~(np.isnan(ema_fast) | np.isnan(ema_slow))
    oscillator = (ema_fast - ema_slow)[mask]
    summation = np.cumsum(oscillator)
    return {
        "times": times[mask].tolist(),
        "oscillator": np.round(oscillator, 4).tolist(),
        "summation": np.round(summation, 4).tolist(),
    }


def compute_trin(advances: np.ndarray, declines: np.ndarray,
                  up_volume: np.ndarray, down_volume: np.ndarray,
                  times: np.ndarray) -> dict:
    """
    TRIN (Arms Index): (A/D) / (UpVol/DownVol).
    Values < 1 = bullish, > 1 = bearish. Divide-by-zero returns NaN.
    """
    ad_ratio = np.where(declines != 0, advances / declines, np.nan)
    vol_ratio = np.where(down_volume != 0, up_volume / down_volume, np.nan)
    trin = np.where(vol_ratio != 0, ad_ratio / vol_ratio, np.nan)
    mask = ~np.isnan(trin)
    return {
        "times": times[mask].tolist(),
        "values": np.round(trin[mask], 4).tolist(),
    }


def compute_new_highs_lows(new_highs: np.ndarray, new_lows: np.ndarray,
                             times: np.ndarray) -> dict:
    """
    New Highs - New Lows differential.
    new_highs: count of stocks making 52-week high per bar.
    new_lows: count of stocks making 52-week low per bar.
    """
    diff = new_highs - new_lows
    return {
        "times": times.tolist(),
        "new_highs": new_highs.tolist(),
        "new_lows": new_lows.tolist(),
        "differential": diff.tolist(),
    }


def compute_up_down_volume_ratio(up_volume: np.ndarray, down_volume: np.ndarray,
                                  times: np.ndarray) -> dict:
    """Up/Down Volume Ratio per bar."""
    ratio = np.where(down_volume != 0, up_volume / down_volume, np.nan)
    mask = ~np.isnan(ratio)
    return {"times": times[mask].tolist(), "values": np.round(ratio[mask], 4).tolist()}


def compute_pct_above_sma(prices: np.ndarray, period: int,
                            times: np.ndarray) -> dict:
    """
    Percentage of constituent stocks above their N-day SMA.
    prices: 2D array, shape (n_bars, n_constituents).
    Returns float 0–100 per bar.
    Called twice: once for period=200, once for period=50.
    """
    import talib
    n_bars, n_stocks = prices.shape
    above = np.zeros(n_bars)
    for j in range(n_stocks):
        sma = talib.SMA(prices[:, j], timeperiod=period)
        above += (prices[:, j] > sma).astype(float)
    pct = above / n_stocks * 100
    # First (period-1) bars are NaN due to SMA warmup
    pct[:period - 1] = np.nan
    mask = ~np.isnan(pct)
    return {"times": times[mask].tolist(), "values": np.round(pct[mask], 2).tolist()}


def compute_tick(uptick_count: np.ndarray, downtick_count: np.ndarray,
                  times: np.ndarray) -> dict:
    """
    TICK index: (number of NYSE stocks on uptick) - (number on downtick).
    uptick_count/downtick_count sourced from index-level yfinance snapshots.
    """
    tick = uptick_count - downtick_count
    return {"times": times.tolist(), "values": tick.tolist()}
