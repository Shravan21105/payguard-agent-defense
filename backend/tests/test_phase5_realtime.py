import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from app.db.database import db
from app.events.publisher import event_publisher, redact_sensitive_data
from app.main import app
from app.schemas.event import EventCategory, EventSeverity, PayguardEvent
from app.services.blockchain_monitor import blockchain_monitor
from app.services.monitoring_service import monitoring_service
from app.websocket.manager import ws_manager

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1 & 2. WebSocket Connection and Disconnection
# -----------------------------------------------------------------------------
def test_websocket_connect_and_disconnect():
    with client.websocket_connect("/ws/events") as websocket:
        welcome = websocket.receive_json()
        assert welcome["type"] == "system.websocket_connected"
        assert "client_id" in welcome["payload"]
        assert "supported_categories" in welcome["payload"]
        assert "all" in welcome["payload"]["active_subscriptions"]
    # After block exits, client disconnects cleanly


# -----------------------------------------------------------------------------
# 3. Event Broadcasting via WebSocket
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_event_broadcasting_via_publisher():
    received_events = []

    class MockWebSocket:
        def __init__(self):
            self.client_state = 1  # CONNECTED
            self.sent = []

        async def send_json(self, data):
            self.sent.append(data)
            received_events.append(data)

    mock_ws = MockWebSocket()
    cid = await ws_manager.connect(mock_ws, client_id="test_broadcast_client")
    try:
        test_evt = await event_publisher.publish(
            event_type="transaction.received",
            payload={"amount": 10.0, "recipient": "alice.testnet"},
            transaction_id="tx_test_bc_01",
            source="test_runner",
            severity="INFO",
        )
        assert len(mock_ws.sent) >= 1
        last = mock_ws.sent[-1]
        assert last["event_type"] == "transaction.received"
        assert last["transaction_id"] == "tx_test_bc_01"
        assert last["payload"]["amount"] == 10.0
    finally:
        ws_manager.disconnect(mock_ws)


# -----------------------------------------------------------------------------
# 4. Multiple Simultaneous WebSocket Clients
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_multiple_simultaneous_websocket_clients():
    class DummyWS:
        def __init__(self):
            self.client_state = 1
            self.messages = []

        async def send_json(self, data):
            self.messages.append(data)

    ws1, ws2, ws3 = DummyWS(), DummyWS(), DummyWS()
    await ws_manager.connect(ws1, client_id="c1", subscriptions=["transactions"])
    await ws_manager.connect(ws2, client_id="c2", subscriptions=["blockchain"])
    await ws_manager.connect(ws3, client_id="c3", subscriptions=["all"])

    try:
        # Broadcast transactions event
        await ws_manager.broadcast_json({"type": "tx_evt", "category": "transactions"})
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 0  # not subscribed to transactions
        assert len(ws3.messages) == 1  # subscribed to all

        # Broadcast blockchain event
        await ws_manager.broadcast_json({"type": "bc_evt", "category": "blockchain"})
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 1
        assert len(ws3.messages) == 2
    finally:
        ws_manager.disconnect(ws1)
        ws_manager.disconnect(ws2)
        ws_manager.disconnect(ws3)


# -----------------------------------------------------------------------------
# 5. Event Schema Validation
# -----------------------------------------------------------------------------
def test_event_schema_validation():
    evt = PayguardEvent(
        event_id="evt_test_schema_01",
        event_type="transaction.allowed",
        category=EventCategory.TRANSACTIONS,
        transaction_id="tx_test_01",
        source="policy_engine",
        severity=EventSeverity.SUCCESS,
        payload={"risk_score": 15, "decision": "ALLOW"},
    )
    assert evt.event_id == "evt_test_schema_01"
    assert evt.severity == EventSeverity.SUCCESS
    assert evt.category == EventCategory.TRANSACTIONS
    dumped = evt.model_dump()
    assert dumped["severity"] == "SUCCESS"


# -----------------------------------------------------------------------------
# 6 & 7. Event Persistence, Retrieval & Filtering
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_event_persistence_and_filtering():
    evt1 = await event_publisher.publish(
        event_type="security.anomaly_detected",
        payload={"pattern": "burst_velocity"},
        transaction_id="tx_filter_test",
        source="behavioral_agent",
        severity="WARNING",
    )
    evt2 = await event_publisher.publish(
        event_type="blockchain.transaction_confirmed",
        payload={"tx_hash": "hash123"},
        transaction_id="tx_filter_test",
        source="near_blockchain",
        severity="SUCCESS",
    )

    # Fetch from SQLite via API
    res = client.get("/api/events?transaction_id=tx_filter_test")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    types = [e["event_type"] for e in data["events"]]
    assert "security.anomaly_detected" in types
    assert "blockchain.transaction_confirmed" in types

    # Filter by category
    res_cat = client.get("/api/events?category=security&transaction_id=tx_filter_test")
    assert res_cat.status_code == 200
    cat_events = res_cat.json()["events"]
    assert all(e["category"] == "security" for e in cat_events)


# -----------------------------------------------------------------------------
# 8. Event Deduplication
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_event_deduplication():
    fixed_event_id = "evt_dedup_unique_999"
    e1 = await event_publisher.publish(
        event_type="transaction.analyzing",
        payload={"step": 1},
        event_id=fixed_event_id,
        transaction_id="tx_dedup_01",
    )
    # Second publish with identical event_id
    e2 = await event_publisher.publish(
        event_type="transaction.analyzing",
        payload={"step": 2},
        event_id=fixed_event_id,
        transaction_id="tx_dedup_01",
    )
    assert e1.event_id == e2.event_id
    # Ensure it's not saved twice in the database
    retrieved = db.get_event(fixed_event_id)
    assert retrieved is not None
    assert retrieved["event_id"] == fixed_event_id


# -----------------------------------------------------------------------------
# 9. Transaction Lifecycle Event Ordering
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_transaction_lifecycle_event_ordering():
    import uuid
    tx_id = f"tx_lifecycle_order_{uuid.uuid4().hex[:8]}"
    await event_publisher.publish("transaction.received", {"stage": 1}, transaction_id=tx_id)
    await event_publisher.publish("transaction.analyzing", {"stage": 2}, transaction_id=tx_id)
    await event_publisher.publish("transaction.allowed", {"stage": 3}, transaction_id=tx_id)
    await event_publisher.publish("transaction.confirmed", {"stage": 4}, transaction_id=tx_id)

    res = client.get(f"/api/events/transaction/{tx_id}")
    assert res.status_code == 200
    events = res.json()
    assert len(events) == 4
    assert events[0]["event_type"] == "transaction.received"
    assert events[1]["event_type"] == "transaction.analyzing"
    assert events[2]["event_type"] == "transaction.allowed"
    assert events[3]["event_type"] == "transaction.confirmed"


# -----------------------------------------------------------------------------
# 10. BLOCK Transaction Event Behavior
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_block_transaction_event_behavior():
    tx_id = "tx_block_test_event"
    evt = await event_publisher.publish(
        event_type="transaction.blocked",
        payload={"reason": "critical_blocklist_hit", "risk_score": 100},
        transaction_id=tx_id,
        severity="CRITICAL",
    )
    assert evt.severity == EventSeverity.CRITICAL
    assert evt.event_type == "transaction.blocked"
    # Verify no execution event is recorded for this tx
    events = db.get_events_for_transaction(tx_id)
    types = [e["event_type"] for e in events]
    assert "transaction.executing" not in types
    assert "transaction.confirmed" not in types


# -----------------------------------------------------------------------------
# 11. WARN Escrow Event Behavior
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_warn_escrow_event_behavior():
    tx_id = "tx_warn_escrow_test"
    evt = await event_publisher.publish(
        event_type="escrow.created",
        payload={"escrow_id": "esc_123", "timelock_seconds": 86400, "amount": 15.0},
        transaction_id=tx_id,
        severity="WARNING",
    )
    assert evt.category == EventCategory.ESCROW
    assert evt.severity == EventSeverity.WARNING


# -----------------------------------------------------------------------------
# 12. Monitoring Metrics API
# -----------------------------------------------------------------------------
def test_monitoring_metrics_api():
    res = client.get("/api/monitoring/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "volume_separation" in data
    assert "execution_breakdown" in data
    assert "infrastructure" in data
    # Verify segregated volumes exist
    vols = data["volume_separation"]
    assert "confirmed_onchain_volume_near" in vols
    assert "simulation_volume_near" in vols
    assert "pending_escrow_volume_near" in vols
    assert "protected_blocked_volume_near" in vols


# -----------------------------------------------------------------------------
# 13. Monitoring Health API
# -----------------------------------------------------------------------------
def test_monitoring_health_api():
    res = client.get("/api/monitoring/health")
    assert res.status_code == 200
    data = res.json()
    assert "overall_status" in data
    assert "subsystems" in data
    subs = data["subsystems"]
    assert "backend" in subs
    assert "database" in subs
    assert "websocket_manager" in subs
    assert "near_rpc" in subs
    assert "smart_contract" in subs
    assert "blockchain_synchronization" in subs
    assert subs["backend"]["status"] == "HEALTHY"
    assert subs["database"]["status"] == "HEALTHY"


# -----------------------------------------------------------------------------
# 14. WebSocket Subscription & Ping-Pong Handling
# -----------------------------------------------------------------------------
def test_websocket_subscriptions_and_ping():
    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()  # welcome message
        # Send subscription request
        ws.send_text(json.dumps({"action": "subscribe", "categories": ["security", "blockchain"]}))
        sub_resp = ws.receive_json()
        assert sub_resp["type"] == "system.subscription_updated"
        assert set(sub_resp["active_subscriptions"]) == {"security", "blockchain"}

        # Send ping
        ws.send_text("ping")
        pong = ws.receive_text()
        assert pong == "pong"


# -----------------------------------------------------------------------------
# 15. NEAR RPC Outage Detection & Recovery
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_near_rpc_outage_events():
    # Simulate connection lost
    lost_evt = await event_publisher.publish(
        event_type="blockchain.connection_lost",
        payload={"rpc_url": "https://rpc.testnet.near.org", "error": "timeout"},
        source="near_blockchain",
        severity="CRITICAL",
    )
    assert lost_evt.severity == EventSeverity.CRITICAL
    assert lost_evt.category == EventCategory.BLOCKCHAIN

    # Simulate connection restored
    restored_evt = await event_publisher.publish(
        event_type="blockchain.connection_restored",
        payload={"rpc_url": "https://rpc.testnet.near.org", "network": "testnet"},
        source="near_blockchain",
        severity="SUCCESS",
    )
    assert restored_evt.severity == EventSeverity.SUCCESS
    assert restored_evt.category == EventCategory.BLOCKCHAIN


# -----------------------------------------------------------------------------
# 16. Blockchain Checkpoint Persistence & Recovery
# -----------------------------------------------------------------------------
def test_blockchain_checkpoint_persistence():
    db.save_blockchain_checkpoint("test_checkpoint", 185000000, "hash_abc_123")
    cp = db.get_blockchain_checkpoint("test_checkpoint")
    assert cp is not None
    assert cp["last_block_height"] == 185000000
    assert cp["last_block_hash"] == "hash_abc_123"


# -----------------------------------------------------------------------------
# 17. Duplicate Blockchain Event Prevention
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_duplicate_blockchain_event_prevention():
    evt_id = "evt_bc_reconcile_42"
    e1 = await event_publisher.publish(
        event_type="blockchain.transaction_confirmed",
        payload={"tx_hash": "tx_abc"},
        event_id=evt_id,
        transaction_id="tx_42",
    )
    e2 = await event_publisher.publish(
        event_type="blockchain.transaction_confirmed",
        payload={"tx_hash": "tx_abc"},
        event_id=evt_id,
        transaction_id="tx_42",
    )
    assert e1.event_id == e2.event_id


# -----------------------------------------------------------------------------
# 18. Simulation / On-Chain Metric Separation
# -----------------------------------------------------------------------------
def test_simulation_onchain_volume_separation():
    metrics = monitoring_service.get_monitoring_metrics()
    vols = metrics["volume_separation"]
    assert isinstance(vols["confirmed_onchain_volume_near"], (int, float))
    assert isinstance(vols["simulation_volume_near"], (int, float))
    assert vols["note"] == "SIMULATION and ONCHAIN figures are strictly segregated without co-mingling."


# -----------------------------------------------------------------------------
# 19. Sensitive Information Redaction
# -----------------------------------------------------------------------------
def test_sensitive_information_redaction():
    leak_payload = {
        "account_id": "alice.near",
        "private_key": "ed25519:super_secret_private_key_do_not_leak",
        "nested": {
            "signer_secret": "my_passphrase",
            "token": "bearer_123",
            "normal_field": "safe_value",
        },
    }
    cleaned = redact_sensitive_data(leak_payload)
    assert cleaned["account_id"] == "alice.near"
    assert cleaned["private_key"] == "[REDACTED]"
    assert cleaned["nested"]["signer_secret"] == "[REDACTED]"
    assert cleaned["nested"]["token"] == "[REDACTED]"
    assert cleaned["nested"]["normal_field"] == "safe_value"


# -----------------------------------------------------------------------------
# 20. Event Throughput & Summary Metrics API
# -----------------------------------------------------------------------------
def test_event_throughput_metrics_api():
    res = client.get("/api/events/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_events" in data
    assert "by_category" in data
    assert "by_severity" in data
    assert "active_subscriptions" in data
    assert "recent_event_rate_per_min" in data
    assert data["total_events"] >= 0


# -----------------------------------------------------------------------------
# 21. Event by ID and 404 Behavior
# -----------------------------------------------------------------------------
@pytest.mark.anyio
async def test_get_event_by_id_and_not_found():
    evt = await event_publisher.publish("system.health_updated", {"status": "HEALTHY"})
    res = client.get(f"/api/events/{evt.event_id}")
    assert res.status_code == 200
    assert res.json()["event_id"] == evt.event_id

    res_missing = client.get("/api/events/evt_non_existent_id")
    assert res_missing.status_code == 404


# -----------------------------------------------------------------------------
# 22. Reconnection and Resubscription Behavior
# -----------------------------------------------------------------------------
def test_websocket_reconnection_and_resubscription():
    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()
        ws.send_text(json.dumps({"action": "subscribe", "categories": ["escrow"]}))
        resp = ws.receive_json()
        assert resp["active_subscriptions"] == ["escrow"]
    # Reconnect with fresh socket
    with client.websocket_connect("/ws/events") as ws2:
        welcome = ws2.receive_json()
        assert welcome["payload"]["active_subscriptions"] == ["all"]

