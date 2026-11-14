# PAYGUARD Phase 6: Multi-Agent AI Architecture & LangGraph Topology

**Project:** PAYGUARD — Autonomous Agent Defense Layer  
**Hackathon Tracks:** AI Security & Defense (SEC) | Agent Economy (AGT)  
**Status:** Completed & Verified  

---

## 1. System Overview & The Core Invariant

PAYGUARD operates on a non-negotiable architectural invariant:

> **"AI analyzes. The policy engine enforces. The smart contract protects."**

Autonomous AI agents operating in Web3 and financial contexts face continuous risks: adversarial prompt injection, unauthorized counterparty redirects, transaction parameter divergence, and sudden velocity spikes. 

Phase 6 upgrades PAYGUARD's AI subsystem from basic heuristics into an advanced ensemble intelligence layer without compromising deterministic authorization boundaries:
- AI models advise with structured probability and findings; they have **zero direct execution authority**.
- A hard deterministic `BLOCK` decision from the policy engine can **never be overridden** by high AI confidence.
- Even if all AI providers experience simultaneous outages, the system falls back safely to deterministic policy evaluation and never defaults to an automatic `ALLOW`.

---

## 2. Multi-Agent Ensemble Architecture

PAYGUARD coordinates four specialized agents via a unified LangGraph `StateGraph`:

```
                       [Incoming TransactionRequest]
                                     │
                                     ▼
                        [Node 1: Input Validation]
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
        [Agent A: Intent]    [Agent B: Behavior]  [Agent C: Security Intel]
        (Semantic Goal &     (Z-Score, Forest,    (Adversarial Injections,
         Scope Consistency)    Velocity Spikes)     Blocklists, Replay)
                 │                   │                   │
                 └───────────────────┼───────────────────┘
                                     ▼
                       [Agent D: Transaction Audit]
                   (Consensus, Disagreement, 4-Quadrant
                    Explainability & Confidence Scoring)
                                     │
                                     ▼
                       [Deterministic Policy Engine]
                     (Hard Limits, Rolling Caps, Quotas)
                                     │
                                     ▼
                      [Canonical Evidence & Vault]
                     (RFC-8785 + Ed25519 Authorization)
```

### Specialized Agents Specification

| Agent | Module | Role | Core Algorithms & Capabilities |
| :--- | :--- | :--- | :--- |
| **Agent A: Intent Analysis** | `app.agents.intent_agent` | Semantic Goal Extraction & Discrepancy Auditing | LLM + Fuzzy Levenshtein regex matching, scope validation, recipient diversion detection, amount deviation scoring (tolerance 15%). |
| **Agent B: Behavioural Risk** | `app.agents.behavioural_agent` | Spending Profiling & Anomaly Detection | Statistical Z-Score ($Z \ge 3.0$), Scikit-learn Isolation Forest (`contamination=0.05`), Counterparty Novelty check, Velocity burst monitoring ($\ge 5\text{ tx/min}$). |
| **Agent C: Security Intel** | `app.agents.security_agent` | Threat Intelligence & Attack Detection | 6-class multi-vector adversarial injection scanner, Near Threat Catalog matching, 120s duplicate replay interceptor, malicious metadata sanitizer. |
| **Agent D: Transaction Audit** | `app.agents.audit_agent` | Multi-Agent Synthesis & Consensus | Agreement / disagreement metric calculation, deterministic aggregation (no simple averaging), missing evidence tracking, 4-quadrant explainable reporting. |

---

## 3. LangGraph Topology & State Machine

The LangGraph orchestration graph (`app.agents.orchestrator.MultiAgentOrchestrator`) defines a deterministic state transition machine:

1. **`START` $\to$ `_validate_node`**: Syntactic sanity checks, parameter normalization, and emission of `transaction.received` event.
2. **`_validate_node` $\to$ `_intent_agent_node`**: Invokes `IntentAnalysisAgent`, evaluates declared natural language purpose against actual recipient and amount, computes `intent_consistency_score`. Emits `ai.intent_analyzed`.
3. **`_intent_agent_node` $\to$ `_behavioural_agent_node`**: Loads persistent `AgentBehavioralProfile` from SQLite; if $< 3$ historical transactions, sets status to `INSUFFICIENT_HISTORY` without artificial baselines; computes Z-Score, Isolation Forest anomaly score, counterparty novelty, and velocity bursts. Emits `ai.behavior_analyzed`.
4. **`_behavioural_agent_node` $\to$ `_security_intel_agent_node`**: Scans purpose and metadata for adversarial injection patterns, checks counterparty against blocked/trusted lists, verifies replay protection. Emits `ai.security_scan_completed`.
5. **`_security_intel_agent_node` $\to$ `_audit_agent_node`**: Synthesizes agent recommendations side-by-side, detects conflicts, aggregates composite risk score with non-negotiable precedence, generates 4-quadrant explainability breakdown. Emits `ai.consensus_completed`.
6. **`_audit_agent_node` $\to$ `_policy_evaluation_node`**: Deterministic policy engine evaluates spending limits, rolling daily caps, and rate limits. If any deterministic check flags `BLOCK`, AI scores cannot override.
7. **`_policy_evaluation_node` $\to$ `_evidence_and_persist_node`**: Computes RFC-8785 canonical hash, stores transaction in SQLite, persists `ai_evaluations` record, updates agent behavioral profile, and emits final verdict (`transaction.allowed`, `transaction.warned`, or `transaction.blocked`).
8. **`_evidence_and_persist_node` $\to$ `END`**.

---

## 4. Failure Recovery & Outage Protocols

- **LLM Provider Outage:** When external LLM APIs (OpenAI, Gemini, Anthropic) time out or fail, the `LLMGateway` automatically transitions to `_deterministic_fallback_audit` with `llm_fallback_used=True`.
- **Adversarial Injections During Outage:** The deterministic fallback continues to run all multi-class adversarial regex filters and prompt injection sanitizers; malicious input is **never** approved due to provider failure.
- **Database Resilience:** SQLite operations use re-entrant locking (`threading.RLock()`) with WAL mode (`PRAGMA journal_mode = WAL`) and parameterized queries, preventing deadlocks during concurrent asynchronous execution.

