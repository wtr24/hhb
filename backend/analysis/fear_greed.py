"""Fear & Greed composite index computation service.

D-14: Six equal-weighted components, each normalised to 0–100 via percentile rank
over a rolling 1-year window. Composite = equal-weighted average.

D-15: Colour bands:
  0–25   = EXTREME FEAR (red)
  25–45  = FEAR (orange)
  45–55  = NEUTRAL (amber)
  55–75  = GREED (green)
  75–100 = EXTREME GREED (bright-green)

All DB queries use the synchronous SessionLocal pattern (same as pivot_points task).
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _percentile_rank(series: list[float], current: float) -> float:
    """Percentile rank of current value within series (0–100).
    Returns 50.0 if series is empty (neutral default).
    """
    if not series:
        return 50.0
    arr = np.array(series, dtype=float)
    return float(np.sum(arr <= current) / len(arr) * 100)


def _score_to_band(score: float) -> str:
    """Map composite score to Fear & Greed band label."""
    if score < 25:
        return "EXTREME FEAR"
    elif score < 45:
        return "FEAR"
    elif score < 55:
        return "NEUTRAL"
    elif score < 75:
        return "GREED"
    else:
        return "EXTREME GREED"


def compute_fear_greed_composite(session: Session) -> dict:
    """Compute the Fear & Greed composite score from DB data.

    Queries the last 365 days of each component series from TimescaleDB.
    Returns:
        {
            "score": float (0–100),
            "band": str,
            "components": [
                {"name": str, "score": float, "source": str},
                ...
            ],
            "computed_at": str (ISO datetime),
        }
    """
    from models.macro_series import MacroSeries
    from models.vix_term_structure import VixTermStructure
    from models.ohlcv import OHLCV

    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    components = []

    # --- Component 1: VIX percentile ---
    # Higher VIX = more fear → invert so high VIX = low score
    vix_rows = (
        session.query(VixTermStructure)
        .filter(VixTermStructure.time >= cutoff)
        .order_by(VixTermStructure.time.asc())
        .all()
    )
    if vix_rows:
        vix_values = [float(r.spot_vix) for r in vix_rows if r.spot_vix is not None]
        current_vix = vix_values[-1] if vix_values else None
        if current_vix is not None:
            raw_pct = _percentile_rank(vix_values, current_vix)
            # Invert: high VIX percentile = more fear = lower score
            vix_score = 100 - raw_pct
            components.append({"name": "VIX pctile", "score": round(vix_score, 1), "source": "^VIX"})
        else:
            logger.warning("fear_greed: VIX component unavailable")
    else:
        logger.warning("fear_greed: no VIX term structure rows within 365 days")

    # --- Component 2: Put/Call ratio ---
    # Higher P/C ratio = more fear → invert
    pcr_rows = (
        session.query(MacroSeries)
        .filter(MacroSeries.series_id == "CBOE_PCR", MacroSeries.time >= cutoff)
        .order_by(MacroSeries.time.asc())
        .all()
    )
    if pcr_rows:
        pcr_values = [float(r.value) for r in pcr_rows if r.value is not None]
        current_pcr = pcr_values[-1] if pcr_values else None
        if current_pcr is not None:
            raw_pct = _percentile_rank(pcr_values, current_pcr)
            pcr_score = 100 - raw_pct
            components.append({"name": "Put/Call", "score": round(pcr_score, 1), "source": "CBOE"})
        else:
            logger.warning("fear_greed: PCR component unavailable")

    # --- Component 3: Market breadth ---
    # Higher % above 200 SMA = more greed → use directly
    breadth_rows = (
        session.query(MacroSeries)
        .filter(MacroSeries.series_id == "BREADTH_PCT200", MacroSeries.time >= cutoff)
        .order_by(MacroSeries.time.asc())
        .all()
    )
    if breadth_rows:
        breadth_values = [float(r.value) for r in breadth_rows if r.value is not None]
        current_breadth = breadth_values[-1] if breadth_values else None
        if current_breadth is not None:
            breadth_score = _percentile_rank(breadth_values, current_breadth)
            components.append({"name": "Breadth", "score": round(breadth_score, 1), "source": "Computed"})
        else:
            logger.warning("fear_greed: breadth component unavailable")
    else:
        logger.warning("fear_greed: no BREADTH_PCT200 rows within 365 days — PENDING FIRST RUN")

    # --- Component 4: Junk bond spread ---
    # Higher HY spread = more fear → invert
    hy_rows = (
        session.query(MacroSeries)
        .filter(MacroSeries.series_id == "BAMLH0A0HYM2", MacroSeries.time >= cutoff)
        .order_by(MacroSeries.time.asc())
        .all()
    )
    if hy_rows:
        hy_values = [float(r.value) for r in hy_rows if r.value is not None]
        current_hy = hy_values[-1] if hy_values else None
        if current_hy is not None:
            raw_pct = _percentile_rank(hy_values, current_hy)
            hy_score = 100 - raw_pct
            components.append({"name": "HY Spread", "score": round(hy_score, 1), "source": "FRED"})
        else:
            logger.warning("fear_greed: HY spread component unavailable")

    # --- Component 5: SPX momentum (125-day ROC) ---
    # Higher 125d return = more greed → use directly
    spx_rows = (
        session.query(OHLCV)
        .filter(OHLCV.ticker == "^GSPC", OHLCV.interval == "1d")
        .order_by(OHLCV.time.desc())
        .limit(130)
        .all()
    )
    if len(spx_rows) >= 126:
        spx_closes = [float(r.close) for r in reversed(spx_rows)]
        roc_125 = (spx_closes[-1] / spx_closes[-126] - 1) * 100
        # Compute 125d ROC series over all available history for percentile rank
        all_spx = (
            session.query(OHLCV)
            .filter(OHLCV.ticker == "^GSPC", OHLCV.interval == "1d", OHLCV.time >= cutoff)
            .order_by(OHLCV.time.asc())
            .all()
        )
        if len(all_spx) >= 126:
            all_closes = [float(r.close) for r in all_spx]
            roc_series = [
                (all_closes[i] / all_closes[i - 125] - 1) * 100
                for i in range(125, len(all_closes))
            ]
            spx_score = _percentile_rank(roc_series, roc_125)
            components.append({"name": "SPX Mom", "score": round(spx_score, 1), "source": "^GSPC"})

    # --- Component 6: Safe haven demand (trade-weighted USD) ---
    # Higher USD vs 20-day SMA = more fear → higher USD above SMA = higher fear = lower greed
    usd_rows = (
        session.query(MacroSeries)
        .filter(MacroSeries.series_id == "DTWEXBGS", MacroSeries.time >= cutoff)
        .order_by(MacroSeries.time.asc())
        .all()
    )
    if len(usd_rows) >= 20:
        usd_values = [float(r.value) for r in usd_rows if r.value is not None]
        if len(usd_values) >= 20:
            current_usd = usd_values[-1]
            sma_20 = np.mean(usd_values[-20:])
            # positive deviation = USD above SMA = safe haven demand = more fear
            usd_deviation = (current_usd / sma_20 - 1) * 100
            # Build deviation series for percentile rank
            deviations = [
                (usd_values[i] / np.mean(usd_values[max(0, i - 20):i]) - 1) * 100
                for i in range(20, len(usd_values))
            ]
            raw_pct = _percentile_rank(deviations, usd_deviation)
            usd_score = 100 - raw_pct
            components.append({"name": "Safe Haven", "score": round(usd_score, 1), "source": "FRED"})

    if not components:
        logger.warning("fear_greed: no components available, returning neutral 50")
        return {
            "score": 50.0,
            "band": "NEUTRAL",
            "components": [],
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    composite = float(np.mean([c["score"] for c in components]))
    band = _score_to_band(composite)

    return {
        "score": round(composite, 1),
        "band": band,
        "components": components,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
