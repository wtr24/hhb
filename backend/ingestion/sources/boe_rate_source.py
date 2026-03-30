"""BoE Bank Rate (IUMABEDR) source — same IADB endpoint as gilt curve.

Stores into macro_series with series_id = "BOE_RATE".
Same User-Agent requirement as boe_source.py.
"""
import csv
import io
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

BOE_URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HHBFin/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_boe_policy_rate() -> list[dict]:
    """Fetch BoE Bank Rate (IUMABEDR) monthly series.

    Returns list of {"date": datetime (UTC), "value": float} dicts.
    """
    params = {
        "Datefrom": "01/Jan/2015",
        "Dateto": "now",
        "SeriesCodes": "IUMABEDR",
        "CSVF": "TT",
        "UsingCodes": "Y",
    }
    response = requests.get(BOE_URL, params=params, headers=HEADERS, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        if response.status_code == 403:
            raise requests.HTTPError(
                "BoE returned 403 — User-Agent header required. Check boe_rate_source.py."
            ) from e
        raise

    content = response.text
    rows = []
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    fieldnames = reader.fieldnames or []

    # Date column is first; value column contains "IUMABEDR"
    date_col = fieldnames[0] if fieldnames else None
    value_col = next((f for f in fieldnames if "IUMABEDR" in f), None)

    if date_col is None or value_col is None:
        logger.error(f"boe_rate_source: unexpected columns: {fieldnames}")
        return []

    for row in reader:
        date_str = row.get(date_col, "").strip()
        val_str = row.get(value_col, "").strip()
        if not date_str or not val_str:
            continue
        try:
            row_date = datetime.strptime(date_str, "%d %b %Y").replace(tzinfo=timezone.utc)
            rows.append({"date": row_date, "value": float(val_str)})
        except (ValueError, TypeError):
            logger.debug(f"boe_rate_source: skipping row date='{date_str}' val='{val_str}'")
            continue

    logger.info(f"boe_rate_source: fetched {len(rows)} Bank Rate observations")
    return rows
