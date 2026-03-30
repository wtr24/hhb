"""ECB SDMX REST API source — Eurozone GDP growth rate.

D-24: ECB SDMX REST, free, no key required.
Series: MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY
Simplified endpoint with ?format=csvdata&lastNObservations=20.

Stores: macro_series with series_id = "ECB_GDP".
"""
import csv
import io
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/"
    "MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY"
    "?format=csvdata&lastNObservations=20"
)

HEADERS = {
    "Accept": "text/csv",
    "User-Agent": "Mozilla/5.0 (compatible; HHBFin/1.0)",
}


def fetch_ecb_gdp() -> list[dict]:
    """Fetch Eurozone GDP growth rate from ECB SDMX REST API.

    Returns list of {"date": datetime (UTC), "value": float} dicts,
    sorted ascending by date. Returns empty list on error (graceful degradation).
    """
    try:
        response = requests.get(ECB_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"ecb_source: request failed: {e}")
        return []

    content = response.text
    if not content.strip():
        logger.warning("ecb_source: empty response from ECB API")
        return []

    rows = []
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []

    # ECB csvdata format: "TIME_PERIOD" column contains "YYYY-QN", "OBS_VALUE" has the value
    for row in reader:
        time_period = row.get("TIME_PERIOD", "").strip()
        obs_value = row.get("OBS_VALUE", "").strip()
        if not time_period or not obs_value:
            continue
        try:
            # Format: "2025-Q4" → parse to first month of quarter
            if "Q" in time_period:
                year_str, q_str = time_period.split("-Q")
                month = (int(q_str) - 1) * 3 + 1
                row_date = datetime(int(year_str), month, 1, tzinfo=timezone.utc)
            else:
                # Fallback: try ISO date
                row_date = datetime.fromisoformat(time_period).replace(tzinfo=timezone.utc)
            rows.append({"date": row_date, "value": float(obs_value)})
        except (ValueError, TypeError) as e:
            logger.debug(f"ecb_source: skipping '{time_period}' = '{obs_value}': {e}")
            continue

    rows.sort(key=lambda r: r["date"])
    logger.info(f"ecb_source: fetched {len(rows)} ECB GDP observations")
    return rows


def fetch_ecb_dfr() -> list[dict]:
    """Fetch ECB Deposit Facility Rate (DFR) — ECB policy rate for MACRO-10.

    Uses ECB SDMX REST API, FM dataflow, key B.U2.EUR.4F.KR.DFR.LEV.
    Returns list of {"date": datetime, "value": float} dicts.
    """
    url = (
        "https://data-api.ecb.europa.eu/service/data/FM/"
        "B.U2.EUR.4F.KR.DFR.LEV"
        "?format=csvdata&lastNObservations=48"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"ecb_dfr fetch failed: {e}")
        return []

    rows = []
    lines = resp.text.splitlines()
    if not lines:
        return []

    reader = csv.DictReader(lines)
    for record in reader:
        time_period = record.get("TIME_PERIOD", "").strip()
        obs_value = record.get("OBS_VALUE", "").strip()
        if not time_period or not obs_value:
            continue
        try:
            # Monthly format YYYY-MM
            if len(time_period) == 7:
                row_date = datetime(int(time_period[:4]), int(time_period[5:7]), 1, tzinfo=timezone.utc)
            else:
                row_date = datetime.fromisoformat(time_period).replace(tzinfo=timezone.utc)
            rows.append({"date": row_date, "value": float(obs_value)})
        except (ValueError, TypeError) as e:
            logger.debug(f"ecb_dfr: skipping '{time_period}' = '{obs_value}': {e}")
            continue

    rows.sort(key=lambda r: r["date"])
    logger.info(f"ecb_dfr: fetched {len(rows)} ECB DFR observations")
    return rows
