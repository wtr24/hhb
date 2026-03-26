import requests
import os
import logging

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


def fetch_fred_series(series_id: str, limit: int = 300) -> list[dict]:
    """Fetch FRED observations for a given series_id.
    Returns list of dicts with 'date' and 'value' keys.
    limit=300 covers ~24 months of monthly data with buffer.
    """
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        raise ValueError("FRED_API_KEY environment variable not set")

    params = {
        "api_key": api_key,
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }

    r = requests.get(FRED_BASE, params=params, timeout=30)
    r.raise_for_status()

    observations = r.json().get("observations", [])
    # Filter out missing values (FRED uses "." for missing)
    return [
        {"date": obs["date"], "value": float(obs["value"])}
        for obs in observations
        if obs.get("value") and obs["value"] != "."
    ]
