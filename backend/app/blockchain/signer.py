import os
import re
from typing import Tuple, Union
import base58
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from app.core.config import settings
from app.core.logging import logger

YOCTO_FACTOR = 10**24


def near_to_yocto(amount_near: float) -> int:
    """Converts a floating-point NEAR amount to yoctoNEAR integer string (1 NEAR = 10^24 yoctoNEAR)."""
    # Use string manipulation to avoid floating-point rounding precision issues
    parts = f"{amount_near:.6f}".split(".")
    whole = int(parts[0])
    frac = parts[1] if len(parts) > 1 else ""
    frac_padded = (frac + "0" * 24)[:24]
    return whole * YOCTO_FACTOR + int(frac_padded)


def yocto_to_near(amount_yocto: Union[int, str]) -> float:
    """Converts yoctoNEAR integer to float NEAR representation."""
    val = int(amount_yocto)
    return round(val / YOCTO_FACTOR, 6)


class PolicySigner:
    """
    Ed25519 Cryptographic Signer for PAYGUARD on-chain authorization tokens.
    Produces RFC-8032 / NEP-413 compliant Ed25519 signatures verified directly
    by the PAYGUARD Rust vault contract via near_sdk::env::ed25519_verify.
    """

    def __init__(
        self,
        private_key_hex_or_base58: str = None,
        environment: str = None,
        expected_public_key: str = None,
    ):
        self._env = (environment or getattr(settings, "ENVIRONMENT", "development")).lower()
        self.is_ephemeral: bool = False
        self.key_source: str = "CONFIGURED"

        self._private_key = self._load_or_validate_key(
            key_str=private_key_hex_or_base58,
            env=self._env,
        )
        self._public_key = self._private_key.public_key()

        raw_pk_bytes = self._public_key.public_bytes_raw()
        self.public_key_hex = raw_pk_bytes.hex()
        self.public_key_base58 = f"ed25519:{base58.b58encode(raw_pk_bytes).decode('ascii')}"

        # Validate against expected public key if configured
        target_pub = expected_public_key or getattr(settings, "POLICY_SIGNER_PUBLIC_KEY", None)
        if target_pub and target_pub.strip():
            self._verify_public_key_match(target_pub.strip())

        if self.is_ephemeral:
            logger.warning(
                f"[PolicySigner] DEVELOPMENT MODE: Running with ephemeral seed key ({self.public_key_base58}). "
                "DO NOT use in production."
            )
        else:
            logger.info(f"[PolicySigner] Initialized with persistent authority public key: {self.public_key_base58}")

    def _load_or_validate_key(self, key_str: str = None, env: str = "development") -> ed25519.Ed25519PrivateKey:
        target = key_str or getattr(settings, "POLICY_SIGNER_PRIVATE_KEY", None)
        is_production = env in ("production", "prod")

        if target and target.strip():
            clean = target.strip()
            if clean.startswith("ed25519:"):
                clean = clean.split(":", 1)[1]
            try:
                # 1. Try 64-char hex format (32 bytes raw seed)
                if len(clean) == 64 and re.fullmatch(r"^[0-9a-fA-F]{64}$", clean):
                    raw = bytes.fromhex(clean)
                    self.is_ephemeral = False
                    self.key_source = "CONFIGURED_HEX"
                    return ed25519.Ed25519PrivateKey.from_private_bytes(raw)

                # 2. Try Base58 format
                decoded = base58.b58decode(clean)
                if len(decoded) == 32:
                    self.is_ephemeral = False
                    self.key_source = "CONFIGURED_BASE58_32B"
                    return ed25519.Ed25519PrivateKey.from_private_bytes(decoded)
                elif len(decoded) == 64:
                    # Keypair containing 32-byte seed + 32-byte public key (standard NEAR CLI secret format)
                    self.is_ephemeral = False
                    self.key_source = "CONFIGURED_BASE58_64B"
                    return ed25519.Ed25519PrivateKey.from_private_bytes(decoded[:32])
                else:
                    raise ValueError(f"Invalid Ed25519 decoded byte length: {len(decoded)} (expected 32 or 64)")
            except Exception as e:
                if is_production:
                    raise ValueError(
                        f"FATAL: Production startup failed. POLICY_SIGNER_PRIVATE_KEY format is invalid: {e}"
                    )
                logger.warning(
                    f"[PolicySigner] Failed to decode supplied key in development mode ({e}). Falling back to dev seed."
                )

        # In production mode, ephemeral fallback is strictly forbidden
        if is_production:
            raise ValueError(
                "FATAL: Production startup failed. In production mode (ENVIRONMENT=production), "
                "POLICY_SIGNER_PRIVATE_KEY must be explicitly configured and cannot be empty."
            )

        # Development fallback with explicit tracking
        self.is_ephemeral = True
        self.key_source = "EPHEMERAL_DEVELOPMENT_SEED"
        dev_seed = b"payguard-vault-dev-signer-key-2026-near!"[:32]
        return ed25519.Ed25519PrivateKey.from_private_bytes(dev_seed)

    def _verify_public_key_match(self, expected_public_key_str: str) -> None:
        """Verifies derived public key matches expected public key configuration."""
        clean_expected = expected_public_key_str.strip()
        if clean_expected.startswith("ed25519:"):
            clean_expected_b58 = clean_expected
        else:
            # Check if hex or bare base58
            try:
                if len(clean_expected) == 64 and re.fullmatch(r"^[0-9a-fA-F]{64}$", clean_expected):
                    raw = bytes.fromhex(clean_expected)
                    clean_expected_b58 = f"ed25519:{base58.b58encode(raw).decode('ascii')}"
                else:
                    clean_expected_b58 = f"ed25519:{clean_expected}"
            except Exception:
                clean_expected_b58 = f"ed25519:{clean_expected}"

        if self.public_key_base58 != clean_expected_b58:
            raise ValueError(
                f"Public key mismatch: Configured public key '{clean_expected_b58}' does not match "
                f"derived authority public key '{self.public_key_base58}'."
            )

    def rotate_key(
        self,
        new_private_key_str: str,
        expected_new_public_key: str = None,
    ) -> str:
        """
        Rotates the active Ed25519 signing key in-memory atomically.
        Validates format, derives new public key, verifies match if provided,
        and returns the new public key base58 string.
        """
        if not new_private_key_str or not new_private_key_str.strip():
            raise ValueError("New signing key cannot be empty for rotation.")

        clean = new_private_key_str.strip()
        if clean.startswith("ed25519:"):
            clean = clean.split(":", 1)[1]

        if len(clean) == 64 and re.fullmatch(r"^[0-9a-fA-F]{64}$", clean):
            raw = bytes.fromhex(clean)
            new_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw)
        else:
            decoded = base58.b58decode(clean)
            if len(decoded) == 32:
                new_key = ed25519.Ed25519PrivateKey.from_private_bytes(decoded)
            elif len(decoded) == 64:
                new_key = ed25519.Ed25519PrivateKey.from_private_bytes(decoded[:32])
            else:
                raise ValueError(f"Invalid new key length ({len(decoded)} bytes). Expected 32 or 64 bytes.")

        new_pub = new_key.public_key()
        raw_pk_bytes = new_pub.public_bytes_raw()
        new_hex = raw_pk_bytes.hex()
        new_b58 = f"ed25519:{base58.b58encode(raw_pk_bytes).decode('ascii')}"

        if expected_new_public_key:
            target = expected_new_public_key.strip()
            if not target.startswith("ed25519:"):
                target = f"ed25519:{target}"
            if new_b58 != target:
                raise ValueError(
                    f"Rotated key public key mismatch: derived '{new_b58}' != expected '{target}'"
                )

        # Atomic commit
        self._private_key = new_key
        self._public_key = new_pub
        self.public_key_hex = new_hex
        self.public_key_base58 = new_b58
        self.is_ephemeral = False
        self.key_source = "ROTATED_KEY"

        logger.info(f"[PolicySigner] Successfully rotated authority key to: {self.public_key_base58}")
        return self.public_key_base58

    @staticmethod
    def create_canonical_payload(
        network_id: str,
        contract_id: str,
        auth_id: str,
        sender_id: str,
        recipient_id: str,
        amount_yocto: int,
        decision: str,
        risk_score: int,
        policy_version: str,
        nonce: int,
        issued_at: int,
        expires_at: int,
    ) -> str:
        """
        Constructs deterministic canonical string matching the Rust contract's
        PolicyAuthorization::to_canonical_bytes() exactly:
        PAYGUARD:v1:<network_id>:<contract_id>:<auth_id>:<sender_id>:<recipient_id>:<amount_yocto>:<decision>:<risk_score>:<policy_version>:<nonce>:<issued_at>:<expires_at>
        """
        return (
            f"PAYGUARD:v1:{network_id}:{contract_id}:{auth_id}:{sender_id}:{recipient_id}:"
            f"{amount_yocto}:{decision.upper()}:{risk_score}:{policy_version}:{nonce}:{issued_at}:{expires_at}"
        )

    def sign_authorization(
        self,
        network_id: str,
        contract_id: str,
        auth_id: str,
        sender_id: str,
        recipient_id: str,
        amount_yocto: int,
        decision: str,
        risk_score: int,
        policy_version: str,
        nonce: int,
        issued_at: int,
        expires_at: int,
    ) -> Tuple[str, str]:
        """
        Signs the canonical authorization payload.
        Returns (canonical_payload_string, signature_hex_128).
        """
        canonical_str = self.create_canonical_payload(
            network_id=network_id,
            contract_id=contract_id,
            auth_id=auth_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount_yocto=amount_yocto,
            decision=decision,
            risk_score=risk_score,
            policy_version=policy_version,
            nonce=nonce,
            issued_at=issued_at,
            expires_at=expires_at,
        )

        sig_bytes = self._private_key.sign(canonical_str.encode("utf-8"))
        signature_hex = sig_bytes.hex()
        return canonical_str, signature_hex

    def verify_signature(
        self,
        canonical_str: str,
        signature_hex: str,
        public_key_str: str = None,
    ) -> bool:
        """Verifies an Ed25519 signature against canonical payload string."""
        try:
            sig_bytes = bytes.fromhex(signature_hex)
            if len(sig_bytes) != 64:
                return False

            if public_key_str:
                clean = public_key_str.replace("ed25519:", "").strip()
                try:
                    pk_bytes = base58.b58decode(clean)
                except Exception:
                    pk_bytes = bytes.fromhex(clean)
                verifier = ed25519.Ed25519PublicKey.from_public_bytes(pk_bytes)
            else:
                verifier = self._public_key

            verifier.verify(sig_bytes, canonical_str.encode("utf-8"))
            return True
        except (InvalidSignature, ValueError, Exception):
            return False


# Global singleton instance
policy_signer = PolicySigner()

