"""
Equity-specific REST endpoints.

Wave 0 stubs: all endpoints return 501 Not Implemented.
Stubs are replaced wave by wave in Phase 3 (Waves 1-4).
"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/equity", tags=["equity"])


@router.get("/earnings/{ticker}")  # EQUITY-04
async def get_earnings(ticker: str):
    """Return earnings calendar dates for a ticker. Implemented in Wave 1."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "earnings"})


@router.get("/dividends/{ticker}")  # EQUITY-05
async def get_dividends(ticker: str):
    """Return dividend ex-dates for a ticker. Implemented in Wave 1."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "dividends"})


@router.get("/fundamentals/{ticker}")  # EQUITY-06 (enhanced with ROE)
async def get_fundamentals(ticker: str):
    """Return fundamentals (P/E, EV/EBITDA, ROE, D/E, market cap). Implemented in Wave 1."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "fundamentals"})


@router.get("/short-interest/{ticker}")  # EQUITY-07
async def get_short_interest(ticker: str):
    """Return short interest data. US-only on free tier. Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "short_interest"})


@router.get("/insiders/{ticker}")  # EQUITY-08
async def get_insiders(ticker: str):
    """Return insider transaction clusters. US-only on free tier. Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "insiders"})


@router.get("/options/{ticker}")  # EQUITY-09
async def get_options(ticker: str):
    """Return options chain with Black-Scholes Greeks. Implemented in Wave 3."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "options"})


@router.get("/news/{ticker}")  # EQUITY-10
async def get_news(ticker: str):
    """Return company news headlines. Implemented in Wave 2."""
    return JSONResponse(status_code=501, content={"status": "not_implemented", "endpoint": "news"})
