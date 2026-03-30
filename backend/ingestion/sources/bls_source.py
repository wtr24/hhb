"""BLS (Bureau of Labor Statistics) API v2 source.

D-23: BLS API v2 POST endpoint. Free API key required — user must register at
https://www.bls.gov/developers/api_faqs.htm#register0

Env var: BLS_API_KEY (no default — warns if missing and skips ingestion).

Fetches: CES0000000001 = Total Nonfarm Payrolls, monthly change.
Stores: macro_series with series_id = "BLS_NFP".
"""
import logging
import os
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def fetch_bls_nfp(start_year: str = "2020") -> list[dict]:
    """Fetch BLS Non-Farm Payrolls total employment via API v2.

    Requires BLS_API_KEY environment variable. Returns empty list (with warning)
    if the key is not set — graceful degradation, not an error.

    Returns list of {"date": datetime (UTC), "value": float} dicts.
    """
    api_key = os.environ.get("BLS_API_KEY", "")
    if not api_key:
        logger.warning(
            "BLS_API_KEY not set — skipping BLS NFP ingestion. "
            "Register a free key at https://www.bls.gov/developers/api_faqs.htm#register0 "
            "and set BLS_API_KEY in your .env file."
        )
        return []

    end_year = str(datetime.now().year)
    payload = {
        "seriesid": ["CES0000000001"],
        "startyear": start_year,
        "endyear": end_year,
        "registrationkey": api_key,
    }
    response = requests.post(BLS_API_URL, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        msg = data.get("message", ["Unknown BLS API error"])[0]
        raise ValueError(f"BLS API error: {msg}")

    series_data = data.get("Results", {}).get("series", [])
    if not series_data:
        logger.warning("BLS API returned no series data")
        return []

    observations = series_data[0].get("data", [])
    rows = []
    for obs in observations:
        year = obs.get("year", "")
        period = obs.get("period", "")  # e.g. "M03" for March
        val_str = obs.get("value", "")
        if not year or not period.startswith("M") or val_str in ("", "-"):
            continue
        try:
            month = int(period[1:])
            row_date = datetime(int(year), month, 1, tzinfo=timezone.utc)
            rows.append({"date": row_date, "value": float(val_str)})
        except (ValueError, TypeError):
            continue

    # Sort ascending by date
    rows.sort(key=lambda r: r["date"])
    logger.info(f"bls_source: fetched {len(rows)} NFP observations")
    return rows
