from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ai.llm_gateway import IntentAuditResult
from app.engine.evidence_engine import AuthorizationEvidence
from app.engine.policy_engine import PolicyEvaluationResult
from app.engine.risk_calculator import RiskAssessment
from app.engine.transaction_validator import ValidationResult
from app.schemas.transaction import DecisionType, TransactionRequest


class AgentExecutionLog(BaseModel):
    """Execution telemetry for a single specialized agent."""
    agent_name: str
    status: str = "SUCCESS"  # SUCCESS, WARNING, FAILED, SKIPPED
    execution_time_ms: float
    findings: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentBehavioralProfile(BaseModel):
    """Persistent behavioral baseline and spending history for an autonomous agent."""
    agent_id: str
    profile_version: int = 1
    transaction_count: int = 0
    average_amount: float = 0.0
    maximum_amount: float = 0.0
    std_dev_amount: float = 0.0
    transaction_frequency_per_day: float = 0.0
    spending_velocity_24h: float = 0.0
    known_recipients: List[str] = Field(default_factory=list)
    recipient_distribution: Dict[str, int] = Field(default_factory=dict)
    allow_count: int = 0
    warn_count: int = 0
    block_count: int = 0
    status: str = "INSUFFICIENT_HISTORY"  # "ACTIVE" | "INSUFFICIENT_HISTORY"
    behavioral_baseline: Dict[str, Any] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnomalyFinding(BaseModel):
    """Structured, explainable anomaly observation."""
    anomaly_type: str  # AMOUNT_SPIKE, VELOCITY_BURST, NOVEL_RECIPIENT, STATISTICAL_DEVIATION, ISOLATION_FOREST_OUTLIER, INSUFFICIENT_HISTORY
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    anomaly_score: float = Field(default=0.0, ge=0.0, le=100.0)
    affected_agent: str
    transaction_id: Optional[str] = "unassigned"
    observed_value: Any
    expected_range: str
    explanation: str
    supporting_evidence: List[str] = Field(default_factory=list)
    detection_method: str  # statistical_zscore, isolation_forest, novelty_check, velocity_monitor
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SecurityAttackFinding(BaseModel):
    """Structured adversarial attack / prompt injection classification."""
    detected_attack_type: str  # PROMPT_INJECTION, INSTRUCTION_OVERRIDE, POLICY_BYPASS_ATTEMPT, RECIPIENT_MANIPULATION, TOOL_MISUSE, CONTEXT_MANIPULATION, DATA_EXFILTRATION_ATTEMPT, SUSPICIOUS_INSTRUCTION
    severity: str = "HIGH"  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    suspicious_text_reference: str
    attack_explanation: str
    affected_component: str
    recommended_mitigation: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AgentConsensusReport(BaseModel):
    """Multi-agent consensus, disagreement metrics, and cross-evaluation consistency."""
    consensus_score: float = Field(default=1.0, ge=0.0, le=1.0, description="0.0 (total disagreement) to 1.0 (unanimous agreement)")
    disagreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_recommendations: Dict[str, str] = Field(default_factory=dict)  # {"IntentAnalysisAgent": "ALLOW", ...}
    agent_risk_scores: Dict[str, int] = Field(default_factory=dict)
    agent_confidences: Dict[str, float] = Field(default_factory=dict)
    conflicting_findings: List[Dict[str, Any]] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    consolidated_risk_summary: str = ""
    recommended_review_level: str = "AUTOMATED_CLEARANCE"  # AUTOMATED_CLEARANCE, ELEVATED_SCRUTINY, MANUAL_OPERATOR_REQUIRED, IMMEDIATE_BLOCK
    has_high_severity_conflict: bool = False


class ExplainableRiskAssessment(BaseModel):
    """Human-understandable risk explanation separating facts, models, and policy authority."""
    risk_category: str = "LOW"  # LOW, MODERATE, HIGH, CRITICAL
    risk_score: int = 0
    observed_facts: List[str] = Field(default_factory=list)
    model_interpretations: List[str] = Field(default_factory=list)
    statistical_anomalies: List[str] = Field(default_factory=list)
    security_warnings: List[str] = Field(default_factory=list)
    uncertainty_factors: List[str] = Field(default_factory=list)
    recommended_review: str = ""
    ai_vs_policy_distinction: str = "AI assessment is advisory telemetry; deterministic policy engine retains sole execution authority."
    plain_language_summary: str = ""


class ConfidenceAssessment(BaseModel):
    """Confidence calibration and uncertainty categorization."""
    confidence_category: str = "HIGH_CONFIDENCE"  # HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, LOW_CONFIDENCE, INSUFFICIENT_EVIDENCE
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    completeness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    fallback_used: bool = False
    uncertainty_reasons: List[str] = Field(default_factory=list)


class BehaviouralRiskResult(BaseModel):
    """Outputs from the Behavioural Risk Agent."""
    anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_anomaly: bool = False
    sender_tx_count_historical: int = 0
    sender_rolling_24h_volume: float = 0.0
    frequency_per_minute: int = 0
    is_velocity_spike: bool = False
    is_amount_spike: bool = False
    behavioural_flags: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    # Phase 6 Enhancements
    anomalies: List[AnomalyFinding] = Field(default_factory=list)
    profile_status: str = "INSUFFICIENT_HISTORY"  # "ACTIVE" | "INSUFFICIENT_HISTORY"
    agent_profile: Optional[AgentBehavioralProfile] = None
    statistical_zscore: Optional[float] = None
    is_novel_recipient: bool = False


class SecurityIntelligenceResult(BaseModel):
    """Outputs from the Security Intelligence Agent."""
    is_blocked_recipient: bool = False
    is_trusted_recipient: bool = False
    is_duplicate_tx: bool = False
    prompt_injection_flagged: bool = False
    security_flags: List[str] = Field(default_factory=list)
    threat_severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    findings_count: int = 0
    # Phase 6 Enhancements
    attack_findings: List[SecurityAttackFinding] = Field(default_factory=list)


class TransactionAuditReport(BaseModel):
    """Synthesized security audit report produced by the Transaction Audit Agent."""
    summary: str
    overall_threat_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    intent_analysis_summary: str
    behavioural_risk_summary: str
    security_intelligence_summary: str
    key_violations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    audit_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    advisory_only: bool = True  # Strict Invariant: Audit agent does not independently authorize
    # Phase 6 Enhancements
    composite_risk_score: int = 0
    recommended_action: str = "ALLOW"
    consensus: Optional[AgentConsensusReport] = None
    explainable_assessment: Optional[ExplainableRiskAssessment] = None
    confidence_assessment: Optional[ConfidenceAssessment] = None


class MultiAgentWorkflowState(BaseModel):
    """Shared state traversed by LangGraph nodes during transaction evaluation."""
    transaction: TransactionRequest
    validation: Optional[Dict[str, Any]] = None
    intent_result: Optional[IntentAuditResult] = None
    behavioural_result: Optional[BehaviouralRiskResult] = None
    security_result: Optional[SecurityIntelligenceResult] = None
    audit_report: Optional[TransactionAuditReport] = None
    policy_checks: Optional[Dict[str, str]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    decision: Optional[DecisionType] = None
    requires_approval: bool = False
    execution_allowed: bool = False
    reasons: List[str] = Field(default_factory=list)
    evidence: Optional[AuthorizationEvidence] = None
    agent_logs: List[AgentExecutionLog] = Field(default_factory=list)
    events_emitted: List[Dict[str, Any]] = Field(default_factory=list)
    # Phase 6 Enhancements
    consensus_report: Optional[AgentConsensusReport] = None
    explainable_assessment: Optional[ExplainableRiskAssessment] = None
    confidence_assessment: Optional[ConfidenceAssessment] = None
    agent_profile: Optional[AgentBehavioralProfile] = None

