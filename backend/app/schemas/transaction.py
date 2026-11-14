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


class TransactionStatus(str, Enum):
    """End-to-End Transaction Lifecycle Statuses (Phase 4)."""
    RECEIVED = "RECEIVED"
    ANALYZING = "ANALYZING"
    ALLOWED = "ALLOWED"
    WARN_PENDING_APPROVAL = "WARN_PENDING_APPROVAL"
    ESCROW_CREATED = "ESCROW_CREATED"
    EXECUTING = "EXECUTING"
    CONFIRMED = "CONFIRMED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


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
        description="Indicates this evaluation is run in simulation mode, not executed on-chain."
    )
    status: Optional[str] = Field(
        default=None,
        description="Lifecycle status: RECEIVED, ANALYZING, ALLOWED, ESCROW_CREATED, EXECUTING, CONFIRMED, BLOCKED, etc."
    )
    tx_hash: Optional[str] = Field(
        default=None,
        description="NEAR blockchain transaction hash or receipt ID."
    )
    block_height: Optional[int] = Field(
        default=None,
        description="NEAR block height where the transaction or escrow was committed."
    )
    block_hash: Optional[str] = Field(
        default=None,
        description="NEAR block hash where the transaction was finalized."
    )
    explorer_url: Optional[str] = Field(
        default=None,
        description="Direct link to view transaction receipt on NearBlocks or NEAR Explorer."
    )
    escrow_id: Optional[str] = Field(
        default=None,
        description="Vault smart contract escrow ID if funds are escrowed."
    )
    error_details: Optional[str] = Field(
        default=None,
        description="Error details if execution or RPC submission failed."
    )
    execution_mode: Optional[str] = Field(
        default="SIMULATION",
        description="Execution mode: ONCHAIN or SIMULATION."
    )
    consensus: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Consensus and agreement metrics across AI agents."
    )
    explainable_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Human-understandable explanation and risk breakdown."
    )
    confidence_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Calibrated confidence and uncertainty analysis."
    )
    agent_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sender behavioral profile and historical baseline status."
    )


class TransactionRecord(TransactionAnalysisResponse):
    """Stored transaction record with execution state and agent metadata."""
    agent_id: Optional[str] = "autonomous-agent-01"
    purpose: Optional[str] = None
    approval_status: Optional[str] = "NONE"  # NONE, PENDING, APPROVED, REJECTED
    evidence_hash: Optional[str] = None
    intent_matched: Optional[bool] = True
    intent_discrepancy: Optional[str] = None


class InitiateTransactionRequest(BaseModel):
    """
    Unified Phase 4 request initiating autonomous agent transaction through:
    1. Multi-Agent AI Intent Auditing
    2. Deterministic Security Policy Engine
    3. Ed25519 Cryptographic Authorization
    4. NEAR Smart Contract Vault On-Chain Execution / Escrow
    """
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
        description="Transaction amount in NEAR tokens (strictly > 0)"
    )
    currency: str = Field(
        default="NEAR",
        description="Asset token denomination."
    )
    agent_id: Optional[str] = Field(
        default="autonomous-agent-01",
        description="Identifier of initiating autonomous agent"
    )
    purpose: Optional[str] = Field(
        default="Autonomous task payment",
        description="Human or Agent declared intent for the transaction"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Contextual metadata provided by agent framework"
    )
    dry_run: bool = Field(
        default=False,
        description="If True, performs multi-agent and policy simulation without submitting to NEAR blockchain."
    )
    network_id: Optional[str] = Field(
        default=None,
        description="Target NEAR network ('testnet' or 'mainnet'). Defaults to server configuration."
    )
    contract_id: Optional[str] = Field(
        default=None,
        description="Target PAYGUARD Vault smart contract ID. Defaults to server configuration."
    )
    timelock_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400 * 7,
        description="Timelock duration in seconds if transaction enters escrow."
    )

