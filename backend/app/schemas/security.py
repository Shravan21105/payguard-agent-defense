from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SecurityAlert(BaseModel):
    """Real-time security alert item."""
    id: str
    timestamp: datetime
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    transaction_id: Optional[str] = None
    recipient: Optional[str] = None
    amount: Optional[float] = None


class SecurityMetricsResponse(BaseModel):
    """Aggregate security metrics for the dashboard."""
    total_monitored: int = Field(..., description="Total transactions evaluated by PAYGUARD")
    approved_count: int = Field(..., description="Transactions allowed and verified")
    warn_count: int = Field(..., description="Transactions flagged with warnings")
    blocked_count: int = Field(..., description="Malicious/prohibited transactions intercepted")
    pending_approvals: int = Field(..., description="Transactions awaiting human-in-the-loop sign-off")
    total_near_volume: float = Field(..., description="Total cumulative volume analyzed in NEAR")
    protected_near_volume: float = Field(..., description="Total malicious volume prevented from drain in NEAR")
    average_risk_score: float = Field(..., description="Mean risk score across monitored transactions")
    active_agents_monitored: int = Field(default=3)
    recent_alerts: List[SecurityAlert] = Field(default_factory=list)
    is_demo_metrics: bool = Field(
        default=True,
        description="Demo indicator: contains initial baseline demo transactions alongside newly analyzed ones."
    )
