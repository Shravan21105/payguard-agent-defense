import asyncio
from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import multi_agent_orchestrator
from app.blockchain.models import (
    OnChainAuthorizationRequest,
    OnChainEscrowActionRequest,
    OnChainExecutionRequest,
)
from app.blockchain.signer import near_to_yocto
from app.core.config import settings
from app.core.logging import logger
from app.db.database import db
from app.engine.evidence_engine import evidence_engine
from app.schemas.transaction import (
    DecisionType,
    InitiateTransactionRequest,
    RiskLevel,
    TransactionAnalysisResponse,
    TransactionRecord,
    TransactionRequest,
    TransactionStatus,
)
from app.services.blockchain_service import blockchain_service
from app.events.publisher import event_publisher
from app.websocket.manager import ws_manager


class TransactionService:
    """
    Manages end-to-end transaction security evaluation lifecycle, LangGraph multi-agent execution,
    cryptographic Ed25519 evidence generation, NEAR Testnet smart contract vault execution,
    timelock escrow creation, and persistent SQLite storage.
    """

    def __init__(self):
        self._sender_locks: Dict[str, asyncio.Lock] = {}
        self._lock_guard = asyncio.Lock()

    async def _get_sender_lock(self, sender: str) -> asyncio.Lock:
        clean = (sender or "default").lower().strip()
        async with self._lock_guard:
            if clean not in self._sender_locks:
                self._sender_locks[clean] = asyncio.Lock()
            return self._sender_locks[clean]

    async def _emit_event(self, event_type: str, transaction_id: str, payload: Dict[str, Any]) -> None:
        """Broadcasts real-time standardized telemetry event through centralized event publisher."""
        try:
            await event_publisher.publish(
                event_type=event_type,
                transaction_id=transaction_id,
                payload=payload,
                source="transaction_service",
            )
        except Exception as e:
            logger.debug(f"[TransactionService] Event emit error ({event_type}): {e}")

    async def analyze_transaction(self, req: TransactionRequest) -> TransactionAnalysisResponse:
        """Runs transaction through full multi-agent LangGraph workflow."""
        return await multi_agent_orchestrator.execute(req)

    async def initiate_transaction(self, req: InitiateTransactionRequest) -> TransactionRecord:
        """
        Unified Phase 4 End-to-End Transaction Pipeline:
        1. Ingests request & assigns unique transaction ID / nonce.
        2. Enforces anti-replay and idempotency.
        3. Sets status RECEIVED and broadcasts event.
        4. Advances to ANALYZING and triggers Multi-Agent intent and behavioral checks.
        5. Evaluates deterministic security policy engine.
        6. Routes decision:
           - ALLOW: Signs Ed25519 authorization, executes on NEAR vault, verifies testnet receipt, sets CONFIRMED.
           - WARN: Signs escrow authorization, creates vault timelock escrow, sets ESCROW_CREATED.
           - BLOCK: Refuses to sign execution authorization, logs finding, sets BLOCKED.
        7. Persists final record and broadcasts lifecycle confirmation.
        """
        tx_id = req.transaction_id or f"tx_pg_{uuid.uuid4().hex[:10]}"

        # 1. Anti-Replay & Idempotency Check
        sender_lock = await self._get_sender_lock(req.sender)
        async with sender_lock:
            existing = db.get_transaction(tx_id)
            if existing and existing.get("status") in ("CONFIRMED", "BLOCKED"):
                logger.info(f"Transaction {tx_id} already exists with status {existing.get('status')}. Returning existing record.")
                return TransactionRecord(**existing)

            # 2. Status: RECEIVED
            await self._emit_event("transaction.received", tx_id, {
                "sender": req.sender,
                "recipient": req.recipient,
                "amount": req.amount,
                "currency": req.currency,
                "purpose": req.purpose,
                "dry_run": req.dry_run,
            })

            db.save_transaction({
                "transaction_id": tx_id,
                "sender": req.sender,
                "recipient": req.recipient,
                "amount": req.amount,
                "currency": req.currency,
                "decision": "PENDING",
                "risk_score": 0,
                "risk_level": "LOW",
                "requires_approval": False,
                "execution_allowed": False,
                "reasons": ["Transaction received, entering security pipeline."],
                "policy_checks": {},
                "agent_id": req.agent_id or "autonomous-agent-01",
                "purpose": req.purpose,
            "approval_status": "NONE",
            "is_mock_simulation": req.dry_run,
            "status": TransactionStatus.RECEIVED.value,
            "execution_mode": "SIMULATION" if req.dry_run else "ONCHAIN",
        })

        # 3. Status: ANALYZING
        await self._emit_event("transaction.analyzing", tx_id, {
            "stage": "Multi-agent intent and behavioral analysis",
        })

        try:
            # 4. Multi-Agent Orchestration & Policy Evaluation
            tx_request = TransactionRequest(
                transaction_id=tx_id,
                sender=req.sender,
                recipient=req.recipient,
                amount=req.amount,
                currency=req.currency,
                agent_id=req.agent_id,
                purpose=req.purpose,
                metadata=req.metadata,
            )
            analysis = await multi_agent_orchestrator.execute(tx_request)

            # 5. Deterministic Routing
            if analysis.decision == DecisionType.BLOCK:
                # Execution authorization strictly withheld
                db.save_transaction({
                    "transaction_id": tx_id,
                    "sender": req.sender,
                    "recipient": req.recipient,
                    "amount": req.amount,
                    "currency": req.currency,
                    "decision": "BLOCK",
                    "risk_score": analysis.risk_score,
                    "risk_level": analysis.risk_level.value,
                    "requires_approval": False,
                    "execution_allowed": False,
                    "confidence_score": analysis.confidence_score,
                    "reasons": analysis.reasons,
                    "policy_checks": analysis.policy_checks,
                    "agent_id": req.agent_id,
                    "purpose": req.purpose,
                    "approval_status": "NONE",
                    "is_mock_simulation": req.dry_run,
                    "status": TransactionStatus.BLOCKED.value,
                    "error_details": "Execution rejected: Deterministic security policy blocked this transaction.",
                    "execution_mode": "SIMULATION" if req.dry_run else "ONCHAIN",
                })

                await self._emit_event("transaction.blocked", tx_id, {
                    "decision": "BLOCK",
                    "risk_score": analysis.risk_score,
                    "reasons": analysis.reasons,
                })

                updated = db.get_transaction(tx_id)
                return TransactionRecord(**updated)

            elif analysis.decision == DecisionType.WARN:
                # Route into timelock escrow pending operator approval
                if req.dry_run:
                    db.save_transaction({
                        "transaction_id": tx_id,
                        "sender": req.sender,
                        "recipient": req.recipient,
                        "amount": req.amount,
                        "currency": req.currency,
                        "decision": "WARN",
                        "risk_score": analysis.risk_score,
                        "risk_level": analysis.risk_level.value,
                        "requires_approval": True,
                        "execution_allowed": False,
                        "confidence_score": analysis.confidence_score,
                        "reasons": analysis.reasons,
                        "policy_checks": analysis.policy_checks,
                        "agent_id": req.agent_id,
                        "purpose": req.purpose,
                        "approval_status": "PENDING",
                        "is_mock_simulation": True,
                        "status": TransactionStatus.WARN_PENDING_APPROVAL.value,
                        "execution_mode": "SIMULATION",
                    })
                    await self._emit_event("transaction.warned", tx_id, {
                        "decision": "WARN",
                        "risk_score": analysis.risk_score,
                        "reasons": analysis.reasons,
                        "mode": "SIMULATION",
                    })
                    updated = db.get_transaction(tx_id)
                    return TransactionRecord(**updated)
                else:
                    # On-chain Escrow Creation
                    auth_req = OnChainAuthorizationRequest(
                        transaction_id=tx_id,
                        sender=req.sender,
                        recipient=req.recipient,
                        amount=req.amount,
                        currency=req.currency,
                        purpose=req.purpose or "Autonomous task payment",
                        network_id=req.network_id or getattr(settings, "NEAR_NETWORK_ID", "testnet"),
                        contract_id=req.contract_id or getattr(settings, "NEAR_VAULT_CONTRACT_ID", "payguard-vault.testnet"),
                        timelock_seconds=req.timelock_seconds or 3600,
                    )
                    signed_auth = await blockchain_service.authorize_transaction(auth_req, analysis=analysis)
                    escrow_record = await blockchain_service.create_escrow(
                        signed_auth, timelock_seconds=req.timelock_seconds or 3600
                    )

                    db.save_transaction({
                        "transaction_id": tx_id,
                        "sender": req.sender,
                        "recipient": req.recipient,
                        "amount": req.amount,
                        "currency": req.currency,
                        "decision": "WARN",
                        "risk_score": analysis.risk_score,
                        "risk_level": analysis.risk_level.value,
                        "requires_approval": True,
                        "execution_allowed": False,
                        "confidence_score": analysis.confidence_score,
                        "reasons": analysis.reasons,
                        "policy_checks": analysis.policy_checks,
                        "agent_id": req.agent_id,
                        "purpose": req.purpose,
                        "approval_status": "PENDING",
                        "is_mock_simulation": False,
                        "status": TransactionStatus.ESCROW_CREATED.value,
                        "escrow_id": escrow_record.escrow_id,
                        "tx_hash": escrow_record.tx_hash,
                        "explorer_url": f"https://testnet.nearblocks.io/txns/{escrow_record.tx_hash}",
                        "execution_mode": "ONCHAIN",
                        "evidence_hash": escrow_record.tx_hash,
                    })

                    await self._emit_event("escrow.created", tx_id, {
                        "escrow_id": escrow_record.escrow_id,
                        "timelock_until": escrow_record.timelock_until,
                        "amount": req.amount,
                        "recipient": req.recipient,
                        "tx_hash": escrow_record.tx_hash,
                    })

                    updated = db.get_transaction(tx_id)
                    return TransactionRecord(**updated)

            else:
                # Decision is ALLOW
                if req.dry_run:
                    db.save_transaction({
                        "transaction_id": tx_id,
                        "sender": req.sender,
                        "recipient": req.recipient,
                        "amount": req.amount,
                        "currency": req.currency,
                        "decision": "ALLOW",
                        "risk_score": analysis.risk_score,
                        "risk_level": analysis.risk_level.value,
                        "requires_approval": False,
                        "execution_allowed": True,
                        "confidence_score": analysis.confidence_score,
                        "reasons": analysis.reasons,
                        "policy_checks": analysis.policy_checks,
                        "agent_id": req.agent_id,
                        "purpose": req.purpose,
                        "approval_status": "APPROVED",
                        "is_mock_simulation": True,
                        "status": TransactionStatus.ALLOWED.value,
                        "execution_mode": "SIMULATION",
                    })
                    await self._emit_event("transaction.allowed", tx_id, {
                        "decision": "ALLOW",
                        "risk_score": analysis.risk_score,
                        "mode": "SIMULATION",
                    })
                    updated = db.get_transaction(tx_id)
                    return TransactionRecord(**updated)
                else:
                    # Full on-chain execution with Ed25519 authorization
                    await self._emit_event("transaction.allowed", tx_id, {
                        "decision": "ALLOW",
                        "risk_score": analysis.risk_score,
                    })

                    # Status: EXECUTING
                    await self._emit_event("transaction.executing", tx_id, {
                        "stage": "Submitting to NEAR Testnet Vault with Ed25519 signature",
                    })

                    auth_req = OnChainAuthorizationRequest(
                        transaction_id=tx_id,
                        sender=req.sender,
                        recipient=req.recipient,
                        amount=req.amount,
                        currency=req.currency,
                        purpose=req.purpose or "Autonomous task payment",
                        network_id=req.network_id or getattr(settings, "NEAR_NETWORK_ID", "testnet"),
                        contract_id=req.contract_id or getattr(settings, "NEAR_VAULT_CONTRACT_ID", "payguard-vault.testnet"),
                    )
                    signed_auth = await blockchain_service.authorize_transaction(auth_req, analysis=analysis)

                    exec_req = OnChainExecutionRequest(authorization=signed_auth)
                    exec_record = await blockchain_service.execute_or_record_onchain(exec_req)

                    db.save_transaction({
                        "transaction_id": tx_id,
                        "sender": req.sender,
                        "recipient": req.recipient,
                        "amount": req.amount,
                        "currency": req.currency,
                        "decision": "ALLOW",
                        "risk_score": analysis.risk_score,
                        "risk_level": analysis.risk_level.value,
                        "requires_approval": False,
                        "execution_allowed": True,
                        "confidence_score": analysis.confidence_score,
                        "reasons": analysis.reasons,
                        "policy_checks": analysis.policy_checks,
                        "agent_id": req.agent_id,
                        "purpose": req.purpose,
                        "approval_status": "CONFIRMED",
                        "is_mock_simulation": False,
                        "status": TransactionStatus.CONFIRMED.value,
                        "tx_hash": exec_record.tx_hash,
                        "block_height": exec_record.block_height,
                        "block_hash": exec_record.block_hash,
                        "explorer_url": exec_record.explorer_url,
                        "execution_mode": "ONCHAIN",
                        "evidence_hash": exec_record.tx_hash,
                    })

                    await self._emit_event("transaction.confirmed", tx_id, {
                        "tx_hash": exec_record.tx_hash,
                        "block_height": exec_record.block_height,
                        "block_hash": exec_record.block_hash,
                        "explorer_url": exec_record.explorer_url,
                        "amount": req.amount,
                        "recipient": req.recipient,
                    })

                    updated = db.get_transaction(tx_id)
                    return TransactionRecord(**updated)

        except Exception as e:
            logger.error(f"[TransactionService] Error initiating transaction {tx_id}: {e}", exc_info=True)
            db.save_transaction({
                "transaction_id": tx_id,
                "sender": req.sender,
                "recipient": req.recipient,
                "amount": req.amount,
                "currency": req.currency,
                "decision": "BLOCK",
                "risk_score": 100,
                "risk_level": "HIGH",
                "requires_approval": False,
                "execution_allowed": False,
                "reasons": [f"Execution error: {str(e)}"],
                "policy_checks": {"data_integrity": "FAILED"},
                "agent_id": req.agent_id,
                "purpose": req.purpose,
                "approval_status": "NONE",
                "status": TransactionStatus.FAILED.value,
                "error_details": str(e),
                "is_mock_simulation": req.dry_run,
                "execution_mode": "SIMULATION" if req.dry_run else "ONCHAIN",
            })
            await self._emit_event("transaction.failed", tx_id, {"error": str(e)})
            raise

    def list_transactions(
        self,
        limit: int = 50,
        decision: Optional[str] = None,
    ) -> List[TransactionRecord]:
        rows = db.list_transactions(limit=limit, decision=decision)
        return [TransactionRecord(**r) for r in rows]

    def get_transaction(self, transaction_id: str) -> Optional[TransactionRecord]:
        row = db.get_transaction(transaction_id)
        if not row:
            return None
        return TransactionRecord(**row)

    def get_authorization_evidence(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        return db.get_authorization_evidence(transaction_id)

    def get_agent_executions(self, transaction_id: str) -> List[Dict[str, Any]]:
        return db.get_agent_executions(transaction_id)

    def list_recent_agent_executions(self, limit: int = 30) -> List[Dict[str, Any]]:
        return db.list_recent_agent_executions(limit=limit)

    def list_pending_approvals(self) -> List[TransactionRecord]:
        rows = db.list_pending_approvals()
        return [TransactionRecord(**r) for r in rows]

    async def record_human_approval(
        self,
        transaction_id: str,
        decision: str,  # 'APPROVE' or 'REJECT'
        operator_id: str = "operator_01",
        reason: Optional[str] = None,
    ) -> Optional[TransactionRecord]:
        """Processes human operator sign-off for a WARN transaction and coordinates on-chain escrow."""
        existing = db.get_transaction(transaction_id)
        if not existing:
            return None

        # CRITICAL SECURITY INVARIANT: Deterministic BLOCK decisions can NEVER be overridden
        if existing.get("decision") == "BLOCK" or existing.get("status") == TransactionStatus.BLOCKED.value:
            logger.warning(f"[Security] Denied attempt to approve deterministically BLOCKED transaction: {transaction_id}")
            raise ValueError(f"Cannot approve deterministically BLOCKED transaction '{transaction_id}'. Deterministic policy blocks cannot be overridden.")

        # STRICT SCOPE: Only transactions that explicitly require human approval can be decided
        if not existing.get("requires_approval") and existing.get("decision") != "WARN":
            raise ValueError(f"Transaction '{transaction_id}' does not require human approval.")

        # ANTI-DOUBLE-APPROVAL / STATE CONSISTENCY: Escrows and approvals cannot be re-decided once resolved
        curr_approval = (existing.get("approval_status") or "").upper()
        curr_status = (existing.get("status") or "").upper()
        if curr_approval in ("APPROVED", "REJECTED", "CONFIRMED") or curr_status in ("CONFIRMED", "RELEASED", "REFUNDED", "REJECTED"):
            logger.warning(f"[Security] Denied attempt to re-decide already resolved transaction: {transaction_id} (status={curr_status}, approval={curr_approval})")
            raise ValueError(f"Transaction '{transaction_id}' has already been resolved ({curr_status}) and cannot be re-approved or re-rejected.")

        # Check if this transaction has an on-chain escrow
        escrow_id = existing.get("escrow_id") or f"escrow_{transaction_id}"
        if existing.get("status") == TransactionStatus.ESCROW_CREATED.value or existing.get("requires_approval"):
            try:
                escrow_action = OnChainEscrowActionRequest(
                    escrow_id=escrow_id,
                    decision=decision,
                    operator_id=operator_id,
                    reason=reason,
                )
                await blockchain_service.decide_escrow(escrow_action)
            except Exception as e:
                logger.warning(f"Escrow coordination warning for {transaction_id}: {e}")

        success = db.record_approval(
            transaction_id=transaction_id,
            decision=decision,
            operator_id=operator_id,
            reason=reason,
        )
        if not success:
            return None

        # If approved, generate updated cryptographic authorization evidence
        if decision == "APPROVE":
            evidence = evidence_engine.generate_evidence(
                transaction_id=transaction_id,
                sender=existing["sender"],
                recipient=existing["recipient"],
                amount=existing["amount"],
                currency=existing["currency"],
                intent_text=existing["purpose"],
                policy_version="1.0.0",
                decision="ALLOW",
                risk_score=existing["risk_score"],
                metadata={
                    "human_approval": True,
                    "operator_id": operator_id,
                    "approved_at": datetime.utcnow().isoformat(),
                    "reason": reason or "Operator authorized release of funds",
                },
            )
            db.save_authorization_evidence(
                transaction_id=transaction_id,
                canonical_payload=evidence.canonical_payload,
                sha256_digest=evidence.sha256_digest,
                policy_version=evidence.policy_version,
                is_tamper_verified=True,
                metadata=evidence.metadata,
            )

        new_status = TransactionStatus.CONFIRMED.value if decision == "APPROVE" else TransactionStatus.REJECTED.value
        exec_allowed = True if decision == "APPROVE" else False

        # Update transaction record status
        tx_dict = db.get_transaction(transaction_id)
        if tx_dict:
            tx_dict["status"] = new_status
            tx_dict["execution_allowed"] = exec_allowed
            tx_dict["approval_status"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
            db.save_transaction(tx_dict)

        # Broadcast update over WebSocket
        event_name = "escrow.released" if decision == "APPROVE" else "escrow.refunded"
        await self._emit_event(event_name, transaction_id, {
            "status": new_status,
            "operator_id": operator_id,
            "reason": reason,
        })

        updated = db.get_transaction(transaction_id)
        return TransactionRecord(**updated) if updated else None


transaction_service = TransactionService()
