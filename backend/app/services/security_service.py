from datetime import datetime
from typing import List
from app.schemas.security import SecurityAlert, SecurityMetricsResponse
from app.schemas.transaction import DecisionType
from app.services.transaction_service import transaction_service


class SecurityService:
    """Aggregates real-time security analytics and threat telemetry."""

    @classmethod
    def get_metrics(cls) -> SecurityMetricsResponse:
        records = transaction_service.list_transactions(limit=500)

        total_monitored = len(records)
        approved_count = sum(1 for r in records if r.decision == DecisionType.ALLOW)
        warn_count = sum(1 for r in records if r.decision == DecisionType.WARN)
        blocked_count = sum(1 for r in records if r.decision == DecisionType.BLOCK)
        pending_approvals = sum(1 for r in records if r.requires_approval)

        total_near_volume = round(sum(r.amount for r in records), 2)
        protected_near_volume = round(
            sum(r.amount for r in records if r.decision == DecisionType.BLOCK), 2
        )
        avg_risk = (
            round(sum(r.risk_score for r in records) / total_monitored, 1)
            if total_monitored > 0
            else 0.0
        )

        unique_agents = len(set(r.agent_id for r in records if r.agent_id))

        # Build recent alerts from blocked & warned transactions
        alerts: List[SecurityAlert] = []
        for r in records:
            if r.decision == DecisionType.BLOCK:
                alerts.append(
                    SecurityAlert(
                        id=f"alert_{r.transaction_id}",
                        timestamp=r.timestamp,
                        severity="CRITICAL",
                        title=f"Exploit Blocked: {r.recipient}",
                        description="; ".join(r.reasons[:2]),
                        transaction_id=r.transaction_id,
                        recipient=r.recipient,
                        amount=r.amount,
                    )
                )
            elif r.decision == DecisionType.WARN:
                alerts.append(
                    SecurityAlert(
                        id=f"alert_{r.transaction_id}",
                        timestamp=r.timestamp,
                        severity="MEDIUM",
                        title=f"Human Approval Required: {r.recipient}",
                        description="; ".join(r.reasons[:2]),
                        transaction_id=r.transaction_id,
                        recipient=r.recipient,
                        amount=r.amount,
                    )
                )

        return SecurityMetricsResponse(
            total_monitored=total_monitored,
            approved_count=approved_count,
            warn_count=warn_count,
            blocked_count=blocked_count,
            pending_approvals=pending_approvals,
            total_near_volume=total_near_volume,
            protected_near_volume=protected_near_volume,
            average_risk_score=avg_risk,
            active_agents_monitored=max(unique_agents, 1),
            recent_alerts=alerts[:10],
            is_demo_metrics=True,
        )


security_service = SecurityService()
