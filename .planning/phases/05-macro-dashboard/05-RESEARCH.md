# Phase 5: Macro Dashboard — Research

**Researched:** 2026-03-30
**Domain:** Macro economics data ingestion + Bloomberg ECO-equivalent frontend
**Confidence:** HIGH (data sources verified by live fetch), MEDIUM (BoE IADB URL — 403 from fetcher but confirmed via search), LOW (VIX6M history depth)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Layout**
- D-01: MACRO module uses sub-tab navigation: `[CURVES] [INDICATORS] [RISK] [SENTIMENT]`. Each sub-tab fixed-height Bloomberg grid — nothing scrolls within a sub-tab.
- D-02: Default landing sub-tab is CURVES.
- D-03: Sub-tab nav is a secondary nav bar rendered below the MACRO module header, amber terminal style. Not a command input.
- D-04: CURVES sub-tab grid — Left 60%: main yield curve chart (US amber + UK gilt green, overlaid). Right 40% top: 2s10s + 5s30s spread time series, stacked. Right 40% bottom: curve shape classifier badge + historical overlay toggle.
- D-05: INDICATORS sub-tab — 3×2 grid: CPI | Core CPI | PCE (top row) / GDP | Unemployment | Policy Rates (bottom row). Each panel: sparkline + current value + MoM/YoY delta. US and UK/EU values side-by-side where available.
- D-06: RISK sub-tab — Left: VIX term structure chart (spot + VIX3M + VIX6M). Right top: regime classifier badge + percentile rank. Right bottom: CBOE put/call ratio time series.
- D-07: SENTIMENT sub-tab — Left: Fear & Greed gauge (0–100) + component breakdown table. Right: DXY/SPX/FTSE 100 at-a-glance strip (15s refresh) + seasonality panel.

**Yield Curve Display**
- D-08: Single chart with toggle controls — US (amber) + UK gilt (green) overlaid, current day. `[TODAY] [+1M] [+1Y]` toggles add/remove historical overlay series as thin dashed lines.
- D-09: Curve shape classifier: `NORMAL` / `FLAT` / `INVERTED ⚠` / `HUMPED`. Show historical context.
- D-10: Real yield panel = nominal 10Y minus TIPS 10Y breakeven (FRED `T10YIE`) as time series.

**BoE Gilt Curve**
- D-11: Source: BoE IADB `IUDMNZC` series via `https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp`.
- D-12: Tenors: 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y, 20Y, 25Y, 30Y (11 tenors — no 1M/3M).
- D-13: Refresh once daily, 24h TTL, store in new `gilt_curve` hypertable.

**Fear & Greed Composite**
- D-14: Six components, equal-weighted, each normalized to 0–100 via percentile rank over rolling 1Y window. Components: VIX percentile (yfinance `^VIX`), Put/call ratio (CBOE free CSV), Market breadth (Phase 4 `ta_market_breadth` — NOTE: actually computed from OHLCV, see risk section), Junk bond spread (FRED `BAMLH0A0HYM2`), SPX momentum (yfinance `^GSPC` 125-day ROC), Safe haven demand (FRED `DTWEXBGS` vs 20-day SMA).
- D-15: Composite = equal-weighted average. Color bands: 0–25 Extreme Fear / 25–45 Fear / 45–55 Neutral / 55–75 Greed / 75–100 Extreme Greed.
- D-16: Display: gauge + numeric score + color band label + component breakdown table.

**FRED Series Expansion**
- D-17: Add to `FRED_SERIES_MAP`: `tips_breakeven_5y: T5YIE`, `tips_breakeven_10y: T10YIE`, `hy_spread: BAMLH0A0HYM2`, `safe_haven_usd: DTWEXBGS`. `policy_rate: FEDFUNDS` already present.

**VIX Term Structure**
- D-18: yfinance `^VIX`, `^VIX3M`, `^VIX6M`. Poll 15m schedule. Store in new `vix_term_structure` hypertable.
- D-19: Contango/backwardation badge: `CONTANGO` (VIX3M > spot) or `BACKWARDATION ⚠` (VIX3M < spot).
- D-20: Regime thresholds: VIX < 15 Low Vol / 15–20 Normal / 20–30 Elevated / > 30 Crisis.

**CBOE Put/Call Ratio**
- D-21: CBOE free daily CSV, scrape once daily, store in `macro_series` under `CBOE_PCR`.

**ONS / BLS / ECB Ingestion**
- D-22: ONS API — UK CPI (`L522`), UK unemployment (`LF2Q`), UK GDP (`ABMI`). Use beta API.
- D-23: BLS API (free key) — US NFP (`CES0000000001`). JSON API v2.
- D-24: ECB SDMX REST API — Eurozone GDP.
- D-25: All store into `macro_series` table — no new models.

### Claude's Discretion
- Exact sparkline library for INDICATORS panels
- Seasonality panel implementation (recharts BarChart or Canvas)
- CBOE put/call scrape retry/fallback strategy
- Exact BoE IADB URL parameter format
- Whether VIX3M/VIX6M have sufficient data coverage — fall back to CBOE historical CSV if spotty

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MACRO-01 | Full US yield curve (1M–30Y) from US Treasury XML displayed, updated every 15m | Already live from Phase 2; frontend display is what Phase 5 adds |
| MACRO-02 | Full UK gilt curve from BoE Statistical Database | BoE IADB `IUDMNZC` via `_iadb-fromshowcolumns.asp` CSV endpoint confirmed |
| MACRO-03 | 2s10s and 5s30s spread as time series with recession zone overlay | Computable from existing `yield_curve` + new `gilt_curve` tables |
| MACRO-04 | Curve shape classifier — Normal / Flat / Inverted / Humped + historical context | Pure backend computation from stored tenor values |
| MACRO-05 | Historical curve overlay — today vs 1M ago vs 1Y ago on same chart | Query `yield_curve` and `gilt_curve` by timestamp offset |
| MACRO-06 | Real yield + breakeven inflation (FRED TIPS series) | FRED `T5YIE`, `T10YIE` confirmed. Add to `FRED_SERIES_MAP` |
| MACRO-07 | US macro panels (CPI, Core CPI, PCE) + UK CPI | CPI/PCE already in FRED map; ONS beta API confirmed for `L522` |
| MACRO-08 | Labour market — US NFP/unemployment + UK employment | BLS API v2 POST for `CES0000000001`; ONS `LF2Q` via beta API |
| MACRO-09 | GDP — US (FRED) + UK (ONS) + EU (ECB) | FRED `GDP` already in map; ONS `ABMI`; ECB SDMX `data-api.ecb.europa.eu` confirmed |
| MACRO-10 | Policy rates — Fed Funds + BoE base rate + ECB rate | FRED `FEDFUNDS` already in map; BoE and ECB ingestion workers needed |
| MACRO-11 | VIX term structure — spot VIX + VIX3M + VIX6M contango/backwardation | `^VIX3M` confirmed via Yahoo Finance; `^VIX6M` exists but limited history |
| MACRO-12 | VIX percentile rank + regime classifier | Pure computation from stored `vix_term_structure` data |
| MACRO-13 | DIY Fear & Greed Index — 6-component composite | All sources resolved; breadth component requires nightly pre-compute task |
| MACRO-14 | DXY/SPX/FTSE at-a-glance (15s refresh) + seasonality panel | Reuses existing WebSocket/OHLCV infrastructure |
</phase_requirements>

---

## Executive Summary

Phase 5 extends the existing macro ingestion foundation (FRED + US Treasury, live since Phase 2) with five new ingestion workers, two new TimescaleDB hypertables, four new FRED series, and a complete React MACRO module replacing the current stub.

The three most reliable sources are fully verified: the CBOE equity put/call ratio CSV downloads without authentication at a stable CDN URL, the ECB SDMX API returns clean CSV with `data-api.ecb.europa.eu`, and the ONS beta API at `api.beta.ons.gov.uk/v1` returns JSON observations for series codes L522/LF2Q/ABMI via a two-step search-then-fetch pattern (the old `api.ons.gov.uk` endpoint was retired November 2024).

The BoE IADB CSV endpoint (`_iadb-fromshowcolumns.asp`) is confirmed via community code examples and search results but returns 403 from automated fetchers — the IUDMNZC series exists in the BoE database, the URL pattern is documented, and the CSV format uses `CSVF=TT` with `UsingCodes=Y`. A `User-Agent` header and brief delay will be required to avoid the 403.

The biggest risk is VIX6M history depth: `^VIX6M` appears to have only about one year of history on Yahoo Finance, making rolling 1Y percentile calculations unstable at phase launch. The fallback is to omit VIX6M from the term structure chart until 5Y history accumulates, using `^VIX` + `^VIX3M` as the contango signal instead.

A second important finding: the `ta_market_breadth` table referenced in CONTEXT.md D-14 does not exist. Phase 4 implemented breadth as in-memory computation from OHLCV in `analysis/breadth.py` but never persisted snapshots to the database. Phase 5 must either (a) add a nightly `compute_breadth_snapshot` Celery beat task that writes a daily % above 200 SMA value to `macro_series` under `BREADTH_PCT200`, or (b) compute it on the fly inside the Fear & Greed API endpoint by querying OHLCV.

**Primary recommendation:** Add a nightly breadth snapshot task (option a). This follows the existing `compute_nightly_pivot_points` pattern, keeps the Fear & Greed API endpoint fast, and persists the signal for historical replay.

---

## Data Source Analysis

### Source 1: BoE IADB Gilt Curve (IUDMNZC)

**Confidence:** MEDIUM (URL pattern confirmed via community code; direct fetch returns 403)

**Endpoint:**
```
https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp
```

**Required parameters:**
| Parameter | Value | Notes |
|-----------|-------|-------|
| `csv.x` | `yes` | Triggers CSV download mode |
| `SeriesCodes` | `IUDMNZC` | Series code for nominal zero-coupon gilt spot curve |
| `Datefrom` | `01/Jan/2020` | DD/MMM/YYYY format |
| `Dateto` | `now` | Literal "now" or specific date |
| `CSVF` | `TT` | Tabular with titles (includes column headers) |
| `UsingCodes` | `Y` | Use series codes rather than labels |
| `VPD` | `Y` | Include provisional data |
| `VFD` | `N` | Exclude observation footnotes |

**Headers required:** Must set `User-Agent` to a browser string. The BoE IADB returns 403 to plain `requests` calls without a user agent. Example: `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"`.

**IUDMNZC column structure:** The IUDMNZC series in the BoE database is a multi-tenor family. The CSV with `CSVF=TT` returns a header row and daily observations. The 11 tenor columns correspond to the tenors mandated in D-12 (6M through 30Y). Based on BoE IADB conventions, individual tenor series codes follow the pattern appended to the base code (e.g., `IUDMNZC.05` for 0.5yr). The CSV output with `SeriesCodes=IUDMNZC` returns all sub-tenors in a single request.

**Caveat (LOW confidence on exact column names):** The BoE IADB 403 restriction prevents direct verification of column header names. The recommended approach is to fetch a small date range (e.g., last 5 days) during Wave 0 implementation, print the raw CSV, and confirm column headers before writing the parser. Use `pandas.read_csv(io.BytesIO(response.content), skiprows=0)` and log the `.columns` attribute.

**Response format:**
```
Date,IUDMNZC.05,IUDMNZC.01,IUDMNZC.02,IUDMNZC.03,IUDMNZC.05,...
01 Jan 2024,4.85,4.72,4.51,...
```
(Date format in BoE CSVs is `DD MMM YYYY` — parse with `datetime.strptime(s, "%d %b %Y")`)

**Rate limits:** None documented. Daily publication (business days only). A 2-second delay between requests is prudent.

**Fallback:** If the BoE IADB URL changes or becomes unavailable, the BoE also publishes yield curve Excel spreadsheets at `https://www.bankofengland.co.uk/statistics/yield-curves`. A secondary scraper using openpyxl could parse the spreadsheet. However, this is significantly more complex and should only be a last resort.

**Schedule:** Once daily via `crontab(hour=18, minute=0)` — BoE typically updates after 17:00 UK time.

---

### Source 2: ONS Beta API (UK CPI, Unemployment, GDP)

**Confidence:** HIGH (live fetch verified — `/v1/data?uri=...` returns full observations array)

**IMPORTANT:** The old `api.ons.gov.uk` endpoint was **retired November 25, 2024**. Use only `api.beta.ons.gov.uk/v1`.

**Two-step access pattern:**

Step 1 — Resolve series URI (run once; URIs are "evergreen" per ONS docs):
```
GET https://api.beta.ons.gov.uk/v1/search?content_type=timeseries&cdids={SERIES_ID}
```
Response contains `items[0].uri`, e.g. `/economy/inflationandpriceindices/timeseries/l522/mm23`

Step 2 — Fetch observations:
```
GET https://api.beta.ons.gov.uk/v1/data?uri={uri_from_step1}
```

**Confirmed URIs for required series:**

| Series | Code | URI |
|--------|------|-----|
| UK CPI (all items, 2015=100) | L522 | `/economy/inflationandpriceindices/timeseries/l522/mm23` |
| UK unemployment rate | LF2Q | (resolve via search — not directly verified) |
| UK GDP (chained volume) | ABMI | (resolve via search — not directly verified) |

**Response structure (verified for L522):**
```json
{
  "years": [{"date": "1988", "value": "48.2", "label": "1988", ...}],
  "quarters": [{"date": "1988 Q1", "value": "48.1", ...}],
  "months": [{"date": "1988 JAN", "value": "48.0", ...}]
}
```
All values are strings. Parse `float(obs["value"])`. Date format: `"YYYY MMM"` for months (e.g., `"2024 DEC"`), `"YYYY Qn"` for quarters, `"YYYY"` for years.

**Coverage:** Monthly data from 1988. Quarters from 1988 Q1. Latest month: 2024 DEC (as of fetch).

**Rate limits:** None documented. No API key required.

**Storing convention:** Use `series_id` = `ONS_L522`, `ONS_LF2Q`, `ONS_ABMI` in `macro_series` table. Source field = `"ons"`.

**Refresh schedule:** Monthly releases. Use `timedelta(hours=24)` Celery beat schedule — data only changes on release dates but polling is harmless.

---

### Source 3: BLS API v2 (US NFP)

**Confidence:** HIGH (official documentation, well-established)

**Endpoint:**
```
POST https://api.bls.gov/publicAPI/v2/timeseries/data/
Content-Type: application/json
```

**Request body:**
```json
{
  "seriesid": ["CES0000000001"],
  "startyear": "2020",
  "endyear": "2026",
  "registrationkey": "{BLS_API_KEY}"
}
```

**Response structure:**
```json
{
  "Results": {
    "series": [{
      "seriesID": "CES0000000001",
      "data": [
        {"year": "2026", "period": "M02", "value": "159456", "footnotes": [...]},
        ...
      ]
    }]
  }
}
```
Period format: `"M01"` through `"M12"` = months, `"M13"` = annual average. Parse date as `f"{year}-{int(period[1:]):02d}-01"`.

**Rate limits:**
- Registered (v2 with key): 500 queries/day, 20 years per query, 50 series per query
- Unregistered (v1): 25 queries/day, 10 years per query

**API key:** `BLS_API_KEY` env var. Free registration at bls.gov. No credit card required.

**Series `CES0000000001`:** Total Nonfarm Employment, Seasonally Adjusted. Values in thousands. Monthly change must be computed: `current_value - previous_value`.

**Storing convention:** `series_id` = `BLS_CES0000000001`. Source = `"bls"`.

**Refresh schedule:** `timedelta(hours=24)` — BLS releases monthly on the first Friday of each month.

---

### Source 4: ECB SDMX REST API (Eurozone GDP)

**Confidence:** HIGH (live fetch verified — CSV response confirmed with actual data)

**Endpoint:**
```
https://data-api.ecb.europa.eu/service/data/MNA/{key}?lastNObservations={n}&format=csvdata
```

**Verified GDP key:**
```
Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY
```
Meaning: Quarterly / Growth rate YoY / Euro area 19+20 / GDP / chain-linked / seasonally adjusted

**Verified response (2024-Q1 through 2025-Q4):**
```
KEY,FREQ,REF_AREA,...,TIME_PERIOD,OBS_VALUE,...
Q.Y.I9.W2....,Q,I9,...,2024-Q1,0.54,...
```
Columns: `KEY`, `TIME_PERIOD` (format: `"2024-Q1"`), `OBS_VALUE` (float, YoY % growth).

**Response format parameter:** `format=csvdata` returns CSV. Without the header `Accept: text/csv`, also works with format parameter.

**Alternative JSON format:** Use `Accept: application/json` header instead.

**Rate limits:** None documented. No API key required.

**BoE base rate (ECB parallel for policy rate):** Use ECB key `FM.B.U2.EUR.4F.KR.MRR_FR.LEV` for ECB Main Refinancing Operations rate.

**Storing convention:** `series_id` = `ECB_GDP_GY` for GDP growth, `ECB_MRR_RATE` for ECB policy rate. Source = `"ecb"`.

**Refresh schedule:** `timedelta(hours=24)`. Quarterly GDP released approx 30 days after quarter end.

---

### Source 5: CBOE Equity Put/Call Ratio

**Confidence:** HIGH (live fetch verified — full CSV data confirmed)

**URL (no login required):**
```
https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv
```

**CSV format (verified):**
```
DATE,CALL,PUT,TOTAL,P/C Ratio
11/1/2006,976510,623929,1600439,0.64
```
Column names: `DATE`, `CALL`, `PUT`, `TOTAL`, `P/C Ratio`
Date format: `M/D/YYYY` (e.g., `"11/1/2006"`) — parse with `datetime.strptime(s, "%m/%d/%Y")`.

**Data coverage:** From 11/1/2006 to present. ~5000+ rows.

**P/C Ratio meaning:** Equity-only put/call ratio (excludes index options). Lower = more calls (bullish/greedy). Higher = more puts (bearish/fearful). Typical range 0.4–1.2.

**Note on index vs equity P/C:** There is also `indexpcarchive.csv` at the same CDN path. D-21 specifies equity put/call; use `equitypc.csv`.

**Storing convention:** Extract last row (latest business day). Store as `series_id` = `CBOE_PCR`, value = `P/C Ratio` float. Source = `"cboe"`.

**Scraping approach:** Use `requests.get(url, timeout=30)`. No `User-Agent` header required (CDN responds to plain requests). Parse CSV with `csv.reader` from `io.StringIO(r.text)`.

**Retry strategy:** CBOE CDN is stable but can have occasional 503 during market hours. Retry up to 3 times with 60s countdown (matches existing `RETRY_COUNTDOWNS` pattern).

**Refresh schedule:** `crontab(hour=21, minute=30)` — CBOE updates after 21:00 UTC (4:30 PM ET close + 30 min processing).

---

### Source 6: VIX Term Structure (yfinance)

**Confidence:** HIGH for `^VIX` and `^VIX3M` / LOW for `^VIX6M` history depth

**Tickers:**
| Ticker | Description | Yahoo Finance Page |
|--------|-------------|-------------------|
| `^VIX` | CBOE Volatility Index (30-day) | Confirmed, long history |
| `^VIX3M` | CBOE S&P 500 3-Month Volatility | Confirmed active on Yahoo Finance |
| `^VIX6M` | CBOE S&P 500 6-Month Volatility | Confirmed active, but history appears limited to ~1 year |

**`^VIX6M` history risk (LOW confidence):** Search results show `^VIX6M` historical data page dated "Feb 23, 2025 - Feb 23, 2026", suggesting only ~1 year of history is available on Yahoo Finance. This makes a rolling 1Y percentile rank unstable at phase launch.

**Recommended fallback for VIX6M:** Store whatever history exists. During the accumulation period (< 1Y of data), show the raw value but suppress the percentile rank display with a `"insufficient history"` badge rather than a potentially misleading percentile.

**yfinance fetch pattern** (mirrors existing OHLCV ingestion):
```python
import yfinance as yf
ticker = yf.Ticker("^VIX3M")
hist = ticker.history(period="5d", interval="1d")
latest_close = float(hist["Close"].iloc[-1])
```

**Storing convention:** Use new `vix_term_structure` hypertable with columns for `spot`, `vix3m`, `vix6m`. Store on 15m schedule alongside existing OHLCV tasks.

---

## Database Schema

### New Table 1: `gilt_curve` (TimescaleDB hypertable)

Mirrors `yield_curve` table but for UK gilt tenors. 11 columns for BoE tenors (6M through 30Y; no 1M/3M as BoE IUDMNZC does not publish them).

```sql
CREATE TABLE gilt_curve (
    time        TIMESTAMPTZ     NOT NULL,
    gc_6month   NUMERIC(8,4),
    gc_1year    NUMERIC(8,4),
    gc_2year    NUMERIC(8,4),
    gc_3year    NUMERIC(8,4),
    gc_5year    NUMERIC(8,4),
    gc_7year    NUMERIC(8,4),
    gc_10year   NUMERIC(8,4),
    gc_15year   NUMERIC(8,4),
    gc_20year   NUMERIC(8,4),
    gc_25year   NUMERIC(8,4),
    gc_30year   NUMERIC(8,4),
    source      VARCHAR(20)     DEFAULT 'boe',
    PRIMARY KEY (time)
);
SELECT create_hypertable('gilt_curve', 'time', if_not_exists => TRUE);
ALTER TABLE gilt_curve SET (timescaledb.compress = true);
SELECT add_compression_policy('gilt_curve', INTERVAL '30 days', if_not_exists => TRUE);
```

### New Table 2: `vix_term_structure` (TimescaleDB hypertable)

Stores spot VIX + VIX3M + VIX6M on 15m cadence.

```sql
CREATE TABLE vix_term_structure (
    time    TIMESTAMPTZ     NOT NULL,
    spot    NUMERIC(8,4),
    vix3m   NUMERIC(8,4),
    vix6m   NUMERIC(8,4),
    source  VARCHAR(20)     DEFAULT 'yfinance',
    PRIMARY KEY (time)
);
SELECT create_hypertable('vix_term_structure', 'time', if_not_exists => TRUE);
ALTER TABLE vix_term_structure SET (timescaledb.compress = true);
SELECT add_compression_policy('vix_term_structure', INTERVAL '30 days', if_not_exists => TRUE);
```

### New Table 3: `breadth_snapshots` (nightly, in `macro_series`)

No new table needed. The nightly breadth computation stores into `macro_series` with:
- `series_id` = `BREADTH_PCT200` (% of seed tickers above 200 SMA)
- `source` = `"computed"`
- One row per nightly run

### Existing `macro_series` additions (no schema change)

New `series_id` values that will populate into the existing table:
```
FRED: T5YIE, T10YIE, BAMLH0A0HYM2, DTWEXBGS
ONS:  ONS_L522, ONS_LF2Q, ONS_ABMI
BLS:  BLS_CES0000000001
ECB:  ECB_GDP_GY, ECB_MRR_RATE
BOE:  BOE_BASE_RATE  (BoE base rate from IADB series IUDBEDR)
CBOE: CBOE_PCR
COMPUTED: BREADTH_PCT200
```

**Note on `series_id` length:** The existing `macro_series.series_id` column is `VARCHAR(30)`. The longest new ID is `BLS_CES0000000001` at 18 chars — within limit. `ECB_MRR_RATE` is 12 chars. No migration needed to extend column width.

### Alembic migration: `0005_macro_dashboard.py`

Single migration file adds `gilt_curve` and `vix_term_structure` hypertables with compression policies. No changes to `macro_series` schema.

```
down_revision = "0004"
```

---

## Backend Architecture

### Ingestion Workers (new files)

All follow the established pattern: `sources/{name}_source.py` fetch function → registered in `tasks.py` → scheduled in `celery_app.py`.

**New source files:**
1. `backend/ingestion/sources/gilt_source.py` — BoE IADB CSV fetch for `IUDMNZC`
2. `backend/ingestion/sources/ons_source.py` — ONS beta API two-step fetch
3. `backend/ingestion/sources/bls_source.py` — BLS API v2 POST
4. `backend/ingestion/sources/ecb_source.py` — ECB SDMX CSV fetch
5. `backend/ingestion/sources/cboe_source.py` — CBOE equity put/call CSV fetch

**New model file:**
- `backend/models/gilt_curve.py` — SQLAlchemy model mirroring `yield_curve.py` pattern
- `backend/models/vix_term_structure.py` — SQLAlchemy model

### Celery Beat Schedule Additions

```python
# celery_app.py additions
"ingest-gilt-curve-daily": {
    "task": "ingestion.tasks.ingest_gilt_curve",
    "schedule": crontab(hour=18, minute=0),  # After BoE 17:00 UK publish
},
"ingest-vix-term-structure-15m": {
    "task": "ingestion.tasks.ingest_vix_term_structure",
    "schedule": timedelta(minutes=15),
},
"ingest-cboe-pcr-daily": {
    "task": "ingestion.tasks.ingest_cboe_pcr",
    "schedule": crontab(hour=21, minute=30),  # After US market close
},
"ingest-ons-daily": {
    "task": "ingestion.tasks.ingest_ons_batch",
    "schedule": timedelta(hours=24),
},
"ingest-bls-daily": {
    "task": "ingestion.tasks.ingest_bls_batch",
    "schedule": timedelta(hours=24),
},
"ingest-ecb-daily": {
    "task": "ingestion.tasks.ingest_ecb_batch",
    "schedule": timedelta(hours=24),
},
"compute-breadth-snapshot": {
    "task": "ingestion.tasks.compute_breadth_snapshot",
    "schedule": crontab(hour=22, minute=0),  # After CBOE task
},
```

### Config Additions (`config.py`)

```python
# Add to FRED_SERIES_MAP:
"tips_breakeven_5y": "T5YIE",
"tips_breakeven_10y": "T10YIE",
"hy_spread": "BAMLH0A0HYM2",
"safe_haven_usd": "DTWEXBGS",

# Add constants:
SCHEDULE_GILT = 86400      # 24h (daily)
SCHEDULE_VIX_TERM = 900    # 15 min
```

### New API Routes

Extend `backend/api/routes/macro.py` with new endpoints. All follow existing `cache_get` / `cache_set` / `get_async_db` pattern.

**New endpoints:**
```
GET /api/macro/gilt-curve                — latest gilt_curve row
GET /api/macro/gilt-curve/history        — last 400 rows (1Y+ daily)
GET /api/macro/yield-curve/spreads       — computed 2s10s, 5s30s from yield_curve + gilt_curve
GET /api/macro/yield-curve/shape         — curve shape classifier (NORMAL/FLAT/INVERTED/HUMPED)
GET /api/macro/vix-term-structure        — latest vix_term_structure row + regime classifier
GET /api/macro/vix-term-structure/history — last 2000 rows (~1Y of 15m data)
GET /api/macro/fear-greed                — composite score + 6 components, computed on request
GET /api/macro/seasonality/{ticker}      — monthly avg returns, 10Y history from OHLCV
```

### TTL Cache Keys

Add to `backend/cache/ttl.py`:
```python
"gilt_curve": 86400,          # 24h (daily publish)
"vix_term_structure": 900,    # 15 min (same as treasury)
"fear_greed": 3600,           # 1h composite
"breadth_snapshot": 86400,    # 24h (nightly compute)
"seasonality": 86400,         # 24h (historical averages)
```

### Fear & Greed Computation

The `/api/macro/fear-greed` endpoint computes the composite on demand from stored data. No separate table needed — all inputs are available in `macro_series`, `vix_term_structure`, and `ohlcv`.

**Computation flow:**
1. Fetch 1Y history of `vix_term_structure` → percentile rank of latest spot value
2. Fetch `macro_series` where `series_id = 'CBOE_PCR'` last 252 rows → percentile rank of latest, **inverted** (high P/C ratio = fear, low = greed; normalize so 100 = extreme greed)
3. Fetch `macro_series` where `series_id = 'BREADTH_PCT200'` last 252 rows → percentile rank
4. Fetch `macro_series` where `series_id = 'BAMLH0A0HYM2'` last 252 rows → percentile rank, **inverted** (high spread = fear)
5. Fetch `ohlcv` for `^GSPC` last 252 rows, compute 125-day ROC → percentile rank
6. Fetch `macro_series` where `series_id = 'DTWEXBGS'` last 252 rows, compute 20-day SMA distance → percentile rank, **inverted** (safe haven demand = fear)
7. Equal-weight average of 6 components

**Normalization formula:**
```python
def pct_rank(series: list[float], current: float) -> float:
    """Return 0-100 percentile rank of current in series."""
    below = sum(1 for x in series if x < current)
    return (below / len(series)) * 100
```

---

## Frontend Architecture

### Component Hierarchy

```
frontend/src/
├── components/
│   └── macro/
│       ├── MacroModule.tsx         — top-level, sub-tab state
│       ├── MacroSubTabNav.tsx      — [CURVES][INDICATORS][RISK][SENTIMENT] nav bar
│       ├── curves/
│       │   ├── CurvesTab.tsx       — left 60% + right 40% grid layout
│       │   ├── YieldCurveChart.tsx — snapshot chart (tenor on x-axis, yield on y-axis)
│       │   ├── SpreadPanel.tsx     — 2s10s + 5s30s time series, stacked
│       │   └── CurveShapePanel.tsx — classifier badge + TODAY/+1M/+1Y toggles
│       ├── indicators/
│       │   ├── IndicatorsTab.tsx   — 3×2 grid layout
│       │   └── MacroPanel.tsx      — reusable sparkline + current value + delta panel
│       ├── risk/
│       │   ├── RiskTab.tsx
│       │   ├── VixTermChart.tsx    — 3-line chart (spot/3M/6M)
│       │   ├── RegimeClassifier.tsx — badge + percentile
│       │   └── PutCallChart.tsx    — put/call ratio time series
│       └── sentiment/
│           ├── SentimentTab.tsx
│           ├── FearGreedGauge.tsx  — large gauge + color fill + component table
│           ├── AtAGlanceStrip.tsx  — DXY/SPX/FTSE 15s refresh (reuses WebSocket hook)
│           └── SeasonalityChart.tsx — monthly avg returns bar chart
├── hooks/
│   └── useMacroData.ts             — fetch all macro endpoints
└── App.tsx                         — add: {activeTab === "MACRO" && <MacroModule />}
```

### Sub-Tab Navigation Pattern

Mirrors the main tab bar in `App.tsx`. Use the same amber monospace button style. Active tab: `bg-terminal-amber text-black font-bold`. Inactive: `hover:bg-terminal-border`.

```tsx
// MacroSubTabNav.tsx — follows same pattern as MODULE_TABS in App.tsx
const MACRO_TABS = ["CURVES", "INDICATORS", "RISK", "SENTIMENT"] as const;
```

### Yield Curve Chart (Snapshot, Not Time Series)

The yield curve chart is unique in this project: x-axis = tenor (categorical: 6M, 1Y, 2Y, ..., 30Y), y-axis = yield %. This is NOT a time series chart — it is a snapshot chart. Use `lightweight-charts` `LineSeries` with explicit tenor labels as time values, or switch to `recharts` `LineChart` with categorical x-axis. Recharts is easier here since the x-axis is categorical.

**Recommendation (Claude's Discretion):** Use `recharts` `LineChart` with `XAxis dataKey="tenor"`. Two lines: US (amber, `TERMINAL.AMBER`) and UK gilt (green, `TERMINAL.GREEN`). Historical overlay lines (dashed, 50% opacity) when `[+1M]` or `[+1Y]` are active.

### Sparkline Charts in INDICATORS Panels

Each macro panel (CPI, GDP, etc.) needs a small sparkline. Use lightweight-charts `AreaSeries` at minimal height (~60px). The `ChartPanel.tsx` already uses lightweight-charts — reuse the same initialization pattern. Alternatively, a pure SVG path sparkline avoids chart overhead for 12-month views.

**Recommendation (Claude's Discretion):** SVG path sparkline for INDICATORS panels (no initialization overhead, trivial to implement, matches Bloomberg density aesthetic).

### Fear & Greed Gauge

A 180-degree arc gauge (semi-circle). Best approach: SVG arc segments colored per band, with a needle at the composite angle. No external library needed — pure SVG is ~50 lines.

```tsx
// Semi-circle arc gauge
// Outer arc: 5 colored bands (red/orange/amber/green/bright-green)
// Needle: rotated from 0° (left extreme = 0) to 180° (right extreme = 100)
const angle = (score / 100) * 180 - 90; // CSS rotation
```

### At-a-Glance Strip (DXY/SPX/FTSE)

Reuse `useEquityWebSocket` hook from `EquityModule`. DXY = `DX-Y.NYB` on yfinance, SPX = `^GSPC`, FTSE = `^FTSE`. These tickers exist in the seed list or can be added. Subscribe to the existing WebSocket channel for live 15s updates.

---

## Fear & Greed Implementation

### Component-by-Component Detail

| Component | Source Data | Normalization | Inversion? |
|-----------|-------------|---------------|-----------|
| VIX percentile | `vix_term_structure.spot` last 252 rows | pct_rank(252-day window) | Yes — high VIX = fear → score 0; low VIX = greed → score 100 |
| Put/call ratio | `macro_series` where `series_id='CBOE_PCR'` last 252 rows | pct_rank | Yes — high P/C = fear → score 0 |
| Market breadth | `macro_series` where `series_id='BREADTH_PCT200'` last 252 rows | pct_rank | No — high breadth = greed → score 100 |
| Junk bond spread | `macro_series` where `series_id='BAMLH0A0HYM2'` last 252 rows | pct_rank | Yes — high spread = fear → score 0 |
| SPX momentum | `ohlcv` where `ticker='^GSPC'` last 252 rows; compute 125-day ROC | pct_rank | No — positive ROC = greed → score 100 |
| Safe haven demand | `macro_series` where `series_id='DTWEXBGS'` last 252 rows; compute (value - SMA20) / SMA20 | pct_rank | Yes — positive divergence (USD rising) = fear → score 0 |

**Rolling window note:** If fewer than 252 rows exist for a component (e.g., CBOE_PCR data only goes back 180 days), use whatever is available. Show `"limited history"` flag in component breakdown table.

**Nightly breadth snapshot task:**
```python
# tasks.py — follows compute_nightly_pivot_points pattern
@app.task
def compute_breadth_snapshot():
    """Compute % of seed tickers above 200 SMA and store in macro_series."""
    from analysis.breadth import compute_pct_above_sma
    # Fetch last 250 days of OHLCV for all SEED_TICKERS
    # Compute pct_above_sma for each ticker with period=200
    # Store average across all tickers as BREADTH_PCT200
```

---

## Risks & Mitigations

### Risk 1: BoE IADB 403 Response
**Severity:** HIGH (blocks gilt curve ingestion entirely)
**What goes wrong:** The BoE IADB returns HTTP 403 to automated requests without a proper User-Agent header.
**Mitigation:** Set `headers={"User-Agent": "Mozilla/5.0 (compatible; personal-research-tool)"}` in `gilt_source.py`. Add a 2-second `time.sleep` before the request. If 403 persists, use exponential backoff with 3 retries before alerting.
**Fallback:** If the CDN endpoint is permanently blocked, the BoE also makes yield curve data available via Excel downloads at `https://www.bankofengland.co.uk/statistics/yield-curves`. Write a secondary `gilt_source_xlsx.py` using `openpyxl` as a failover, invoked if the primary CSV fetch fails 3+ times in a row.
**CRITICAL:** Implement the User-Agent fix in Wave 0 and manually verify the fetch succeeds before relying on it.

### Risk 2: VIX6M Limited History
**Severity:** MEDIUM (degrades quality of VIX term structure display)
**What goes wrong:** `^VIX6M` has approximately 1 year of Yahoo Finance history. A 1Y percentile rank over 1Y of data is meaningless (the score will always cluster near the median).
**Mitigation:** Display `^VIX6M` raw value in the term structure chart (the line still shows contango/backwardation structure). Suppress VIX6M from the Fear & Greed VIX percentile component (use only spot VIX). In the regime classifier, use spot VIX exclusively (consistent with D-20 which only references spot VIX thresholds). After accumulating 252 days of VIX6M data, enable the full percentile display.
**Implementation:** Add a `history_depth_ok` flag to the API response. Frontend shows `"accumulating history"` badge if flag is false.

### Risk 3: ONS Beta API Breaking Changes
**Severity:** LOW-MEDIUM (ONS labeled this API "beta" with possible breaking changes)
**What goes wrong:** ONS has already retired one API (Nov 2024). The beta API may evolve.
**Mitigation:** The two-step URI resolution approach is stable because URIs are documented as "evergreen". Hardcode the URIs after resolving them once during Wave 0 testing, and store them in `config.py`. If the endpoint changes, only the base URL needs updating.

### Risk 4: CBOE CDN URL Stability
**Severity:** MEDIUM (CBOE periodically restructures their CDN paths)
**What goes wrong:** The `cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv` URL may change.
**Mitigation:** If the CDN URL returns non-200, fall back to parsing the daily statistics page at `https://www.cboe.com/us/options/market_statistics/daily/` using BeautifulSoup. The P/C ratio table is present on that page as well.
**Testing:** Verify the CDN URL is still active during Wave 0 before committing to it.

### Risk 5: `ta_market_breadth` Table Does Not Exist
**Severity:** HIGH if not addressed in plan (blocks Fear & Greed breadth component)
**What goes wrong:** CONTEXT.md D-14 references `ta_market_breadth table` as if it exists. It does not. Phase 4 computed breadth in memory in `analysis/breadth.py` but never persisted snapshots.
**Mitigation:** Phase 5 must include a `compute_breadth_snapshot` nightly Celery task (see Backend Architecture section) as an explicit Wave 0 task. The breadth component for Fear & Greed becomes available only after the first nightly run following deployment.
**Planner action:** Make `compute_breadth_snapshot` task creation the first backend wave item. The Fear & Greed endpoint should degrade gracefully if `BREADTH_PCT200` has zero rows (show 50/neutral for that component with a "pending first run" note).

### Risk 6: BLS API Key Requirement
**Severity:** LOW (easy to mitigate)
**What goes wrong:** BLS API v2 requires free registration. If `BLS_API_KEY` is not set, NFP ingestion fails silently.
**Mitigation:** Check env var in `bls_source.py` (mirrors `fred_source.py` pattern). Add `BLS_API_KEY` to `.env.example`. Document signup URL at `https://data.bls.gov/registrationEngine/registerGateway.action`. The API key is delivered by email within minutes of registration.

### Risk 7: ECB SDMX Key String Complexity
**Severity:** LOW (now verified to work)
**What goes wrong:** The ECB GDP key string is 44 characters long and looks intimidating. Future maintainers may not know how to construct new ECB queries.
**Mitigation:** Document the key structure in `ecb_source.py` comments. The ECB Data Portal at `data.ecb.europa.eu` allows browsing series to find key strings. For policy rate: use `FM.B.U2.EUR.4F.KR.MRR_FR.LEV`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | `backend/tests/` existing structure |
| Quick run command | `pytest backend/tests/ -x -q` |
| Full suite command | `pytest backend/tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| MACRO-01 | US Treasury yield curve display | smoke | Frontend visual check | Existing ingestion; frontend-only |
| MACRO-02 | BoE gilt curve ingestion + display | unit + smoke | `pytest backend/tests/ingestion/test_gilt_source.py -x` | Wave 0 gap |
| MACRO-03 | 2s10s + 5s30s spread computation | unit | `pytest backend/tests/api/test_macro_routes.py::test_spreads -x` | Wave 0 gap |
| MACRO-04 | Curve shape classifier | unit | `pytest backend/tests/api/test_macro_routes.py::test_curve_shape -x` | Wave 0 gap |
| MACRO-05 | Historical overlay data at -1M, -1Y | unit | `pytest backend/tests/api/test_macro_routes.py::test_curve_history -x` | Wave 0 gap |
| MACRO-06 | TIPS breakeven FRED series | unit | `pytest backend/tests/ingestion/test_fred_source.py -x` | Extend existing |
| MACRO-07 | CPI + UK CPI panel display | unit + smoke | `pytest backend/tests/ingestion/test_ons_source.py -x` | Wave 0 gap |
| MACRO-08 | NFP/unemployment via BLS + ONS | unit | `pytest backend/tests/ingestion/test_bls_source.py -x` | Wave 0 gap |
| MACRO-09 | GDP via FRED + ONS + ECB | unit | `pytest backend/tests/ingestion/test_ecb_source.py -x` | Wave 0 gap |
| MACRO-10 | Policy rates panel | smoke | Frontend visual; data from existing FRED + new BoE rate series | — |
| MACRO-11 | VIX term structure chart + contango badge | unit | `pytest backend/tests/ingestion/test_vix_term.py -x` | Wave 0 gap |
| MACRO-12 | VIX regime classifier | unit | `pytest backend/tests/api/test_macro_routes.py::test_vix_regime -x` | Wave 0 gap |
| MACRO-13 | Fear & Greed composite (all 6 components) | unit | `pytest backend/tests/api/test_macro_routes.py::test_fear_greed -x` | Wave 0 gap |
| MACRO-14 | At-a-glance strip + seasonality | smoke | Frontend visual | WebSocket reuse |

### Data Source Insertion Checks

Each new ingestion source needs a smoke test that verifies at least one row was inserted:

```python
# Pattern for each source test
def test_gilt_curve_insertion(db_session):
    from ingestion.sources.gilt_source import fetch_gilt_curve
    rows = fetch_gilt_curve()
    assert len(rows) >= 1
    assert rows[0]["gc_10year"] is not None  # must have 10Y tenor

def test_ons_insertion():
    from ingestion.sources.ons_source import fetch_ons_series
    obs = fetch_ons_series("L522")  # UK CPI
    assert len(obs) >= 12  # at least 12 months
    assert float(obs[0]["value"]) > 0

def test_cboe_pcr():
    from ingestion.sources.cboe_source import fetch_cboe_pcr
    pcr = fetch_cboe_pcr()
    assert 0.0 < pcr < 5.0  # sanity range for P/C ratio
```

### Fear & Greed Unit Tests

```python
def test_pct_rank_normalization():
    series = list(range(100))
    assert pct_rank(series, 50) == pytest.approx(50.0, abs=1)
    assert pct_rank(series, 99) == pytest.approx(99.0, abs=1)
    assert pct_rank(series, 0) == pytest.approx(0.0, abs=1)

def test_fear_greed_neutral_with_missing_components():
    # If breadth component is missing, composite should still return
    # the average of the remaining 5, not raise an exception
    ...
```

### Sampling Rate
- Per task commit: `pytest backend/tests/ -x -q`
- Per wave merge: `pytest backend/tests/ -q`
- Phase gate: Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/ingestion/test_gilt_source.py` — BoE IADB fetch test
- [ ] `backend/tests/ingestion/test_ons_source.py` — ONS beta API test (L522, LF2Q, ABMI)
- [ ] `backend/tests/ingestion/test_bls_source.py` — BLS API v2 test (CES0000000001)
- [ ] `backend/tests/ingestion/test_ecb_source.py` — ECB SDMX test (GDP + policy rate)
- [ ] `backend/tests/ingestion/test_cboe_source.py` — CBOE PCR CSV test
- [ ] `backend/tests/ingestion/test_vix_term.py` — yfinance VIX3M/VIX6M test
- [ ] `backend/tests/api/test_macro_routes.py` — spread/shape/VIX/Fear-Greed endpoint tests

---

## Standard Stack

### Core (no new packages — all already in stack)
| Library | Use |
|---------|-----|
| `requests` | All HTTP fetches (BoE, ONS, BLS, ECB, CBOE) |
| `sqlalchemy` | ORM for new models (`GiltCurve`, `VixTermStructure`) |
| `yfinance` | VIX term structure tickers |
| `celery` | New beat schedule entries |
| `redis` | Cache for new TTL entries |

### Supporting (Claude's Discretion for frontend charts)
| Library | Version | Already in Use | Use |
|---------|---------|---------------|-----|
| `recharts` | Check `package.json` | Likely yes | Yield curve snapshot chart (categorical x-axis), sparklines |
| `lightweight-charts` | Already in use | Yes | VIX term structure time series (matches existing CandleChart) |

### Frontend check needed
```bash
grep "recharts\|lightweight-charts" /c/hhbfin/frontend/package.json
```
Verify which charting libraries are already installed before planning imports.

---

## Code Examples

### BoE IADB Fetch Pattern (gilt_source.py)
```python
# Source: BoE IADB CSV endpoint — confirmed pattern from community code examples
import requests, csv, io, time
from datetime import datetime

BOE_URL = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"
BOE_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; personal-research-tool)"}

def fetch_gilt_curve() -> list[dict]:
    time.sleep(2)  # Be polite to BoE servers
    params = {
        "csv.x": "yes",
        "SeriesCodes": "IUDMNZC",
        "Datefrom": "01/Jan/2024",
        "Dateto": "now",
        "CSVF": "TT",
        "UsingCodes": "Y",
        "VPD": "Y",
        "VFD": "N",
    }
    r = requests.get(BOE_URL, params=params, headers=BOE_HEADERS, timeout=30)
    r.raise_for_status()
    # Parse CSV — headers in first row
    reader = csv.DictReader(io.StringIO(r.text))
    rows = []
    for row in reader:
        # NOTE: verify exact column names during Wave 0 — log reader.fieldnames
        try:
            date = datetime.strptime(row["DATE"].strip(), "%d %b %Y")
        except (KeyError, ValueError):
            continue
        rows.append({"date": date, "raw": row})
    return rows
```

### ONS Beta API Fetch Pattern (ons_source.py)
```python
# Source: Verified via live fetch of L522 data (2026-03-30)
import requests

ONS_BASE = "https://api.beta.ons.gov.uk/v1"
# Hardcode URIs after resolving once (URIs are documented as evergreen)
ONS_URIS = {
    "L522": "/economy/inflationandpriceindices/timeseries/l522/mm23",  # UK CPI
    "LF2Q": None,  # resolve on first run
    "ABMI": None,  # resolve on first run
}

def resolve_uri(series_id: str) -> str:
    r = requests.get(f"{ONS_BASE}/search", params={
        "content_type": "timeseries", "cdids": series_id
    }, timeout=15)
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        raise ValueError(f"ONS series {series_id} not found")
    return items[0]["uri"]

def fetch_ons_series(series_id: str) -> list[dict]:
    uri = ONS_URIS.get(series_id) or resolve_uri(series_id)
    r = requests.get(f"{ONS_BASE}/data", params={"uri": uri}, timeout=15)
    r.raise_for_status()
    data = r.json()
    # Use monthly observations; fall back to quarters if months empty
    obs_list = data.get("months") or data.get("quarters") or []
    return [
        {"date": obs["date"], "value": float(obs["value"])}
        for obs in obs_list
        if obs.get("value")
    ]
```

### ECB SDMX Fetch Pattern (ecb_source.py)
```python
# Source: Verified via live fetch confirming 2024-Q1 through 2025-Q4 data (2026-03-30)
import requests, csv, io

ECB_BASE = "https://data-api.ecb.europa.eu/service/data"
ECB_SERIES = {
    "gdp_growth": "MNA/Q.Y.I9.W2.S1.S1.B.B1GQ._Z._Z._Z.EUR.LR.GY",
    "ecb_rate":   "FM/B.U2.EUR.4F.KR.MRR_FR.LEV",
}

def fetch_ecb_series(key: str, last_n: int = 40) -> list[dict]:
    flow_key = ECB_SERIES[key]
    url = f"{ECB_BASE}/{flow_key}"
    params = {"lastNObservations": last_n, "format": "csvdata"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    return [
        {"date": row["TIME_PERIOD"], "value": float(row["OBS_VALUE"])}
        for row in reader
        if row.get("OBS_VALUE")
    ]
```

### CBOE PCR Fetch Pattern (cboe_source.py)
```python
# Source: Verified via live fetch — equitypc.csv returns full history (2026-03-30)
import requests, csv, io
from datetime import datetime

CBOE_PCR_URL = "https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv"

def fetch_cboe_pcr_latest() -> dict:
    """Fetch the latest equity put/call ratio. Returns {'date': date, 'value': float}."""
    r = requests.get(CBOE_PCR_URL, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)
    last = rows[-1]  # Last row = latest business day
    return {
        "date": datetime.strptime(last["DATE"].strip(), "%m/%d/%Y"),
        "value": float(last["P/C Ratio"]),
    }
```

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| `requests` | All HTTP fetches | Yes | Already in backend |
| `yfinance` | VIX term structure | Yes | Already in backend |
| `celery` | New beat tasks | Yes | Already in stack |
| `redis` | Cache | Yes | Already in stack |
| `lxml` | BoE XML (treasury uses it) | Yes | Already in backend |
| BoE IADB endpoint | gilt_source.py | Likely yes | 403 from automated fetchers; User-Agent fix required |
| ONS beta API | ons_source.py | Yes | Verified live |
| BLS API v2 | bls_source.py | Yes (after key) | `BLS_API_KEY` env var required |
| ECB SDMX | ecb_source.py | Yes | Verified live |
| CBOE CDN | cboe_source.py | Yes | Verified live |
| `^VIX3M` yfinance | vix_term_structure | Yes | Yahoo Finance page confirmed active |
| `^VIX6M` yfinance | vix_term_structure | Yes (limited) | ~1Y history only |

**Missing dependencies with fallback:**
- `^VIX6M` limited history — show raw value, suppress percentile rank until 252 days accumulated
- `BREADTH_PCT200` data — gracefully defaults to 50 (neutral) until first nightly compute run

**Missing dependencies with no fallback:**
- `BLS_API_KEY` — NFP ingestion fails without it. Must add to `.env.example` and document signup.

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|-----------------|-------|
| `api.ons.gov.uk` (V0) | `api.beta.ons.gov.uk/v1` | V0 retired Nov 2024 — do NOT use old URL |
| ECB SDW legacy endpoint `sdw-wsrest.ecb.europa.eu` | `data-api.ecb.europa.eu` | Both work; new portal is preferred |

---

## Open Questions

1. **BoE IADB exact column header names**
   - What we know: IUDMNZC series exists, CSV format confirmed, `CSVF=TT` returns titled CSV
   - What's unclear: Whether columns are named `IUDMNZC.05` or `IUDMNZC_0.5` or `6 month` etc.
   - Recommendation: Log `reader.fieldnames` in Wave 0 fetch test and update the model accordingly before implementation

2. **ONS LF2Q and ABMI URIs**
   - What we know: L522 URI confirmed as `/economy/inflationandpriceindices/timeseries/l522/mm23`
   - What's unclear: Exact URIs for LF2Q (unemployment) and ABMI (GDP)
   - Recommendation: Resolve via `/v1/search?content_type=timeseries&cdids=LF2Q` during Wave 0 and hardcode in `config.py`

3. **BoE policy base rate series code**
   - What we know: IUDBEDR is the BoE base rate series code in IADB (referenced in research)
   - What's unclear: Whether it follows the same CSV download pattern as IUDMNZC
   - Recommendation: Reuse the same `gilt_source.py` fetch function with `SeriesCodes=IUDBEDR`; verify during Wave 0

4. **recharts vs lightweight-charts for yield curve snapshot**
   - What we know: lightweight-charts is already used for time-series charts
   - What's unclear: Whether lightweight-charts supports categorical (non-time) x-axis
   - Recommendation: lightweight-charts requires a time value on x-axis; use recharts for the tenor snapshot chart. Verify recharts is in `package.json` first.

---

## Sources

### Primary (HIGH confidence)
- CBOE equity put/call CSV live fetch (2026-03-30): `cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv`
- ECB SDMX live fetch (2026-03-30): `data-api.ecb.europa.eu/service/data/MNA/...`
- ONS beta API live fetch (2026-03-30): `api.beta.ons.gov.uk/v1/data?uri=/economy/inflationandpriceindices/timeseries/l522/mm23`
- BLS API v2 official guide: `bd-econ.com/blsapi.html`
- ONS V0 retirement blog: `onsdigital.blog.gov.uk/2024/09/16/changes-were-making-to-our-api-service/`
- ONS developer hub migration guide: `developer.ons.gov.uk/retirement/v0api/`

### Secondary (MEDIUM confidence)
- BoE IADB URL pattern: community Python code examples and WebSearch results confirming `_iadb-fromshowcolumns.asp` with `csv.x=yes` parameters
- BoE IUDMNZC series existence: confirmed via BoE Database search results URL showing valid series page
- `^VIX3M` availability: Yahoo Finance historical data page confirmed active
- BLS rate limits (500/day): confirmed via multiple independent sources

### Tertiary (LOW confidence)
- `^VIX6M` history depth: Yahoo Finance search result shows "Feb 23, 2025 - Feb 23, 2026" range, implying ~1Y. Not verified by direct API call.
- BoE IADB CSV column header format (exact names): blocked by 403. Community examples show `Datefrom`/`Dateto` params but not exact output column names for IUDMNZC.

---

## Metadata

**Confidence breakdown:**
- Data source endpoints: HIGH (ONS, ECB, CBOE live-verified; BLS official docs)
- BoE IADB endpoint: MEDIUM (URL pattern confirmed; User-Agent fix needed; column names unverified)
- VIX6M history depth: LOW (inferred from search snippet)
- Frontend patterns: HIGH (directly read from existing codebase)
- DB schema: HIGH (mirrors existing patterns)

**Research date:** 2026-03-30
**Valid until:** 2026-05-30 (stable APIs; 60 days before recheck)
