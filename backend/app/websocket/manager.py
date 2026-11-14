import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set
import uuid
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from app.core.logging import logger


class WebSocketManager:
    """
    Robust real-time telemetry connection manager for PAYGUARD Phase 5.
    Supports:
    - Multiple simultaneous client connections with unique client IDs
    - Dynamic category-based subscriptions (transactions, security, blockchain, escrow, system, all)
    - Heartbeat tracking and graceful disconnect cleanup
    - Safe non-blocking asynchronous event dispatching
    - Health diagnostics and active client metrics
    - DoS connection limit and subscription category whitelisting
    """

    MAX_CONNECTIONS: int = 200
    ALLOWED_CATEGORIES: Set[str] = {"transactions", "security", "blockchain", "escrow", "system", "all"}

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
        self.client_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.total_connections_ever: int = 0
        self.total_messages_broadcast: int = 0
        self.last_broadcast_time: Optional[str] = None

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
        subscriptions: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Registers a new WebSocket client and configures subscriptions."""
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            logger.warning(f"[WebSocketManager] Connection rejected: maximum capacity ({self.MAX_CONNECTIONS}) reached.")
            if hasattr(websocket, "close"):
                await websocket.close(code=1008, reason="Server connection capacity reached")
            return None

        if hasattr(websocket, "accept"):
            await websocket.accept()
        cid = client_id or f"client_{uuid.uuid4().hex[:8]}"

        self.active_connections.append(websocket)
        raw_subs = subscriptions or ["all"]
        sanitized_subs = {s.lower().strip() for s in raw_subs if s.lower().strip() in self.ALLOWED_CATEGORIES}
        subs = sanitized_subs if sanitized_subs else {"all"}
        self.client_subscriptions[websocket] = subs
        self.client_metadata[websocket] = {
            "client_id": cid,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "subscriptions": subs,
            "last_ping": datetime.now(timezone.utc).isoformat(),
        }
        self.total_connections_ever += 1

        logger.info(f"[WebSocketManager] Client connected ({cid}). Active clients: {len(self.active_connections)}")
        return cid

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a client connection and cleans up associated state."""
        meta = self.client_metadata.get(websocket, {})
        cid = meta.get("client_id", "unknown")

        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.client_subscriptions.pop(websocket, None)
        self.client_metadata.pop(websocket, None)

        logger.info(f"[WebSocketManager] Client disconnected ({cid}). Active clients: {len(self.active_connections)}")

    def update_subscriptions(self, websocket: WebSocket, categories: List[str]) -> Set[str]:
        """Updates the subscribed event categories for a client, enforcing category whitelist."""
        if websocket in self.client_subscriptions:
            sanitized = {c.lower().strip() for c in categories if c.lower().strip() in self.ALLOWED_CATEGORIES}
            subs = sanitized if sanitized else {"all"}
            self.client_subscriptions[websocket] = subs
            if websocket in self.client_metadata:
                self.client_metadata[websocket]["subscriptions"] = subs
            return subs
        return set()

    def record_heartbeat(self, websocket: WebSocket) -> None:
        """Records ping timestamp for a client."""
        if websocket in self.client_metadata:
            self.client_metadata[websocket]["last_ping"] = datetime.now(timezone.utc).isoformat()

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> bool:
        """Delivers a direct JSON message to a specific connected client."""
        state = getattr(websocket, "client_state", None)
        if state is not None and state != WebSocketState.CONNECTED and state != 1:
            self.disconnect(websocket)
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"[WebSocketManager] Error sending personal message: {e}")
            self.disconnect(websocket)
            return False

    async def broadcast_json(self, data: dict, category: Optional[str] = None) -> int:
        """
        Asynchronously broadcasts an event to all clients subscribed to its category.
        Non-blocking: dispatches concurrently across connections without halting the event loop.
        """
        cat = category or data.get("category", "transactions")
        targets: List[WebSocket] = []

        for conn in list(self.active_connections):
            subs = self.client_subscriptions.get(conn, set())
            if "all" in subs or cat in subs or not subs:
                targets.append(conn)

        if not targets:
            return 0

        async def _safe_send(ws: WebSocket):
            try:
                state = getattr(ws, "client_state", None)
                if state is None or state == WebSocketState.CONNECTED or state == 1:
                    await ws.send_json(data)
                    return True
                else:
                    self.disconnect(ws)
                    return False
            except Exception as e:
                logger.debug(f"[WebSocketManager] Dropped disconnected client: {e}")
                self.disconnect(ws)
                return False

        results = await asyncio.gather(*[_safe_send(ws) for ws in targets], return_exceptions=True)
        sent_count = sum(1 for r in results if r is True)

        self.total_messages_broadcast += sent_count
        self.last_broadcast_time = datetime.now(timezone.utc).isoformat()
        return sent_count

    def get_health_metrics(self) -> Dict[str, Any]:
        """Returns live diagnostics of active WebSocket connections and throughput."""
        return {
            "status": "HEALTHY" if len(self.active_connections) >= 0 else "DEGRADED",
            "active_connections": len(self.active_connections),
            "total_connections_ever": self.total_connections_ever,
            "total_messages_broadcast": self.total_messages_broadcast,
            "last_broadcast_time": self.last_broadcast_time,
            "clients": [
                {
                    "client_id": meta.get("client_id"),
                    "connected_at": meta.get("connected_at"),
                    "subscriptions": list(meta.get("subscriptions", [])),
                }
                for meta in self.client_metadata.values()
            ],
        }


ws_manager = WebSocketManager()
