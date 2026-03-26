import requests
import logging

logger = logging.getLogger(__name__)

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1"
TARGET_CURRENCIES = ["GBP", "EUR", "JPY", "CHF", "AUD", "CAD", "NZD", "NOK", "SEK"]


def fetch_fx_rates(base: str = "USD") -> dict:
    """Fetch latest FX rates from Frankfurter API.
    Returns dict with 'amount', 'base', 'date', 'rates' keys.
    No API key needed.
    """
    r = requests.get(
        f"{FRANKFURTER_BASE}/latest",
        params={"base": base, "symbols": ",".join(TARGET_CURRENCIES)},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # {"amount": 1.0, "base": "USD", "date": "...", "rates": {...}}
