"""BoE IADB nominal zero-coupon gilt curve source.

Mirrors treasury_source.py structure: fetch function returns list of dicts.
CRITICAL: Requires User-Agent header — BoE returns 403 without it.
"""
import csv
import io
import logging
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

BOE_URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"

# IUDMNZC series code suffix to gilt_curve column name
TENOR_MAP = {
    "IUDMNZC.A6": "tenor_6m",
    "IUDMNZC.A12": "tenor_1y",
    "IUDMNZC.A24": "tenor_2y",
    "IUDMNZC.A36": "tenor_3y",
    "IUDMNZC.A60": "tenor_5y",
    "IUDMNZC.A84": "tenor_7y",
    "IUDMNZC.A120": "tenor_10y",
    "IUDMNZC.A180": "tenor_15y",
    "IUDMNZC.A240": "tenor_20y",
    "IUDMNZC.A300": "tenor_25y",
    "IUDMNZC.A360": "tenor_30y",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HHBFin/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_boe_gilt_curve() -> list[dict]:
    """Fetch BoE IADB IUDMNZC nominal zero-coupon gilt curve.

    Returns list of dicts, each with:
      {"date": datetime (UTC), "tenor_6m": float|None, ..., "tenor_30y": float|None}

    Raises requests.HTTPError on non-2xx (including 403 if User-Agent missing).
    """
    params = {
        "Datefrom": "01/Jan/2020",
        "Dateto": "now",
        "SeriesCodes": "IUDMNZC",
        "CSVF": "TT",
        "UsingCodes": "Y",
    }
    response = requests.get(BOE_URL, params=params, headers=HEADERS, timeout=30)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        if response.status_code == 403:
            raise requests.HTTPError(
                "BoE returned 403 — User-Agent header missing or blocked. "
                f"Check HEADERS in boe_source.py. URL: {response.url}"
            ) from e
        raise

    content = response.text
    rows = []
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    for row in reader:
        # First column is the date column; field name varies but is always first
        date_col = reader.fieldnames[0] if reader.fieldnames else None
        if date_col is None:
            continue
        date_str = row.get(date_col, "").strip()
        if not date_str:
            continue
        try:
            row_date = datetime.strptime(date_str, "%d %b %Y").replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning(f"boe_source: unrecognised date format '{date_str}', skipping row")
            continue

        parsed = {"date": row_date}
        for col_name, tenor_key in TENOR_MAP.items():
            raw = row.get(col_name, "").strip()
            if raw == "" or raw is None:
                parsed[tenor_key] = None
            else:
                try:
                    parsed[tenor_key] = float(raw)
                except (ValueError, TypeError):
                    parsed[tenor_key] = None
        rows.append(parsed)

    logger.info(f"boe_source: fetched {len(rows)} gilt curve rows")
    return rows
