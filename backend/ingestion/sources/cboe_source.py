"""CBOE equity put/call ratio source.

D-21: CBOE publishes a free daily equity P/C ratio CSV at:
  https://cdn.cboe.com/data/us/options/market_statistics/daily_equity_pc_ratio.csv

Columns: DATE, P/C Ratio (or similar). Take the most recent date row.
Store in macro_series table with series_id = "CBOE_PCR".
"""
import csv
import io
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

CBOE_PCR_URL = "https://cdn.cboe.com/data/us/options/market_statistics/daily_equity_pc_ratio.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HHBFin/1.0)",
}


def fetch_cboe_pcr() -> dict:
    """Fetch CBOE daily equity put/call ratio.

    Returns dict:
        {"date": datetime (UTC), "value": float, "source": "cboe"}

    Raises ValueError if CSV cannot be parsed or is empty.
    Raises requests.HTTPError on HTTP errors.
    """
    response = requests.get(CBOE_PCR_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    content = response.text
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        raise ValueError("CBOE PCR CSV returned empty content")

    # Take the most recent row (last row in the file, ascending date order)
    latest = rows[-1]

    # Flexible column name handling — CBOE may use 'DATE' or 'date'
    date_val = None
    pcr_val = None
    for key, val in latest.items():
        k_lower = key.strip().lower()
        if k_lower == "date":
            date_val = val.strip()
        elif "p/c" in k_lower or "put" in k_lower or "ratio" in k_lower:
            pcr_val = val.strip()

    if date_val is None or pcr_val is None:
        raise ValueError(
            f"CBOE PCR CSV: could not identify date/pcr columns. "
            f"Available columns: {list(latest.keys())}"
        )

    try:
        # CBOE date format is typically MM/DD/YYYY
        row_date = datetime.strptime(date_val, "%m/%d/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        # Try ISO format fallback
        row_date = datetime.fromisoformat(date_val).replace(tzinfo=timezone.utc)

    pcr = float(pcr_val)

    logger.info(f"cboe_source: fetched PCR {pcr} for {row_date.date()}")
    return {"date": row_date, "value": pcr, "source": "cboe"}
