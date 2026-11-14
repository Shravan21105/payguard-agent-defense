import os
import pytest
import base58
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from app.main import app
from app.blockchain.signer import PolicySigner, near_to_yocto


client = TestClient(app)


def test_production_startup_without_signing_key_fails():
    """In production mode, PolicySigner must fail immediately if no private key is provided."""
    with pytest.raises(ValueError, match="FATAL: Production startup failed.*POLICY_SIGNER_PRIVATE_KEY must be explicitly configured"):
        PolicySigner(private_key_hex_or_base58=None, environment="production")


def test_production_startup_with_valid_hex_key():
    """Valid 32-byte (64 hex) private key succeeds in production mode without ephemeral flags."""
    raw_seed = os.urandom(32)
    hex_key = raw_seed.hex()

    signer = PolicySigner(private_key_hex_or_base58=hex_key, environment="production")
    assert signer.is_ephemeral is False
    assert signer.key_source == "CONFIGURED_HEX"
    assert signer.public_key_hex is not None
    assert signer.public_key_base58.startswith("ed25519:")


def test_production_startup_with_valid_base58_key():
    """Valid 32-byte base58 private key succeeds in production mode."""
    raw_seed = os.urandom(32)
    b58_key = f"ed25519:{base58.b58encode(raw_seed).decode('ascii')}"

    signer = PolicySigner(private_key_hex_or_base58=b58_key, environment="production")
    assert signer.is_ephemeral is False
    assert signer.key_source == "CONFIGURED_BASE58_32B"
    assert signer.public_key_base58.startswith("ed25519:")


def test_invalid_key_format_fails_in_production():
    """Corrupted or invalid key formats must raise ValueError in production."""
    with pytest.raises(ValueError, match="FATAL: Production startup failed"):
        PolicySigner(private_key_hex_or_base58="invalid-malformed-seed-key", environment="production")

    with pytest.raises(ValueError, match="FATAL: Production startup failed"):
        PolicySigner(private_key_hex_or_base58="00112233aabbcc", environment="production")  # Too short hex


def test_public_private_key_mismatch_fails():
    """If an expected public key does not match the configured private key, startup must fail."""
    raw_seed_a = os.urandom(32)
    raw_seed_b = os.urandom(32)
    key_a_hex = raw_seed_a.hex()

    priv_b = ed25519.Ed25519PrivateKey.from_private_bytes(raw_seed_b)
    pub_b_b58 = f"ed25519:{base58.b58encode(priv_b.public_key().public_bytes_raw()).decode('ascii')}"

    with pytest.raises(ValueError, match="Public key mismatch"):
        PolicySigner(
            private_key_hex_or_base58=key_a_hex,
            environment="production",
            expected_public_key=pub_b_b58,
        )


def test_signing_and_verification_compatibility():
    """Signed authorization payloads must strictly verify against derived public key."""
    raw_seed = os.urandom(32)
    signer = PolicySigner(private_key_hex_or_base58=raw_seed.hex(), environment="development")

    canonical_str, sig_hex = signer.sign_authorization(
        network_id="testnet",
        contract_id="payguard-vault.testnet",
        auth_id="auth-test-verify-1",
        sender_id="alice.near",
        recipient_id="bob.near",
        amount_yocto=near_to_yocto(5.0),
        decision="ALLOW",
        risk_score=5,
        policy_version="1.0.0",
        nonce=55,
        issued_at=1700000000,
        expires_at=1700000300,
    )

    # Valid verification
    assert signer.verify_signature(canonical_str, sig_hex) is True
    assert signer.verify_signature(canonical_str, sig_hex, signer.public_key_base58) is True

    # Tampered message
    tampered = canonical_str.replace(":5000000000000000000000000:", ":10000000000000000000000000:")
    assert signer.verify_signature(tampered, sig_hex) is False

    # Tampered signature
    corrupt_sig = sig_hex[:126] + ("00" if sig_hex[-2:] != "00" else "ff")
    assert signer.verify_signature(canonical_str, corrupt_sig) is False


def test_key_rotation():
    """Key rotation replaces active signer and invalidates signatures from old key under new public key."""
    seed_a = os.urandom(32)
    seed_b = os.urandom(32)

    signer = PolicySigner(private_key_hex_or_base58=seed_a.hex(), environment="development")
    old_pub = signer.public_key_base58

    # Sign with Key A
    canonical_str, sig_a = signer.sign_authorization(
        network_id="testnet",
        contract_id="payguard-vault.testnet",
        auth_id="auth-rotate-1",
        sender_id="alice.near",
        recipient_id="bob.near",
        amount_yocto=near_to_yocto(1.0),
        decision="ALLOW",
        risk_score=0,
        policy_version="1.0.0",
        nonce=1,
        issued_at=1700000000,
        expires_at=1700000300,
    )

    assert signer.verify_signature(canonical_str, sig_a, old_pub) is True

    # Rotate to Key B
    new_pub = signer.rotate_key(seed_b.hex())
    assert new_pub != old_pub
    assert signer.public_key_base58 == new_pub
    assert signer.key_source == "ROTATED_KEY"

    # Signature produced by Key A MUST FAIL verification against new Key B public key
    assert signer.verify_signature(canonical_str, sig_a, new_pub) is False

    # Sign with Key B
    canonical_str_b, sig_b = signer.sign_authorization(
        network_id="testnet",
        contract_id="payguard-vault.testnet",
        auth_id="auth-rotate-2",
        sender_id="alice.near",
        recipient_id="bob.near",
        amount_yocto=near_to_yocto(1.0),
        decision="ALLOW",
        risk_score=0,
        policy_version="1.0.0",
        nonce=2,
        issued_at=1700000000,
        expires_at=1700000300,
    )
    assert signer.verify_signature(canonical_str_b, sig_b, new_pub) is True
    assert signer.verify_signature(canonical_str_b, sig_b) is True


def test_development_mode_identifies_ephemeral_key():
    """In development mode without configured key, ephemeral key is used and explicitly flagged."""
    signer = PolicySigner(private_key_hex_or_base58=None, environment="development")
    assert signer.is_ephemeral is True
    assert signer.key_source == "EPHEMERAL_DEVELOPMENT_SEED"
    assert signer.public_key_base58.startswith("ed25519:")


def test_block_decision_never_receives_executable_authorization_signature():
    """A BLOCK transaction MUST NEVER receive an executable cryptographic signature."""
    req = {
        "sender": "agent-drainer.near",
        "recipient": "malicious-drainer.near",
        "amount": 1000.0,
        "currency": "NEAR",
        "purpose": "Adversarial drain attempt",
        "network_id": "testnet",
    }
    response = client.post("/api/blockchain/authorize", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["signature"] == ""
    assert data["execution_ready"] is False
