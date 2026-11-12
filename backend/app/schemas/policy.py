from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PolicyConfig(BaseModel):
    """Configurable security policy definitions."""

    max_tx_amount: float = Field(
        default=50.0,
        gt=0,
        description="Maximum NEAR allowed in a single transaction before WARN or BLOCK"
    )
    daily_spending_limit: float = Field(
        default=200.0,
        gt=0,
        description="Maximum cumulative NEAR allowed within a 24h rolling window"
    )
    max_tx_frequency_per_minute: int = Field(
        default=10,
        gt=0,
        description="Max transactions from the same sender allowed in a 60-second window"
    )
    duplicate_window_seconds: int = Field(
        default=120,
        ge=0,
        description="Window to flag duplicate (same sender, recipient, amount) transactions"
    )
    trusted_recipients: List[str] = Field(
        default_factory=lambda: [
            "oracle.near",
            "treasury.payguard.near",
            "verified-vendor.near",
            "agent-registry.near",
            "near-staked-pool.near",
        ],
        description="Whitelisted recipients known to be safe"
    )
    blocked_recipients: List[str] = Field(
        default_factory=lambda: [
            "malicious-drainer.near",
            "phishing-scam.near",
            "known-exploiter.near",
            "blacklisted-mixer.near",
        ],
        description="Hard-blocked counterparties"
    )
    require_approval_for_unknown: bool = Field(
        default=True,
        description="Whether transactions to unlisted recipients require manual human approval"
    )
    high_risk_threshold: int = Field(
        default=70,
        ge=1,
        le=100,
        description="Score at which transactions trigger a BLOCK or require strict approval"
    )
    medium_risk_threshold: int = Field(
        default=30,
        ge=1,
        le=99,
        description="Score at which transactions trigger a WARN"
    )
    enable_frequency_check: bool = Field(default=True)
    enable_duplicate_detection: bool = Field(default=True)


class PolicyUpdateRequest(BaseModel):
    """Payload to update security policies."""
    max_tx_amount: Optional[float] = Field(None, gt=0)
    daily_spending_limit: Optional[float] = Field(None, gt=0)
    max_tx_frequency_per_minute: Optional[int] = Field(None, gt=0)
    duplicate_window_seconds: Optional[int] = Field(None, ge=0)
    trusted_recipients: Optional[List[str]] = None
    blocked_recipients: Optional[List[str]] = None
    require_approval_for_unknown: Optional[bool] = None
    high_risk_threshold: Optional[int] = Field(None, ge=1, le=100)
    medium_risk_threshold: Optional[int] = Field(None, ge=1, le=99)
    enable_frequency_check: Optional[bool] = None
    enable_duplicate_detection: Optional[bool] = None


class PolicyResponse(BaseModel):
    """Response containing active policy configuration and metadata."""
    version: str = "1.0.0"
    updated_at: datetime
    config: PolicyConfig
