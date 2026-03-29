"""
Technical Analysis REST endpoints — TA-01 through TA-08.

Three routes:
  GET /api/ta/indicators/{ticker}  — compute any indicator on OHLCV data
  GET /api/ta/pivots/{ticker}       — serve pre-computed pivot point levels
  GET /api/ta/intermarket/{ticker}  — rolling correlations for intermarket pairs

Mirrors the DB session dependency, Redis cache helper, and error-handling
patterns established in backend/api/routes/equity.py.
"""
import json
import logging
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_db
from ..redis_client import get_redis
from analysis import indicators as ind
from analysis.garch import compute_garch_volatility
from analysis.pivot_points import compute_all_methods  # noqa: F401 (not used in route but kept for reference)
from analysis.intermarket import compute_rolling_correlation, INTERMARKET_PAIRS
from models.ohlcv import OHLCV
from models.pivot_points import PivotPoints
from models.ta_pattern_stats import TAPatternStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ta", tags=["technical_analysis"])

# ---------------------------------------------------------------------------
# Indicator dispatch table — built once at module load, never rebuilt per-call.
# Each entry is a callable: fn(ohlcv_arrays: dict, params: dict) -> dict
# ---------------------------------------------------------------------------
# ohlcv_arrays keys: closes, highs, lows, opens, volumes, times (all np.ndarray)
# params keys: period, period2, period3 (all Optional[int], may be absent)

def _build_dispatch(ohlcv: dict, p: dict):
    """Helper that returns a dict of named callables bound to ohlcv."""
    closes = ohlcv["closes"]
    highs = ohlcv["highs"]
    lows = ohlcv["lows"]
    volumes = ohlcv["volumes"]
    times = ohlcv["times"]
    return {
        # TA-01 Moving Averages
        "SMA":          lambda: ind.compute_sma(closes, times, period=p.get("period", 20)),
        "EMA":          lambda: ind.compute_ema(closes, times, period=p.get("period", 20)),
        "DEMA":         lambda: ind.compute_dema(closes, times, period=p.get("period", 20)),
        "TEMA":         lambda: ind.compute_tema(closes, times, period=p.get("period", 20)),
        "WMA":          lambda: ind.compute_wma(closes, times, period=p.get("period", 20)),
        "LWMA":         lambda: ind.compute_lwma(closes, times, period=p.get("period", 20)),
        "HMA":          lambda: ind.compute_hma(closes, times, period=p.get("period", 20)),
        "VWMA":         lambda: ind.compute_vwma(closes, volumes, times, period=p.get("period", 20)),
        "GOLDEN_CROSS": lambda: ind.compute_golden_death_cross(closes, times, fast=p.get("period", 50), slow=p.get("period2", 200)),
        "EMA_RIBBON":   lambda: ind.compute_ema_ribbon(closes, times),
        # TA-02 Momentum
        "RSI":          lambda: ind.compute_rsi(closes, times, period=p.get("period", 14)),
        "STOCH_RSI":    lambda: ind.compute_stoch_rsi(closes, times),
        "MACD":         lambda: ind.compute_macd(closes, times, fast=p.get("period", 12), slow=p.get("period2", 26), signal=p.get("period3", 9)),
        "STOCH":        lambda: ind.compute_stochastic(highs, lows, closes, times),
        "WILLIAMS_R":   lambda: ind.compute_williams_r(highs, lows, closes, times, period=p.get("period", 14)),
        "CCI":          lambda: ind.compute_cci(highs, lows, closes, times, period=p.get("period", 20)),
        "ROC":          lambda: ind.compute_roc(closes, times, period=p.get("period", 12)),
        "MOM":          lambda: ind.compute_momentum(closes, times, period=p.get("period", 10)),
        "DPO":          lambda: ind.compute_dpo(closes, times, period=p.get("period", 20)),
        "TRIX":         lambda: ind.compute_trix(closes, times, period=p.get("period", 15)),
        "ULTOSC":       lambda: ind.compute_ultimate_oscillator(highs, lows, closes, times),
        "PPO":          lambda: ind.compute_ppo(closes, times),
        "KDJ":          lambda: ind.compute_kdj(highs, lows, closes, times),
        "CMO":          lambda: ind.compute_cmo(closes, times, period=p.get("period", 14)),
        # TA-03 Trend Strength
        "ADX":          lambda: ind.compute_adx(highs, lows, closes, times, period=p.get("period", 14)),
        "AROON":        lambda: ind.compute_aroon(highs, lows, times, period=p.get("period", 25)),
        "SAR":          lambda: ind.compute_parabolic_sar(highs, lows, times),
        "SUPERTREND":   lambda: ind.compute_supertrend(highs, lows, closes, times),
        "VORTEX":       lambda: ind.compute_vortex(highs, lows, closes, times),
        "ICHIMOKU":     lambda: ind.compute_ichimoku(highs, lows, closes, times),
        "MASS_INDEX":   lambda: ind.compute_mass_index(highs, lows, times),
        # TA-04 Volatility
        "BBANDS":       lambda: ind.compute_bollinger_bands(closes, times, period=p.get("period", 20)),
        "KC":           lambda: ind.compute_keltner_channel(highs, lows, closes, times),
        "DC":           lambda: ind.compute_donchian_channel(highs, lows, times),
        "ATR":          lambda: ind.compute_atr(highs, lows, closes, times, period=p.get("period", 14)),
        "HV":           lambda: ind.compute_historical_vol(closes, times),
        "HV_PARKINSON": lambda: ind.compute_historical_vol_parkinson(highs, lows, times),
        "CHAIKIN_VOL":  lambda: ind.compute_chaikin_volatility(highs, lows, times),
        "ULCER":        lambda: ind.compute_ulcer_index(closes, times),
        # TA-05 Volume
        "OBV":          lambda: ind.compute_obv(closes, volumes, times),
        "VWAP":         lambda: ind.compute_vwap(closes, highs, lows, volumes, times),
        "VWAP_BANDS":   lambda: ind.compute_vwap_sd_bands(closes, highs, lows, volumes, times),
        "AD":           lambda: ind.compute_ad_line(highs, lows, closes, volumes, times),
        "CMF":          lambda: ind.compute_cmf(highs, lows, closes, volumes, times),
        "MFI":          lambda: ind.compute_mfi(highs, lows, closes, volumes, times),
        "VOL_PROFILE":  lambda: ind.compute_volume_profile(closes, volumes),
        "CVD":          lambda: ind.compute_cvd(closes, volumes, times),
        "VROC":         lambda: ind.compute_vroc(volumes, times),
        "EOM":          lambda: ind.compute_ease_of_movement(highs, lows, volumes, times),
        "NVI_PVI":      lambda: ind.compute_nvi_pvi(closes, volumes, times),
        "FORCE":        lambda: ind.compute_force_index(closes, volumes, times),
        # TA-04 GARCH — handled via separate branch, sentinel value here
        "GARCH":        None,
    }


# Whitelist: all valid indicator names (prevents injection)
INDICATOR_WHITELIST: set[str] = {
    "SMA", "EMA", "DEMA", "TEMA", "WMA", "LWMA", "HMA", "VWMA",
    "GOLDEN_CROSS", "EMA_RIBBON",
    "RSI", "STOCH_RSI", "MACD", "STOCH", "WILLIAMS_R", "CCI",
    "ROC", "MOM", "DPO", "TRIX", "ULTOSC", "PPO", "KDJ", "CMO",
    "ADX", "AROON", "SAR", "SUPERTREND", "VORTEX", "ICHIMOKU", "MASS_INDEX",
    "BBANDS", "KC", "DC", "ATR", "HV", "HV_PARKINSON", "CHAIKIN_VOL", "ULCER",
    "OBV", "VWAP", "VWAP_BANDS", "AD", "CMF", "MFI", "VOL_PROFILE",
    "CVD", "VROC", "EOM", "NVI_PVI", "FORCE",
    "GARCH",
}

VALID_INTERMARKET_WINDOWS: set[int] = {30, 90, 252}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_ohlcv_rows(ticker: str, timeframe: str, db: AsyncSession) -> list:
    """Fetch up to 500 OHLCV rows ordered by time ascending."""
    result = await db.execute(
        select(OHLCV)
        .where(OHLCV.ticker == ticker, OHLCV.interval == timeframe)
        .order_by(OHLCV.time.asc())
        .limit(500)
    )
    return result.scalars().all()


def _rows_to_arrays(rows: list) -> dict:
    """Convert OHLCV model rows into numpy arrays dict."""
    times = np.array([
        row.time.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(row.time, "strftime") else str(row.time)
        for row in rows
    ])
    closes = np.array([float(r.close) if r.close is not None else np.nan for r in rows], dtype=float)
    highs = np.array([float(r.high) if r.high is not None else np.nan for r in rows], dtype=float)
    lows = np.array([float(r.low) if r.low is not None else np.nan for r in rows], dtype=float)
    opens = np.array([float(r.open) if r.open is not None else np.nan for r in rows], dtype=float)
    volumes = np.array([float(r.volume) if r.volume is not None else 0.0 for r in rows], dtype=float)
    return {
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "opens": opens,
        "volumes": volumes,
        "times": times,
    }


# ---------------------------------------------------------------------------
# Route 1: Standard indicator endpoint
# ---------------------------------------------------------------------------

@router.get("/indicators/{ticker}")
async def get_indicator(
    ticker: str,
    indicator: str = Query(..., description="Indicator name from the whitelist"),
    timeframe: str = Query(default="1d", description="OHLCV interval (1d, 1wk, 1h, 4h)"),
    period: Optional[int] = Query(default=None, description="Primary period parameter"),
    period2: Optional[int] = Query(default=None, description="Secondary period parameter"),
    period3: Optional[int] = Query(default=None, description="Tertiary period parameter"),
    db: AsyncSession = Depends(get_async_db),
):
    """Return computed indicator values for the given ticker and timeframe.

    Returns 400 for unknown indicator names (whitelist enforcement).
    Returns 422 if OHLCV data is unavailable.
    Cache TTL: 300 seconds (Redis key ta:{ticker}:{indicator}:{timeframe}:{period}).
    """
    indicator = indicator.upper()
    if indicator not in INDICATOR_WHITELIST:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown indicator '{indicator}'. Valid indicators: {sorted(INDICATOR_WHITELIST)}",
        )

    cache_key = f"ta:{ticker}:{indicator}:{timeframe}:{period}"
    redis_client = get_redis()
    cached_raw = redis_client.get(cache_key)
    if cached_raw:
        try:
            return json.loads(cached_raw)
        except (json.JSONDecodeError, TypeError):
            pass

    rows = await _fetch_ohlcv_rows(ticker, timeframe, db)
    if not rows:
        raise HTTPException(
            status_code=422,
            detail=f"No OHLCV data for {ticker}/{timeframe}. Ingest data first.",
        )

    arrays = _rows_to_arrays(rows)
    params = {}
    if period is not None:
        params["period"] = period
    if period2 is not None:
        params["period2"] = period2
    if period3 is not None:
        params["period3"] = period3

    # GARCH branch: uses garch.py, requires minimum bar check
    if indicator == "GARCH":
        data = compute_garch_volatility(arrays["closes"])
    else:
        dispatch = _build_dispatch(arrays, params)
        try:
            data = dispatch[indicator]()
        except Exception as exc:
            logger.error("Indicator %s computation error for %s/%s: %s", indicator, ticker, timeframe, exc)
            raise HTTPException(status_code=500, detail=f"Indicator computation failed: {str(exc)[:200]}")

    response = {
        "ticker": ticker,
        "indicator": indicator,
        "timeframe": timeframe,
        "data": data,
    }
    try:
        redis_client.set(cache_key, json.dumps(response, default=str), ex=300)
    except Exception:
        pass  # cache failure is non-fatal

    return response


# ---------------------------------------------------------------------------
# Route 2: Pivot points endpoint
# ---------------------------------------------------------------------------

@router.get("/pivots/{ticker}")
async def get_pivots(
    ticker: str,
    timeframe: str = Query(default="1d", description="Pivot timeframe (1d, 1wk)"),
    method: Optional[str] = Query(default=None, description="Pivot method: standard, woodie, camarilla, fibonacci, demark"),
    db: AsyncSession = Depends(get_async_db),
):
    """Return latest pre-computed pivot point levels for the ticker and timeframe.

    Returns all 5 methods if method param is omitted.
    Returns 404 if nightly pivot task has not yet run for this ticker/timeframe.
    No Redis cache — DB read is fast.
    """
    query = (
        select(PivotPoints)
        .where(PivotPoints.ticker == ticker, PivotPoints.timeframe == timeframe)
        .order_by(desc(PivotPoints.time))
    )
    if method:
        query = query.where(PivotPoints.method == method.lower())

    result = await db.execute(query.limit(10))
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No pivot point data for {ticker}/{timeframe}. Run the nightly pivot task first.",
        )

    # Deduplicate: keep one row per method (most recent time already selected by ORDER BY DESC)
    seen: set[str] = set()
    pivots = []
    for row in rows:
        if row.method not in seen:
            seen.add(row.method)
            pivots.append({
                "method": row.method,
                "time": row.time.isoformat() if hasattr(row.time, "isoformat") else str(row.time),
                "pp": row.pp,
                "r1": row.r1,
                "r2": row.r2,
                "r3": row.r3,
                "s1": row.s1,
                "s2": row.s2,
                "s3": row.s3,
            })

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "pivots": pivots,
    }


# ---------------------------------------------------------------------------
# Route 3: Intermarket correlations endpoint
# ---------------------------------------------------------------------------

@router.get("/intermarket/{ticker}")
async def get_intermarket(
    ticker: str,
    window: int = Query(default=90, description="Rolling window in days: 30, 90, or 252"),
    db: AsyncSession = Depends(get_async_db),
):
    """Return rolling correlations for intermarket pairs involving the given ticker.

    Valid window values: 30, 90, 252. Returns 400 for invalid window.
    Cache TTL: 3600 seconds.
    """
    if window not in VALID_INTERMARKET_WINDOWS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid window '{window}'. Must be one of: {sorted(VALID_INTERMARKET_WINDOWS)}",
        )

    cache_key = f"ta:intermarket:{ticker}:{window}"
    redis_client = get_redis()
    cached_raw = redis_client.get(cache_key)
    if cached_raw:
        try:
            return json.loads(cached_raw)
        except (json.JSONDecodeError, TypeError):
            pass

    # Collect all pairs involving this ticker
    relevant_pairs = [
        (a, b) for a, b in INTERMARKET_PAIRS
        if a == ticker or b == ticker
    ]

    if not relevant_pairs:
        raise HTTPException(
            status_code=404,
            detail=f"Ticker '{ticker}' is not part of any configured intermarket pair.",
        )

    correlations = []
    for ticker_a, ticker_b in relevant_pairs:
        counterpart = ticker_b if ticker_a == ticker else ticker_a

        rows_a = await _fetch_ohlcv_rows(ticker_a, "1d", db)
        rows_b = await _fetch_ohlcv_rows(ticker_b, "1d", db)

        if not rows_a or not rows_b:
            correlations.append({
                "pair": f"{ticker_a}/{ticker_b}",
                "window": window,
                "times": [],
                "values": [],
                "error": f"Missing OHLCV data for {ticker_a if not rows_a else ticker_b}",
            })
            continue

        # Align series on timestamps
        times_a = {
            (row.time.date() if hasattr(row.time, "date") else row.time): float(row.close)
            for row in rows_a if row.close is not None
        }
        times_b = {
            (row.time.date() if hasattr(row.time, "date") else row.time): float(row.close)
            for row in rows_b if row.close is not None
        }
        common_times = sorted(set(times_a.keys()) & set(times_b.keys()))

        if not common_times:
            correlations.append({
                "pair": f"{ticker_a}/{ticker_b}",
                "window": window,
                "times": [],
                "values": [],
                "error": "No overlapping timestamps between the two series",
            })
            continue

        series_a = np.array([times_a[t] for t in common_times], dtype=float)
        series_b = np.array([times_b[t] for t in common_times], dtype=float)
        times_arr = np.array([str(t) for t in common_times])

        result = compute_rolling_correlation(series_a, series_b, times_arr, window)
        correlations.append({
            "pair": f"{ticker_a}/{ticker_b}",
            "counterpart": counterpart,
            "window": result["window"],
            "times": result.get("times", []),
            "values": result.get("values", []),
            **({"error": result["error"]} if "error" in result else {}),
        })

    response = {
        "ticker": ticker,
        "window": window,
        "correlations": correlations,
    }
    try:
        redis_client.set(cache_key, json.dumps(response, default=str), ex=3600)
    except Exception:
        pass  # cache failure is non-fatal

    return response


# ---------------------------------------------------------------------------
# Route 4: Candlestick pattern detections (current bar)
# ---------------------------------------------------------------------------

@router.get("/patterns/{ticker}")
async def get_patterns(
    ticker: str,
    timeframe: str = Query(default="1d", description="OHLCV interval (1d, 1wk, 1h, 4h)"),
    db: AsyncSession = Depends(get_async_db),
):
    """Return candlestick patterns active on the most recent bar for the given ticker.

    Runs all 61 TA-Lib CDL* functions on the last ~200 bars.
    Fetches pre-computed stats (win_rate, p_value) from ta_pattern_stats for each active pattern.
    Returns only patterns where the last bar signal != 0.
    Cache TTL: 300 seconds.
    """
    cache_key = f"ta:patterns:{ticker}:{timeframe}"
    redis_client = get_redis()
    cached_raw = redis_client.get(cache_key)
    if cached_raw:
        try:
            return json.loads(cached_raw)
        except (json.JSONDecodeError, TypeError):
            pass

    rows = await _fetch_ohlcv_rows(ticker, timeframe, db)
    if not rows:
        raise HTTPException(
            status_code=422,
            detail=f"No OHLCV data for {ticker}/{timeframe}. Ingest data first.",
        )

    arrays = _rows_to_arrays(rows)

    # Import lazily to avoid circular import and keep module load fast
    from analysis.candlestick_patterns import detect_all_patterns
    all_signals = detect_all_patterns(
        arrays["opens"], arrays["highs"], arrays["lows"], arrays["closes"]
    )

    # Only patterns active on the LAST bar
    active_pattern_names = [
        name for name, sig_arr in all_signals.items()
        if len(sig_arr) > 0 and sig_arr[-1] != 0
    ]
    last_signals = {name: int(all_signals[name][-1]) for name in active_pattern_names}

    # Determine last bar date for response
    last_bar_date = str(rows[-1].time.date()) if hasattr(rows[-1].time, "date") else str(rows[-1].time)

    # Fetch pre-computed stats from DB for each active pattern
    stats_map: dict[str, dict] = {}
    if active_pattern_names:
        from sqlalchemy import text
        result = await db.execute(
            select(TAPatternStats)
            .where(
                TAPatternStats.ticker == ticker,
                TAPatternStats.timeframe == timeframe,
                TAPatternStats.pattern_name.in_(active_pattern_names),
            )
            .order_by(desc(TAPatternStats.time))
        )
        stat_rows = result.scalars().all()
        # Keep only the most recent stat per pattern
        for sr in stat_rows:
            if sr.pattern_name not in stats_map:
                stats_map[sr.pattern_name] = {
                    "win_rate": sr.win_rate,
                    "p_value": sr.p_value,
                    "n_occurrences": sr.n_occurrences,
                    "is_bullish": sr.is_bullish,
                }

    patterns = []
    for name in active_pattern_names:
        stat = stats_map.get(name, {})
        patterns.append({
            "name": name,
            "signal": last_signals[name],
            "win_rate": stat.get("win_rate"),
            "p_value": stat.get("p_value"),
            "n_occurrences": stat.get("n_occurrences"),
            "is_bullish": stat.get("is_bullish", last_signals[name] == 100),
        })

    response = {
        "ticker": ticker,
        "timeframe": timeframe,
        "bar_date": last_bar_date,
        "patterns": patterns,
    }
    try:
        redis_client.set(cache_key, json.dumps(response, default=str), ex=300)
    except Exception:
        pass  # cache failure is non-fatal

    return response


# ---------------------------------------------------------------------------
# Route 5: Pattern stats (historical win rates)
# ---------------------------------------------------------------------------

@router.get("/pattern-stats/{ticker}")
async def get_pattern_stats(
    ticker: str,
    timeframe: str = Query(default="1d", description="OHLCV interval (1d, 1wk)"),
    pattern: Optional[str] = Query(default=None, description="Filter by pattern name (returns all if omitted)"),
    db: AsyncSession = Depends(get_async_db),
):
    """Return pre-computed win rates and p-values for candlestick patterns.

    Queries ta_pattern_stats for most recent nightly run for this ticker/timeframe.
    Optionally filter by pattern name.
    Returns all patterns with win_rate, p_value, n_occurrences.
    """
    query = (
        select(TAPatternStats)
        .where(
            TAPatternStats.ticker == ticker,
            TAPatternStats.timeframe == timeframe,
        )
        .order_by(desc(TAPatternStats.time))
    )
    if pattern:
        query = query.where(TAPatternStats.pattern_name == pattern.upper())

    result = await db.execute(query.limit(200))
    stat_rows = result.scalars().all()

    if not stat_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No pattern stats for {ticker}/{timeframe}. Run the nightly candlestick stats task first.",
        )

    # Deduplicate: keep one row per pattern (most recent time already sorted by ORDER BY DESC)
    seen: set[str] = set()
    patterns_out = []
    for row in stat_rows:
        if row.pattern_name not in seen:
            seen.add(row.pattern_name)
            patterns_out.append({
                "pattern_name": row.pattern_name,
                "is_bullish": row.is_bullish,
                "n_occurrences": row.n_occurrences,
                "n_wins": row.n_wins,
                "win_rate": row.win_rate,
                "p_value": row.p_value,
                "computed_at": row.time.isoformat() if hasattr(row.time, "isoformat") else str(row.time),
            })

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "patterns": patterns_out,
    }
