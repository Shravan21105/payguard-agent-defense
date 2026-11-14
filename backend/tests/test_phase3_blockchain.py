import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.blockchain.signer import PolicySigner, near_to_yocto, yocto_to_near
from app.blockchain.models import (
    SignedPolicyAuthorization,
    OnChainAuthorizationRequest,
    OnChainExecutionRequest,
    OnChainEscrowRecord,
    OnChainTransactionRecord,
    NEARNodeStatus,
)

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. Unit Tests for Cryptographic Policy Signer
# -----------------------------------------------------------------------------
def test_policy_signer_initialization_and_keys():
    signer = PolicySigner()
    assert signer.public_key_hex is not None
    assert len(signer.public_key_hex) == 64
    assert signer.public_key_base58.startswith("ed25519:")
    assert len(signer.public_key_base58) > 40


def test_yocto_conversion():
    assert near_to_yocto(1.0) == 10**24
    assert near_to_yocto(0.5) == 5 * 10**23
    assert near_to_yocto(10.0) == 10**25
    assert yocto_to_near(10**24) == 1.0
    assert yocto_to_near(5 * 10**23) == 0.5


def test_policy_signer_canonical_message_and_signature():
    signer = PolicySigner()
    canonical_str, sig_hex = signer.sign_authorization(
        network_id="testnet",
        contract_id="payguard-vault.testnet",
        auth_id="auth-test-12345",
        sender_id="alice.testnet",
        recipient_id="bob.testnet",
        amount_yocto=near_to_yocto(2.5),
        decision="ALLOW",
        risk_score=15,
        policy_version="1.0.0",
        nonce=101,
        issued_at=1700000000,
        expires_at=1700000300,
    )

    expected_prefix = "PAYGUARD:v1:testnet:payguard-vault.testnet:auth-test-12345:alice.testnet:bob.testnet:"
    assert canonical_str.startswith(expected_prefix)
    assert ":ALLOW:15:1.0.0:101:1700000000:1700000300" in canonical_str

    # Sign and verify
    assert len(sig_hex) == 128  # 64 bytes = 128 hex chars
    assert signer.verify_signature(canonical_str, sig_hex) is True

    # Tampered message check
    tampered_str = canonical_str.replace(":ALLOW:", ":BLOCK:")
    assert signer.verify_signature(tampered_str, sig_hex) is False


# -----------------------------------------------------------------------------
# 2. Integration Tests: Authorization Endpoint
# -----------------------------------------------------------------------------
def test_blockchain_authorize_safe_transaction():
    ts = int(time.time() * 1000)
    req = {
        "sender": f"agent-safe-{ts}.near",
        "recipient": "oracle.near",
        "amount": 2.5,
        "currency": "NEAR",
        "purpose": "Routine query fee payment",
        "network_id": "testnet",
    }
    response = client.post("/api/blockchain/authorize", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["signature"] is not None
    assert len(data["signature"]) == 128
    assert data["signer_public_key"].startswith("ed25519:")
    assert data["sender_id"] == req["sender"]
    assert data["recipient_id"] == req["recipient"]
    assert data["amount_yocto"] == str(near_to_yocto(2.5))
    assert data["expires_at"] > data["issued_at"]
    assert data["execution_ready"] is True


def test_blockchain_authorize_blocked_transaction():
    req = {
        "sender": "agent-compromised.near",
        "recipient": "malicious-drainer.near",
        "amount": 500.0,
        "currency": "NEAR",
        "purpose": "Unauthorized treasury drain",
        "network_id": "testnet",
    }
    response = client.post("/api/blockchain/authorize", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    # Cryptographic signature MUST BE WITHHELD for BLOCK decisions
    assert data["signature"] == ""
    assert data["execution_ready"] is False
    assert any("block" in r.lower() or "recipient" in r.lower() for r in data["reasons"])


# -----------------------------------------------------------------------------
# 3. Integration Tests: Execution & Anti-Replay
# -----------------------------------------------------------------------------
def test_blockchain_execute_and_replay_protection():
    ts = int(time.time() * 1000)
    auth_req = {
        "sender": f"agent-exec-{ts}.near",
        "recipient": "oracle.near",
        "amount": 1.0,
        "currency": "NEAR",
        "purpose": "Decentralized oracle feed query payment",
        "network_id": "testnet",
    }
    auth_resp = client.post("/api/blockchain/authorize", json=auth_req)
    assert auth_resp.status_code == 200
    signed_auth = auth_resp.json()
    assert signed_auth["decision"] == "ALLOW"
    assert signed_auth["signature"] != ""

    # First execution attempt -> should succeed
    exec_req = {
        "authorization": signed_auth,
        "caller_account_id": signed_auth["sender_id"],
    }
    exec_resp = client.post("/api/blockchain/execute", json=exec_req)
    assert exec_resp.status_code == 200
    tx_record = exec_resp.json()
    assert tx_record["status"] in ("CONFIRMED", "SUCCESS")
    assert tx_record["tx_hash"] is not None
    assert tx_record["sender_id"] == signed_auth["sender_id"]

    # Replay attempt with same authorization -> must be rejected (400)
    replay_resp = client.post("/api/blockchain/execute", json=exec_req)
    assert replay_resp.status_code == 400
    detail_lower = replay_resp.json()["detail"].lower()
    assert "already been consumed" in detail_lower or "replay attack" in detail_lower


# -----------------------------------------------------------------------------
# 4. Integration Tests: Escrow Lifecycle (WARN)
# -----------------------------------------------------------------------------
def test_blockchain_escrow_lifecycle():
    ts = int(time.time() * 1000)
    unique_recipient = f"unverified-partner-{ts}.near"
    auth_req = {
        "sender": f"agent-escrow-{ts}.near",
        "recipient": unique_recipient,
        "amount": 15.0,
        "currency": "NEAR",
        "purpose": "High-value transfer to unverified partner",
        "network_id": "testnet",
    }
    auth_resp = client.post("/api/blockchain/authorize", json=auth_req)
    assert auth_resp.status_code == 200
    signed_auth = auth_resp.json()

    # Create escrow
    escrow_resp = client.post(
        "/api/blockchain/escrow?timelock_seconds=3600",
        json=signed_auth,
    )
    assert escrow_resp.status_code == 200
    escrow_record = escrow_resp.json()
    escrow_id = escrow_record["escrow_id"]
    assert escrow_record["status"] == "PENDING_APPROVAL"

    # Approve escrow
    approve_resp = client.post(
        f"/api/blockchain/escrow/{escrow_id}/approve?operator_id=human_supervisor&reason=Cleared_by_audit"
    )
    assert approve_resp.status_code == 200
    approved_record = approve_resp.json()
    assert approved_record["status"] in ("APPROVED", "RELEASED")


def test_blockchain_escrow_rejection():
    ts = int(time.time() * 1000)
    auth_req = {
        "sender": f"agent-reject-{ts}.near",
        "recipient": f"unverified-vendor-{ts}.near",
        "amount": 12.0,
        "currency": "NEAR",
        "purpose": "High-value transfer to unverified partner",
        "network_id": "testnet",
    }
    auth_resp = client.post("/api/blockchain/authorize", json=auth_req)
    signed_auth = auth_resp.json()
    assert signed_auth["decision"] == "WARN"

    escrow_resp = client.post(
        "/api/blockchain/escrow?timelock_seconds=7200",
        json=signed_auth,
    )
    escrow_id = escrow_resp.json()["escrow_id"]

    # Reject escrow
    reject_resp = client.post(
        f"/api/blockchain/escrow/{escrow_id}/reject?operator_id=security_officer&reason=Counterparty_flagged"
    )
    assert reject_resp.status_code == 200
    rejected_record = reject_resp.json()
    assert rejected_record["status"] in ("REJECTED", "REFUNDED")


# -----------------------------------------------------------------------------
# 5. Integration Tests: Status & Diagnostics
# -----------------------------------------------------------------------------
def test_blockchain_status():
    response = client.get("/api/blockchain/status")
    assert response.status_code == 200
    data = response.json()
    assert data["network"] == "testnet"
    assert data["vault_contract"] is not None
    assert data["signer_public_key"].startswith("ed25519:")
    assert data["status"] in ("ONLINE", "CONNECTED", "DEGRADED (OFFLINE FALLBACK)", "OFFLINE")


def test_blockchain_transactions_list():
    response = client.get("/api/blockchain/transactions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
