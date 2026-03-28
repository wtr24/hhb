SEED_TICKERS = [
    "AAPL", "MSFT", "LLOY.L", "BARC.L",
    "^FTSE", "^FTMC", "BTC-USD", "GBP=X", "EURUSD=X",
]

# Finnhub WebSocket eligible symbols: US stocks, forex, crypto only.
# Excludes LSE (.L suffix), indices (^ prefix), and Yahoo FX aliases (= suffix).
# Free tier: max 50 concurrent subscriptions; 1 connection per API key.
FINNHUB_WS_SYMBOLS = [
    t for t in SEED_TICKERS
    if not t.endswith(".L") and not t.startswith("^") and "=" not in t
]

FRED_SERIES_MAP = {
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "pce": "PCEPI",
    "gdp": "GDP",
    "fed_funds": "FEDFUNDS",
    "unemployment": "UNRATE",
    "treasury_10y": "GS10",
    "treasury_2y": "GS2",
}

RETRY_COUNTDOWNS = [60, 300, 900]
SCHEDULE_OHLCV = 300
SCHEDULE_MACRO = 3600
SCHEDULE_FX = 30
SCHEDULE_TREASURY = 900
