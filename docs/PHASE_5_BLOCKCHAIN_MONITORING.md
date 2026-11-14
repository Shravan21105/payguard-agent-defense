# PAYGUARD — PHASE 5: BLOCKCHAIN MONITORING & NEAR SYNCHRONIZATION SPECIFICATION

## 1. System Role

The **Blockchain Monitor** is a dedicated background service within the PAYGUARD architecture responsible for continuously checking NEAR Testnet status, validating transaction execution receipts, tracking smart contract block heights, and ensuring zero data loss across RPC network disturbances.

---

## 2. Monitor Lifecycle & Operation

### 2.1 Polling Loop (`BlockchainMonitor`)
1. **Cadence**: Executes an asynchronous non-blocking polling cycle every 10 seconds.
2. **Target RPC Endpoints**:
   - `https://rpc.testnet.near.org`
   - Configurable fallback endpoints via environment variables.
3. **Execution Pipeline**:
   - Query node status (`/status` or JSON-RPC `status` method).
   - Extract `latest_block_height` and node latency.
   - Persist state checkpoint to `blockchain_checkpoints` table in SQLite.
   - Scan for transactions marked `PENDING` or executing on-chain.
   - Query transaction finality status via `EXPERIMENTAL_tx_status`.
   - Upon confirmation, transition transaction status to `CONFIRMED` and emit `blockchain.tx_confirmed`.
   - Upon rejection or smart contract error, transition to `FAILED` and emit `blockchain.tx_failed`.

---

## 3. Resilience & Outage Handling

### 3.1 Network Disruption Detection
- If 3 consecutive RPC requests fail or exceed timeout thresholds (5000ms):
  - Mark blockchain monitor state as `DEGRADED` or `OFFLINE`.
  - Emit event `blockchain.connection_lost` with severity `WARNING`.
  - Frontend status indicator in `LiveMonitoring.tsx` immediately reflects disconnected state with yellow/red badge.

### 3.2 Network Restoration & Checkpoint Resumption
- Upon RPC connectivity restoration:
  - Fetch latest block height from NEAR Testnet.
  - Compare with highest block checkpoint recorded in `blockchain_checkpoints`.
  - Calculate missed block span.
  - Emit `blockchain.connection_restored` with severity `INFO`, documenting downtime duration and blocks synchronized.
  - Re-verify any pending transaction receipts initiated during the degraded interval.

---

## 4. Checkpoint Persistence Schema

Checkpoints are stored in the `blockchain_checkpoints` SQLite table:

```sql
CREATE TABLE IF NOT EXISTS blockchain_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    last_block_height INTEGER NOT NULL,
    last_block_hash TEXT,
    updated_at TEXT NOT NULL
);
```

Whenever the monitor observes a newer block, it atomically updates the checkpoint record. Upon backend restart, the monitor inspects this record to ensure continuity.

---

## 5. Smart Contract Events & Receipt Verification

For all transactions authorized by the Ed25519 `PolicySigner`, PAYGUARD validates the on-chain execution receipt:
1. Receipt hash must match the transaction hash emitted by the NEAR JSON-RPC response.
2. The executing contract must be `payguard-vault.testnet`.
3. Execution outcomes must have status `SuccessValue` or empty success string (no `Failure` or execution panics).
4. Emitted NEP-297 events (`EVENT_JSON:{"standard":"nep297","version":"1.0.0","event":"direct_transfer_executed",...}`) are parsed and recorded.

---

## 6. Distinguishing Application vs Blockchain Events

A strict tenet of PAYGUARD:
- **Application Evaluation Event (`transaction.evaluated`)**: Signifies internal deterministic policy and AI audit approval. **This is not proof of on-chain fund movement.**
- **Authorization Signed Event (`authorization.signed`)**: Signifies an Ed25519 cryptographic token was generated.
- **Blockchain Confirmed Event (`blockchain.tx_confirmed`)**: Signifies that the NEAR Testnet RPC returned an immutable receipt hash and verified block inclusion. Only at this point is the transaction marked `CONFIRMED` in the dashboard.

