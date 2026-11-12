from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class TransactionRequest(BaseModel):
    """Incoming transaction request initiated by an autonomous AI agent."""

    transaction_id: Optional[str] = Field(
        default=None,
        description="Unique identifier. Generated automatically if omitted."
    )
    sender: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Sender NEAR account or Agent ID (e.g., agent-executor.near)"
    )
    recipient: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Recipient NEAR account or contract address"
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount in NEAR tokens (must be strictly > 0)"
    )
    currency: str = Field(
        default="NEAR",
        description="Asset token denomination. Phase 1 supports NEAR."
    )
    agent_id: Optional[str] = Field(
        default="autonomous-agent-01",
        description="Identifier of initiating autonomous agent"
    )
    purpose: Optional[str] = Field(
        default="Autonomous task payment",
        description="Human/Agent declared intent for the transaction"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Arbitrary contextual metadata provided by agent framework"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Timestamp of request origination"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() != "NEAR":
            raise ValueError("Only 'NEAR' currency is supported in Phase 1.")
        return v.upper()


class PolicyCheckSummary(BaseModel):
    """Breakdown of individual deterministic security checks."""
    amount_limit: str = CheckStatus.PASSED.value
    daily_limit: str = CheckStatus.PASSED.value
    recipient_status: str = CheckStatus.PASSED.value
    duplicate_check: str = CheckStatus.PASSED.value
    frequency_check: str = CheckStatus.PASSED.value
    data_integrity: str = CheckStatus.PASSED.value


class TransactionAnalysisResponse(BaseModel):
    """Structured security decision response returned by the PAYGUARD engine."""

    transaction_id: str
    sender: str
    recipient: str
    amount: float
    currency: str = "NEAR"
    decision: DecisionType
    risk_score: int = Field(..., ge=0, le=100, description="Computed risk score from 0 (safe) to 100 (critical)")
    risk_level: RiskLevel
    requires_approval: bool
    reasons: List[str] = Field(default_factory=list)
    policy_checks: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime
    execution_allowed: bool
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    is_mock_simulation: bool = Field(
        default=True,
        description="Indicates this evaluation is run in Phase 1 simulation mode, not executed on-chain."
    )


class TransactionRecord(TransactionAnalysisResponse):
    """Stored transaction record with execution state and agent metadata."""
    agent_id: Optional[str] = "autonomous-agent-01"
    purpose: Optional[str] = None
    approval_status: Optional[str] = "NONE"  # NONE, PENDING, APPROVED, REJECTED
