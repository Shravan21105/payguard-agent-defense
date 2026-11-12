from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.engine.policy_engine import PolicyEngine, PolicyEvaluationResult
from app.engine.risk_calculator import RiskCalculator
from app.engine.transaction_validator import TransactionValidator, ValidationResult
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import (
    CheckStatus,
    DecisionType,
    RiskLevel,
    TransactionAnalysisResponse,
    TransactionRequest,
)


class DecisionEngine:
    """
    Core Deterministic Decision Engine for PAYGUARD.
    Coordinates validation, policy checks, and risk scoring to produce
    immutable, explainable financial security decisions.

    CRITICAL INVARIANT:
    AI analyzes. Policy engine enforces. Smart contract protects.
    A hard BLOCK must NEVER be overridden by any AI/probabilistic score.
    """

    def __init__(self, policy: Optional[PolicyConfig] = None):
        self.policy = policy or PolicyConfig()
        self.policy_engine = PolicyEngine(self.policy)

    def update_policy(self, new_policy: PolicyConfig) -> None:
        self.policy = new_policy
        self.policy_engine.update_policy(new_policy)

    def evaluate_transaction(
        self,
        tx: TransactionRequest,
        recent_history: Optional[List[Dict]] = None,
    ) -> TransactionAnalysisResponse:
        """
        Deterministically evaluates a transaction request against active policies.
        Produces ALLOW, WARN, or BLOCK decisions.
        """
        # Ensure transaction has an ID and timestamp
        tx_id = tx.transaction_id or f"tx_{uuid.uuid4().hex[:12]}"
        tx_timestamp = tx.timestamp or datetime.utcnow()

        # Step 1: Syntactic & Structural Data Validation
        validation: ValidationResult = TransactionValidator.validate(tx)

        # Step 2: Policy Rule Checks
        eval_result: PolicyEvaluationResult = self.policy_engine.evaluate(
            tx=tx,
            validation=validation,
            recent_history=recent_history,
        )

        # Step 3: Risk Assessment
        norm = validation.normalized
        amount = norm.get("amount", tx.amount if tx.amount else 0.0)
        recipient = norm.get("recipient", tx.recipient)
        sender = norm.get("sender", tx.sender)

        risk_assessment = RiskCalculator.calculate(
            amount=amount,
            recipient=recipient,
            sender=sender,
            policy=self.policy,
            rolling_daily_volume=eval_result.rolling_daily_volume,
            tx_count_last_minute=eval_result.tx_count_last_minute,
            is_duplicate=eval_result.is_duplicate,
            is_blocked=eval_result.is_blocked and eval_result.checks.get("recipient_status") == CheckStatus.BLOCKED.value,
            is_trusted=eval_result.is_trusted,
            has_purpose=bool(tx.purpose and tx.purpose.strip()),
        )

        # Step 4: Deterministic Decision Synthesis
        # Decision Hierarchy: BLOCK > WARN > ALLOW
        reasons = list(eval_result.reasons)
        requires_approval = False
        execution_allowed = False

        if eval_result.is_blocked or risk_assessment.level == RiskLevel.HIGH:
            decision = DecisionType.BLOCK
            execution_allowed = False
            requires_approval = False
            if risk_assessment.level == RiskLevel.HIGH and "Risk score exceeds high-risk threshold." not in reasons:
                reasons.append(f"Risk score ({risk_assessment.score}) exceeds high-risk threshold ({self.policy.high_risk_threshold}).")
        elif eval_result.requires_approval or risk_assessment.level == RiskLevel.MEDIUM:
            decision = DecisionType.WARN
            execution_allowed = False
            requires_approval = True
            if risk_assessment.level == RiskLevel.MEDIUM and "Risk score in elevated medium-risk band." not in reasons:
                reasons.append(f"Elevated risk score ({risk_assessment.score}) requires human verification.")
        else:
            decision = DecisionType.ALLOW
            execution_allowed = True
            requires_approval = False
            reasons.append("All deterministic security policies and risk thresholds passed.")

        # Structure normalized policy checks map
        policy_checks_map = {
            "data_integrity": eval_result.checks.get("data_integrity", CheckStatus.PASSED.value),
            "recipient_status": eval_result.checks.get("recipient_status", CheckStatus.PASSED.value),
            "amount_limit": eval_result.checks.get("amount_limit", CheckStatus.PASSED.value),
            "daily_limit": eval_result.checks.get("daily_limit", CheckStatus.PASSED.value),
            "duplicate_check": eval_result.checks.get("duplicate_check", CheckStatus.PASSED.value),
            "frequency_check": eval_result.checks.get("frequency_check", CheckStatus.PASSED.value),
        }

        return TransactionAnalysisResponse(
            transaction_id=tx_id,
            sender=sender,
            recipient=recipient,
            amount=amount,
            currency="NEAR",
            decision=decision,
            risk_score=risk_assessment.score,
            risk_level=risk_assessment.level,
            requires_approval=requires_approval,
            reasons=reasons,
            policy_checks=policy_checks_map,
            timestamp=tx_timestamp,
            execution_allowed=execution_allowed,
            confidence_score=0.98 if decision == DecisionType.ALLOW else 0.95,
            is_mock_simulation=True,
        )
