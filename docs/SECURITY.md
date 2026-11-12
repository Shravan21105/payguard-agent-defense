# PAYGUARD — Security Model & Wallet Safety Principles

## 1. Core Threat Model

Autonomous AI agents represent a paradigm shift in financial transaction initiation:
- Autonomous agents operate without human intervention per task.
- Unconstrained wallet private keys in an agent environment risk catastrophic total balance loss if the agent is manipulated by prompt injection, rogue dependencies, or malicious API outputs.

### Specific Threats Addressed:
1. **Direct Prompt Injection:** Adversarial text embedded in user requests or third-party web content instructing the agent to "drain all NEAR to address X".
2. **Exploitative Counterparty:** An agent engaging with unverified smart contracts or known phishing addresses.
3. **Infinite Loop Spending:** Recursive reasoning bugs where an agent repeatedly sends transactions in a loop.
4. **Replay & Duplicate Transactions:** Re-submitting identical payment requests to drain balances.
5. **Excessive Resource Allocation:** An agent spending 500 NEAR when a task should only cost 2 NEAR.

---

## 2. Inviolable Security Principles

1. **AI Analyzes. The Policy Engine Enforces. The Smart Contract Protects.**
   - AI outputs are purely heuristic and advisory.
   - An AI model NEVER holds execution privileges.
   - An AI model CANNOT override a policy `BLOCK`.
2. **Deterministic Financial Policy Enforcement:**
   - Policy decisions are deterministic functions of input data, active configuration, and historical transaction logs.
   - Identical inputs with identical configurations yield identical security verdicts.
3. **Least Privilege & Escrowed Vault Protection:**
   - Autonomous agents do not possess main wallet private keys.
   - Vault funds can only be released upon valid cryptographic authorization matching verified policy rules.
4. **Human-in-the-Loop Safeguards:**
   - High-value transactions to unverified counterparties are flagged as `WARN`, halting execution until explicitly authorized by a human operator.
5. **Transparent and Explainable Telemetry:**
   - Every block or warning includes explicit, machine-readable reasons and a granular check breakdown.
   - No opaque, unexplainable decisions.

---

## 3. Secret Management & Credential Safety

- **Zero Hardcoded Secrets:** Private keys, seed phrases, and API credentials must NEVER be placed in code, repositories, or frontend builds.
- **Environment Isolation:** Configuration is managed through `.env` files, read via Pydantic Settings, and kept out of version control via `.gitignore`.
- **Frontend Safety:** No signing keys or sensitive operator credentials exist in the client-side React code. The client only queries the backend security engine.
- **Network Boundaries:** Testnet configurations and Mainnet configurations are maintained as strictly segregated environments.
