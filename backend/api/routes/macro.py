import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_async_db
from ..redis_client import get_redis
from cache.ttl import cache_get, cache_set
from models.macro_series import MacroSeries
from models.gilt_curve import GiltCurve
from models.vix_term_structure import VixTermStructure
from models.ohlcv import OHLCV
from ingestion.config import FRED_SERIES_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["macro"])


@router.get("/macro/curves")
async def get_macro_curves(db: AsyncSession = Depends(get_async_db)):
    """MACRO-01 through MACRO-06: US + UK yield curves, spreads, shape, real yield."""
    redis_client = get_redis()
    cached = cache_get(redis_client, "macro_curves:latest")
    if cached:
        return cached

    cutoff_90d = datetime.now(timezone.utc) - timedelta(days=90)
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)
    cutoff_1y = datetime.now(timezone.utc) - timedelta(days=365)

    # US curve — latest row from yield_curve table
    from models.yield_curve import YieldCurve
    us_result = await db.execute(
        select(YieldCurve).order_by(desc(YieldCurve.time)).limit(1)
    )
    us_latest = us_result.scalars().first()
    us_curve = []
    tenor_map = [
        ("1M", "bc_1month"), ("3M", "bc_3month"), ("6M", "bc_6month"),
        ("1Y", "bc_1year"), ("2Y", "bc_2year"), ("3Y", "bc_3year"),
        ("5Y", "bc_5year"), ("7Y", "bc_7year"), ("10Y", "bc_10year"),
        ("20Y", "bc_20year"), ("30Y", "bc_30year"),
    ]
    if us_latest:
        for label, field in tenor_map:
            val = getattr(us_latest, field, None)
            if val is not None:
                us_curve.append({"tenor": label, "yield": float(val)})

    # UK gilt curve — latest row from gilt_curve table
    uk_result = await db.execute(
        select(GiltCurve).order_by(desc(GiltCurve.time)).limit(1)
    )
    uk_latest = uk_result.scalars().first()
    uk_curve = []
    gilt_tenors = [
        ("6M", "tenor_6m"), ("1Y", "tenor_1y"), ("2Y", "tenor_2y"),
        ("3Y", "tenor_3y"), ("5Y", "tenor_5y"), ("7Y", "tenor_7y"),
        ("10Y", "tenor_10y"), ("15Y", "tenor_15y"), ("20Y", "tenor_20y"),
        ("25Y", "tenor_25y"), ("30Y", "tenor_30y"),
    ]
    if uk_latest:
        for label, field in gilt_tenors:
            val = getattr(uk_latest, field, None)
            if val is not None:
                uk_curve.append({"tenor": label, "yield": float(val)})

    # Historical overlays: +1M and +1Y ago
    def _curve_from_yield_curve_row(row, tm):
        result = []
        for label, field in tm:
            val = getattr(row, field, None)
            if val is not None:
                result.append({"tenor": label, "yield": float(val)})
        return result

    us_1m_result = await db.execute(
        select(YieldCurve)
        .where(YieldCurve.time <= cutoff_30d)
        .order_by(desc(YieldCurve.time))
        .limit(1)
    )
    us_1m_row = us_1m_result.scalars().first()
    us_curve_1m_ago = _curve_from_yield_curve_row(us_1m_row, tenor_map) if us_1m_row else []

    us_1y_result = await db.execute(
        select(YieldCurve)
        .where(YieldCurve.time <= cutoff_1y)
        .order_by(desc(YieldCurve.time))
        .limit(1)
    )
    us_1y_row = us_1y_result.scalars().first()
    us_curve_1y_ago = _curve_from_yield_curve_row(us_1y_row, tenor_map) if us_1y_row else []

    uk_1m_result = await db.execute(
        select(GiltCurve)
        .where(GiltCurve.time <= cutoff_30d)
        .order_by(desc(GiltCurve.time))
        .limit(1)
    )
    uk_1m_row = uk_1m_result.scalars().first()
    uk_curve_1m_ago = []
    if uk_1m_row:
        for label, field in gilt_tenors:
            val = getattr(uk_1m_row, field, None)
            if val is not None:
                uk_curve_1m_ago.append({"tenor": label, "yield": float(val)})

    uk_1y_result = await db.execute(
        select(GiltCurve)
        .where(GiltCurve.time <= cutoff_1y)
        .order_by(desc(GiltCurve.time))
        .limit(1)
    )
    uk_1y_row = uk_1y_result.scalars().first()
    uk_curve_1y_ago = []
    if uk_1y_row:
        for label, field in gilt_tenors:
            val = getattr(uk_1y_row, field, None)
            if val is not None:
                uk_curve_1y_ago.append({"tenor": label, "yield": float(val)})

    # Spreads 2s10s and 5s30s — last 90 days from yield_curve table
    # 2s10s = 2Y minus 10Y (positive = inverted, i.e. 2Y > 10Y)
    spreads_result = await db.execute(
        select(YieldCurve)
        .where(YieldCurve.time >= cutoff_90d)
        .order_by(asc(YieldCurve.time))
    )
    spread_rows = spreads_result.scalars().all()

    spreads_2s10s = []
    spreads_5s30s = []
    for row in spread_rows:
        if row.bc_2year is not None and row.bc_10year is not None:
            spreads_2s10s.append({
                "date": row.time.isoformat(),
                "value": round(float(row.bc_2year) - float(row.bc_10year), 4),
            })
        if row.bc_5year is not None and row.bc_30year is not None:
            spreads_5s30s.append({
                "date": row.time.isoformat(),
                "value": round(float(row.bc_5year) - float(row.bc_30year), 4),
            })

    # Curve shape classifier from current 2s10s spread
    curve_shape = "NORMAL"
    curve_shape_context = ""
    if us_latest:
        s2 = float(us_latest.bc_2year or 0)
        s5 = float(us_latest.bc_5year or 0)
        s10 = float(us_latest.bc_10year or 0)
        spread_2s10s = s2 - s10
        if spread_2s10s > 0.05:
            curve_shape = "INVERTED"
        elif abs(spread_2s10s) <= 0.05:
            curve_shape = "FLAT"
        elif s5 > s2 and s5 > s10:
            curve_shape = "HUMPED"
        else:
            curve_shape = "NORMAL"

        # Count consecutive months in current shape
        if spreads_2s10s:
            months_in_shape = 0
            current_inverted = spread_2s10s > 0.05
            for sp in reversed(spreads_2s10s):
                is_inverted = sp["value"] > 0.05
                if is_inverted == current_inverted:
                    months_in_shape += 1
                else:
                    break
            months_count = max(1, months_in_shape // 21)  # ~21 trading days per month
            if curve_shape == "INVERTED":
                curve_shape_context = f"Inverted for {months_count} month{'s' if months_count != 1 else ''}"
            elif curve_shape == "FLAT":
                curve_shape_context = f"Flat for {months_count} month{'s' if months_count != 1 else ''}"

    # Real yield = GS10 minus T10YIE (TIPS 10Y breakeven) — last 90 days
    gs10_result = await db.execute(
        select(MacroSeries)
        .where(MacroSeries.series_id == "GS10", MacroSeries.time >= cutoff_90d)
        .order_by(asc(MacroSeries.time))
    )
    gs10_rows = {row.time.date(): float(row.value) for row in gs10_result.scalars().all() if row.value}

    tips_result = await db.execute(
        select(MacroSeries)
        .where(MacroSeries.series_id == "T10YIE", MacroSeries.time >= cutoff_90d)
        .order_by(asc(MacroSeries.time))
    )
    tips_rows = {row.time.date(): float(row.value) for row in tips_result.scalars().all() if row.value}

    real_yield = []
    for d in sorted(gs10_rows.keys()):
        if d in tips_rows:
            real_yield.append({
                "date": d.isoformat(),
                "value": round(gs10_rows[d] - tips_rows[d], 4),
            })

    response = {
        "us_curve": us_curve,
        "uk_curve": uk_curve,
        "us_curve_1m_ago": us_curve_1m_ago,
        "us_curve_1y_ago": us_curve_1y_ago,
        "uk_curve_1m_ago": uk_curve_1m_ago,
        "uk_curve_1y_ago": uk_curve_1y_ago,
        "spreads_2s10s": spreads_2s10s,
        "spreads_5s30s": spreads_5s30s,
        "curve_shape": curve_shape,
        "curve_shape_context": curve_shape_context,
        "real_yield": real_yield,
        "stale": us_latest is None and uk_latest is None,
    }
    cache_set(redis_client, "macro_curves:latest", response, "macro_curves")
    return response


@router.get("/macro/indicators")
async def get_macro_indicators(db: AsyncSession = Depends(get_async_db)):
    """MACRO-07 through MACRO-10: CPI, Core CPI, PCE, GDP, Unemployment, Policy Rates."""
    redis_client = get_redis()
    cached = cache_get(redis_client, "macro_indicators:latest")
    if cached:
        return cached

    def _series_to_history(rows, limit=24):
        """Convert MacroSeries rows (newest first) to [value...] list (newest last)."""
        vals = [float(r.value) for r in rows[:limit] if r.value is not None]
        return list(reversed(vals))

    def _mom(history):
        if len(history) < 2:
            return None
        return round(history[-1] - history[-2], 4)

    def _yoy(history):
        if len(history) < 13:
            return None
        return round(history[-1] - history[-13], 4)

    async def _fetch(series_id, limit=36):
        r = await db.execute(
            select(MacroSeries)
            .where(MacroSeries.series_id == series_id)
            .order_by(desc(MacroSeries.time))
            .limit(limit)
        )
        return r.scalars().all()

    # CPI
    us_cpi = await _fetch("CPIAUCSL")
    uk_cpi = await _fetch("ONS_CPI")
    cpi_hist_us = _series_to_history(us_cpi)
    cpi_hist_uk = _series_to_history(uk_cpi)

    # Core CPI
    us_core = await _fetch("CPILFESL")
    core_hist_us = _series_to_history(us_core)

    # PCE
    us_pce = await _fetch("PCEPI")
    pce_hist_us = _series_to_history(us_pce)

    # GDP
    us_gdp = await _fetch("GDP")
    uk_gdp = await _fetch("ONS_GDP")
    eu_gdp = await _fetch("ECB_GDP")
    gdp_hist_us = _series_to_history(us_gdp)
    gdp_hist_uk = _series_to_history(uk_gdp)
    gdp_hist_eu = _series_to_history(eu_gdp)

    # Unemployment
    us_unemp = await _fetch("UNRATE")
    uk_unemp = await _fetch("ONS_UNEMPLOYMENT")
    unemp_hist_us = _series_to_history(us_unemp)
    unemp_hist_uk = _series_to_history(uk_unemp)

    # Policy Rates
    fed = await _fetch("FEDFUNDS")
    boe = await _fetch("BOE_RATE")
    # ECB rate sourced from FRED DFF equivalent: use ECBDFR if available, else placeholder
    ecb_rate = await _fetch("ECB_DFR")
    fed_hist = _series_to_history(fed)
    boe_hist = _series_to_history(boe)
    ecb_hist = _series_to_history(ecb_rate)

    response = {
        "cpi": {
            "us": cpi_hist_us[-1] if cpi_hist_us else None,
            "uk": cpi_hist_uk[-1] if cpi_hist_uk else None,
            "history_us": cpi_hist_us,
            "history_uk": cpi_hist_uk,
            "mom": _mom(cpi_hist_us),
            "yoy": _yoy(cpi_hist_us),
        },
        "core_cpi": {
            "us": core_hist_us[-1] if core_hist_us else None,
            "history_us": core_hist_us,
            "mom": _mom(core_hist_us),
            "yoy": _yoy(core_hist_us),
        },
        "pce": {
            "us": pce_hist_us[-1] if pce_hist_us else None,
            "history_us": pce_hist_us,
            "mom": _mom(pce_hist_us),
            "yoy": _yoy(pce_hist_us),
        },
        "gdp": {
            "us": gdp_hist_us[-1] if gdp_hist_us else None,
            "uk": gdp_hist_uk[-1] if gdp_hist_uk else None,
            "eu": gdp_hist_eu[-1] if gdp_hist_eu else None,
            "history_us": gdp_hist_us,
            "history_uk": gdp_hist_uk,
            "history_eu": gdp_hist_eu,
            "qoq": _mom(gdp_hist_us),
        },
        "unemployment": {
            "us": unemp_hist_us[-1] if unemp_hist_us else None,
            "uk": unemp_hist_uk[-1] if unemp_hist_uk else None,
            "history_us": unemp_hist_us,
            "history_uk": unemp_hist_uk,
            "mom": _mom(unemp_hist_us),
        },
        "policy_rates": {
            "fed": fed_hist[-1] if fed_hist else None,
            "boe": boe_hist[-1] if boe_hist else None,
            "ecb": ecb_hist[-1] if ecb_hist else None,
            "history_fed": fed_hist,
            "history_boe": boe_hist,
            "history_ecb": ecb_hist,
        },
        "stale": not any([us_cpi, uk_cpi, us_gdp]),
    }
    cache_set(redis_client, "macro_indicators:latest", response, "macro_indicators")
    return response


@router.get("/macro/risk")
async def get_macro_risk(db: AsyncSession = Depends(get_async_db)):
    """MACRO-11, MACRO-12: VIX term structure, regime, percentile, put/call ratio."""
    redis_client = get_redis()
    cached = cache_get(redis_client, "macro_risk:latest")
    if cached:
        return cached

    cutoff_90d = datetime.now(timezone.utc) - timedelta(days=90)
    cutoff_1y = datetime.now(timezone.utc) - timedelta(days=365)
    cutoff_5y = datetime.now(timezone.utc) - timedelta(days=1825)

    # VIX term structure — 90 days
    vix_result = await db.execute(
        select(VixTermStructure)
        .where(VixTermStructure.time >= cutoff_90d)
        .order_by(asc(VixTermStructure.time))
    )
    vix_rows = vix_result.scalars().all()

    vix_history = [
        {
            "date": r.time.isoformat(),
            "spot": float(r.spot_vix),
            "vix3m": float(r.vix_3m) if r.vix_3m is not None else None,
            "vix6m": float(r.vix_6m) if r.vix_6m is not None else None,
        }
        for r in vix_rows
    ]

    latest_vix = vix_rows[-1] if vix_rows else None
    contango = bool(latest_vix.contango) if latest_vix and latest_vix.contango is not None else None
    regime = latest_vix.regime if latest_vix else "NORMAL"

    # history_depth_ok: True if >= 252 rows in vix_term_structure total
    count_result = await db.execute(select(func.count()).select_from(VixTermStructure))
    total_vix_rows = count_result.scalar() or 0
    history_depth_ok = total_vix_rows >= 252

    # VIX percentile ranks — 1Y and 5Y windows
    vix_1y_result = await db.execute(
        select(VixTermStructure.spot_vix)
        .where(VixTermStructure.time >= cutoff_1y)
    )
    vix_1y_values = [float(r) for r in vix_1y_result.scalars().all() if r is not None]

    vix_5y_result = await db.execute(
        select(VixTermStructure.spot_vix)
        .where(VixTermStructure.time >= cutoff_5y)
    )
    vix_5y_values = [float(r) for r in vix_5y_result.scalars().all() if r is not None]

    current_spot = float(latest_vix.spot_vix) if latest_vix else None
    percentile_1y = None
    percentile_5y = None
    if current_spot is not None:
        import numpy as np
        if vix_1y_values:
            percentile_1y = round(float(np.sum(np.array(vix_1y_values) <= current_spot) / len(vix_1y_values) * 100), 1)
        if vix_5y_values:
            percentile_5y = round(float(np.sum(np.array(vix_5y_values) <= current_spot) / len(vix_5y_values) * 100), 1)

    # Put/call ratio — last 90 days
    pcr_result = await db.execute(
        select(MacroSeries)
        .where(MacroSeries.series_id == "CBOE_PCR", MacroSeries.time >= cutoff_90d)
        .order_by(asc(MacroSeries.time))
    )
    pcr_rows = pcr_result.scalars().all()
    put_call_ratio = [
        {"date": r.time.isoformat(), "value": float(r.value)}
        for r in pcr_rows if r.value is not None
    ]

    response = {
        "vix_term_structure": vix_history,
        "history_depth_ok": history_depth_ok,
        "contango": contango,
        "regime": regime,
        "percentile_1y": percentile_1y,
        "percentile_5y": percentile_5y,
        "put_call_ratio": put_call_ratio,
        "stale": latest_vix is None,
    }
    cache_set(redis_client, "macro_risk:latest", response, "macro_risk")
    return response


@router.get("/macro/sentiment")
async def get_macro_sentiment(db: AsyncSession = Depends(get_async_db)):
    """MACRO-13, MACRO-14: Fear & Greed composite + seasonality."""
    redis_client = get_redis()
    cached = cache_get(redis_client, "macro_sentiment:latest")
    if cached:
        return cached

    # Fear & Greed — use synchronous SessionLocal (fear_greed.py uses sync session)
    from analysis.fear_greed import compute_fear_greed_composite
    from api.database import SessionLocal

    try:
        with SessionLocal() as sync_session:
            fear_greed = compute_fear_greed_composite(sync_session)
    except Exception as e:
        logger.error(f"fear_greed computation failed: {e}")
        fear_greed = {"score": 50.0, "band": "NEUTRAL", "components": [], "computed_at": None}

    # Seasonality data — SPX monthly average returns (10Y of OHLCV history)
    cutoff_10y = datetime.now(timezone.utc) - timedelta(days=3650)
    spx_result = await db.execute(
        select(OHLCV)
        .where(OHLCV.ticker == "^GSPC", OHLCV.interval == "1d", OHLCV.time >= cutoff_10y)
        .order_by(asc(OHLCV.time))
    )
    spx_rows = spx_result.scalars().all()

    # Compute monthly average returns
    monthly_returns: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    prev_close = None
    for row in spx_rows:
        close = float(row.close)
        if prev_close is not None and prev_close > 0:
            daily_ret = (close / prev_close - 1) * 100
            monthly_returns[row.time.month].append(daily_ret)
        prev_close = close

    month_labels = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    seasonality_data = []
    for m in range(1, 13):
        returns = monthly_returns[m]
        avg = round(sum(returns) / len(returns), 4) if returns else 0.0
        seasonality_data.append({"month": month_labels[m - 1], "avg_return": avg})

    response = {
        "fear_greed": fear_greed,
        "seasonality": {
            "ticker": "^GSPC",
            "monthly_avg": seasonality_data,
        },
        "stale": False,
    }
    cache_set(redis_client, "macro_sentiment:latest", response, "macro_sentiment")
    return response


@router.get("/macro/{series}")
async def get_macro_series(series: str, db: AsyncSession = Depends(get_async_db)):
    """Return macro time series per D-14/D-15.
    Uses friendly name (e.g. 'cpi') mapped to FRED ID (e.g. 'CPIAUCSL').
    Returns last 24 months of observations by default.
    """
    if series not in FRED_SERIES_MAP:
        return JSONResponse(status_code=404, content={
            "error": f"Unknown series '{series}'. Available: {list(FRED_SERIES_MAP.keys())}"
        })

    fred_id = FRED_SERIES_MAP[series]
    redis_client = get_redis()

    # Check cache first
    cached = cache_get(redis_client, f"macro_series:{series}")
    if cached:
        return cached

    # Query TimescaleDB for last 24 months (~730 days)
    result = await db.execute(
        select(MacroSeries)
        .where(MacroSeries.series_id == fred_id)
        .order_by(desc(MacroSeries.time))
        .limit(300)
    )
    rows = result.scalars().all()

    if not rows:
        return JSONResponse(status_code=404, content={
            "error": f"No data for series '{series}' ({fred_id}). Run ingestion first."
        })

    observations = [
        {"date": row.time.isoformat(), "value": float(row.value) if row.value else None}
        for row in rows
    ]

    response = {
        "series": series,
        "fred_id": fred_id,
        "observations": observations,
        "stale": False,
        "last_updated": rows[0].time.isoformat() if rows else None,
    }

    cache_set(redis_client, f"macro_series:{series}", response, "macro")
    return response
