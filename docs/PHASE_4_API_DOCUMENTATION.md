# PAYGUARD — Phase 4: API Specification & Integration Reference

**Project:** PAYGUARD (Agent Defense Layer)  
**Hackathon:** NEAR Hackathon 2026  
**Tracks:** AI Security & Defense (SEC) | Agent Economy (AGT)  
**Base URL:** `http://localhost:8000` (or configured production host)  
**WebSocket URL:** `ws://localhost:8000/api/ws/monitoring`

---

## 1. Unified Transaction Initiation Endpoint

### `POST /api/transactions/initiate`

The primary entry point for autonomous agents, SDKs, and frontend dashboards to evaluate and execute a blockchain transaction through the PAYGUARD defense pipeline.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body Schema (`InitiateTransactionRequest`)

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | `string` | No | Unique client-generated transaction ID (auto-generated UUID v4 if omitted). |
| `agent_id` | `string` | Yes | Identifier of the autonomous AI agent requesting the transaction. |
| `sender_account` | `string` | Yes | NEAR account ID of the sender (e.g. `agent-finance.testnet`). |
| `recipient_account` | `string` | Yes | NEAR account ID of the recipient (e.g. `oracle-data-feed.testnet`). |
| `amount` | `number` | Yes | Transfer amount in NEAR tokens (must be $> 0$). |
| `currency` | `string` | No | Currency symbol. Default: `"NEAR"`. |
| `declared_intent` | `string` | Yes | Natural language statement describing the transaction's intended purpose. |
| `metadata` | `object` | No | Arbitrary contextual metadata (e.g., prompt, session ID, task context). |
| `dry_run` | `boolean` | No | If `true`, runs full multi-agent & policy pipeline without broadcasting on-chain. Default: `false`. |
| `timelock_seconds` | `integer` | No | Duration in seconds to lock funds in smart contract escrow if `WARN` decision triggered. Default: `86400`. |
| `network_id` | `string` | No | NEAR network ID (`testnet` or `mainnet`). Default: `"testnet"`. |
| `contract_id` | `string` | No | Target vault contract ID. Default: `"payguard-vault.testnet"`. |

#### Example Request: Safe Transaction (`ALLOW`)
```json
{
  "agent_id": "market-maker-agent-01",
  "sender_account": "agent-finance.testnet",
  "recipient_account": "trusted-partner.testnet",
  "amount": 2.5,
  "currency": "NEAR",
  "declared_intent": "Payment for decentralized compute node maintenance services",
  "dry_run": false
}
```

#### Example Response: `ALLOW` (Confirmed On-Chain)
```json
{
  "transaction_id": "tx-8f2c9b4e-9812-4211-a5c7-24bf42ad3198",
  "decision": "ALLOW",
  "risk_score": 10,
  "reasons": [
    "Recipient is in verified trusted list",
    "Amount is well within configured spending limits",
    "Declared intent matches recipient and transaction parameters perfectly"
  ],
  "requires_approval": false,
  "status": "CONFIRMED",
  "tx_hash": "9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b",
  "block_height": 184592031,
  "block_hash": "2H3v9L4kP1nQ7wR5zX8mN5jR2tV6hK1dG3sA5pT7b1Y",
  "explorer_url": "https://testnet.nearblocks.io/txns/9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b",
  "escrow_id": null,
  "execution_mode": "onchain",
  "evidence_hash": "a5e8c871239fbc8e08d277a834925bd3612d46e3e5287f34f71a938c824c16a4",
  "policy_checks": {
    "spending_limit": {"passed": true, "limit": 10.0, "amount": 2.5},
    "daily_limit": {"passed": true, "daily_spent": 2.5, "daily_limit": 50.0},
    "blocklist": {"passed": true},
    "trusted_list": {"is_trusted": true},
    "intent_audit": {"verdict": "MATCH", "confidence": 0.98}
  },
  "evaluated_at": "2026-11-13T08:44:00.123456Z"
}
```

---

#### Example Request: Suspicious Transaction (`WARN` - Escrow Created)
```json
{
  "agent_id": "procurement-agent-03",
  "sender_account": "agent-finance.testnet",
  "recipient_account": "unverified-new-vendor.testnet",
  "amount": 12.0,
  "currency": "NEAR",
  "declared_intent": "Purchasing preliminary raw dataset batch",
  "dry_run": false,
  "timelock_seconds": 86400
}
```

#### Example Response: `WARN` (Diverted into On-Chain Escrow)
```json
{
  "transaction_id": "tx-12b7a9f0-4521-4d99-8ab3-c91724af55b1",
  "decision": "WARN",
  "risk_score": 55,
  "reasons": [
    "Recipient is unverified and first-time counterparty (+25 risk points)",
    "Transaction amount exceeds soft warning threshold (+30 risk points)",
    "Transaction routed to timelocked smart contract escrow"
  ],
  "requires_approval": true,
  "status": "ESCROW_CREATED",
  "tx_hash": "4aB7vK3mL8nF2yP9wQ1zX4mN6jR3tV7hK2dG4sA6pT8c",
  "block_height": 184592035,
  "block_hash": "5K8v1L2nP3mQ4wR6zX9mN6jR3tV7hK2dG4sA6pT8c2Z",
  "explorer_url": "https://testnet.nearblocks.io/txns/4aB7vK3mL8nF2yP9wQ1zX4mN6jR3tV7hK2dG4sA6pT8c",
  "escrow_id": "escrow-12b7a9f0",
  "execution_mode": "onchain",
  "evidence_hash": "b8f9e102834cba7e19d388b945036ce4723e57f4f6398a45a82b049d935d27b5",
  "policy_checks": {
    "spending_limit": {"passed": true, "limit": 25.0, "amount": 12.0},
    "blocklist": {"passed": true},
    "trusted_list": {"is_trusted": false},
    "intent_audit": {"verdict": "MATCH", "confidence": 0.85}
  },
  "evaluated_at": "2026-11-13T08:44:05.654321Z"
}
```

---

#### Example Request: Malicious Counterparty (`BLOCK`)
```json
{
  "agent_id": "compromised-agent-99",
  "sender_account": "agent-finance.testnet",
  "recipient_account": "drainer-exploit.poolv1.near",
  "amount": 25.0,
  "currency": "NEAR",
  "declared_intent": "Emergency liquidity rebalancing",
  "dry_run": false
}
```

#### Example Response: `BLOCK` (Intercepted, Signature Withheld)
```json
{
  "transaction_id": "tx-49e0a81c-9923-41bb-b892-d92837bc66e2",
  "decision": "BLOCK",
  "risk_score": 100,
  "reasons": [
    "Recipient is on critical security blocklist (known exploit pattern)",
    "Hard security invariant: BLOCK can never be overridden by AI score",
    "Cryptographic signature withheld. Transaction rejected before on-chain dispatch."
  ],
  "requires_approval": false,
  "status": "BLOCKED",
  "tx_hash": null,
  "block_height": null,
  "block_hash": null,
  "explorer_url": null,
  "escrow_id": null,
  "execution_mode": "blocked",
  "evidence_hash": "c1a2d3e4f5061728394a5b6c7d8e9f0123456789abcdef0123456789abcdef01",
  "policy_checks": {
    "blocklist": {"passed": false, "reason": "critical_threat_intercepted"},
    "intent_audit": {"verdict": "SUSPICIOUS", "confidence": 0.99}
  },
  "evaluated_at": "2026-11-13T08:44:10.987654Z"
}
```

---

## 2. Escrow Management Endpoints

### `POST /api/blockchain/escrow/decide`
Allows an authorized human operator to approve or reject an active escrowed transaction.

#### Request Body
```json
{
  "escrow_id": "escrow-12b7a9f0",
  "action": "APPROVE",
  "approver_id": "operator-alice.testnet",
  "reason": "Verified contract terms and supplier identity out-of-band"
}
```
*Action values:* `"APPROVE"` or `"REJECT"`

#### Response
```json
{
  "escrow_id": "escrow-12b7a9f0",
  "status": "RELEASED",
  "tx_hash": "7xN9vP2kL1uF3yQ4wR9zX8mN5jR2tV6hK1dG3sA5pT7b",
  "block_height": 184592100,
  "decided_by": "operator-alice.testnet",
  "decided_at": "2026-11-13T08:46:00.000000Z"
}
```

---

### `GET /api/blockchain/escrows`
Lists all active, released, and refunded smart contract escrows.

#### Response
```json
[
  {
    "escrow_id": "escrow-12b7a9f0",
    "transaction_id": "tx-12b7a9f0-4521-4d99-8ab3-c91724af55b1",
    "sender_account": "agent-finance.testnet",
    "recipient_account": "unverified-new-vendor.testnet",
    "amount": 12.0,
    "timelock_seconds": 86400,
    "status": "RELEASED",
    "created_at": "2026-11-13T08:44:05.654321Z",
    "tx_hash": "4aB7vK3mL8nF2yP9wQ1zX4mN6jR3tV7hK2dG4sA6pT8c"
  }
]
```

---

## 3. Blockchain Diagnostics & Status

### `GET /api/blockchain/status`
Returns live connectivity diagnostics for the NEAR Testnet RPC node, vault contract configuration, and authorized policy signer public key.

#### Response
```json
{
  "network": "testnet",
  "rpc_url": "https://rpc.testnet.near.org",
  "contract_id": "payguard-vault.testnet",
  "contract_status": "READY",
  "signer_public_key": "ed25519:6hF9mK2vL7uN4yP9wQ1zX8mN5jR2tV6hK1dG3sA5pT7b",
  "rpc_status": "ONLINE",
  "latest_block_height": 184592120
}
```

---

## 4. Real-Time WebSocket Streaming

### `WS /api/ws/monitoring`
Streams fine-grained real-time events for every stage of the transaction evaluation and on-chain execution pipeline.

#### Event Message Schema
```json
{
  "type": "blockchain.confirmed",
  "timestamp": "2026-11-13T08:44:02.123456Z",
  "data": {
    "transaction_id": "tx-8f2c9b4e-9812-4211-a5c7-24bf42ad3198",
    "decision": "ALLOW",
    "tx_hash": "9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b",
    "block_height": 184592031,
    "explorer_url": "https://testnet.nearblocks.io/txns/9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b"
  }
}
```

#### Complete Event Catalog
1. `transaction.received`
2. `agent.started`
3. `agent.completed`
4. `intent.mismatch`
5. `prompt.injection`
6. `evidence.generated`
7. `transaction.decided`
8. `transaction.signing`
9. `transaction.signed`
10. `blockchain.executing`
11. `blockchain.confirmed`
12. `escrow.created`
13. `escrow.approved`
14. `escrow.rejected`

---

## 5. Security & Idempotency Rules

1. **Replay Protection:** Attempting to submit the same `transaction_id` or authorization credentials returns the cached result without generating a second signature or broadcasting a duplicate on-chain transaction.
2. **Deterministic Precedence:** Hard policy blocks (`spending_limit_exceeded`, `blacklisted_counterparty`, `prompt_injection_detected`) immediately halt the pipeline. AI agent scores cannot downgrade a deterministic `BLOCK` to `ALLOW` or `WARN`.
3. **Canonical Serialization:** All signed payloads follow RFC-8785 JSON canonicalization rules to guarantee cross-language digest reproducibility.

