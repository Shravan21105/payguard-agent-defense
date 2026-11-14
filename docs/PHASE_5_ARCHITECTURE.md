# PAYGUARD — PHASE 5: REAL-TIME MONITORING & EVENT STREAMING ARCHITECTURE

## 1. Executive Summary

Phase 5 introduces a comprehensive, low-latency real-time monitoring and event streaming architecture to PAYGUARD (Agent Defense Layer). It creates an event-driven nervous system linking:
1. **Agent Transaction Intent & Multi-Agent Evaluation** (Phase 2)
2. **Deterministic Financial Policy Enforcement** (Phase 1)
3. **Ed25519 Cryptographic Authorization** (Phase 3)
4. **NEAR Smart Contract Vault Execution** (Phase 4)
5. **Continuous Blockchain Synchronization & Outage Recovery** (Phase 5)
6. **Live Multi-Subscriber WebSocket Streaming & Real-Time Security Operations Center (SOC)** (Phase 5)

Core Architecture Tenet:
> **"AI analyzes. The policy engine enforces. The smart contract protects. The event stream monitors with cryptographic fidelity."**

---

## 2. Real-Time Event Architecture & Flow

```
                      +------------------------------------------+
                      |         Autonomous AI Agent              |
                      +------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                            PAYGUARD BACKEND PIPELINE                             |
|                                                                                   |
|  [Agent Intent & Behavioral Analysis] ---> Emits: agent.intent_evaluated          |
|                 |                                                                 |
|                 v                                                                 |
|  [Deterministic Policy Engine]        ---> Emits: policy.evaluated, policy.block  |
|                 |                                                                 |
|                 v                                                                 |
|  [Ed25519 Authorization Signer]       ---> Emits: authorization.signed            |
|                 |                                                                 |
|                 v                                                                 |
|  [NEAR Testnet RPC & Vault Execution] ---> Emits: blockchain.tx_submitted,        |
|                                                   blockchain.tx_confirmed,       |
|                                                   escrow.created                  |
+-----------------------------------------------------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                         CENTRAL EVENT PUBLISHER                                   |
|                                                                                   |
|  - Validates RFC-3339 timestamp, UUID, Category, Severity                         |
|  - Automated Credential Redaction: Strips private keys, seeds, auth tokens        |
|  - In-Memory Ring Buffer Deduplication (prevents storm conditions)                |
|  - Asynchronous Non-Blocking Broadcast via asyncio.gather                        |
|  - SQLite Event Persistence (indexed on timestamp, category, severity, tx_id)     |
+-----------------------------------------------------------------------------------+
                |                                                  |
                v                                                  v
+-------------------------------+              +------------------------------------+
|     SQLite Event Store        |              |       WebSocket Manager            |
|  - events table               |              |  - Dynamic client tracking         |
|  - blockchain_checkpoints     |              |  - Topic subscriptions             |
|  - Zero data loss durability  |              |  - Heartbeat ping/pong (20s)       |
+-------------------------------+              +------------------------------------+
                                                                   |
                                                                   v
+-----------------------------------------------------------------------------------+
|                             FRONTEND LIVE DASHBOARDS                              |
|                                                                                   |
|  - LiveMonitoring.tsx: Real-time SOC feed, category filters, payload inspector   |
|  - Overview.tsx: Segregated volume breakdown (On-Chain vs Simulation vs Escrow)   |
|  - Transactions.tsx: Real-time row updates, 5-tab audit modal with lifecycle      |
|  - Approvals.tsx: Real-time Human-in-the-Loop escrow queue                        |
+-----------------------------------------------------------------------------------+
```

---

## 3. Event Taxonomy & Data Models

### 3.1 Standard Event Schema (`PayguardEvent`)

Every event emitted across the entire application conforms to a unified schema defined in `backend/app/schemas/event.py`:

```python
class PayguardEvent(BaseModel):
    event_id: str                      # Format: evt_<uuid4_hex[:12]>
    event_type: str                    # Dot-delimited: domain.action (e.g. blockchain.tx_confirmed)
    category: EventCategory            # transactions | escrow | security | blockchain | system
    transaction_id: Optional[str]      # Correlated transaction ID if applicable
    timestamp: str                     # RFC-3339 UTC timestamp
    source: str                        # backend | blockchain | agent | policy_engine | smart_contract
    severity: EventSeverity            # INFO | SUCCESS | WARNING | CRITICAL
    payload: Dict[str, Any]            # Sanitized, structured event metadata
```

### 3.2 Event Categories & Event Types

| Category | Typical Events | Description |
| :--- | :--- | :--- |
| `transactions` | `transaction.initiated`, `transaction.evaluated`, `transaction.allowed`, `transaction.blocked` | Full lifecycle of agent payment evaluation |
| `escrow` | `escrow.created`, `escrow.approved`, `escrow.rejected`, `escrow.released`, `escrow.refunded` | Human-in-the-loop timelocked escrow events |
| `security` | `security.threat_detected`, `security.prompt_injection_blocked`, `security.anomaly_flagged` | Threat intelligence and agent defense telemetry |
| `blockchain` | `blockchain.tx_submitted`, `blockchain.tx_confirmed`, `blockchain.tx_failed`, `blockchain.connection_restored` | On-chain NEAR Testnet execution status |
| `system` | `system.welcome`, `system.subscription_updated`, `system.heartbeat`, `system.ready` | WebSocket protocol and health telemetry |

---

## 4. Volume Segregation Architecture

### 4.1 Strict Invariant: On-Chain vs Simulation Separation

A paramount requirement in PAYGUARD is maintaining an uncompromised distinction between:
- **`confirmed_onchain_volume_near`**: Actual NEAR tokens moved or committed to `payguard-vault.testnet` on NEAR Testnet with verified cryptographic receipts.
- **`simulation_volume_near`**: Hypothetical NEAR volume processed in dry-run or mock simulation mode.
- **`pending_escrow_volume_near`**: Active NEAR held inside on-chain smart contract timelock awaiting operator decision.
- **`protected_blocked_volume_near`**: Malicious or unauthorized NEAR value successfully intercepted and prevented from on-chain execution.

The metrics engine in `backend/app/services/monitoring_service.py` computes these metrics through strict SQL queries isolating `is_mock_simulation = 0` and confirmed NEAR transaction hashes.

---

## 5. Security & Sensitive Data Redaction

All events pass through `redact_sensitive_data()` before persistence or broadcast:
- Keys matching `private_key`, `secret_key`, `seed_phrase`, `api_key`, `authorization_token`, `auth_token`, `secret` are replaced with `"[REDACTED]"`.
- Ed25519 private key seed material is strictly confined to memory and never persisted in database logs, event payloads, or WebSocket broadcasts.
- Public keys (`ed25519:...`) and SHA-256 digests remain intact for cryptographic transparency and verifiable evidence verification.

---

## 6. Resilience & Outage Recovery

### 6.1 NEAR RPC Monitoring & Checkpoints
The `BlockchainMonitor` service (`backend/app/services/blockchain_monitor.py`):
1. Polls NEAR Testnet RPC status and latest block height every 10 seconds.
2. Persists the highest scanned block height to the `blockchain_checkpoints` SQLite table.
3. Upon detecting RPC timeout or network unreachable, emits `blockchain.connection_lost` (severity `WARNING`).
4. Upon successful re-connection, emits `blockchain.connection_restored` (severity `INFO`) with recovered block height and latency.
5. Inquiries regarding unconfirmed executing transactions are re-polled via `EXPERIMENTAL_tx_status` or `tx` RPC endpoints to verify final settlement.

### 6.2 WebSocket Resilience
1. **Exponential Backoff Reconnection**: Frontend reconnects starting at 1000ms up to 15000ms.
2. **Heartbeat Protocol**: Active ping/pong every 20 seconds detects dead connections immediately.
3. **Deduplication Buffer**: A 200-event ring buffer ensures replayed or duplicate WebSocket frames are never rendered twice.

