import time
from typing import Tuple
from app.agents.schemas import AgentExecutionLog
from app.ai.llm_gateway import IntentAuditResult, llm_gateway
from app.core.logging import logger
from app.schemas.transaction import TransactionRequest


class IntentAnalysisAgent:
    """
    Specialized Agent A: Intent Analysis Agent
    Audits the declared natural language goal of an autonomous agent against
    actual financial parameters to detect semantic divergence and prompt injection.
    """

    NAME = "IntentAnalysisAgent"

    @classmethod
    async def analyze(cls, tx: TransactionRequest) -> Tuple[IntentAuditResult, AgentExecutionLog]:
        start = time.perf_counter()
        logger.info(f"[{cls.NAME}] Auditing intent for tx {tx.transaction_id} from {tx.sender}")

        intent_result = await llm_gateway.audit_intent(
            purpose_text=tx.purpose or "",
            actual_sender=tx.sender,
            actual_recipient=tx.recipient,
            actual_amount=tx.amount,
            actual_currency=tx.currency,
            metadata=tx.metadata,
        )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        status = "SUCCESS"
        if intent_result.prompt_injection_detected or not intent_result.intent_matches_transaction:
            status = "WARNING" if intent_result.severity in ("MEDIUM", "LOW") else "CRITICAL"

        log = AgentExecutionLog(
            agent_name=cls.NAME,
            status=status,
            execution_time_ms=duration_ms,
            findings={
                "intent_matches": intent_result.intent_matches_transaction,
                "recipient_matches": intent_result.recipient_matches,
                "amount_matches": intent_result.amount_matches,
                "amount_deviation_percent": intent_result.amount_deviation_percent,
                "prompt_injection_detected": intent_result.prompt_injection_detected,
                "severity": intent_result.severity,
                "suspicious_indicators": intent_result.suspicious_indicators,
                "provider_used": intent_result.llm_provider_used,
                "intent_consistency_score": intent_result.intent_consistency_score,
                "intent_summary": intent_result.intent_summary,
                "explanation": intent_result.explanation,
                "task_scope_valid": intent_result.task_scope_valid,
                "detected_attack_type": intent_result.detected_attack_type,
            },
        )

        return intent_result, log


intent_agent = IntentAnalysisAgent()

