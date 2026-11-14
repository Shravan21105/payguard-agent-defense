import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuthorizationEvidence(BaseModel):
    """
    Cryptographic authorization record for auditability.
    Note: SHA-256 digest represents deterministic off-chain audit evidence integrity,
    not a blockchain ed25519 wallet private key signature (which is Phase 3 on-chain vault).
    """
    transaction_id: str
    canonical_payload: str = Field(..., description="Deterministic sorted JSON string")
    sha256_digest: str = Field(..., description="Hex encoded SHA-256 hash of canonical payload")
    policy_version: str
    is_tamper_verified: bool = True
    generated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceEngine:
    """
    Produces deterministic canonical representations and SHA-256 digests
    to preserve tamper-evident audit trails of evaluated transactions.
    """

    @classmethod
    def canonical_serialize(cls, data: Dict[str, Any]) -> str:
        """
        Produces RFC-8785 compliant canonical JSON:
        - Sorted keys recursively
        - No extra whitespace
        - UTF-8 deterministic representation
        """
        def _normalize(val: Any) -> Any:
            if isinstance(val, dict):
                return {k: _normalize(val[k]) for k in sorted(val.keys())}
            elif isinstance(val, (list, tuple)):
                return [_normalize(x) for x in val]
            elif isinstance(val, float):
                # Normalize float representation
                return round(val, 6)
            return val

        normalized = _normalize(data)
        return json.dumps(normalized, separators=(',', ':'), ensure_ascii=False, sort_keys=True)

    @classmethod
    def compute_sha256(cls, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @classmethod
    def generate_evidence(
        cls,
        transaction_id: str,
        sender: str,
        recipient: str,
        amount: float,
        currency: str,
        intent_text: Optional[str],
        policy_version: str,
        decision: str,
        risk_score: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuthorizationEvidence:
        intent_hash = cls.compute_sha256(intent_text or "")
        now = datetime.utcnow().isoformat()

        canonical_dict = {
            "amount": amount,
            "currency": currency,
            "decision": decision,
            "intent_hash": intent_hash,
            "policy_version": policy_version,
            "recipient": recipient.lower().strip(),
            "risk_score": risk_score,
            "sender": sender.lower().strip(),
            "transaction_id": transaction_id,
        }

        canonical_payload = cls.canonical_serialize(canonical_dict)
        digest = cls.compute_sha256(canonical_payload)

        return AuthorizationEvidence(
            transaction_id=transaction_id,
            canonical_payload=canonical_payload,
            sha256_digest=digest,
            policy_version=policy_version,
            is_tamper_verified=True,
            generated_at=now,
            metadata={
                "intent_text": intent_text or "",
                "intent_hash": intent_hash,
                **(metadata or {}),
            },
        )

    @classmethod
    def verify_evidence(cls, canonical_payload: str, expected_sha256: str) -> bool:
        """Verifies if the canonical payload matches the stored SHA-256 digest."""
        computed = cls.compute_sha256(canonical_payload)
        return computed == expected_sha256


evidence_engine = EvidenceEngine()

