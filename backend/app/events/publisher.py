from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
import uuid

from app.core.logging import logger
from app.db.database import db
from app.schemas.event import EventCategory, EventSeverity, PayguardEvent
from app.websocket.manager import ws_manager

SENSITIVE_KEY_SUBSTRINGS = {"private_key", "secret", "seed", "token", "password", "signer_secret", "api_key", "credential"}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts sensitive cryptographic secrets, seed phrases, or credentials."""
    if isinstance(data, dict):
        clean = {}
        for k, v in data.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEY_SUBSTRINGS):
                clean[k] = "[REDACTED]"
            else:
                clean[k] = redact_sensitive_data(v)
        return clean
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


class EventPublisher:
    """
    Centralized event publisher for PAYGUARD Phase 5.
    Unifies all backend services, multi-agent evaluation nodes, deterministic policy checks,
    and NEAR blockchain monitoring into a single standardized, persisted, and real-time event pipeline.
    """

    def __init__(self, max_recent_ids: int = 5000):
        self._recent_event_ids: Set[str] = set()
        self._id_ring_buffer: deque = deque(maxlen=max_recent_ids)

    def _derive_category(self, event_type: str) -> EventCategory:
        if event_type.startswith("transaction."):
            return EventCategory.TRANSACTIONS
        elif event_type.startswith("escrow."):
            return EventCategory.ESCROW
        elif event_type.startswith("security.") or "prompt." in event_type or "intent." in event_type:
            return EventCategory.SECURITY
        elif event_type.startswith("blockchain."):
            return EventCategory.BLOCKCHAIN
        elif event_type.startswith("system.") or event_type.startswith("metrics."):
            return EventCategory.SYSTEM
        return EventCategory.TRANSACTIONS

    def _derive_severity(self, event_type: str) -> EventSeverity:
        if any(term in event_type for term in ["blocked", "failed", "prompt_injection", "anomaly", "connection_lost", "critical"]):
            return EventSeverity.CRITICAL
        elif any(term in event_type for term in ["warn", "warning", "threshold", "escrow.created", "rejected"]):
            return EventSeverity.WARNING
        elif any(term in event_type for term in ["confirmed", "allowed", "approved", "released", "restored", "success"]):
            return EventSeverity.SUCCESS
        return EventSeverity.INFO

    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        transaction_id: Optional[str] = None,
        source: str = "backend",
        severity: Optional[str] = None,
        category: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> PayguardEvent:
        """
        Validates, sanitizes, deduplicates, persists, and broadcasts a standardized PayguardEvent.
        """
        evt_id = event_id or f"evt_{uuid.uuid4().hex[:12]}"

        # Prevent duplicate processing
        if evt_id in self._recent_event_ids:
            logger.debug(f"[EventPublisher] Dropping duplicate event {evt_id}")
            existing = db.get_event(evt_id)
            if existing:
                return PayguardEvent(**existing)

        # Derive category and severity if not explicitly provided
        cat = EventCategory(category.lower()) if category else self._derive_category(event_type)
        sev = EventSeverity(severity) if severity else self._derive_severity(event_type)

        # Redact any private credentials or signing secrets
        clean_payload = redact_sensitive_data(payload)

        # Build timezone-aware UTC ISO timestamp
        ts = datetime.now(timezone.utc).isoformat()

        event = PayguardEvent(
            event_id=evt_id,
            event_type=event_type,
            category=cat,
            transaction_id=transaction_id or clean_payload.get("transaction_id"),
            timestamp=ts,
            source=source,
            severity=sev,
            payload=clean_payload,
        )

        # Track event ID in memory deduplication buffer
        self._recent_event_ids.add(evt_id)
        if len(self._id_ring_buffer) == self._id_ring_buffer.maxlen:
            oldest_id = self._id_ring_buffer.popleft()
            self._recent_event_ids.discard(oldest_id)
        self._id_ring_buffer.append(evt_id)

        # 1. Persist to SQLite ledger
        try:
            db.save_event(event.model_dump())
        except Exception as e:
            logger.warning(f"[EventPublisher] Failed to persist event {evt_id}: {e}")

        # 2. Prepare wire format maintaining backwards compatibility
        wire_data = {
            "type": event.event_type,
            "event_type": event.event_type,
            "event_id": event.event_id,
            "transaction_id": event.transaction_id,
            "category": event.category.value,
            "severity": event.severity.value,
            "timestamp": event.timestamp,
            "source": event.source,
            "payload": event.payload,
        }

        # 3. Broadcast to subscribed WebSocket clients
        try:
            await ws_manager.broadcast_json(wire_data, category=event.category.value)
        except Exception as e:
            logger.debug(f"[EventPublisher] WebSocket dispatch warning for {evt_id}: {e}")

        return event


event_publisher = EventPublisher()

