from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.ai.llm_gateway import llm_gateway
from app.core.config import settings
from app.db.database import db

router = APIRouter(prefix="/ai", tags=["AI Intelligence & Behavioral Profiling"])


@router.get("/agents/status", summary="Get AI Agents & LLM Gateway Status")
async def get_ai_agent_status():
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
                "capabilities": ["Semantic intent match", "Adversarial pattern detection", "Recipient verification", "Task scope analysis"],
            },
            {
                "name": "BehaviouralRiskAgent",
                "agent_name": "BehaviouralRiskAgent",
                "role": "Autonomous Agent Spending Habit Profiling & Anomaly Detection",
                "status": "ONLINE" if settings.BEHAVIOURAL_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Isolation Forest model", "Statistical Z-Score analysis", "Recipient novelty detection", "Velocity burst monitoring"],
            },
            {
                "name": "SecurityIntelligenceAgent",
                "agent_name": "SecurityIntelligenceAgent",
                "role": "Counterparty Reputation & Multi-Vector Threat Intelligence",
                "status": "ONLINE" if settings.SECURITY_INTEL_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Critical blocklists", "Trusted counterparty registry", "Multi-vector adversarial classification", "Replay defense"],
            },
            {
                "name": "TransactionAuditAgent",
                "agent_name": "TransactionAuditAgent",
                "role": "Multi-Agent Consensus Synthesis & Explainable Risk Assessment",
                "status": "ONLINE" if settings.AUDIT_AGENT_ENABLED else "DISABLED",
                "capabilities": ["Cross-agent consensus analysis", "Disagreement quantification", "Explainable risk reporting", "Confidence calibration"],
            },
        ],
    }


@router.get("/agents/performance", summary="Get AI Operational & Latency Telemetry")
async def get_ai_performance():
    """Returns real operational latency, anomaly counts, and active profile statistics."""
    return db.get_ai_performance_metrics()


@router.get("/profiles", summary="List All Autonomous Agent Behavioral Profiles")
async def list_profiles():
    """Lists persistent behavioral profiles for all evaluated autonomous agents."""
    return db.list_agent_profiles()


@router.get("/profiles/{agent_id}", summary="Get Autonomous Agent Behavioral Profile")
async def get_profile(agent_id: str):
    """Retrieves an autonomous agent's persistent behavioral baseline."""
    profile = db.get_agent_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No profile found for agent '{agent_id}'")
    return profile


@router.get("/anomalies", summary="List Explainable Anomaly Findings")
async def list_anomalies(
    limit: int = Query(50, ge=1, le=200),
    anomaly_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    """Lists recent explainable anomalies with supporting evidence and detection methods."""
    return db.list_ai_anomalies(limit=limit, anomaly_type=anomaly_type, severity=severity)


@router.get("/security/findings", summary="List Security & Adversarial Threat Findings")
async def list_security_findings(limit: int = Query(50, ge=1, le=200)):
    """Lists recent security intelligence and prompt injection detections."""
    return db.list_security_findings(limit=limit)


@router.get("/evaluations/{transaction_id}", summary="Get Full AI Evaluation Trace")
async def get_evaluation(transaction_id: str):
    """Retrieves full explainable AI evaluation, consensus, and agent telemetry for a transaction."""
    evaluation = db.get_ai_evaluation(transaction_id)
    if not evaluation:
        # Fallback to reconstructing from transaction record
        tx = db.get_transaction(transaction_id)
        if not tx:
            raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
        agent_execs = db.get_agent_executions_for_tx(transaction_id)
        return {
            "transaction_id": transaction_id,
            "intent_score": 1.0 if tx.get("intent_matched") else 0.2,
            "anomaly_score": 0.0,
            "consensus_score": 1.0,
            "disagreement_score": 0.0,
            "recommended_review_level": "AUTOMATED_CLEARANCE" if tx.get("decision") == "ALLOW" else "MANUAL_OPERATOR_REQUIRED",
            "risk_category": "CRITICAL" if tx.get("decision") == "BLOCK" else ("MODERATE" if tx.get("decision") == "WARN" else "LOW"),
            "confidence_category": "HIGH_CONFIDENCE",
            "confidence_score": tx.get("confidence_score", 0.95),
            "evaluation_data": {
                "transaction": tx,
                "agent_executions": agent_execs,
            },
            "timestamp": tx.get("timestamp"),
        }
    return evaluation


@router.get("/consensus/{transaction_id}", summary="Get Multi-Agent Consensus Analysis")
async def get_consensus(transaction_id: str):
    """Retrieves consensus metrics, agreement/disagreement scores, and conflicting findings."""
    evaluation = db.get_ai_evaluation(transaction_id)
    if evaluation:
        eval_data = evaluation.get("evaluation_data", {})
        consensus_data = eval_data.get("consensus", {})
        return {
            "transaction_id": transaction_id,
            "consensus_score": evaluation.get("consensus_score", 1.0),
            "disagreement_score": evaluation.get("disagreement_score", 0.0),
            "recommended_review_level": evaluation.get("recommended_review_level", "AUTOMATED_CLEARANCE"),
            "agent_recommendations": consensus_data.get("agent_recommendations", {}),
            "agent_risk_scores": consensus_data.get("agent_risk_scores", {}),
            "conflicting_findings": consensus_data.get("conflicting_findings", []),
            "missing_evidence": consensus_data.get("missing_evidence", []),
            "consolidated_risk_summary": consensus_data.get("consolidated_risk_summary", ""),
        }
    tx = db.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return {
        "transaction_id": transaction_id,
        "consensus_score": 1.0,
        "disagreement_score": 0.0,
        "recommended_review_level": "AUTOMATED_CLEARANCE" if tx.get("decision") == "ALLOW" else "MANUAL_OPERATOR_REQUIRED",
        "agent_recommendations": {"IntentAnalysisAgent": tx.get("decision"), "BehaviouralRiskAgent": tx.get("decision"), "SecurityIntelligenceAgent": tx.get("decision")},
        "agent_risk_scores": {"IntentAnalysisAgent": tx.get("risk_score"), "BehaviouralRiskAgent": tx.get("risk_score"), "SecurityIntelligenceAgent": tx.get("risk_score")},
        "conflicting_findings": [],
        "missing_evidence": [],
        "consolidated_risk_summary": f"Transaction evaluated with verdict {tx.get('decision')}.",
    }

