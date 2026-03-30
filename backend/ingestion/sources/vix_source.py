"""VIX term structure source — fetches spot VIX, VIX3M, VIX6M via yfinance fast_info.

D-18: tickers ^VIX (spot), ^VIX3M (3-month), ^VIX6M (6-month).
D-20: Regime thresholds: < 15 = LOW_VOL, 15–20 = NORMAL, 20–30 = ELEVATED, > 30 = CRISIS.
D-19: contango bool = VIX3M > spot_vix.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

logger = logging.getLogger(__name__)

VIX_TICKERS = ["^VIX", "^VIX3M", "^VIX6M"]
HISTORY_DEPTH_THRESHOLD = 252  # ~1 trading year


def _classify_regime(spot: float) -> str:
    """D-20 regime classifier."""
    if spot < 15:
        return "LOW_VOL"
    elif spot < 20:
        return "NORMAL"
    elif spot < 30:
        return "ELEVATED"
    else:
        return "CRISIS"


def fetch_vix_term_structure(history_row_count: int = 0) -> dict:
    """Fetch current VIX spot + VIX3M + VIX6M from yfinance fast_info.

    Args:
        history_row_count: number of existing vix_term_structure rows in DB.
            Used to compute history_depth_ok flag for frontend badge.

    Returns dict:
        {
            "time": datetime (UTC now),
            "spot_vix": float,
            "vix_3m": float | None,
            "vix_6m": float | None,
            "contango": bool | None,  # None if vix_3m unavailable
            "regime": str,
            "history_depth_ok": bool,  # True if history_row_count >= 252
        }
    """
    try:
        vix = yf.Ticker("^VIX")
        spot_vix = vix.fast_info.get("last_price") or vix.fast_info.get("lastPrice")
        if spot_vix is None:
            # Fallback: get last close from history
            hist = vix.history(period="1d")
            spot_vix = float(hist["Close"].iloc[-1]) if not hist.empty else None
        if spot_vix is None:
            raise ValueError("Could not retrieve spot VIX price")
        spot_vix = float(spot_vix)
    except Exception as e:
        logger.error(f"vix_source: failed to fetch spot VIX: {e}")
        raise

    vix_3m: Optional[float] = None
    vix_6m: Optional[float] = None

    try:
        t3m = yf.Ticker("^VIX3M")
        v3m = t3m.fast_info.get("last_price") or t3m.fast_info.get("lastPrice")
        if v3m is None:
            hist3m = t3m.history(period="1d")
            v3m = float(hist3m["Close"].iloc[-1]) if not hist3m.empty else None
        vix_3m = float(v3m) if v3m is not None else None
    except Exception as e:
        logger.warning(f"vix_source: VIX3M unavailable: {e}")

    try:
        t6m = yf.Ticker("^VIX6M")
        v6m = t6m.fast_info.get("last_price") or t6m.fast_info.get("lastPrice")
        if v6m is None:
            hist6m = t6m.history(period="1d")
            v6m = float(hist6m["Close"].iloc[-1]) if not hist6m.empty else None
        vix_6m = float(v6m) if v6m is not None else None
    except Exception as e:
        logger.warning(f"vix_source: VIX6M unavailable: {e}")

    contango = (vix_3m > spot_vix) if vix_3m is not None else None
    regime = _classify_regime(spot_vix)
    history_depth_ok = history_row_count >= HISTORY_DEPTH_THRESHOLD

    return {
        "time": datetime.now(timezone.utc),
        "spot_vix": spot_vix,
        "vix_3m": vix_3m,
        "vix_6m": vix_6m,
        "contango": contango,
        "regime": regime,
        "history_depth_ok": history_depth_ok,
    }
