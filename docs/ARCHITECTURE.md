# PAYGUARD — Architecture & System Design

**Tagline:** Intelligent Security Infrastructure for Autonomous AI Agents  
**NEAR Hackathon 2026** — AI Security & Defense (SEC) / Agent Economy (AGT)

---

## 1. System Overview

PAYGUARD acts as a deterministic defense middleware inserted between autonomous AI agents and blockchain execution layers.

### The Central Security Principle:
```
AI analyzes. The policy engine enforces. The smart contract protects.
```

- **AI is Advisory:** AI machine learning models and heuristics analyze behavioral anomalies and compute explainable risk scores. An AI recommendation can NEVER override a hard policy BLOCK.
- **The Policy Engine is Authoritative:** Enforces deterministic invariants (per-transaction limits, 24h rolling velocity limits, address blocklists/whitelists, duplicate transaction detection).
- **The Smart Contract is Guardian:** On-chain vault holds funds and only releases tokens upon receipt of verified policy authorization.

---

## 2. High-Level Component Architecture

```
+--------------------------------------------------------------------------+
|                        AUTONOMOUS AI AGENT LAYER                         |
|  (Agent Frameworks: LangChain, CrewAI, AutoGPT, Custom NEAR Agents)      |
+--------------------------------------------------------------------------+
                                     │
                     HTTP POST /api/transactions/analyze
                                     ▼
+--------------------------------------------------------------------------+
|                       PAYGUARD SECURITY BACKEND                          |
|                                                                          |
|  1. TransactionValidator: Structural, schema & sanity checks             |
|  2. PolicyEngine: Deterministic rule verification                        |
|     ├── Per-TX spending limit                                            |
|     ├── Daily rolling volume ceiling                                     |
|     ├── Counterparty blocklist & trusted list verification               |
|     ├── Duplicate transaction detection (120s window)                    |
|     └── Frequency / velocity burst protection                            |
|  3. RiskCalculator: Explainable risk scoring (0-100)                      |
|  4. DecisionEngine: Synthesizes verdict (ALLOW / WARN / BLOCK)           |
|  5. BehaviouralAnomalyDetector: Scikit-learn Isolation Forest telemetry   |
|  6. Telemetry & WebSockets: Live event stream to security dashboard      |
+--------------------------------------------------------------------------+
                                     │
           ALLOW                     │ WARN                     │ BLOCK
             ▼                       ▼                          ▼
+----------------------+   +-------------------+   +-----------------------+
| Authorized Execution |   | Human-in-the-Loop |   | Immediate Intercept   |
| (Simulated in Ph1,   |   | Review Queue      |   | (Funds safe in vault, |
| NEAR Vault in Ph2)   |   | (Operator signoff)|   | exploit prevented)    |
+----------------------+   +-------------------+   +-----------------------+
```

---

## 3. Data Flow

1. **Agent Intent Submission:** Autonomous agent initiates a financial transaction request specifying sender, recipient, amount, currency, and declared task purpose.
2. **Syntactic Validation:** `TransactionValidator` verifies NEAR address format, non-zero positive amounts, and data integrity.
3. **Deterministic Policy Check:** `PolicyEngine` checks:
   - Is recipient on the `blocked_recipients` list? -> Hard `BLOCKED`.
   - Is transaction identical to another within `duplicate_window_seconds`? -> Hard `FAILED`.
   - Does amount exceed `max_tx_amount`? -> Hard `FAILED`.
   - Does projected 24h volume exceed `daily_spending_limit`? -> Hard `FAILED`.
   - Does transaction velocity exceed `max_tx_frequency_per_minute`? -> Hard `FAILED`.
   - Is recipient unknown? -> `WARNING` (triggers human-in-the-loop requirement).
4. **Explainable Risk Scoring:** `RiskCalculator` computes an additive, explainable 0–100 score across threat categories.
5. **Deterministic Decision Synthesis:** `DecisionEngine` assigns:
   - `BLOCK`: Hard restriction violated or risk score >= `high_risk_threshold`.
   - `WARN`: Requires human operator approval or risk score >= `medium_risk_threshold`.
   - `ALLOW`: Passed all policies and risk score < `medium_risk_threshold`.
6. **Broadcasting & Persistence:** Result recorded in security telemetry log and broadcast over WebSockets to the active React dashboard.

---

## 4. Security Architecture & Threat Vectors Mitigated

| Threat Vector | Mitigation Mechanism | Engine Component |
| :--- | :--- | :--- |
| **Malicious Address Drain** | Instant hard BLOCK on known exploiter/drainer accounts | `PolicyEngine` (Blocklist) |
| **Excessive Spending** | Strict numerical ceilings per transaction and 24h window | `PolicyEngine` (Amount & Daily Limits) |
| **Replay / Duplicate Attacks** | Deduplication hash checking within rolling time window | `PolicyEngine` (Duplicate Check) |
| **Prompt Injection Manipulation** | Deterministic code boundaries; LLM cannot authorize funds | `DecisionEngine` Invariant |
| **Flooding / Infinite Loops** | Transaction velocity rate-limiting per sender agent | `PolicyEngine` (Frequency Check) |
| **Unverified Counterparties** | Human-in-the-loop mandatory review escalation | `DecisionEngine` (WARN Workflow) |

---

## 5. Technology Stack

- **Backend:** Python 3.11.9, FastAPI, Pydantic v2, Pydantic Settings, Uvicorn, WebSockets.
- **AI / ML:** Scikit-learn (Isolation Forest baseline), explainable heuristic risk engines.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide React, Axios.
- **Blockchain (Future Phases):** NEAR Protocol Testnet, Rust `near-sdk`, NEAR JavaScript SDK.
