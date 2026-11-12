from datetime import datetime, timedelta
import threading
from typing import Any, Dict, List, Optional
from app.engine.decision_engine import DecisionEngine
from app.schemas.transaction import (
    DecisionType,
    RiskLevel,
    TransactionAnalysisResponse,
    TransactionRecord,
    TransactionRequest,
)
from app.services.policy_service import policy_service


class TransactionService:
    """
    Manages transaction analysis lifecycle, history repository, and metric tracking.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._transactions: List[TransactionRecord] = []
        self._decision_engine = DecisionEngine(policy_service.get_policy())
        self._seed_mock_history()

    def _seed_mock_history(self) -> None:
        """Seed initial baseline demonstration records, explicitly tagged as mock."""
        now = datetime.utcnow()
        mock_data = [
            {
                "transaction_id": "tx_demo_001",
                "sender": "agent-alpha.near",
                "recipient": "oracle.near",
                "amount": 2.5,
                "currency": "NEAR",
                "decision": DecisionType.ALLOW,
                "risk_score": 12,
                "risk_level": RiskLevel.LOW,
                "requires_approval": False,
                "reasons": ["All deterministic security policies and risk thresholds passed."],
                "policy_checks": {
                    "data_integrity": "PASSED",
                    "recipient_status": "PASSED",
                    "amount_limit": "PASSED",
                    "daily_limit": "PASSED",
                    "duplicate_check": "PASSED",
                    "frequency_check": "PASSED",
                },
                "timestamp": now - timedelta(minutes=45),
                "execution_allowed": True,
                "confidence_score": 0.98,
                "is_mock_simulation": True,
                "agent_id": "agent-alpha.near",
                "purpose": "Fetch decentralized oracle price feeds",
                "approval_status": "APPROVED",
            },
            {
                "transaction_id": "tx_demo_002",
                "sender": "agent-alpha.near",
                "recipient": "malicious-drainer.near",
                "amount": 100.0,
                "currency": "NEAR",
                "decision": DecisionType.BLOCK,
                "risk_score": 95,
                "risk_level": RiskLevel.HIGH,
                "requires_approval": False,
                "reasons": [
                    "Recipient 'malicious-drainer.near' is on the critical blocklist.",
                    "Transaction amount (100.00 NEAR) exceeds maximum per-transaction limit (50.00 NEAR).",
                    "Risk score (95) exceeds high-risk threshold (70).",
                ],
                "policy_checks": {
                    "data_integrity": "PASSED",
                    "recipient_status": "BLOCKED",
                    "amount_limit": "FAILED",
                    "daily_limit": "PASSED",
                    "duplicate_check": "PASSED",
                    "frequency_check": "PASSED",
                },
                "timestamp": now - timedelta(minutes=30),
                "execution_allowed": False,
                "confidence_score": 0.99,
                "is_mock_simulation": True,
                "agent_id": "agent-alpha.near",
                "purpose": "Unauthorized liquidation drain attempt (intercepted)",
                "approval_status": "NONE",
            },
            {
                "transaction_id": "tx_demo_003",
                "sender": "agent-beta.near",
                "recipient": "unverified-agent-dex.near",
                "amount": 35.0,
                "currency": "NEAR",
                "decision": DecisionType.WARN,
                "risk_score": 45,
                "risk_level": RiskLevel.MEDIUM,
                "requires_approval": True,
                "reasons": [
                    "Recipient 'unverified-agent-dex.near' is an unverified counterparty.",
                    "Elevated risk score (45) requires human verification.",
                ],
                "policy_checks": {
                    "data_integrity": "PASSED",
                    "recipient_status": "WARNING",
                    "amount_limit": "PASSED",
                    "daily_limit": "PASSED",
                    "duplicate_check": "PASSED",
                    "frequency_check": "PASSED",
                },
                "timestamp": now - timedelta(minutes=15),
                "execution_allowed": False,
                "confidence_score": 0.92,
                "is_mock_simulation": True,
                "agent_id": "agent-beta.near",
                "purpose": "Liquidity rebalancing on external contract",
                "approval_status": "PENDING",
            },
            {
                "transaction_id": "tx_demo_004",
                "sender": "agent-gamma.near",
                "recipient": "treasury.payguard.near",
                "amount": 15.0,
                "currency": "NEAR",
                "decision": DecisionType.ALLOW,
                "risk_score": 5,
                "risk_level": RiskLevel.LOW,
                "requires_approval": False,
                "reasons": ["All deterministic security policies and risk thresholds passed."],
                "policy_checks": {
                    "data_integrity": "PASSED",
                    "recipient_status": "PASSED",
                    "amount_limit": "PASSED",
                    "daily_limit": "PASSED",
                    "duplicate_check": "PASSED",
                    "frequency_check": "PASSED",
                },
                "timestamp": now - timedelta(minutes=5),
                "execution_allowed": True,
                "confidence_score": 0.99,
                "is_mock_simulation": True,
                "agent_id": "agent-gamma.near",
                "purpose": "Automated protocol staking contribution",
                "approval_status": "APPROVED",
            },
        ]
        for item in mock_data:
            self._transactions.append(TransactionRecord(**item))

    def _get_recent_history_dicts(self) -> List[Dict[str, Any]]:
        return [
            {
                "transaction_id": t.transaction_id,
                "sender": t.sender,
                "recipient": t.recipient,
                "amount": t.amount,
                "decision": t.decision.value,
                "timestamp": t.timestamp,
            }
            for t in self._transactions
        ]

    def analyze_transaction(self, req: TransactionRequest) -> TransactionAnalysisResponse:
        """Evaluates an incoming agent transaction using active policies."""
        with self._lock:
            # Sync policy from policy service
            self._decision_engine.update_policy(policy_service.get_policy())

            history = self._get_recent_history_dicts()
            result = self._decision_engine.evaluate_transaction(req, recent_history=history)

            # Record in repository
            record = TransactionRecord(
                **result.model_dump(),
                agent_id=req.agent_id or "autonomous-agent-01",
                purpose=req.purpose,
                approval_status="PENDING" if result.requires_approval else ("APPROVED" if result.decision == DecisionType.ALLOW else "NONE"),
            )
            # Insert at the top of recent transactions
            self._transactions.insert(0, record)
            return result

    def list_transactions(
        self,
        limit: int = 50,
        decision: Optional[str] = None,
    ) -> List[TransactionRecord]:
        with self._lock:
            txs = self._transactions
            if decision:
                txs = [t for t in txs if t.decision.value.upper() == decision.upper()]
            return txs[:limit]

    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        with self._lock:
            for t in self._transactions:
                if t.transaction_id == transaction_id:
                    return t
            return None


transaction_service = TransactionService()
