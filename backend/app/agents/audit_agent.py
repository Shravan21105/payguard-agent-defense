import time
from typing import List, Tuple

from app.agents.schemas import (
    AgentExecutionLog,
    BehaviouralRiskResult,
    SecurityIntelligenceResult,
    TransactionAuditReport,
)
from app.ai.llm_gateway import IntentAuditResult
from app.core.logging import logger
from app.schemas.transaction import TransactionRequest


import time
from typing import Any, Dict, List, Tuple

from app.agents.schemas import (
    AgentConsensusReport,
    AgentExecutionLog,
    BehaviouralRiskResult,
    ConfidenceAssessment,
    ExplainableRiskAssessment,
    SecurityIntelligenceResult,
    TransactionAuditReport,
)
from app.ai.llm_gateway import IntentAuditResult
from app.core.logging import logger
from app.schemas.transaction import TransactionRequest


class TransactionAuditAgent:
    """
    Specialized Agent D: Transaction Audit Agent
    Aggregates findings from Intent, Behavioural, and Security Intelligence agents.
    Synthesizes multi-agent consensus, cross-agent disagreement analysis,
    confidence calibration, and an explainable AI risk report.

    CRITICAL INVARIANT:
    The audit agent is purely advisory and must NOT independently authorize transactions.
    """

    NAME = "TransactionAuditAgent"

    @classmethod
    def synthesize_report(
        cls,
        tx: TransactionRequest,
        intent_res: IntentAuditResult,
        behaviour_res: BehaviouralRiskResult,
        sec_res: SecurityIntelligenceResult,
    ) -> Tuple[TransactionAuditReport, AgentExecutionLog]:
        start = time.perf_counter()
        logger.info(f"[{cls.NAME}] Synthesizing multi-agent security audit for tx {tx.transaction_id}")

        violations: List[str] = []
        recommendations: List[str] = []
        conflicting_findings: List[Dict[str, Any]] = []
        missing_evidence: List[str] = []

        # ---------------------------------------------------------------------
        # 1. Derive individual agent recommendations & risk scores
        # ---------------------------------------------------------------------
        # Intent Agent recommendation
        if intent_res.prompt_injection_detected or not intent_res.recipient_matches:
            intent_rec = "BLOCK"
            intent_score = 95
        elif not intent_res.amount_matches or not intent_res.intent_matches_transaction:
            intent_rec = "WARN"
            intent_score = 65
        else:
            intent_rec = "ALLOW"
            intent_score = 10

        # Behavioural Agent recommendation
        if behaviour_res.is_anomaly or behaviour_res.is_amount_spike or behaviour_res.is_velocity_spike:
            beh_rec = "WARN"
            beh_score = min(85, max(45, int(behaviour_res.anomaly_score * 100)))
        else:
            beh_rec = "ALLOW"
            beh_score = int(behaviour_res.anomaly_score * 50)

        # Security Intelligence Agent recommendation
        if sec_res.is_blocked_recipient or sec_res.is_duplicate_tx or sec_res.prompt_injection_flagged or sec_res.threat_severity == "CRITICAL":
            sec_rec = "BLOCK"
            sec_score = 100
        elif not sec_res.is_trusted_recipient or sec_res.threat_severity in ("HIGH", "MEDIUM"):
            sec_rec = "WARN"
            sec_score = 50
        else:
            sec_rec = "ALLOW"
            sec_score = 5

        agent_recs = {
            "IntentAnalysisAgent": intent_rec,
            "BehaviouralRiskAgent": beh_rec,
            "SecurityIntelligenceAgent": sec_rec,
        }
        agent_scores = {
            "IntentAnalysisAgent": intent_score,
            "BehaviouralRiskAgent": beh_score,
            "SecurityIntelligenceAgent": sec_score,
        }
        agent_confs = {
            "IntentAnalysisAgent": round(intent_res.confidence, 2),
            "BehaviouralRiskAgent": round(behaviour_res.confidence, 2),
            "SecurityIntelligenceAgent": 0.99 if sec_rec == "BLOCK" else (0.95 if sec_res.is_trusted_recipient else 0.88),
        }

        # ---------------------------------------------------------------------
        # 2. Consensus & Disagreement Calculation
        # ---------------------------------------------------------------------
        recs_list = [intent_rec, beh_rec, sec_rec]
        most_common_count = max(recs_list.count(r) for r in set(recs_list))
        if most_common_count == 3:
            consensus_score = 1.0
            disagreement_score = 0.0
        elif most_common_count == 2:
            consensus_score = 0.67
            disagreement_score = 0.33
        else:
            consensus_score = 0.0
            disagreement_score = 1.0

        # Detect specific semantic conflicts
        if intent_rec == "ALLOW" and beh_rec in ("WARN", "BLOCK"):
            conflicting_findings.append({
                "agent_a": "IntentAnalysisAgent",
                "finding_a": f"Declared intent matches parameters (score={intent_res.intent_consistency_score:.2f})",
                "agent_b": "BehaviouralRiskAgent",
                "finding_b": f"Behavioral outlier detected (flags={len(behaviour_res.behavioural_flags)})",
            })
        if intent_rec == "ALLOW" and sec_rec == "BLOCK":
            conflicting_findings.append({
                "agent_a": "IntentAnalysisAgent",
                "finding_a": "Natural language intent appeared legitimate",
                "agent_b": "SecurityIntelligenceAgent",
                "finding_b": f"Critical security violation detected ({sec_res.threat_severity})",
            })
        if beh_rec == "ALLOW" and sec_rec == "BLOCK":
            conflicting_findings.append({
                "agent_a": "BehaviouralRiskAgent",
                "finding_a": "Spending metrics within statistical limits",
                "agent_b": "SecurityIntelligenceAgent",
                "finding_b": "Recipient is on malicious blocklist or duplicate transaction detected",
            })

        # Missing evidence check
        if not tx.purpose:
            missing_evidence.append("Declared transaction purpose text was omitted by the agent.")
        if behaviour_res.profile_status == "INSUFFICIENT_HISTORY":
            missing_evidence.append("Insufficient historical transaction baseline for sender account.")

        # High-severity conflict rule: Never average away a CRITICAL or BLOCK finding
        has_high_severity_conflict = any(r == "BLOCK" for r in recs_list) or sec_res.threat_severity == "CRITICAL" or intent_res.prompt_injection_detected
        if has_high_severity_conflict:
            recommended_review = "IMMEDIATE_BLOCK"
            overall_severity = "CRITICAL"
        elif any(r == "WARN" for r in recs_list) or disagreement_score > 0.0:
            recommended_review = "MANUAL_OPERATOR_REQUIRED" if any(r == "WARN" for r in recs_list) else "ELEVATED_SCRUTINY"
            overall_severity = "HIGH" if disagreement_score > 0.5 or sec_res.threat_severity == "HIGH" else "MEDIUM"
        else:
            recommended_review = "AUTOMATED_CLEARANCE"
            overall_severity = "LOW"

        # Deterministic aggregate composite risk score
        if has_high_severity_conflict:
            composite_risk_score = max(agent_scores.values())
        else:
            # Weighted aggregation: 40% Security, 35% Intent, 25% Behavioral + disagreement penalty
            base_score = int(0.40 * sec_score + 0.35 * intent_score + 0.25 * beh_score)
            disagreement_penalty = int(disagreement_score * 15)
            composite_risk_score = min(100, base_score + disagreement_penalty)

        consensus_report = AgentConsensusReport(
            consensus_score=round(consensus_score, 2),
            disagreement_score=round(disagreement_score, 2),
            agent_recommendations=agent_recs,
            agent_risk_scores=agent_scores,
            agent_confidences=agent_confs,
            conflicting_findings=conflicting_findings,
            missing_evidence=missing_evidence,
            consolidated_risk_summary=f"Consensus: {consensus_score*100:.0f}% agreement across agents. Review Level: {recommended_review}.",
            recommended_review_level=recommended_review,
            has_high_severity_conflict=has_high_severity_conflict,
        )

        # ---------------------------------------------------------------------
        # 3. Explainable Risk Assessment Layer
        # ---------------------------------------------------------------------
        observed_facts = [
            f"Sender: {tx.sender}",
            f"Recipient: {tx.recipient}",
            f"Amount: {tx.amount:.2f} {tx.currency}",
            f"Historical transactions recorded: {behaviour_res.sender_tx_count_historical}",
            f"Rolling 24h spending volume: {behaviour_res.sender_rolling_24h_volume:.2f} NEAR",
        ]

        model_interpretations = [
            f"Intent consistency score: {intent_res.intent_consistency_score:.2f} ({intent_res.intent_summary or 'Intent analyzed'})",
            f"Task scope validation: {'VALID' if intent_res.task_scope_valid else 'VIOLATED'}",
        ]
        if intent_res.detected_attack_type:
            model_interpretations.append(f"Adversarial classification: {intent_res.detected_attack_type}")

        statistical_anomalies = [
            f"Isolation Forest anomaly score: {behaviour_res.anomaly_score:.2f} ({'ANOMALOUS' if behaviour_res.is_anomaly else 'NORMATIVE'})",
            f"Transaction velocity: {behaviour_res.frequency_per_minute} tx/min in last 60 seconds",
            f"Recipient novelty: {'NOVEL RECIPIENT' if behaviour_res.is_novel_recipient else 'KNOWN COUNTERPARTY'}",
        ]
        if behaviour_res.statistical_zscore is not None:
            statistical_anomalies.append(f"Amount statistical Z-Score: {behaviour_res.statistical_zscore:.2f}")

        security_warnings = list(sec_res.security_flags)
        if intent_res.prompt_injection_detected:
            security_warnings.append("Hostile prompt injection instruction detected in transaction description.")

        uncertainty_factors = []
        if behaviour_res.profile_status == "INSUFFICIENT_HISTORY":
            uncertainty_factors.append("Sender has fewer than 3 historical transactions; behavioral baseline is not fully calibrated.")
        if intent_res.llm_fallback_used:
            uncertainty_factors.append("Deterministic NLP fallback was utilized for intent evaluation.")
        if disagreement_score > 0.0:
            uncertainty_factors.append(f"Multi-agent disagreement detected (disagreement score: {disagreement_score:.2f}).")

        # Map overall severity to risk category
        risk_category_map = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "MEDIUM": "MODERATE",
            "LOW": "LOW",
        }
        risk_cat = risk_category_map.get(overall_severity, "MODERATE")

        explainable_assessment = ExplainableRiskAssessment(
            risk_category=risk_cat,
            risk_score=composite_risk_score,
            observed_facts=observed_facts,
            model_interpretations=model_interpretations,
            statistical_anomalies=statistical_anomalies,
            security_warnings=security_warnings,
            uncertainty_factors=uncertainty_factors,
            recommended_review=f"Action level: {recommended_review}. Verification of recipient and intent integrity recommended.",
            ai_vs_policy_distinction="AI evaluation constitutes advisory threat intelligence. The deterministic policy engine retains sole execution authority.",
            plain_language_summary=(
                f"Transaction evaluated with {risk_cat} risk (score: {composite_risk_score}/100). "
                f"{len(security_warnings)} security warnings and {len(statistical_anomalies)} behavioral indicators analyzed."
            ),
        )

        # ---------------------------------------------------------------------
        # 4. Confidence Calibration & Uncertainty Management
        # ---------------------------------------------------------------------
        if behaviour_res.profile_status == "INSUFFICIENT_HISTORY" and not tx.purpose:
            conf_cat = "INSUFFICIENT_EVIDENCE"
            conf_score = 0.50
        elif intent_res.llm_fallback_used or disagreement_score >= 0.5:
            conf_cat = "LOW_CONFIDENCE"
            conf_score = 0.65
        elif disagreement_score > 0.0 or behaviour_res.is_novel_recipient:
            conf_cat = "MEDIUM_CONFIDENCE"
            conf_score = 0.80
        else:
            conf_cat = "HIGH_CONFIDENCE"
            conf_score = 0.95

        completeness_score = round(1.0 - (len(missing_evidence) * 0.25), 2)
        confidence_assessment = ConfidenceAssessment(
            confidence_category=conf_cat,
            confidence_score=conf_score,
            completeness_score=completeness_score,
            fallback_used=intent_res.llm_fallback_used,
            uncertainty_reasons=uncertainty_factors or ["No significant uncertainty factors identified."],
        )

        # ---------------------------------------------------------------------
        # 5. Consolidate Violations and Recommendations
        # ---------------------------------------------------------------------
        violations.extend(intent_res.suspicious_indicators)
        violations.extend(behaviour_res.behavioural_flags)
        violations.extend(sec_res.security_flags)
        unique_violations = list(dict.fromkeys(violations))

        if overall_severity == "CRITICAL":
            recommendations.append("Immediate transaction termination recommended. Do not release vault assets.")
            recommendations.append("Flag initiating agent account for security review.")
        elif overall_severity in ("HIGH", "MEDIUM"):
            recommendations.append("Escalate transaction to human operator review queue before execution.")
            recommendations.append("Verify recipient account authenticity and intent validity.")
        else:
            recommendations.append("Transaction verified against multi-agent security checks.")

        summary = (
            f"Transaction evaluated with threat level {overall_severity} ({risk_cat}). "
            f"Multi-agent consensus agreement: {consensus_score*100:.0f}%. "
            f"{len(unique_violations)} security findings identified across intent, behavioral, and counterparty scans."
        )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = AgentExecutionLog(
            agent_name=cls.NAME,
            status="SUCCESS",
            execution_time_ms=duration_ms,
            findings={
                "overall_threat_level": overall_severity,
                "risk_category": risk_cat,
                "composite_risk_score": composite_risk_score,
                "consensus_score": consensus_score,
                "disagreement_score": disagreement_score,
                "conflicts_count": len(conflicting_findings),
                "confidence_category": conf_cat,
                "violations_count": len(unique_violations),
                "summary": summary,
            },
        )

        rec_action = "BLOCK" if overall_severity == "CRITICAL" else ("WARN" if overall_severity in ("HIGH", "MEDIUM") else "ALLOW")

        report = TransactionAuditReport(
            summary=summary,
            overall_threat_level=overall_severity,
            composite_risk_score=composite_risk_score,
            recommended_action=rec_action,
            intent_analysis_summary=intent_res.reasoning,
            behavioural_risk_summary=(
                f"Isolation Forest score: {behaviour_res.anomaly_score:.2f}; "
                f"Velocity: {behaviour_res.frequency_per_minute} tx/min; "
                f"Profile: {behaviour_res.profile_status}."
            ),
            security_intelligence_summary=f"Counterparty: {'BLOCKED' if sec_res.is_blocked_recipient else ('TRUSTED' if sec_res.is_trusted_recipient else 'UNVERIFIED')}.",
            key_violations=unique_violations,
            recommendations=recommendations,
            advisory_only=True,
            consensus=consensus_report,
            explainable_assessment=explainable_assessment,
            confidence_assessment=confidence_assessment,
        )

        return report, log


audit_agent = TransactionAuditAgent()

