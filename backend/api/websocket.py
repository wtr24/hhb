import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager with per-channel fan-out (per D-07, D-10).
    Single instance. Redis pub/sub listener calls broadcast_to_channel.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.channel_subscriptions: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.unsubscribe_all(websocket)

    def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a client to a specific channel (per D-07)."""
        self.channel_subscriptions.setdefault(channel, set()).add(websocket)

    def unsubscribe_all(self, websocket: WebSocket):
        """Remove client from all channel subscriptions."""
        for subs in self.channel_subscriptions.values():
            subs.discard(websocket)

    async def broadcast_to_channel(self, channel: str, message: dict):
        """Fan out message to all clients subscribed to channel (per D-10)."""
        dead = []
        for ws in list(self.channel_subscriptions.get(channel, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unsubscribe_all(ws)
            if ws in self.active_connections:
                self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        """Legacy broadcast-all (kept for backward compatibility)."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    async def send_initial_snapshot(self, websocket: WebSocket, channel: str):
        """D-09: On subscribe, send latest TimescaleDB row immediately."""
        from api.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            row = await _fetch_latest_for_channel(channel, session)
            if row:
                await websocket.send_json({**row, "stale": True, "channel": channel})


manager = ConnectionManager()


async def _fetch_latest_for_channel(channel: str, session) -> dict | None:
    """Fetch latest DB row for a given pub/sub channel."""
    parts = channel.split(":", 1)
    if len(parts) != 2:
        return None

    channel_type, identifier = parts

    if channel_type == "quotes":
        from models.ohlcv import OHLCV
        result = await session.execute(
            select(OHLCV).where(OHLCV.ticker == identifier).order_by(desc(OHLCV.time)).limit(1)
        )
        row = result.scalar_one_or_none()
        if row:
            return {
                "ticker": row.ticker,
                "price": float(row.close) if row.close else None,
                "open": float(row.open) if row.open else None,
                "high": float(row.high) if row.high else None,
                "low": float(row.low) if row.low else None,
                "close": float(row.close) if row.close else None,
                "volume": int(row.volume) if row.volume else None,
                "timestamp": row.time.isoformat(),
            }

    elif channel_type == "macro":
        from models.macro_series import MacroSeries
        from ingestion.config import FRED_SERIES_MAP
        fred_id = FRED_SERIES_MAP.get(identifier)
        if fred_id:
            result = await session.execute(
                select(MacroSeries).where(MacroSeries.series_id == fred_id)
                .order_by(desc(MacroSeries.time)).limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                return {
                    "series": identifier,
                    "value": float(row.value) if row.value else None,
                    "timestamp": row.time.isoformat(),
                }

    elif channel_type == "fx":
        from models.fx_rate import FXRate
        # Channel format: fx:USDGBP — base=first 3 chars, quote=last 3 chars
        if len(identifier) == 6:
            base, quote = identifier[:3], identifier[3:]
            result = await session.execute(
                select(FXRate).where(FXRate.base == base, FXRate.quote == quote)
                .order_by(desc(FXRate.time)).limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                return {
                    "base": row.base,
                    "quote": row.quote,
                    "rate": float(row.rate),
                    "timestamp": row.time.isoformat(),
                }

    return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with channel subscription support (per D-07).

    Client sends: {"action": "subscribe", "channels": ["quotes:AAPL", "fx:USDGBP"]}
    Server pushes: messages matching subscribed channels
    On subscribe: server sends latest DB row immediately (per D-09)
    """
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "invalid_json"})
                continue

            action = data.get("action")

            if action == "subscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    manager.subscribe(websocket, channel)
                    # D-09: send initial snapshot from TimescaleDB
                    await manager.send_initial_snapshot(websocket, channel)
                await websocket.send_json({"action": "subscribed", "channels": channels})

            elif action == "unsubscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    subs = manager.channel_subscriptions.get(channel, set())
                    subs.discard(websocket)
                await websocket.send_json({"action": "unsubscribed", "channels": channels})

            else:
                await websocket.send_json({"error": "unknown_action", "received": action})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
