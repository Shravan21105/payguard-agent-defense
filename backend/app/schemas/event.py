from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    TRANSACTIONS = "transactions"
    ESCROW = "escrow"
    SECURITY = "security"
    BLOCKCHAIN = "blockchain"
    SYSTEM = "system"


class EventSeverity(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class PayguardEvent(BaseModel):
    event_id: str = Field(..., description="Unique deterministic or UUID-based event ID")
    event_type: str = Field(..., description="Standardized event name, e.g. transaction.confirmed")
    category: EventCategory = Field(default=EventCategory.TRANSACTIONS, description="Event classification")
    transaction_id: Optional[str] = Field(default=None, description="Associated transaction ID if applicable")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="UTC ISO 8601 timestamp")
    source: str = Field(default="backend", description="Source subsystem emitting the event")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Operational severity")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Redacted event details and telemetry")


class EventListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    events: List[PayguardEvent]


class EventMetricsResponse(BaseModel):
    total_events: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    active_subscriptions: int
    recent_event_rate_per_min: float

