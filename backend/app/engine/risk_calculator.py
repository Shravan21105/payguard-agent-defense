from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import RiskLevel


@dataclass
class RiskFactor:
    name: str
    weight: int
    description: str


@dataclass
class RiskAssessment:
    score: int
    level: RiskLevel
    factors: List[RiskFactor] = field(default_factory=list)
    breakdown: Dict[str, int] = field(default_factory=dict)


class RiskCalculator:
    """
    Configurable, explainable risk assessment engine.
    Calculates deterministic risk scores from 0 (minimal risk) to 100 (critical risk).
    Note: Risk scores represent rule-based heuristic threat indicators,
    not empirically validated probabilistic fraud models.
    """

    @classmethod
    def calculate(
        cls,
        amount: float,
        recipient: str,
        sender: str,
        policy: PolicyConfig,
        rolling_daily_volume: float = 0.0,
        tx_count_last_minute: int = 0,
        is_duplicate: bool = False,
        is_blocked: bool = False,
        is_trusted: bool = False,
        has_purpose: bool = True,
    ) -> RiskAssessment:
        score = 0
        factors: List[RiskFactor] = []
        breakdown: Dict[str, int] = {}

        # 1. Counterparty threat level
        if is_blocked:
            score += 100
            factor = RiskFactor(
                name="blocked_counterparty",
                weight=100,
                description=f"Recipient '{recipient}' is on the security blocklist.",
            )
            factors.append(factor)
            breakdown["blocked_counterparty"] = 100
        elif is_trusted:
            factor = RiskFactor(
                name="trusted_counterparty",
                weight=0,
                description=f"Recipient '{recipient}' is on the verified trusted list.",
            )
            factors.append(factor)
            breakdown["trusted_counterparty"] = 0
        else:
            # Unknown recipient
            unknown_pts = 35
            score += unknown_pts
            factor = RiskFactor(
                name="unknown_counterparty",
                weight=unknown_pts,
                description=f"Recipient '{recipient}' is unknown/unverified.",
            )
            factors.append(factor)
            breakdown["unknown_counterparty"] = unknown_pts

        # 2. Duplicate detection
        if is_duplicate:
            dup_pts = 85
            score += dup_pts
            factor = RiskFactor(
                name="duplicate_transaction",
                weight=dup_pts,
                description="Identical transaction detected within deduplication window.",
            )
            factors.append(factor)
            breakdown["duplicate_transaction"] = dup_pts

        # 3. Per-transaction amount ratio against policy limit
        if policy.max_tx_amount > 0:
            ratio = amount / policy.max_tx_amount
            amount_pts = 0
            if ratio > 1.0:
                amount_pts = 50
                desc = f"Amount ({amount} NEAR) exceeds max transaction limit ({policy.max_tx_amount} NEAR)."
            elif ratio >= 0.8:
                amount_pts = 30
                desc = f"Amount ({amount} NEAR) is within 80-100% of max limit."
            elif ratio >= 0.5:
                amount_pts = 15
                desc = f"Amount ({amount} NEAR) is 50-80% of max limit."
            elif ratio >= 0.2:
                amount_pts = 5
                desc = f"Amount ({amount} NEAR) is 20-50% of max limit."
            else:
                desc = f"Amount ({amount} NEAR) is well within limits (< 20%)."

            if amount_pts > 0:
                score += amount_pts
                factors.append(RiskFactor(name="amount_ratio", weight=amount_pts, description=desc))
                breakdown["amount_ratio"] = amount_pts

        # 4. Daily cumulative spending impact
        if policy.daily_spending_limit > 0:
            projected_daily = rolling_daily_volume + amount
            daily_ratio = projected_daily / policy.daily_spending_limit
            daily_pts = 0
            if daily_ratio > 1.0:
                daily_pts = 40
                desc = f"Projected daily spend ({projected_daily:.2f} NEAR) exceeds daily limit ({policy.daily_spending_limit} NEAR)."
            elif daily_ratio >= 0.8:
                daily_pts = 20
                desc = f"Projected daily spend ({projected_daily:.2f} NEAR) is near daily ceiling (>=80%)."
            elif daily_ratio >= 0.5:
                daily_pts = 10
                desc = f"Projected daily spend ({projected_daily:.2f} NEAR) is moderate (>=50%)."
            else:
                desc = "Projected daily spend is low (< 50%)."

            if daily_pts > 0:
                score += daily_pts
                factors.append(RiskFactor(name="daily_limit_impact", weight=daily_pts, description=desc))
                breakdown["daily_limit_impact"] = daily_pts

        # 5. Frequency / Velocity Check
        if policy.enable_frequency_check and policy.max_tx_frequency_per_minute > 0:
            if tx_count_last_minute >= policy.max_tx_frequency_per_minute:
                freq_pts = 45
                score += freq_pts
                factors.append(
                    RiskFactor(
                        name="excessive_frequency",
                        weight=freq_pts,
                        description=f"Transaction velocity ({tx_count_last_minute}/min) exceeds safety limit ({policy.max_tx_frequency_per_minute}/min).",
                    )
                )
                breakdown["excessive_frequency"] = freq_pts
            elif tx_count_last_minute >= (policy.max_tx_frequency_per_minute * 0.7):
                freq_pts = 15
                score += freq_pts
                factors.append(
                    RiskFactor(
                        name="elevated_frequency",
                        weight=freq_pts,
                        description=f"Elevated transaction velocity ({tx_count_last_minute}/min).",
                    )
                )
                breakdown["elevated_frequency"] = freq_pts

        # 6. Missing purpose or explanation
        if not has_purpose:
            purpose_pts = 10
            score += purpose_pts
            factors.append(
                RiskFactor(
                    name="missing_purpose",
                    weight=purpose_pts,
                    description="Autonomous agent provided no intent or task purpose.",
                )
            )
            breakdown["missing_purpose"] = purpose_pts

        # Clamp score between 0 and 100
        final_score = max(0, min(100, score))

        # Classify level according to policy thresholds
        if final_score >= policy.high_risk_threshold:
            level = RiskLevel.HIGH
        elif final_score >= policy.medium_risk_threshold:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskAssessment(
            score=final_score,
            level=level,
            factors=factors,
            breakdown=breakdown,
        )

