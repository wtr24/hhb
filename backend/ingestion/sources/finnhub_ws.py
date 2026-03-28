"""
Finnhub WebSocket client for live US stock quotes.

Finnhub free tier: US stocks + forex + crypto only.
LSE tickers (.L suffix) not supported — fall back to yfinance 5m polling via
existing Celery beat ingest_ohlcv_batch. Indices (^FTSE etc.) not supported either.

Publishes trade data to Redis pub/sub channel quotes:{symbol} in the same message
format as Phase 2 D-08 ingest_ticker, so the existing WebSocket fan-out in
api/websocket.py requires no changes.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

import websockets

logger = logging.getLogger(__name__)

_WS_URL = "wss://ws.finnhub.io?token={api_key}"
_RECONNECT_DELAY = 5  # seconds between reconnect attempts


def is_finnhub_ws_eligible(symbol: str) -> bool:
    """Return True if the symbol is eligible for Finnhub WebSocket (free tier).

    Eligible: US stocks, forex pairs, crypto.
    Ineligible: LSE tickers (.L suffix), indices (^ prefix).

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. "AAPL", "LLOY.L", "^FTSE", "BTC-USD".

    Returns
    -------
    bool
    """
    if symbol.endswith(".L"):
        return False
    if symbol.startswith("^"):
        return False
    return True


class FinnhubWebSocket:
    """Async Finnhub WebSocket client.

    Connects to wss://ws.finnhub.io, subscribes to eligible tickers from
    FINNHUB_WS_SYMBOLS, and publishes trade messages to Redis pub/sub
    channel quotes:{symbol} so the existing api/websocket.py fan-out
    delivers them to browser clients.

    Usage (from FastAPI lifespan)::

        finnhub_ws = FinnhubWebSocket(api_key, redis_client)
        task = asyncio.create_task(finnhub_ws.connect_and_listen())
        ...
        task.cancel()
    """

    def __init__(self, api_key: str, redis_client):
        self.api_key = api_key
        self.redis_client = redis_client
        self.subscribed_symbols: set[str] = set()
        self._ws = None

    async def connect_and_listen(self):
        """Main loop: connect, subscribe to seed tickers, listen for trades.

        Reconnects automatically on disconnect or error with a 5-second delay.
        Runs until the asyncio task is cancelled (on FastAPI shutdown).
        """
        from ingestion.config import FINNHUB_WS_SYMBOLS

        url = _WS_URL.format(api_key=self.api_key)
        while True:
            try:
                logger.info("Finnhub WS: connecting to %s", url.split("?")[0])
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    self.subscribed_symbols.clear()
                    # Subscribe to all eligible seed tickers
                    for symbol in FINNHUB_WS_SYMBOLS:
                        await self.subscribe(symbol)
                    logger.info(
                        "Finnhub WS: subscribed to %d symbols: %s",
                        len(self.subscribed_symbols),
                        sorted(self.subscribed_symbols),
                    )
                    # Listen for messages until disconnect
                    async for raw in ws:
                        await self._handle_message(raw)
            except asyncio.CancelledError:
                logger.info("Finnhub WS: listener cancelled — shutting down")
                raise
            except Exception as exc:
                logger.warning(
                    "Finnhub WS: connection lost (%s) — reconnecting in %ds",
                    exc,
                    _RECONNECT_DELAY,
                )
                self._ws = None
                await asyncio.sleep(_RECONNECT_DELAY)

    async def subscribe(self, symbol: str):
        """Send a subscribe message for a symbol.

        Only US-eligible symbols (no .L suffix, no ^ prefix) are accepted.
        LSE tickers are silently skipped — they use yfinance Celery polling.

        Parameters
        ----------
        symbol : str
            Ticker symbol to subscribe to.
        """
        if not is_finnhub_ws_eligible(symbol):
            logger.debug("Finnhub WS: skipping ineligible symbol %s (LSE/index)", symbol)
            return
        if self._ws is None:
            logger.warning("Finnhub WS: subscribe called before connection for %s", symbol)
            return
        msg = json.dumps({"type": "subscribe", "symbol": symbol})
        await self._ws.send(msg)
        self.subscribed_symbols.add(symbol)

    async def _handle_message(self, raw: str):
        """Parse a Finnhub trade message and publish to Redis pub/sub.

        Message format::

            {"type": "trade", "data": [{"s": "AAPL", "p": 189.5, "t": 1575526691134, "v": 0.01}]}

        Each trade item is published to quotes:{symbol} as a JSON string matching
        the Phase 2 D-08 format used by ingest_ticker.

        Parameters
        ----------
        raw : str
            Raw WebSocket message string.
        """
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.debug("Finnhub WS: could not parse message: %s", raw[:200])
            return

        if parsed.get("type") != "trade":
            # ping/pong or subscription confirmation — ignore
            return

        for item in parsed.get("data") or []:
            symbol = item.get("s")
            price = item.get("p")
            timestamp_ms = item.get("t")
            volume = item.get("v")

            if not symbol or price is None:
                continue

            # Convert ms timestamp to ISO 8601 string (UTC)
            if timestamp_ms:
                ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()
            else:
                ts = datetime.now(tz=timezone.utc).isoformat()

            # Phase 2 D-08 message format (consistent with ingest_ticker pub/sub)
            msg = {
                "channel": f"quotes:{symbol}",
                "ticker": symbol,
                "price": price,
                "volume": volume,
                "timestamp": ts,
                "stale": False,
            }

            try:
                self.redis_client.publish(f"quotes:{symbol}", json.dumps(msg, default=str))
            except Exception as exc:
                logger.error("Finnhub WS: Redis publish failed for %s: %s", symbol, exc)
