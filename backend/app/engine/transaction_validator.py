import math
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
from app.schemas.transaction import TransactionRequest


def clean_account_id(raw: Optional[str]) -> str:
    """
    Normalizes account identifier to lowercase NFKC and strips
    hidden zero-width spaces, bidi overrides, and control characters.
    """
    if not raw:
        return ""
    norm = unicodedata.normalize("NFKC", str(raw))
    stripped = "".join(ch for ch in norm if unicodedata.category(ch)[0] != "C")
    return stripped.strip().lower()


class ValidationResult:
    """Encapsulates outcome of syntactic and structural transaction validation."""

    def __init__(self, is_valid: bool, errors: List[str], normalized: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.errors = errors
        self.normalized = normalized or {}


class TransactionValidator:
    """
    Syntactic and structural validator for incoming agent transactions.
    Ensures data integrity before policy evaluation.
    """

    # NEAR Account naming regex: standard accounts (e.g. name.near) or implicit (64 hex characters)
    # Allows lowercase alphanumeric characters, separators (.-_), length 2 to 64 chars.
    NEAR_ACCOUNT_REGEX = re.compile(r"^(([a-z\d]+[\-_])*[a-z\d]+\.)*([a-z\d]+[\-_])*[a-z\d]+$|^[a-f0-9]{64}$")

    @classmethod
    def validate(cls, tx: TransactionRequest) -> ValidationResult:
        errors: List[str] = []

        # 1. Amount checks
        if tx.amount is None:
            errors.append("Transaction amount is missing.")
        elif math.isnan(tx.amount) or math.isinf(tx.amount):
            errors.append("Transaction amount must be a finite numerical value.")
        elif tx.amount <= 0:
            errors.append("Transaction amount must be strictly greater than 0.")
        elif tx.amount < 0.000001:
            errors.append("Transaction amount is below minimum precision threshold (0.000001 NEAR).")
        elif tx.amount > 1_000_000_000:
            errors.append("Transaction amount exceeds maximum allowable supply threshold (1,000,000,000 NEAR).")

        # 2. Currency check
        if not tx.currency or tx.currency.upper() != "NEAR":
            errors.append(f"Unsupported currency '{tx.currency}'. Phase 1 only supports 'NEAR'.")

        # 3. Sender checks
        sender = clean_account_id(tx.sender)
        if not sender:
            errors.append("Sender account identifier is required.")
        elif len(sender) < 2 or len(sender) > 64:
            errors.append(f"Sender account '{sender}' must be between 2 and 64 characters.")
        elif not cls.NEAR_ACCOUNT_REGEX.match(sender):
            errors.append(f"Sender account '{sender}' contains invalid characters for NEAR protocol.")

        # 4. Recipient checks
        recipient = clean_account_id(tx.recipient)
        if not recipient:
            errors.append("Recipient account identifier is required.")
        elif len(recipient) < 2 or len(recipient) > 64:
            errors.append(f"Recipient account '{recipient}' must be between 2 and 64 characters.")
        elif not cls.NEAR_ACCOUNT_REGEX.match(recipient):
            errors.append(f"Recipient account '{recipient}' contains invalid characters for NEAR protocol.")

        # 5. Circular / Self-transfer check
        if sender and recipient and sender == recipient:
            errors.append("Self-transfers are invalid: sender and recipient cannot be identical.")

        # Normalized clean payload
        normalized = {
            "sender": sender,
            "recipient": recipient,
            "amount": round(float(tx.amount), 6) if (tx.amount and not math.isnan(tx.amount)) else 0.0,
            "currency": "NEAR",
            "agent_id": tx.agent_id or "autonomous-agent-01",
            "purpose": (tx.purpose or "").strip() or "Autonomous transaction",
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            normalized=normalized,
        )

