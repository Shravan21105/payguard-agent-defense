# PAYGUARD — Phase 4: End-to-End Architecture Specification

**Project:** PAYGUARD (Agent Defense Layer)  
**Hackathon:** NEAR Hackathon 2026  
**Tracks:** AI Security & Defense (SEC) | Agent Economy (AGT)  
**Core Invariant:** *AI analyzes. The policy engine enforces. The smart contract protects.*

---

## 1. Executive Summary

Phase 4 delivers the complete, seamless end-to-end integration connecting the React Frontend, FastAPI Backend, Multi-Agent Intent & Behavioral Evaluation, Deterministic Policy Engine, Ed25519 Cryptographic Signer, and NEAR Smart Contract Vault (`payguard-vault.testnet`).

In Phase 4, PAYGUARD unifies all prior phases into a single autonomous-agent transaction defense platform:
1. Any AI agent or developer submits a single call to `POST /api/transactions/initiate`.
2. The transaction undergoes multi-agent LLM intention auditing and behavioral analysis (LangGraph).
3. The deterministic policy engine enforces hard non-overridable constraints (spending limits, velocity, blocklists).
4. If `ALLOW`: An Ed25519 canonical cryptographic signature is generated, verified against anti-replay records, executed on NEAR Testnet, verified via JSON-RPC, and assigned a live NearBlocks explorer link.
5. If `WARN`: Funds are diverted into a timelocked on-chain smart contract escrow awaiting authorized human sign-off.
6. If `BLOCK`: The transaction is intercepted before on-chain submission, cryptographic signature is withheld, and no funds leave the vault.
7. Telemetry is streamed in real time across 12 WebSocket event types, and audit records persist in SQLite.

---

## 2. End-to-End System Architecture

```
                                  +---------------------------------------+
                                  |         AUTONOMOUS AI AGENT           |
                                  |   (e.g., LangChain, CrewAI, AutoGen)  |
                                  +-------------------+-------------------+
                                                      |
                                                      | POST /api/transactions/initiate
                                                      v
+---------------------------------------------------------------------------------------------------------+
|                                        PAYGUARD BACKEND (FastAPI)                                       |
|                                                                                                         |
|  1. Syntactic Validation & Idempotency Check                                                            |
|     * Verifies transaction format, amounts (>0), accounts                                               |
|     * Prevents duplicate submission via idempotency key and tx status                                   |
|                                                                                                         |
|  2. Multi-Agent Security Intelligence (LangGraph)                                                       |
|     +-------------------------+     +--------------------------+     +-------------------------------+  |
|     |  Intent Analysis Agent  |     |  Behavioral Risk Agent   |     | Security Intelligence Agent   |  |
|     |  - LLM Intent Auditing  |     |  - Isolation Forest ML   |     | - Blocklist & Threat Intel    |  |
|     |  - Prompt Injection     |     |  - Rolling spend volume  |     | - Fast duplicate check (120s) |  |
|     +-------------------------+     +--------------------------+     +-------------------------------+  |
|                                                  |                                                      |
|                                                  v                                                      |
|                                     +--------------------------+                                        |
|                                     | Transaction Audit Agent  |                                        |
|                                     | - Explainable Risk Score |                                        |
|                                     +--------------------------+                                        |
|                                                  |                                                      |
|  3. Deterministic Policy Enforcement             v                                                      |
|     * Policy rules evaluate bounds (limits, velocity, allowlists/blocklists)                            |
|     * INVARIANT: Deterministic BLOCK can NEVER be overridden by AI score                                |
|     * Generates Decision: ALLOW | WARN | BLOCK                                                          |
|                                                                                                         |
|  4. Cryptographic Authorization & On-Chain Dispatch                                                      |
|     +---------------------------------------------------------------------------------------------+     |
|     | Decision == ALLOW:                                                                          |     |
|     |   * Ed25519 canonical signature created over domain-separated message                       |     |
|     |   * Replay protection check (auth_id, nonce)                                                |     |
|     |   * NEAR Testnet direct execution (or dry-run simulation)                                   |     |
|     |   * NearBlocks Explorer receipt verification                                                |     |
|     +---------------------------------------------------------------------------------------------+     |
|     | Decision == WARN:                                                                           |     |
|     |   * Timelock escrow created (contract or dry-run)                                            |     |
|     |   * Queued in Human Approval queue                                                          |     |
|     +---------------------------------------------------------------------------------------------+     |
|     | Decision == BLOCK:                                                                          |     |
|     |   * Signature WITHHELD. Execution REJECTED. Threat logged in SQLite.                        |     |
|     +---------------------------------------------------------------------------------------------+     |
|                                                  |                                                      |
|  5. Event Telemetry & Audit Persistence          v                                                      |
|     * Real-time WebSocket broadcasting across 12 event types                                            |
|     * SQLite ACID persistence (transactions, evidence, agent traces)                                    |
+------------------------------------+------------------------------------+-------------------------------+
                                     |                                    |
                    WebSocket Events |                                    | On-Chain Execution
                                     v                                    v
           +------------------------------------+       +------------------------------------+
           |     PAYGUARD DASHBOARD (React)     |       |    NEAR TESTNET SMART CONTRACT     |
           |                                    |       |         (payguard-vault)           |
           |  * Live Monitoring Telemetry       |       |  * Native Ed25519 signature verify |
           |  * NearBlocks Explorer Deep Links  |       |  * Nonce & Auth ID replay storage  |
           |  * On-Chain Audit Receipt Modals   |       |  * Timelock Escrow Vault           |
           |  * Human Operator Approvals Queue  |       |  * Direct Token Transfer Dispatch  |
           +------------------------------------+       +------------------------------------+
```

---

## 3. Transaction Lifecycle State Machine

PAYGUARD defines an explicit 11-stage transaction lifecycle:

```
[ RECEIVED ]
     │
     ▼
[ ANALYZING ]  (Multi-Agent Intent & Behavioral Evaluation)
     │
     ├───────────────────────┬────────────────────────┐
     ▼                       ▼                        ▼
[ ALLOWED ]               [ WARN ]                [ BLOCKED ]
     │                       │                        │
     ▼                       ▼                        ▼
[ EXECUTING ]       [ ESCROW_CREATED ]       (Transaction Halted)
     │                       │
     ▼                       ├────────────────────────┐
[ CONFIRMED ]                ▼                        ▼
(NearBlocks link)   [ APPROVED ]             [ REJECTED ]
                             │                        │
                             ▼                        ▼
                        [ EXECUTING ]            [ REFUNDED ]
                             │
                             ▼
                        [ CONFIRMED ]
```

### State Definitions

| State | Description | Next Permitted States |
| :--- | :--- | :--- |
| `RECEIVED` | Transaction received by API; syntactic validation passed. | `ANALYZING` |
| `ANALYZING` | Multi-agent LangGraph pipeline is evaluating intent, risk, and policies. | `ALLOWED`, `WARN`, `BLOCKED`, `FAILED` |
| `ALLOWED` | Policy engine synthesized ALLOW decision; ready for signature & execution. | `EXECUTING`, `CONFIRMED`, `FAILED` |
| `WARN` | Risk score elevated or manual review triggered; awaiting escrow creation. | `ESCROW_CREATED`, `EXECUTING`, `FAILED` |
| `BLOCKED` | Hard policy violation or critical threat detected; execution halted. | Terminal state |
| `EXECUTING` | Ed25519 signature generated; interacting with NEAR RPC / vault contract. | `CONFIRMED`, `FAILED` |
| `CONFIRMED` | On-chain execution succeeded; block height, hash, and explorer URL recorded. | Terminal state |
| `ESCROW_CREATED` | Transaction deposited into on-chain escrow awaiting human approval. | `APPROVED`, `REJECTED`, `EXPIRED` |
| `APPROVED` | Human operator approved the escrowed transaction. | `EXECUTING`, `CONFIRMED`, `FAILED` |
| `REJECTED` | Human operator rejected the transaction; funds refunded to sender. | `REFUNDED` |
| `REFUNDED` | Escrowed funds successfully refunded to sender account. | Terminal state |
| `FAILED` | Network failure, contract panic, or execution error encountered. | Terminal state |

---

## 4. Cryptographic Security & Anti-Replay Architecture

### Canonical Domain-Separated Serialization

To prevent cross-contract and cross-chain replay attacks, PAYGUARD employs a strict domain-separated canonical serialization format before signing with Ed25519:

```
PAYGUARD:v1:<network_id>:<contract_id>:<auth_id>:<sender_id>:<recipient_id>:<amount_yocto>:<decision>:<risk_score>:<policy_version>:<nonce>:<issued_at>:<expires_at>
```

**Fields:**
- `domain`: `PAYGUARD:v1` (fixed protocol prefix)
- `network_id`: e.g. `testnet` or `mainnet`
- `contract_id`: Target vault contract account (e.g. `payguard-vault.testnet`)
- `auth_id`: Cryptographically random UUID v4 identifying the authorization
- `sender_id`: Agent account initiating the transfer
- `recipient_id`: Target destination account
- `amount_yocto`: Exact amount in yoctoNEAR ($10^{24}$ yocto = 1 NEAR)
- `decision`: Evaluated deterministic outcome (`ALLOW` or `WARN`)
- `risk_score`: Calibrated integer score (0-100)
- `policy_version`: Active security policy version string (e.g. `1.0.0`)
- `nonce`: Monotonically increasing cryptographic nonce
- `issued_at`: UTC Unix timestamp in milliseconds
- `expires_at`: UTC Unix timestamp in milliseconds (typically `issued_at + 300,000ms`)

### Ed25519 Verification

- The backend generates a 64-byte Ed25519 signature using the authorized policy private key.
- The smart contract verifies the signature using native NEAR host function `near_sdk::env::ed25519_verify(sig, msg, public_key)`.
- If the signature does not match or has expired (`expires_at < current_block_timestamp`), the contract panics and reverts immediately.

### Dual-Layer Anti-Replay Protection

Replay protection is enforced both in the backend and on-chain:
1. **Smart Contract Storage:** The contract stores used `auth_id`s in a `LookupSet<String>` and nonces in a `LookupSet<u64>`. Any re-submission of an existing `auth_id` or `nonce` causes an immediate contract panic with `ERR_AUTH_ALREADY_USED` or `ERR_NONCE_ALREADY_USED`.
2. **Backend Database:** The SQLite database tracks all `auth_id` records in `authorization_evidence`. Submitting an existing `auth_id` returns an idempotent cached response without duplicate signing or on-chain execution.

---

## 5. Dual Execution Paths

### Path A: Direct Execution (`ALLOW`)

1. Transaction is analyzed: Risk Score $< 40$, all deterministic policies pass.
2. Signer generates canonical message & Ed25519 signature.
3. If `dry_run=False`: Transaction dispatched to `execute_transfer` on NEAR Testnet contract.
4. Receipt is checked; NearBlocks explorer link is generated:  
   `https://testnet.nearblocks.io/txns/{tx_hash}`
5. Status transitions to `CONFIRMED`.

### Path B: Timelocked Escrow (`WARN`)

1. Transaction has elevated risk ($40 \le \text{Risk Score} \le 70$) or unknown counterparty.
2. System deposits transfer into contract escrow via `create_escrow` with a timelock (e.g. 86,400 seconds).
3. Status transitions to `ESCROW_CREATED`.
4. Transaction appears in the Human Approvals dashboard.
5. If Approved: Operator signs off, contract transfers funds to recipient, status becomes `CONFIRMED`.
6. If Rejected or Timelock Expires: Funds are refunded back to the sender account, status becomes `REFUNDED`.

### Path C: Deterministic Interception (`BLOCK`)

1. Critical risk detected ($\text{Risk Score} > 70$), blocklist match, or prompt injection.
2. Status transitions immediately to `BLOCKED`.
3. **No signature is ever generated.** Private key remains untouched.
4. Transaction is aborted; zero funds leave the agent wallet.

---

## 6. Real-Time Telemetry & WebSocket Event Catalog

PAYGUARD broadcasts 12 standardized event types over `ws://{host}/api/ws/monitoring`:

| Event Type | Trigger | Payload Highlights |
| :--- | :--- | :--- |
| `transaction.received` | API receives transaction | `transaction_id`, `sender`, `recipient`, `amount` |
| `agent.started` | Multi-agent node begins | `agent_name`, `node`, `timestamp` |
| `agent.completed` | Multi-agent node finishes | `agent_name`, `verdict`, `confidence`, `latency_ms` |
| `intent.mismatch` | Declared intent deviates | `discrepancy_details`, `similarity_score` |
| `prompt.injection` | Injection pattern detected | `pattern`, `risk_score` |
| `evidence.generated` | RFC-8785 evidence computed | `evidence_hash`, `canonical_length` |
| `transaction.decided` | Policy synthesis completed | `decision`, `risk_score`, `reasons` |
| `transaction.signing` | Ed25519 signature initiated | `auth_id`, `nonce`, `contract_id` |
| `transaction.signed` | Signature generated | `signature_hex` (truncated), `expires_at` |
| `blockchain.executing`| Sent to NEAR RPC | `contract_id`, `method_name` |
| `blockchain.confirmed`| Verified receipt on NEAR | `tx_hash`, `block_height`, `explorer_url` |
| `escrow.created` | Deposited into escrow | `escrow_id`, `timelock_seconds`, `amount` |
| `escrow.approved` | Operator approves escrow | `escrow_id`, `approver_id`, `tx_hash` |
| `escrow.rejected` | Operator rejects escrow | `escrow_id`, `refund_tx_hash` |

---

## 7. Storage & Persistence Architecture

The backend database (`backend/payguard.db`) maintains complete relational records across 6 core tables:

1. `transactions`: Full 29-column lifecycle record including `status`, `tx_hash`, `block_height`, `block_hash`, `explorer_url`, `escrow_id`, `error_details`, and `execution_mode`.
2. `agent_executions`: Latency, confidence, and output traces for each of the 4 specialized agents.
3. `security_findings`: Granular threat items, rule codes, and severities.
4. `authorization_evidence`: RFC-8785 canonical JSON payloads, SHA-256 evidence digests, and Ed25519 signatures.
5. `approval_records`: Timestamps, operator identifiers, and decision notes for manual approvals.
6. `policies`: Live configuration limits, thresholds, and blocklists.

Automatic schema migration ensures backwards compatibility across all phases without data loss.

