import asyncio
from datetime import datetime
import json
import time
from typing import Any, Dict, List, Optional, TypedDict
import uuid

from langgraph.graph import END, START, StateGraph

from app.agents.audit_agent import audit_agent
from app.agents.behavioural_agent import behavioural_agent
from app.agents.intent_agent import intent_agent
from app.agents.schemas import (
    AgentExecutionLog,
    BehaviouralRiskResult,
    SecurityIntelligenceResult,
    TransactionAuditReport,
)
from app.agents.security_agent import security_intelligence_agent
from app.ai.llm_gateway import IntentAuditResult
from app.core.config import settings
from app.core.logging import logger
from app.db.database import db
from app.engine.decision_engine import DecisionEngine
from app.engine.evidence_engine import AuthorizationEvidence, evidence_engine
from app.engine.policy_engine import PolicyEngine
from app.engine.risk_calculator import RiskCalculator
from app.engine.transaction_validator import TransactionValidator, ValidationResult
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import (
    CheckStatus,
    DecisionType,
    RiskLevel,
    TransactionAnalysisResponse,
    TransactionRecord,
    TransactionRequest,
)
from app.services.policy_service import policy_service
from app.websocket.manager import ws_manager


class OrchestratorState(TypedDict, total=False):
    tx_id: str
    transaction: Dict[str, Any]
    validation: Dict[str, Any]
    intent_result: Optional[Dict[str, Any]]
    behavioural_result: Optional[Dict[str, Any]]
    security_result: Optional[Dict[str, Any]]
    audit_report: Optional[Dict[str, Any]]
    policy_checks: Dict[str, str]
    risk_assessment: Dict[str, Any]
    decision: str
    requires_approval: bool
    execution_allowed: bool
    reasons: List[str]
    evidence: Optional[Dict[str, Any]]
    agent_logs: List[Dict[str, Any]]
    events_emitted: List[Dict[str, Any]]
    error: Optional[str]


class MultiAgentOrchestrator:
    """
    Central Multi-Agent Security Orchestrator using LangGraph.
    Coordinates input validation, Intent Analysis, Behavioural Risk Analysis,
    Security Intelligence, Transaction Audit, Deterministic Policy Enforcement,
    Evidence Generation, Database Persistence, and Real-Time WebSocket Streaming.
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(OrchestratorState)

        # Register nodes
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("intent_agent", self._intent_agent_node)
        workflow.add_node("behavioural_agent", self._behavioural_agent_node)
        workflow.add_node("security_agent", self._security_agent_node)
        workflow.add_node("audit_agent", self._audit_agent_node)
        workflow.add_node("policy_enforcement", self._policy_enforcement_node)
        workflow.add_node("evidence_and_persist", self._evidence_and_persist_node)

        # Define graph edges (deterministic sequential flow with safe branching)
        workflow.add_edge(START, "validate")
        workflow.add_edge("validate", "intent_agent")
        workflow.add_edge("intent_agent", "behavioural_agent")
        workflow.add_edge("behavioural_agent", "security_agent")
        workflow.add_edge("security_agent", "audit_agent")
        workflow.add_edge("audit_agent", "policy_enforcement")
        workflow.add_edge("policy_enforcement", "evidence_and_persist")
        workflow.add_edge("evidence_and_persist", END)

        return workflow.compile()

    async def _emit_event(self, event_type: str, tx_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcasts real-time event to connected WebSocket clients and central publisher."""
        event = {
            "type": event_type,
            "transaction_id": tx_id,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        try:
            await ws_manager.broadcast_json(event)
        except Exception as e:
            logger.debug(f"WebSocket emit failed ({event_type}): {e}")

        # Also broadcast and persist via Phase 5 centralized EventPublisher
        try:
            from app.events.publisher import event_publisher
            from app.schemas.event import EventCategory, EventSeverity

            cat = EventCategory.SECURITY if ("security" in event_type or "attack" in event_type or "anomaly" in event_type or "intent" in event_type) else EventCategory.TRANSACTIONS
            sev = EventSeverity.CRITICAL if ("block" in event_type or "mismatch" in event_type) else (EventSeverity.WARNING if "warn" in event_type or "anomaly" in event_type else EventSeverity.INFO)

            await event_publisher.publish(
                event_type=event_type,
                category=cat,
                transaction_id=tx_id,
                source="agent",
                severity=sev,
                payload=payload,
            )
        except Exception as e:
            logger.debug(f"Publisher broadcast skipped: {e}")

        return event

    # -------------------------------------------------------------------------
    # Node 1: Input Validation
    # -------------------------------------------------------------------------
    async def _validate_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_dict = state["transaction"]
        tx_req = TransactionRequest(**tx_dict)
        tx_id = state["tx_id"]

        await self._emit_event("transaction.received", tx_id, {
            "sender": tx_req.sender,
            "recipient": tx_req.recipient,
            "amount": tx_req.amount,
            "purpose": tx_req.purpose,
        })

        await self._emit_event("ai.evaluation_started", tx_id, {
            "sender": tx_req.sender,
            "recipient": tx_req.recipient,
            "amount": tx_req.amount,
            "purpose": tx_req.purpose,
        })

        validation: ValidationResult = TransactionValidator.validate(tx_req)
        return {
            "validation": {
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "normalized": validation.normalized,
            }
        }

    # -------------------------------------------------------------------------
    # Node 2: Intent Analysis Agent
    # -------------------------------------------------------------------------
    async def _intent_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]

        await self._emit_event("agent.started", tx_id, {"agent_name": "IntentAnalysisAgent"})

        intent_res, log = await intent_agent.analyze(tx_req)

        await self._emit_event("agent.completed", tx_id, {
            "agent_name": "IntentAnalysisAgent",
            "duration_ms": log.execution_time_ms,
            "findings": log.findings,
        })

        await self._emit_event("ai.intent_analyzed", tx_id, {
            "intent_consistency_score": intent_res.intent_consistency_score,
            "intent_matches": intent_res.intent_matches_transaction,
            "recipient_matches": intent_res.recipient_matches,
            "amount_matches": intent_res.amount_matches,
            "task_scope_valid": intent_res.task_scope_valid,
            "detected_attack_type": intent_res.detected_attack_type,
            "explanation": intent_res.explanation,
        })

        if not intent_res.intent_matches_transaction or intent_res.prompt_injection_detected:
            await self._emit_event("intent.mismatch", tx_id, {
                "severity": intent_res.severity,
                "reasoning": intent_res.reasoning,
                "prompt_injection_detected": intent_res.prompt_injection_detected,
                "indicators": intent_res.suspicious_indicators,
            })

        return {
            "intent_result": intent_res.model_dump(),
            "agent_logs": [log.model_dump()],
        }

    # -------------------------------------------------------------------------
    # Node 3: Behavioural Risk Agent
    # -------------------------------------------------------------------------
    async def _behavioural_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]

        await self._emit_event("agent.started", tx_id, {"agent_name": "BehaviouralRiskAgent"})

        # Retrieve recent history from database
        history = db.list_transactions(limit=100)
        is_trusted = False
        if state.get("security_result"):
            is_trusted = state["security_result"].get("is_trusted_recipient", False)

        behaviour_res, log = behavioural_agent.analyze(
            tx=tx_req,
            recent_history=history,
            is_trusted_recipient=is_trusted,
        )

        await self._emit_event("agent.completed", tx_id, {
            "agent_name": "BehaviouralRiskAgent",
            "duration_ms": log.execution_time_ms,
            "findings": log.findings,
        })

        await self._emit_event("ai.behavior_analyzed", tx_id, {
            "anomaly_score": behaviour_res.anomaly_score,
            "is_anomaly": behaviour_res.is_anomaly,
            "profile_status": behaviour_res.profile_status,
            "is_velocity_spike": behaviour_res.is_velocity_spike,
            "is_amount_spike": behaviour_res.is_amount_spike,
            "is_novel_recipient": behaviour_res.is_novel_recipient,
            "anomalies_count": len(behaviour_res.anomalies),
        })

        for anomaly in behaviour_res.anomalies:
            await self._emit_event("ai.anomaly_detected", tx_id, anomaly.model_dump())

        existing_logs = state.get("agent_logs", [])
        return {
            "behavioural_result": behaviour_res.model_dump(),
            "agent_logs": existing_logs + [log.model_dump()],
        }

    # -------------------------------------------------------------------------
    # Node 4: Security Intelligence Agent
    # -------------------------------------------------------------------------
    async def _security_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]
        policy = policy_service.get_policy()

        await self._emit_event("agent.started", tx_id, {"agent_name": "SecurityIntelligenceAgent"})

        history = db.list_transactions(limit=100)
        prompt_injection = False
        if state.get("intent_result"):
            prompt_injection = state["intent_result"].get("prompt_injection_detected", False)

        sec_res, log = security_intelligence_agent.analyze(
            tx=tx_req,
            policy=policy,
            recent_history=history,
            prompt_injection_flag=prompt_injection,
        )

        await self._emit_event("agent.completed", tx_id, {
            "agent_name": "SecurityIntelligenceAgent",
            "duration_ms": log.execution_time_ms,
            "findings": log.findings,
        })

        await self._emit_event("ai.security_scan_completed", tx_id, {
            "threat_severity": sec_res.threat_severity,
            "findings_count": sec_res.findings_count,
            "is_blocked": sec_res.is_blocked_recipient,
            "is_duplicate": sec_res.is_duplicate_tx,
            "attack_findings_count": len(sec_res.attack_findings),
        })

        existing_logs = state.get("agent_logs", [])
        return {
            "security_result": sec_res.model_dump(),
            "agent_logs": existing_logs + [log.model_dump()],
        }

    # -------------------------------------------------------------------------
    # Node 5: Transaction Audit Agent
    # -------------------------------------------------------------------------
    async def _audit_agent_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]

        await self._emit_event("agent.started", tx_id, {"agent_name": "TransactionAuditAgent"})

        intent_res = IntentAuditResult(**(state.get("intent_result") or {}))
        behaviour_res = BehaviouralRiskResult(**(state.get("behavioural_result") or {}))
        sec_res = SecurityIntelligenceResult(**(state.get("security_result") or {}))

        report, log = audit_agent.synthesize_report(
            tx=tx_req,
            intent_res=intent_res,
            behaviour_res=behaviour_res,
            sec_res=sec_res,
        )

        await self._emit_event("agent.completed", tx_id, {
            "agent_name": "TransactionAuditAgent",
            "duration_ms": log.execution_time_ms,
            "findings": log.findings,
        })

        if report.consensus:
            await self._emit_event("ai.consensus_completed", tx_id, {
                "consensus_score": report.consensus.consensus_score,
                "disagreement_score": report.consensus.disagreement_score,
                "recommended_review_level": report.consensus.recommended_review_level,
                "has_high_severity_conflict": report.consensus.has_high_severity_conflict,
                "conflicts_count": len(report.consensus.conflicting_findings),
            })

        existing_logs = state.get("agent_logs", [])
        return {
            "audit_report": report.model_dump(),
            "agent_logs": existing_logs + [log.model_dump()],
        }

    # -------------------------------------------------------------------------
    # Node 6: Policy Enforcement & Risk Scoring
    # -------------------------------------------------------------------------
    async def _policy_enforcement_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]
        policy = policy_service.get_policy()
        policy_engine = PolicyEngine(policy)

        # Run deterministic checks
        val_data = state["validation"]
        validation = ValidationResult(
            is_valid=val_data["is_valid"],
            errors=val_data["errors"],
            normalized=val_data["normalized"],
        )
        history = db.list_transactions(limit=100)
        eval_result = policy_engine.evaluate(tx=tx_req, validation=validation, recent_history=history)

        # Integrated Risk Scoring (Deterministic rules + AI threat telemetry)
        intent_res = state.get("intent_result") or {}
        behaviour_res = state.get("behavioural_result") or {}
        sec_res = state.get("security_result") or {}

        # Base deterministic risk calculation
        risk_calc = RiskCalculator.calculate(
            amount=tx_req.amount,
            recipient=tx_req.recipient,
            sender=tx_req.sender,
            policy=policy,
            rolling_daily_volume=eval_result.rolling_daily_volume,
            tx_count_last_minute=eval_result.tx_count_last_minute,
            is_duplicate=eval_result.is_duplicate,
            is_blocked=eval_result.is_blocked and eval_result.checks.get("recipient_status") == CheckStatus.BLOCKED.value,
            is_trusted=eval_result.is_trusted,
            has_purpose=bool(tx_req.purpose and tx_req.purpose.strip()),
        )

        final_score = risk_calc.score
        reasons = list(eval_result.reasons)

        # Incorporate AI Threat Telemetry into composite score:
        # 1. Prompt Injection detected
        if intent_res.get("prompt_injection_detected"):
            final_score = max(final_score, 98)
            reasons.append("CRITICAL: Prompt injection attack attempt confirmed by AI Intent Agent.")

        # 2. Intent Discrepancy (recipient mismatch or amount divergence)
        if not intent_res.get("intent_matches_transaction", True):
            if intent_res.get("severity") == "CRITICAL":
                final_score = max(final_score, 85)
                reasons.append(f"Intent Discrepancy: {intent_res.get('reasoning')}")
            else:
                final_score = min(100, final_score + 35)
                reasons.append(f"Intent Discrepancy: {intent_res.get('reasoning')}")

        # 3. Behavioral Anomaly Outlier
        if behaviour_res.get("is_anomaly"):
            final_score = min(100, final_score + 25)
            reasons.append("Behavioral Outlier: Isolation Forest detected anomalous spending velocity.")

        # Classify final risk level
        if final_score >= policy.high_risk_threshold:
            risk_level = RiskLevel.HIGH
        elif final_score >= policy.medium_risk_threshold:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # -------------------------------------------------------------
        # Decision Synthesis (Strict Invariant: Hard BLOCK always wins)
        # -------------------------------------------------------------
        requires_approval = False
        execution_allowed = False

        if eval_result.is_blocked or risk_level == RiskLevel.HIGH or intent_res.get("prompt_injection_detected"):
            decision = DecisionType.BLOCK
            execution_allowed = False
            requires_approval = False
        elif (
            eval_result.requires_approval
            or risk_level == RiskLevel.MEDIUM
            or not intent_res.get("intent_matches_transaction", True)
        ):
            decision = DecisionType.WARN
            execution_allowed = False
            requires_approval = True
        else:
            decision = DecisionType.ALLOW
            execution_allowed = True
            requires_approval = False
            if not reasons:
                reasons.append("All deterministic security policies and AI intent audits passed.")

        # Structure normalized policy checks map
        policy_checks_map = {
            "data_integrity": eval_result.checks.get("data_integrity", CheckStatus.PASSED.value),
            "recipient_status": eval_result.checks.get("recipient_status", CheckStatus.PASSED.value),
            "amount_limit": eval_result.checks.get("amount_limit", CheckStatus.PASSED.value),
            "daily_limit": eval_result.checks.get("daily_limit", CheckStatus.PASSED.value),
            "duplicate_check": eval_result.checks.get("duplicate_check", CheckStatus.PASSED.value),
            "frequency_check": eval_result.checks.get("frequency_check", CheckStatus.PASSED.value),
            "intent_audit": "PASSED" if intent_res.get("intent_matches_transaction", True) else (
                "FAILED" if intent_res.get("severity") == "CRITICAL" else "WARNING"
            ),
        }

        await self._emit_event("policy.evaluated", tx_id, {
            "policy_checks": policy_checks_map,
            "decision": decision.value,
        })

        await self._emit_event("risk.assessed", tx_id, {
            "risk_score": final_score,
            "risk_level": risk_level.value,
            "reasons": reasons,
        })

        return {
            "policy_checks": policy_checks_map,
            "risk_assessment": {
                "score": final_score,
                "level": risk_level.value,
                "breakdown": risk_calc.breakdown,
            },
            "decision": decision.value,
            "requires_approval": requires_approval,
            "execution_allowed": execution_allowed,
            "reasons": reasons,
        }

    # -------------------------------------------------------------------------
    # Node 7: Cryptographic Evidence & Persistence
    # -------------------------------------------------------------------------
    async def _evidence_and_persist_node(self, state: OrchestratorState) -> OrchestratorState:
        tx_req = TransactionRequest(**state["transaction"])
        tx_id = state["tx_id"]
        policy = policy_service.get_policy()
        decision_str = state["decision"]
        risk_score = state["risk_assessment"]["score"]
        risk_level_str = state["risk_assessment"]["level"]
        intent_res = state.get("intent_result") or {}

        # Generate cryptographic authorization evidence
        evidence: AuthorizationEvidence = evidence_engine.generate_evidence(
            transaction_id=tx_id,
            sender=tx_req.sender,
            recipient=tx_req.recipient,
            amount=tx_req.amount,
            currency=tx_req.currency,
            intent_text=tx_req.purpose,
            policy_version="1.0.0",
            decision=decision_str,
            risk_score=risk_score,
            metadata={
                "risk_level": risk_level_str,
                "intent_matched": intent_res.get("intent_matches_transaction", True),
                "prompt_injection_flagged": intent_res.get("prompt_injection_detected", False),
            },
        )

        await self._emit_event("evidence.generated", tx_id, {
            "sha256_digest": evidence.sha256_digest,
            "policy_version": evidence.policy_version,
            "canonical_payload": evidence.canonical_payload,
        })

        # Persist transaction in SQLite database
        tx_record = {
            "transaction_id": tx_id,
            "sender": tx_req.sender,
            "recipient": tx_req.recipient,
            "amount": tx_req.amount,
            "currency": tx_req.currency,
            "decision": decision_str,
            "risk_score": risk_score,
            "risk_level": risk_level_str,
            "requires_approval": state["requires_approval"],
            "execution_allowed": state["execution_allowed"],
            "confidence_score": 0.98 if decision_str == "ALLOW" else 0.95,
            "reasons": state["reasons"],
            "policy_checks": state["policy_checks"],
            "agent_id": tx_req.agent_id or "autonomous-agent-01",
            "purpose": tx_req.purpose,
            "approval_status": "PENDING" if state["requires_approval"] else ("APPROVED" if decision_str == "ALLOW" else "NONE"),
            "intent_matched": intent_res.get("intent_matches_transaction", True),
            "intent_discrepancy": intent_res.get("reasoning") if not intent_res.get("intent_matches_transaction", True) else None,
            "is_mock_simulation": True,
            "timestamp": (tx_req.timestamp or datetime.utcnow()).isoformat(),
        }
        db.save_transaction(tx_record)

        # Persist authorization evidence
        db.save_authorization_evidence(
            transaction_id=tx_id,
            canonical_payload=evidence.canonical_payload,
            sha256_digest=evidence.sha256_digest,
            policy_version=evidence.policy_version,
            is_tamper_verified=True,
            metadata=evidence.metadata,
        )

        # Persist agent execution logs
        for log_dict in state.get("agent_logs", []):
            db.save_agent_execution(
                transaction_id=tx_id,
                agent_name=log_dict["agent_name"],
                status=log_dict["status"],
                execution_time_ms=log_dict["execution_time_ms"],
                findings=log_dict["findings"],
            )

        # Persist comprehensive AI evaluation record & consensus (Phase 6)
        audit_rep = state.get("audit_report") or {}
        consensus_dict = audit_rep.get("consensus") or {}
        explainable_dict = audit_rep.get("explainable_assessment") or {}
        confidence_dict = audit_rep.get("confidence_assessment") or {}
        behaviour_res = state.get("behavioural_result") or {}
        sec_res = state.get("security_result") or {}

        eval_record = {
            "transaction_id": tx_id,
            "intent_score": intent_res.get("intent_consistency_score", 1.0),
            "anomaly_score": behaviour_res.get("anomaly_score", 0.0),
            "consensus_score": consensus_dict.get("consensus_score", 1.0),
            "disagreement_score": consensus_dict.get("disagreement_score", 0.0),
            "recommended_review_level": consensus_dict.get("recommended_review_level", "AUTOMATED_CLEARANCE"),
            "risk_category": explainable_dict.get("risk_category", "LOW"),
            "confidence_category": confidence_dict.get("confidence_category", "HIGH_CONFIDENCE"),
            "confidence_score": confidence_dict.get("confidence_score", 0.95),
            "evaluation_data": {
                "intent": intent_res,
                "behavioural": behaviour_res,
                "security": sec_res,
                "audit": audit_rep,
                "consensus": consensus_dict,
                "explainable_assessment": explainable_dict,
                "confidence_assessment": confidence_dict,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        db.save_ai_evaluation(eval_record)

        # Update autonomous agent behavioral profile using verified history (Phase 6)
        try:
            db.update_agent_profile_from_history(tx_req.sender, tx_record)
        except Exception as e:
            logger.debug(f"Profile update note: {e}")

        # Persist security findings if any critical issues were detected
        if decision_str == "BLOCK":
            db.save_security_finding(
                finding_id=f"find_{tx_id}",
                transaction_id=tx_id,
                category="Exploit Attempt Intercepted",
                severity="CRITICAL",
                title=f"Blocked Threat: {tx_req.recipient}",
                description="; ".join(state["reasons"][:2]),
                indicator=tx_req.recipient,
            )
        elif decision_str == "WARN":
            db.save_security_finding(
                finding_id=f"find_{tx_id}",
                transaction_id=tx_id,
                category="Human Verification Required",
                severity="MEDIUM",
                title=f"Suspicious Transfer: {tx_req.recipient}",
                description="; ".join(state["reasons"][:2]),
                indicator=tx_req.recipient,
            )

        # Emit final verdict event
        verdict_event_type = (
            "transaction.allowed" if decision_str == "ALLOW"
            else ("transaction.warned" if decision_str == "WARN" else "transaction.blocked")
        )
        await self._emit_event(verdict_event_type, tx_id, {
            "decision": decision_str,
            "risk_score": risk_score,
            "risk_level": risk_level_str,
            "execution_allowed": state["execution_allowed"],
            "requires_approval": state["requires_approval"],
            "sha256_digest": evidence.sha256_digest,
        })

        if state["requires_approval"]:
            await self._emit_event("approval.required", tx_id, {
                "recipient": tx_req.recipient,
                "amount": tx_req.amount,
                "reasons": state["reasons"],
            })

        return {"evidence": evidence.model_dump()}

    async def execute(self, tx_req: TransactionRequest) -> TransactionAnalysisResponse:
        """Executes the full LangGraph workflow for an incoming transaction."""
        tx_id = tx_req.transaction_id or f"tx_{uuid.uuid4().hex[:12]}"
        initial_state: OrchestratorState = {
            "tx_id": tx_id,
            "transaction": tx_req.model_dump(),
            "reasons": [],
            "agent_logs": [],
            "events_emitted": [],
        }

        # Run through the compiled LangGraph workflow
        final_state = await self.graph.ainvoke(initial_state)

        tx_timestamp = tx_req.timestamp or datetime.utcnow()
        audit_rep = final_state.get("audit_report") or {}
        beh_rep = final_state.get("behavioural_result") or {}

        return TransactionAnalysisResponse(
            transaction_id=tx_id,
            sender=tx_req.sender,
            recipient=tx_req.recipient,
            amount=tx_req.amount,
            currency="NEAR",
            decision=DecisionType(final_state["decision"]),
            risk_score=final_state["risk_assessment"]["score"],
            risk_level=RiskLevel(final_state["risk_assessment"]["level"]),
            requires_approval=final_state["requires_approval"],
            reasons=final_state["reasons"],
            policy_checks=final_state["policy_checks"],
            timestamp=tx_timestamp,
            execution_allowed=final_state["execution_allowed"],
            confidence_score=0.98 if final_state["decision"] == "ALLOW" else 0.95,
            is_mock_simulation=True,
            consensus=audit_rep.get("consensus"),
            explainable_assessment=audit_rep.get("explainable_assessment"),
            confidence_assessment=audit_rep.get("confidence_assessment"),
            agent_profile=beh_rep.get("agent_profile"),
        )


multi_agent_orchestrator = MultiAgentOrchestrator()

