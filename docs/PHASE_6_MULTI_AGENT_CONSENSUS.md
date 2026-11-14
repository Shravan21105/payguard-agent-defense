# PAYGUARD Phase 6: Multi-Agent Consensus & Disagreement Quantification

**Project:** PAYGUARD — Autonomous Agent Defense Layer  
**Subsystem:** Transaction Audit Agent & Orchestrator Synthesis  

---

## 1. Multi-Agent Ensemble Synthesis

When evaluating complex Web3 financial actions, specialized agents may arrive at conflicting observations:
- The **Intent Analysis Agent** may find that declared intent matches parameters perfectly (`ALLOW`).
- The **Behavioural Risk Agent** may note normal amount limits (`ALLOW`).
- The **Security Intelligence Agent** may discover that the counterparty address is on a critical exploit blocklist (`BLOCK`).

### The Anti-Averaging Invariant
In traditional ensembles, taking the arithmetic mean of risk scores ($[10, 10, 95] \to 38.3$) would dilute a critical security finding into an innocuous "low/medium" score, permitting unauthorized capital drain.

**PAYGUARD strictly forbids simple averaging:**
- If **any** specialized agent flags `BLOCK` or `CRITICAL` severity, the composite risk score is bounded to:
  $$\text{composite\_risk\_score} = \max(\text{agent\_scores}) \ge 95$$
- The consensus status is flagged with `has_high_severity_conflict = True`.
- The recommended review level is locked to `IMMEDIATE_BLOCK`.

---

## 2. Agreement & Disagreement Quantification

The Transaction Audit Agent computes granular agreement metrics across the three evaluating agents (Intent, Behavioral, Security):

### 2.1 Consensus Score ($C$)
Let $R = [r_1, r_2, r_3]$ be the set of recommendations (`ALLOW`, `WARN`, `BLOCK`).
Let $M = \max_{r \in \{\text{ALLOW}, \text{WARN}, \text{BLOCK}\}} \text{count}(r)$.
$$C = \frac{M}{3}$$
- If all 3 agents agree: $C = 1.0$ (Unanimous Consensus).
- If 2 agents agree and 1 disagrees: $C = 0.67$ (Majority Consensus).
- If all 3 differ (ALLOW, WARN, BLOCK): $C = 0.33$ (High Disagreement).

### 2.2 Disagreement Score ($D$)
$$D = 1.0 - C$$

---

## 3. Recommended Review Levels

| Review Level | Condition | Operational Consequence |
| :--- | :--- | :--- |
| **`AUTOMATED_CLEARANCE`** | $C \ge 0.67$, all recommendations $\in \{\text{ALLOW}\}$, deterministic checks pass. | Vault releases transaction directly on-chain without human escrow. |
| **`ELEVATED_SCRUTINY`** | Discrepancy detected or novel recipient flagged ($R \in \{\text{WARN}\}$). | Routed to timelocked on-chain escrow with automated warnings. |
| **`MANUAL_OPERATOR_REQUIRED`** | Semantic conflict between agents, or agent in `INSUFFICIENT_HISTORY`. | Requires human multisig operator approval before vault release. |
| **`IMMEDIATE_BLOCK`** | Any agent flags `BLOCK`, blocked counterparty, or prompt injection. | Vault hard-rejects transfer; no override possible. |

