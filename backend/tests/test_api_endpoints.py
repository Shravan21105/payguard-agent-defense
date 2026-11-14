import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["application"] == "PAYGUARD"
    assert data["version"] in ("0.1.0", "0.2.0")


def test_analyze_transaction_allowed():
    import time
    payload = {
        "sender": f"agent-api-safe-{int(time.time() * 1000)}.near",
        "recipient": "oracle.near",
        "amount": 3.0,
        "currency": "NEAR",
        "purpose": "Decentralized oracle fee",
    }
    response = client.post("/api/transactions/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["execution_allowed"] is True
    assert data["requires_approval"] is False
    assert data["risk_score"] < 30
    assert "data_integrity" in data["policy_checks"]


def test_analyze_transaction_blocked_by_blocklist():
    payload = {
        "sender": "agent-test.near",
        "recipient": "malicious-drainer.near",
        "amount": 2.0,
        "currency": "NEAR",
        "purpose": "Suspicious transfer",
    }
    response = client.post("/api/transactions/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["execution_allowed"] is False
    assert data["policy_checks"]["recipient_status"] == "BLOCKED"


def test_analyze_transaction_warn_unknown_recipient():
    import time
    unique_recipient = f"new-unlisted-{int(time.time() * 1000)}.near"
    payload = {
        "sender": f"agent-warn-{int(time.time() * 1000)}.near",
        "recipient": unique_recipient,
        "amount": 10.0,
        "currency": "NEAR",
        "purpose": "Transfer to unknown counterparty",
    }
    response = client.post("/api/transactions/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "WARN"
    assert data["requires_approval"] is True


def test_get_transactions_list():
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_transaction_by_id():
    # First query list to get an id
    list_resp = client.get("/api/transactions")
    first_tx = list_resp.json()[0]
    tx_id = first_tx["transaction_id"]

    response = client.get(f"/api/transactions/{tx_id}")
    assert response.status_code == 200
    assert response.json()["transaction_id"] == tx_id


def test_get_transaction_not_found():
    response = client.get("/api/transactions/non_existent_tx_9999")
    assert response.status_code == 404


def test_get_and_update_policies():
    # 1. Get current
    get_resp = client.get("/api/policies")
    assert get_resp.status_code == 200
    policy_data = get_resp.json()
    assert "config" in policy_data
    original_max = policy_data["config"]["max_tx_amount"]

    # 2. Update
    new_max = 65.0
    post_resp = client.post("/api/policies", json={"max_tx_amount": new_max})
    assert post_resp.status_code == 200
    assert post_resp.json()["config"]["max_tx_amount"] == new_max

    # 3. Restore original
    client.post("/api/policies", json={"max_tx_amount": original_max})


def test_get_security_metrics():
    response = client.get("/api/security/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_monitored" in data
    assert "approved_count" in data
    assert "blocked_count" in data
    assert "protected_near_volume" in data
    assert "recent_alerts" in data
    assert data["total_monitored"] >= 4

