SEED_TICKERS = [
    "AAPL", "MSFT", "LLOY.L", "BARC.L",
    "^FTSE", "^FTMC", "BTC-USD", "GBP=X", "EURUSD=X",
    "^GSPC",     # SPX — seasonality + at-a-glance strip (MACRO-14)
    "DX-Y.NYB",  # DXY — at-a-glance strip (MACRO-14)
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
    "tips_breakeven_5y": "T5YIE",
    "tips_breakeven_10y": "T10YIE",
    "hy_spread": "BAMLH0A0HYM2",
    "safe_haven_usd": "DTWEXBGS",
}

RETRY_COUNTDOWNS = [60, 300, 900]
SCHEDULE_OHLCV = 300
SCHEDULE_MACRO = 3600
SCHEDULE_FX = 30
SCHEDULE_TREASURY = 900
SCHEDULE_BOE = 86400      # BoE gilt curve: once daily
SCHEDULE_VIX = 900        # VIX term structure: every 15 minutes
SCHEDULE_CBOE = 86400     # CBOE put/call ratio: once daily
SCHEDULE_ONS = 86400      # ONS UK stats: once daily
SCHEDULE_BLS = 86400      # BLS US NFP: once daily
SCHEDULE_ECB = 86400      # ECB Eurozone GDP: once daily
