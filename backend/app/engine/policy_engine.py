from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.engine.transaction_validator import ValidationResult
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import CheckStatus, TransactionRequest


@dataclass
class PolicyEvaluationResult:
    """Detailed outcomes of each discrete policy check."""
    checks: Dict[str, str]
    reasons: List[str]
    is_blocked: bool
    requires_approval: bool
    is_trusted: bool
    is_duplicate: bool
    rolling_daily_volume: float
    tx_count_last_minute: int


class PolicyEngine:
    """
    Deterministic security policy evaluation engine.
    Executes rules against incoming transactions and agent state.
    """

    def __init__(self, policy: Optional[PolicyConfig] = None):
        self.policy = policy or PolicyConfig()

    def update_policy(self, new_policy: PolicyConfig) -> None:
        self.policy = new_policy

    def evaluate(
        self,
        tx: TransactionRequest,
        validation: ValidationResult,
        recent_history: Optional[List[Dict]] = None,
    ) -> PolicyEvaluationResult:
        """
        Executes all deterministic policy checks.
        All checks are purely deterministic given the transaction and historical state.
        """
        recent_history = recent_history or []
        checks: Dict[str, str] = {}
        reasons: List[str] = []
        is_blocked = False
        requires_approval = False

        now = tx.timestamp or datetime.utcnow()

        # -------------------------------------------------------------
        # A & H. Data Integrity Check
        # -------------------------------------------------------------
        if not validation.is_valid:
            checks["data_integrity"] = CheckStatus.FAILED.value
            is_blocked = True
            for err in validation.errors:
                reasons.append(f"Validation failure: {err}")
        else:
            checks["data_integrity"] = CheckStatus.PASSED.value

        norm = validation.normalized
        sender = norm.get("sender", tx.sender).lower()
        recipient = norm.get("recipient", tx.recipient).lower()
        amount = norm.get("amount", tx.amount or 0.0)

        # -------------------------------------------------------------
        # D & E. Recipient Verification
        # -------------------------------------------------------------
        trusted_set = {r.lower().strip() for r in self.policy.trusted_recipients}
        blocked_set = {r.lower().strip() for r in self.policy.blocked_recipients}

        is_trusted = recipient in trusted_set
        is_recipient_blocked = recipient in blocked_set

        if is_recipient_blocked:
            checks["recipient_status"] = CheckStatus.BLOCKED.value
            is_blocked = True
            reasons.append(f"Recipient '{recipient}' is on the critical blocklist.")
        elif is_trusted:
            checks["recipient_status"] = CheckStatus.PASSED.value
        else:
            # Unknown recipient
            checks["recipient_status"] = CheckStatus.WARNING.value
            reasons.append(f"Recipient '{recipient}' is an unverified counterparty.")
            if self.policy.require_approval_for_unknown:
                requires_approval = True

        # -------------------------------------------------------------
        # F. Duplicate Transaction Detection
        # -------------------------------------------------------------
        is_duplicate = False
        if self.policy.enable_duplicate_detection and validation.is_valid:
            window_cutoff = now - timedelta(seconds=self.policy.duplicate_window_seconds)
            for prev in recent_history:
                # Do not check against the current transaction itself
                if prev.get("transaction_id") and tx.transaction_id and prev.get("transaction_id") == tx.transaction_id:
                    continue

                prev_time = prev.get("timestamp")
                if isinstance(prev_time, str):
                    try:
                        prev_time = datetime.fromisoformat(prev_time.replace("Z", "+00:00"))
                    except Exception:
                        continue
                if prev_time and prev_time >= window_cutoff:
                    if (
                        prev.get("sender", "").lower() == sender
                        and prev.get("recipient", "").lower() == recipient
                        and abs(float(prev.get("amount", 0.0)) - amount) < 0.000001
                    ):
                        is_duplicate = True
                        break

            if is_duplicate:
                checks["duplicate_check"] = CheckStatus.FAILED.value
                is_blocked = True
                reasons.append(
                    f"Duplicate transaction detected within {self.policy.duplicate_window_seconds}s deduplication window."
                )
            else:
                checks["duplicate_check"] = CheckStatus.PASSED.value
        else:
            checks["duplicate_check"] = CheckStatus.SKIPPED.value if not validation.is_valid else CheckStatus.PASSED.value

        # -------------------------------------------------------------
        # G. Frequency Check (Rate-limiting per sender)
        # -------------------------------------------------------------
        minute_cutoff = now - timedelta(seconds=60)
        recent_txs_last_min = [
            t for t in recent_history
            if t.get("sender", "").lower() == sender
            and not (t.get("transaction_id") and tx.transaction_id and t.get("transaction_id") == tx.transaction_id)
            and (
                t.get("timestamp") >= minute_cutoff
                if isinstance(t.get("timestamp"), datetime)
                else True
            )
        ]
        tx_count_last_minute = len(recent_txs_last_min)

        if self.policy.enable_frequency_check and validation.is_valid:
            if tx_count_last_minute >= self.policy.max_tx_frequency_per_minute:
                checks["frequency_check"] = CheckStatus.FAILED.value
                is_blocked = True
                reasons.append(
                    f"Transaction velocity ({tx_count_last_minute} tx/min) exceeds limit ({self.policy.max_tx_frequency_per_minute} tx/min)."
                )
            else:
                checks["frequency_check"] = CheckStatus.PASSED.value
        else:
            checks["frequency_check"] = CheckStatus.PASSED.value

        # -------------------------------------------------------------
        # B. Per-Transaction Amount Limit
        # -------------------------------------------------------------
        if amount > self.policy.max_tx_amount:
            checks["amount_limit"] = CheckStatus.FAILED.value
            is_blocked = True
            reasons.append(
                f"Transaction amount ({amount:.2f} NEAR) exceeds maximum per-transaction limit ({self.policy.max_tx_amount:.2f} NEAR)."
            )
        elif amount >= (self.policy.max_tx_amount * 0.8):
            checks["amount_limit"] = CheckStatus.WARNING.value
            reasons.append(
                f"Transaction amount ({amount:.2f} NEAR) is near maximum per-transaction limit ({self.policy.max_tx_amount:.2f} NEAR)."
            )
            requires_approval = True
        else:
            checks["amount_limit"] = CheckStatus.PASSED.value

        # -------------------------------------------------------------
        # C. Daily Spending Limit (Rolling 24h)
        # -------------------------------------------------------------
        day_cutoff = now - timedelta(days=1)
        rolling_daily_volume = 0.0
        for t in recent_history:
            if t.get("transaction_id") and tx.transaction_id and t.get("transaction_id") == tx.transaction_id:
                continue
            if t.get("sender", "").lower() != sender:
                continue

            t_time = t.get("timestamp")
            if isinstance(t_time, str):
                try:
                    t_time = datetime.fromisoformat(t_time.replace("Z", "+00:00"))
                except Exception:
                    t_time = None
            if t_time and t_time < day_cutoff:
                continue

            t_dec = (t.get("decision") or "").upper()
            t_stat = (t.get("status") or "").upper()

            # Exclude blocked, failed, and rejected transactions
            if t_dec == "BLOCK" or t_stat in ("BLOCKED", "FAILED", "REJECTED"):
                continue

            if (
                t_dec in ("ALLOW", "PENDING_EXECUTION", "APPROVED", "WARN", "PENDING")
                or t_stat in ("RECEIVED", "ANALYZING", "EXECUTING", "CONFIRMED", "WARN_PENDING_APPROVAL", "ESCROW_CREATED")
            ):
                rolling_daily_volume += float(t.get("amount", 0.0))

        projected_daily = rolling_daily_volume + amount
        if projected_daily > self.policy.daily_spending_limit:
            checks["daily_limit"] = CheckStatus.FAILED.value
            is_blocked = True
            reasons.append(
                f"Projected 24h spending ({projected_daily:.2f} NEAR) exceeds daily allowance ({self.policy.daily_spending_limit:.2f} NEAR)."
            )
        elif projected_daily >= (self.policy.daily_spending_limit * 0.8):
            checks["daily_limit"] = CheckStatus.WARNING.value
            reasons.append(
                f"Projected 24h spending ({projected_daily:.2f} NEAR) utilizes >=80% of daily limit ({self.policy.daily_spending_limit:.2f} NEAR)."
            )
            requires_approval = True
        else:
            checks["daily_limit"] = CheckStatus.PASSED.value

        return PolicyEvaluationResult(
            checks=checks,
            reasons=reasons,
            is_blocked=is_blocked,
            requires_approval=requires_approval,
            is_trusted=is_trusted,
            is_duplicate=is_duplicate,
            rolling_daily_volume=rolling_daily_volume,
            tx_count_last_minute=tx_count_last_minute,
        )

