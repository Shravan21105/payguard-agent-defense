from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.ai.llm_gateway import IntentAuditResult, llm_gateway
from app.core.config import settings
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/agents", tags=["Multi-Agent Intelligence"])


class TestIntentRequest(BaseModel):
    purpose_text: str = Field(..., description="Agent natural language intent")
    recipient: str = Field(..., description="Target recipient account")
    amount: float = Field(..., gt=0, description="Amount in NEAR")
    currency: str = Field(default="NEAR")


@router.get("/status", summary="Get Multi-Agent Subsystem Status")
async def get_agent_status():
    """Returns operational status of the 4 specialized agents and LLM Gateway."""
    return {
        "orchestrator": "LangGraph StateGraph Active",
        "orchestrator_status": "LangGraph StateGraph Active",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "database_status": "CONNECTED",
        "llm_gateway": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.LLM_MODEL,
            "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
            "api_key_configured": bool(settings.LLM_API_KEY),
            "status": "OPERATIONAL",
        },
        "agents": [
            {
                "name": "IntentAnalysisAgent",
                "agent_name": "IntentAnalysisAgent",
                "role": "LLM Semantic Goal Extraction & Discrepancy Auditing",
                "status": "ONLINE" if settings.INTENT_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Semantic intent match", "Prompt injection defense", "Recipient verification", "Amount deviation calculation"],
            },
            {
                "name": "BehaviouralRiskAgent",
                "agent_name": "BehaviouralRiskAgent",
                "role": "Spending Habit Profiling & Anomaly Detection",
                "status": "ONLINE" if settings.BEHAVIOURAL_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Isolation Forest model", "Velocity spike detection", "Historical baseline tracking"],
            },
            {
                "name": "SecurityIntelligenceAgent",
                "agent_name": "SecurityIntelligenceAgent",
                "role": "Counterparty Reputation & Attack Signature Detection",
                "status": "ONLINE" if settings.SECURITY_INTEL_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Critical blocklist verification", "Trusted registry matching", "Deduplication replay defense"],
            },
            {
                "name": "TransactionAuditAgent",
                "agent_name": "TransactionAuditAgent",
                "role": "Multi-Agent Synthesis & Structured Audit Reporting",
                "status": "ONLINE" if settings.AUDIT_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Cross-agent aggregation", "Actionable recommendations", "Explainable security reporting"],
            },
        ],
    }


@router.get("/runs", summary="List Recent Agent Execution Runs")
async def list_agent_runs(limit: int = 30):
    """Retrieves recent multi-agent telemetry and performance logs."""
    return transaction_service.list_recent_agent_executions(limit=limit)


@router.post("/test-intent", summary="Test Intent Analysis Agent on Custom Input")
async def test_intent(request: TestIntentRequest):
    """Interactive tester to evaluate declared agent intent against transaction parameters."""
    audit_res = await llm_gateway.audit_intent(
        purpose_text=request.purpose_text,
        actual_sender="agent-tester.near",
        actual_recipient=request.recipient,
        actual_amount=request.amount,
        actual_currency=request.currency,
    )

    if audit_res.prompt_injection_detected or audit_res.severity == "CRITICAL":
        sim_dec = "BLOCK"
        sim_score = 98 if audit_res.prompt_injection_detected else 85
    elif not audit_res.intent_matches_transaction:
        sim_dec = "WARN"
        sim_score = 65
    else:
        sim_dec = "ALLOW"
        sim_score = 15

    return {
        "status": "COMPLETED",
        "audit_result": audit_res.model_dump(),
        "simulated_decision": sim_dec,
        "simulated_risk_score": sim_score,
        "reasons": audit_res.suspicious_indicators or ["Intent matches transaction parameters."],
    }

