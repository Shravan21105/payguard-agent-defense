import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.agents.schemas import (
    AgentExecutionLog,
    SecurityAttackFinding,
    SecurityIntelligenceResult,
)
from app.ai.llm_gateway import llm_gateway
from app.core.logging import logger
from app.schemas.policy import PolicyConfig
from app.schemas.transaction import TransactionRequest


class SecurityIntelligenceAgent:
    """
    Specialized Agent C: Security Intelligence Agent
    Evaluates counterparty reputation, critical blocklists, duplicate replay
    patterns, adversarial prompt injections, and metadata attack payloads.
    Enhanced in Phase 6 with multi-vector adversarial classification.
    """

    NAME = "SecurityIntelligenceAgent"

    @classmethod
    def analyze(
        cls,
        tx: TransactionRequest,
        policy: PolicyConfig,
        recent_history: Optional[List[Dict[str, Any]]] = None,
        prompt_injection_flag: bool = False,
    ) -> Tuple[SecurityIntelligenceResult, AgentExecutionLog]:
        start = time.perf_counter()
        logger.info(f"[{cls.NAME}] Scanning threat intelligence for counterparty '{tx.recipient}'")

        recent_history = recent_history or []
        flags: List[str] = []
        attack_findings: List[SecurityAttackFinding] = []
        severity = "LOW"

        norm_recipient = (tx.recipient or "").strip().lower()
        blocked_set = {r.lower().strip() for r in policy.blocked_recipients}
        trusted_set = {r.lower().strip() for r in policy.trusted_recipients}

        is_blocked = norm_recipient in blocked_set
        is_trusted = norm_recipient in trusted_set

        # 1. Blocklist inspection
        if is_blocked:
            msg = f"CRITICAL: Recipient '{norm_recipient}' is on the active malicious exploit blocklist."
            flags.append(msg)
            severity = "CRITICAL"
            attack_findings.append(SecurityAttackFinding(
                detected_attack_type="POLICY_BYPASS_ATTEMPT",
                severity="CRITICAL",
                confidence=1.0,
                suspicious_text_reference=norm_recipient,
                attack_explanation=msg,
                affected_component="Counterparty Registry & Vault",
                recommended_mitigation="Strict deterministic BLOCK. Withhold Ed25519 authorization token.",
            ))
        elif not is_trusted:
            flags.append(f"Recipient '{norm_recipient}' is not on the verified counterparty registry.")
            if severity == "LOW":
                severity = "MEDIUM"

        # 2. Duplicate / Replay pattern inspection
        is_duplicate = False
        now = tx.timestamp or datetime.utcnow()
        window_cutoff = now - timedelta(seconds=policy.duplicate_window_seconds)

        for prev in recent_history:
            prev_time = prev.get("timestamp")
            if isinstance(prev_time, str):
                try:
                    prev_time = datetime.fromisoformat(prev_time.replace("Z", "+00:00"))
                except Exception:
                    continue
            if prev_time and prev_time >= window_cutoff:
                if (
                    prev.get("sender", "").lower() == tx.sender.lower()
                    and prev.get("recipient", "").lower() == norm_recipient
                    and abs(float(prev.get("amount", 0.0)) - tx.amount) < 0.000001
                ):
                    is_duplicate = True
                    msg = f"Duplicate payment detected within {policy.duplicate_window_seconds}s deduplication window."
                    flags.append(msg)
                    severity = "CRITICAL"
                    attack_findings.append(SecurityAttackFinding(
                        detected_attack_type="SUSPICIOUS_INSTRUCTION",
                        severity="CRITICAL",
                        confidence=0.99,
                        suspicious_text_reference=f"tx_id={prev.get('transaction_id')}",
                        attack_explanation=msg,
                        affected_component="Anti-Replay Mechanism",
                        recommended_mitigation="Enforce atomic deduplication block.",
                    ))
                    break

        # 3. Phase 6 Adversarial Pattern Scanning on purpose and metadata
        try:
            meta_str = json.dumps(tx.metadata or {}, default=str)
        except Exception:
            meta_str = str(tx.metadata or {})
        combined_text = f"{tx.purpose or ''} {meta_str}"
        detected_attacks = llm_gateway.detect_adversarial_patterns(combined_text)
        for atk in detected_attacks:
            atk_type = atk["detected_attack_type"]
            atk_sev = atk["severity"]
            atk_msg = f"Adversarial vector detected [{atk_type}]: {atk['attack_explanation']}"
            flags.append(atk_msg)
            if atk_sev == "CRITICAL":
                severity = "CRITICAL"
            elif severity != "CRITICAL":
                severity = "HIGH"

            attack_findings.append(SecurityAttackFinding(
                detected_attack_type=atk_type,
                severity=atk_sev,
                confidence=atk["confidence"],
                suspicious_text_reference=atk["suspicious_text_reference"],
                attack_explanation=atk["attack_explanation"],
                affected_component=atk["affected_component"],
                recommended_mitigation=atk["recommended_mitigation"],
            ))

        # 4. Metadata keyword inspection fallback
        if tx.metadata:
            meta_str = str(tx.metadata).lower()
            suspicious_keywords = ["drain", "private_key", "dump", "exec", "sudo", "bypass"]
            for kw in suspicious_keywords:
                if kw in meta_str and not any(kw in f for f in flags):
                    flags.append(f"Suspicious metadata instruction keyword detected: '{kw}'")
                    if severity != "CRITICAL":
                        severity = "HIGH"

        if prompt_injection_flag:
            msg = "Prompt injection attack vector confirmed by Intent Analysis Agent."
            if msg not in flags:
                flags.append(msg)
            severity = "CRITICAL"

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = AgentExecutionLog(
            agent_name=cls.NAME,
            status="CRITICAL" if severity == "CRITICAL" else ("WARNING" if severity != "LOW" else "SUCCESS"),
            execution_time_ms=duration_ms,
            findings={
                "is_blocked": is_blocked,
                "is_trusted": is_trusted,
                "is_duplicate": is_duplicate,
                "threat_severity": severity,
                "attack_findings_count": len(attack_findings),
                "flags": flags,
            },
        )

        result = SecurityIntelligenceResult(
            is_blocked_recipient=is_blocked,
            is_trusted_recipient=is_trusted,
            is_duplicate_tx=is_duplicate,
            prompt_injection_flagged=prompt_injection_flag or len(attack_findings) > 0,
            security_flags=flags,
            threat_severity=severity,
            findings_count=len(flags),
            attack_findings=attack_findings,
        )

        return result, log


security_intelligence_agent = SecurityIntelligenceAgent()

