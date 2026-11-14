from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.db.database import db
from app.schemas.event import EventListResponse, EventMetricsResponse, PayguardEvent
from app.services.monitoring_service import monitoring_service
from app.websocket.manager import ws_manager

router = APIRouter(tags=["Real-Time Monitoring & Events"])


@router.get("/events", response_model=EventListResponse, summary="List Real-Time Telemetry Events")
async def list_events(
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    category: Optional[str] = Query(None, description="Filter by category (transactions, security, blockchain, escrow, system)"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, SUCCESS, WARNING, CRITICAL)"),
    transaction_id: Optional[str] = Query(None, description="Filter by transaction ID"),
    source: Optional[str] = Query(None, description="Filter by source subsystem"),
):
    """Retrieves paginated and filtered historical events from the persistent event ledger."""
    events_raw, total = db.list_events(
        limit=limit,
        offset=offset,
        event_type=event_type,
        category=category,
        severity=severity,
        transaction_id=transaction_id,
        source=source,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": [PayguardEvent(**evt) for evt in events_raw],
    }


@router.get("/events/metrics", response_model=EventMetricsResponse, summary="Get Event Throughput Metrics")
async def get_event_metrics():
    """Returns event count distribution by category, severity, and rate per minute."""
    metrics = db.get_event_metrics()
    ws_health = ws_manager.get_health_metrics()
    return {
        "total_events": metrics["total_events"],
        "by_category": metrics["by_category"],
        "by_severity": metrics["by_severity"],
        "active_subscriptions": ws_health["active_connections"],
        "recent_event_rate_per_min": metrics["recent_event_rate_per_min"],
    }


@router.get("/events/transaction/{transaction_id}", response_model=List[PayguardEvent], summary="Get Chronological Transaction Lifecycle Events")
async def get_transaction_events(transaction_id: str):
    """Retrieves the complete lifecycle event sequence for a given transaction."""
    events_raw = db.get_events_for_transaction(transaction_id)
    return [PayguardEvent(**evt) for evt in events_raw]


@router.get("/events/{event_id}", response_model=PayguardEvent, summary="Get Event by ID")
async def get_event_by_id(event_id: str):
    """Retrieves details of a single event by its unique ID."""
    event_raw = db.get_event(event_id)
    if not event_raw:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return PayguardEvent(**event_raw)


@router.get("/monitoring/metrics", summary="Get Live Monitoring Operational Metrics")
async def get_monitoring_metrics():
    """
    Returns live system metrics with strict segregation of SIMULATION volume
    and verified ONCHAIN volume, active escrows, throughput, and WebSocket stats.
    """
    return monitoring_service.get_monitoring_metrics()


@router.get("/monitoring/health", summary="Deep Subsystem Health Diagnostics")
@router.get("/events/monitoring/health", summary="Deep Subsystem Health Diagnostics Alias", include_in_schema=False)
async def get_monitoring_health():
    """
    Deep operational probe across FastAPI, SQLite, WebSocketManager, NEAR RPC,
    Smart Contract configuration, and background synchronization services.
    """
    return await monitoring_service.get_monitoring_health()

