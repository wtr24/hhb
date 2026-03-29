"""
Intermarket correlation analysis — TA-08.

Rolling correlations for: DXY/Gold, Yields/USD, VIX/SPX, Credit Spreads/Equities,
Oil/CPI, Copper/Growth, BTC/SPX.

Pure functions — caller fetches OHLCV series from TimescaleDB.
All price series must be aligned by timestamp before calling.
"""
import numpy as np


INTERMARKET_PAIRS = [
    ("DXY", "GC=F"),      # DXY vs Gold
    ("^TNX", "DX-Y.NYB"), # 10Y Yield vs USD
    ("^VIX", "^GSPC"),    # VIX vs S&P 500
    ("HYG", "^GSPC"),     # HY Credit (proxy) vs Equities
    ("CL=F", "CPIAUCSL"), # Crude Oil vs CPI (monthly, lower freq)
    ("HG=F", "^GSPC"),    # Copper vs S&P 500 (growth proxy)
    ("BTC-USD", "^GSPC"), # Bitcoin vs S&P 500
]


def compute_rolling_correlation(series_a: np.ndarray, series_b: np.ndarray,
                                 times: np.ndarray, window: int) -> dict:
    """
    Rolling Pearson correlation between two equal-length price series.
    Returns correlation values with NaN for the first (window-1) bars.
    Input: price levels (not returns). Correlation computed on log returns internally.
    """
    if len(series_a) != len(series_b):
        raise ValueError(f"series length mismatch: {len(series_a)} vs {len(series_b)}")
    if len(series_a) < window + 1:
        return {"times": [], "values": [], "window": window,
                "error": f"insufficient data — need {window + 1} bars minimum"}
    # Use log returns for stationarity
    ret_a = np.diff(np.log(np.maximum(series_a, 1e-10)))
    ret_b = np.diff(np.log(np.maximum(series_b, 1e-10)))
    corr = np.full(len(series_a), np.nan)
    for i in range(window - 1, len(ret_a)):
        wa = ret_a[i - window + 1:i + 1]
        wb = ret_b[i - window + 1:i + 1]
        if np.std(wa) > 0 and np.std(wb) > 0:
            corr[i + 1] = float(np.corrcoef(wa, wb)[0, 1])
    mask = ~np.isnan(corr)
    return {
        "times": times[mask].tolist(),
        "values": np.round(corr[mask], 4).tolist(),
        "window": window,
    }


def compute_all_correlations(pair_data: dict[str, np.ndarray],
                               times: np.ndarray) -> dict:
    """
    Compute 30D, 90D, 1Y rolling correlations for all 7 pairs.

    pair_data: {ticker: price_array} for all tickers referenced in INTERMARKET_PAIRS.
    Returns nested dict: {pair_label: {30: {...}, 90: {...}, 252: {...}}}
    Missing tickers are skipped (returns error entry for that pair).
    """
    windows = {"30d": 30, "90d": 90, "1y": 252}
    results = {}
    for ticker_a, ticker_b in INTERMARKET_PAIRS:
        label = f"{ticker_a}/{ticker_b}"
        if ticker_a not in pair_data or ticker_b not in pair_data:
            results[label] = {"error": f"data missing for {ticker_a} or {ticker_b}"}
            continue
        results[label] = {}
        for window_label, window in windows.items():
            results[label][window_label] = compute_rolling_correlation(
                pair_data[ticker_a], pair_data[ticker_b], times, window
            )
    return results
