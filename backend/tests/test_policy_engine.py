from datetime import datetime, timedelta
import pytest
from app.engine.decision_engine import DecisionEngine
from app.engine.transaction_validator import TransactionValidator
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import (
    CheckStatus,
    DecisionType,
    RiskLevel,
    TransactionRequest,
)


@pytest.fixture
def default_policy() -> PolicyConfig:
    return PolicyConfig(
        max_tx_amount=50.0,
        daily_spending_limit=200.0,
        max_tx_frequency_per_minute=5,
        duplicate_window_seconds=120,
        trusted_recipients=["oracle.near", "treasury.payguard.near", "vendor.near"],
        blocked_recipients=["malicious-drainer.near", "hacker.near"],
        require_approval_for_unknown=True,
        high_risk_threshold=70,
        medium_risk_threshold=30,
    )


@pytest.fixture
def engine(default_policy: PolicyConfig) -> DecisionEngine:
    return DecisionEngine(default_policy)


# 1. Valid transaction test
def test_valid_transaction_allowed(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-alpha.near",
        recipient="oracle.near",
        amount=5.0,
        currency="NEAR",
        purpose="Regular oracle update",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.ALLOW
    assert result.execution_allowed is True
    assert result.requires_approval is False
    assert result.risk_level == RiskLevel.LOW
    assert result.risk_score < 30
    assert result.policy_checks["amount_limit"] == CheckStatus.PASSED.value
    assert result.policy_checks["recipient_status"] == CheckStatus.PASSED.value
    assert result.policy_checks["data_integrity"] == CheckStatus.PASSED.value


# 2. Trusted recipient test
def test_trusted_recipient_low_risk(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="treasury.payguard.near",
        amount=10.0,
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.ALLOW
    assert result.policy_checks["recipient_status"] == CheckStatus.PASSED.value
    assert result.risk_score < 30


# 3. Unknown recipient test
def test_unknown_recipient_triggers_warn(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="completely-unknown-service.near",
        amount=10.0,
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.WARN
    assert result.requires_approval is True
    assert result.execution_allowed is False
    assert result.policy_checks["recipient_status"] == CheckStatus.WARNING.value
    assert any("unverified counterparty" in r for r in result.reasons)


# 4. Blocked recipient test
def test_blocked_recipient_triggers_hard_block(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="malicious-drainer.near",
        amount=1.0,
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.BLOCK
    assert result.execution_allowed is False
    assert result.requires_approval is False
    assert result.risk_level == RiskLevel.HIGH
    assert result.risk_score >= 70
    assert result.policy_checks["recipient_status"] == CheckStatus.BLOCKED.value
    assert any("critical blocklist" in r for r in result.reasons)


# 5. Spending limit exceeded test
def test_spending_limit_exceeded_triggers_block(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="vendor.near",
        amount=75.0,  # Max limit is 50.0
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.BLOCK
    assert result.execution_allowed is False
    assert result.policy_checks["amount_limit"] == CheckStatus.FAILED.value
    assert any("exceeds maximum per-transaction limit" in r for r in result.reasons)


# 6. Daily limit exceeded test
def test_daily_limit_exceeded_triggers_block(engine: DecisionEngine):
    # Prepare previous history with 180 NEAR already spent today
    now = datetime.utcnow()
    recent_history = [
        {
            "transaction_id": "tx_prev_01",
            "sender": "agent-01.near",
            "recipient": "vendor.near",
            "amount": 180.0,
            "decision": "ALLOW",
            "timestamp": now - timedelta(hours=2),
        }
    ]
    # Attempt 30 NEAR more -> total 210 NEAR, exceeding 200 daily limit
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="vendor.near",
        amount=30.0,
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx, recent_history=recent_history)

    assert result.decision == DecisionType.BLOCK
    assert result.policy_checks["daily_limit"] == CheckStatus.FAILED.value
    assert any("exceeds daily allowance" in r for r in result.reasons)


# 7. Duplicate transaction detection test
def test_duplicate_transaction_triggers_block(engine: DecisionEngine):
    now = datetime.utcnow()
    recent_history = [
        {
            "transaction_id": "tx_first",
            "sender": "agent-01.near",
            "recipient": "vendor.near",
            "amount": 15.0,
            "decision": "ALLOW",
            "timestamp": now - timedelta(seconds=30),  # Within 120s duplicate window
        }
    ]
    # Identical transaction submitted
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="vendor.near",
        amount=15.0,
        currency="NEAR",
        timestamp=now,
    )
    result = engine.evaluate_transaction(tx, recent_history=recent_history)

    assert result.decision == DecisionType.BLOCK
    assert result.policy_checks["duplicate_check"] == CheckStatus.FAILED.value
    assert any("Duplicate transaction detected" in r for r in result.reasons)


# 8. Invalid amount validation test
def test_invalid_amount_rejected():
    with pytest.raises(Exception):
        # Pydantic schema validation enforces gt=0
        TransactionRequest(
            sender="agent-01.near",
            recipient="vendor.near",
            amount=-10.0,
            currency="NEAR",
        )

    # Directly test TransactionValidator with bad data
    fake_tx = TransactionRequest.model_construct(
        sender="agent-01.near",
        recipient="vendor.near",
        amount=0.0,
        currency="NEAR",
    )
    val_res = TransactionValidator.validate(fake_tx)
    assert val_res.is_valid is False
    assert any("strictly greater than 0" in e for e in val_res.errors)


# 9. WARN decision test
def test_warn_decision_requires_human_approval(engine: DecisionEngine):
    # Near the limit: 42 NEAR out of 50 NEAR max (>80%) to trusted recipient
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="vendor.near",
        amount=42.0,
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.WARN
    assert result.requires_approval is True
    assert result.execution_allowed is False
    assert result.policy_checks["amount_limit"] == CheckStatus.WARNING.value


# 10. Hard BLOCK decision test
def test_hard_block_is_never_overridden(engine: DecisionEngine):
    tx = TransactionRequest(
        sender="agent-01.near",
        recipient="hacker.near",
        amount=0.1,  # Small amount, but to blocked address
        currency="NEAR",
    )
    result = engine.evaluate_transaction(tx)

    assert result.decision == DecisionType.BLOCK
    assert result.execution_allowed is False
    assert result.requires_approval is False


# 11. Determinism verification test
def test_determinism_identical_inputs_produce_identical_outputs(engine: DecisionEngine):
    tx = TransactionRequest(
        transaction_id="tx_fixed_determinism",
        sender="agent-test.near",
        recipient="vendor.near",
        amount=12.345,
        currency="NEAR",
        purpose="Determinism test",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )

    result_1 = engine.evaluate_transaction(tx)
    result_2 = engine.evaluate_transaction(tx)

    assert result_1.decision == result_2.decision
    assert result_1.risk_score == result_2.risk_score
    assert result_1.risk_level == result_2.risk_level
    assert result_1.requires_approval == result_2.requires_approval
    assert result_1.policy_checks == result_2.policy_checks
    assert result_1.reasons == result_2.reasons

