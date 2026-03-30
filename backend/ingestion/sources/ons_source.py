"""ONS (Office for National Statistics) API source.

D-22: ONS beta API (free, no key). Fetches UK CPI, unemployment, and GDP.
API base: https://api.beta.ons.gov.uk/v1
Note: the OLD api.ons.gov.uk was retired November 2024 — use api.beta.ons.gov.uk only.

Two-step pattern per series:
  1. GET timeseries/{series_code}/dataset to get dataset_id
  2. GET datasets/{dataset_id}/timeseries/{series_code}/data to get observations

Stores into macro_series with series_id prefixed "ONS_":
  - L522 (UK CPI) → series_id = "ONS_CPI"
  - LF2Q (UK unemployment rate) → series_id = "ONS_UNEMPLOYMENT"
  - ABMI (UK GDP index) → series_id = "ONS_GDP"
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

ONS_BASE = "https://api.beta.ons.gov.uk/v1"

ONS_SERIES = {
    "ONS_CPI": "L522",
    "ONS_UNEMPLOYMENT": "LF2Q",
    "ONS_GDP": "ABMI",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HHBFin/1.0)",
    "Accept": "application/json",
}


def _fetch_ons_series(series_code: str) -> list[dict]:
    """Fetch all available observations for a single ONS timeseries code.

    Returns list of {"date": datetime (UTC), "value": float} dicts, newest first.
    """
    # Step 1: get the dataset ID for this timeseries
    meta_url = f"{ONS_BASE}/timeseries/{series_code.lower()}/dataset"
    meta_resp = requests.get(meta_url, headers=HEADERS, timeout=30)
    meta_resp.raise_for_status()
    meta = meta_resp.json()

    # The dataset_id is at the top level of the response
    dataset_id = meta.get("id") or meta.get("uri", "").split("/")[-1]
    if not dataset_id:
        raise ValueError(f"ONS: could not determine dataset_id for series {series_code}")

    # Step 2: fetch the timeseries observations
    data_url = f"{ONS_BASE}/datasets/{dataset_id}/timeseries/{series_code.lower()}/data"
    data_resp = requests.get(data_url, headers=HEADERS, timeout=30)
    data_resp.raise_for_status()
    payload = data_resp.json()

    # ONS returns data in years / quarters / months / months objects
    # Try months first (CPI, unemployment), then quarters (GDP), then years
    observations_raw = (
        payload.get("months") or
        payload.get("quarters") or
        payload.get("years") or
        []
    )

    rows = []
    for obs in observations_raw:
        date_str = obs.get("date", "")
        val_str = obs.get("value", "")
        if not date_str or val_str in ("", None):
            continue
        try:
            # ONS date formats: "2026 Jan" (monthly), "2026 Q1" (quarterly), "2025" (annual)
            if "Q" in date_str:
                # Convert "2026 Q1" → first month of quarter
                year, q = date_str.split(" Q")
                month = (int(q) - 1) * 3 + 1
                row_date = datetime(int(year), month, 1, tzinfo=timezone.utc)
            elif len(date_str) == 4:
                row_date = datetime(int(date_str), 1, 1, tzinfo=timezone.utc)
            else:
                row_date = datetime.strptime(date_str, "%Y %b").replace(tzinfo=timezone.utc)
            rows.append({"date": row_date, "value": float(val_str)})
        except (ValueError, TypeError) as e:
            logger.debug(f"ONS: skipping observation '{date_str}' = '{val_str}': {e}")
            continue

    logger.info(f"ons_source: fetched {len(rows)} observations for {series_code}")
    return rows


def fetch_ons_series_all() -> dict[str, list[dict]]:
    """Fetch all three ONS series. Returns {series_id: [obs_dicts]} mapping."""
    result = {}
    for series_id, series_code in ONS_SERIES.items():
        try:
            result[series_id] = _fetch_ons_series(series_code)
        except Exception as e:
            logger.error(f"ons_source: failed to fetch {series_code} ({series_id}): {e}")
            result[series_id] = []
    return result
