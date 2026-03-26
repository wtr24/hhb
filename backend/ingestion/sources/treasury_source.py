import requests
import lxml.etree as ET
from datetime import date, datetime, timezone
import logging

logger = logging.getLogger(__name__)

TREASURY_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"

TENOR_FIELDS = [
    "BC_1MONTH", "BC_2MONTH", "BC_3MONTH", "BC_6MONTH",
    "BC_1YEAR", "BC_2YEAR", "BC_3YEAR", "BC_5YEAR",
    "BC_7YEAR", "BC_10YEAR", "BC_20YEAR", "BC_30YEAR",
]

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
}


def fetch_treasury_yield_curve() -> list[dict]:
    """Fetch US Treasury daily yield curve XML for current month.
    Returns list of dicts with 'date' (from XML NEW_DATE, not now()) and bc_* tenor keys.
    """
    year_month = date.today().strftime("%Y%m")
    r = requests.get(
        TREASURY_URL,
        params={"data": "daily_treasury_yield_curve", "field_tdr_date_value": year_month},
        timeout=30,
    )
    r.raise_for_status()

    root = ET.fromstring(r.content)

    rows = []
    for entry in root.findall(".//atom:entry", NS):
        content = entry.find("atom:content", NS)
        if content is None:
            continue
        properties = content.find("m:properties", NS)
        if properties is None:
            continue

        # Use NEW_DATE from XML as timestamp — NOT datetime.now() (Research Pitfall 6)
        date_el = properties.find("d:NEW_DATE", NS)
        if date_el is None or date_el.text is None:
            continue

        # Parse date string — Treasury format: "2026-03-25T00:00:00"
        try:
            row_date = datetime.fromisoformat(date_el.text.replace("Z", "+00:00"))
            if row_date.tzinfo is None:
                row_date = row_date.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        row = {"date": row_date}
        for field in TENOR_FIELDS:
            el = properties.find(f"d:{field}", NS)
            if el is not None and el.text:
                try:
                    row[field.lower()] = float(el.text)
                except (ValueError, TypeError):
                    row[field.lower()] = None
            else:
                row[field.lower()] = None
        rows.append(row)

    return rows
