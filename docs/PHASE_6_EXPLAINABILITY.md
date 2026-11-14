# PAYGUARD Phase 6: Explainable AI Risk Assessment Framework

**Project:** PAYGUARD — Autonomous Agent Defense Layer  
**Subsystem:** Explainable AI Risk Layer  

---

## 1. The Four-Quadrant Explainability Framework

Security operators and smart contract verifiers must not be presented with opaque "black-box" scores. PAYGUARD partitions its evaluation results into four distinct, auditable categories:

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│         1. OBSERVED FACTS             │      2. STATISTICAL ANOMALIES         │
│  - Sender: agent-dev.near             │  - Z-Score: 0.12 (Normative)          │
│  - Recipient: oracle.near             │  - Isolation Forest: 0.08             │
│  - Amount: 2.50 NEAR                  │  - Velocity: 1 tx/min                 │
│  - Historical Transactions: 12        │  - Counterparty: Known counterparty   │
├───────────────────────────────────────┼───────────────────────────────────────┤
│      3. MODEL INTERPRETATIONS         │        4. SECURITY WARNINGS           │
│  - Intent Consistency: 1.00 (Match)   │  - Adversarial injection: Clean       │
│  - Declared Goal: "Oracle fee query"  │  - Counterparty reputation: Verified  │
│  - Task Scope: Valid                  │  - Anti-Replay status: Unique nonce   │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### 1.1 Observed Facts (Deterministic Parameters)
Factual, tamper-evident parameters extracted directly from the signed transaction request and historical database state (sender address, recipient, nominal transfer amount, rolling volume).

### 1.2 Statistical Anomalies (Quantitative ML)
Mathematical metrics derived from agent history: Z-scores relative to standard deviation, Isolation Forest multi-dimensional outlier flags, counterparty novelty indices, and burst frequencies.

### 1.3 Model Interpretations (Semantic Analysis)
Natural language understandings extracted by NLP models: declared purpose summary, extracted intended counterparty, amount tolerance deviation, and task scope validity.

### 1.4 Security Warnings (Threat Findings)
Deterministic threat markers: blacklisted address flags, adversarial pattern classifications (`INSTRUCTION_OVERRIDE`, `POLICY_BYPASS_ATTEMPT`), and duplicate replay detections.

---

## 2. Confidence Calibration & Uncertainty Scoring

Each evaluation synthesizes a `ConfidenceAssessment`:
- **`HIGH_CONFIDENCE`:** Complete parameters, active behavioral baseline ($\ge 3$ txs), unanimous agent consensus ($C = 1.0$).
- **`MEDIUM_CONFIDENCE`:** Active baseline, but minor intent divergence ($15\% - 30\%$) or one agent reporting non-critical disagreement.
- **`LOW_CONFIDENCE`:** LLM fallback used or agent history absent.
- **`INSUFFICIENT_EVIDENCE`:** Agent status is `INSUFFICIENT_HISTORY`; parameters lack declared natural language rationale.

---

## 3. Clear AI vs. Policy Authority Distinction

Every explainable report explicitly displays the invariant notice:

> *"AI evaluation constitutes advisory threat intelligence. The deterministic policy engine retains sole execution authority. An AI recommendation cannot approve a blocked counterparty or exceed configured spending caps."*

