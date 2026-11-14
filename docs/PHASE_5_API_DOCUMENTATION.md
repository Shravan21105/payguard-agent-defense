# PAYGUARD — PHASE 5: REST & REAL-TIME API SPECIFICATION

## 1. Overview

Phase 5 adds dedicated REST endpoints and WebSocket protocols for live event tracking, event query and pagination, audit timelines, and system-wide monitoring telemetry.

Base URLs:
- REST API: `http://127.0.0.1:8000/api`
- WebSocket: `ws://127.0.0.1:8000/ws/events` or `ws://127.0.0.1:8000/api/ws/events`

---

## 2. Event Endpoints

### 2.1 List Historical Events
`GET /api/events`

Query parameters:
- `limit` (integer, default: 50, max: 200)
- `category` (string, optional: `transactions`, `escrow`, `security`, `blockchain`, `system`)
- `severity` (string, optional: `INFO`, `SUCCESS`, `WARNING`, `CRITICAL`)
- `transaction_id` (string, optional: query events for specific transaction)

**Sample Response (`200 OK`):**
```json
{
  "events": [
    {
      "event_id": "evt_a83c719e5d20",
      "event_type": "blockchain.tx_confirmed",
      "category": "blockchain",
      "transaction_id": "tx_safe_agent_001",
      "timestamp": "2026-11-13T10:45:35.000000Z",
      "source": "blockchain",
      "severity": "SUCCESS",
      "payload": {
        "tx_hash": "6gP7tXq4Z...uW9",
        "block_height": 184592031,
        "contract_id": "payguard-vault.testnet"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### 2.2 Get Event by ID
`GET /api/events/{event_id}`

**Sample Response (`200 OK`):**
Returns single `PayguardEvent` object matching `event_id`. Returns `404 Not Found` if missing.

### 2.3 Get Transaction Lifecycle Events
`GET /api/events/transaction/{transaction_id}`

Returns an array of `PayguardEvent` objects sorted chronologically by timestamp, documenting the step-by-step lifecycle of the transaction from initiation, multi-agent evaluation, deterministic check, signature generation, to NEAR Testnet confirmation.

### 2.4 Get Event Metrics & Throughput
`GET /api/events/metrics`

**Sample Response (`200 OK`):**
```json
{
  "total_events": 1420,
  "events_by_category": {
    "transactions": 850,
    "security": 210,
    "blockchain": 230,
    "escrow": 80,
    "system": 50
  },
  "events_by_severity": {
    "INFO": 920,
    "SUCCESS": 230,
    "WARNING": 80,
    "CRITICAL": 190
  },
  "active_websocket_connections": 2,
  "total_broadcasts": 1420
}
```

---

## 3. Monitoring & Telemetry Endpoints

### 3.1 Get Aggregated Monitoring Metrics
`GET /api/monitoring/metrics`

Returns strict segregated volume statistics, decision distributions, and throughput indicators.

**Sample Response (`200 OK`):**
```json
{
  "total_transactions": 254,
  "allowed_count": 190,
  "warn_count": 28,
  "blocked_count": 36,
  "confirmed_onchain_volume_near": 342.50,
  "simulation_volume_near": 128.75,
  "pending_escrow_volume_near": 45.00,
  "protected_blocked_volume_near": 980.20,
  "average_risk_score": 18.4,
  "average_latency_ms": 14.2
}
```

### 3.2 Get Infrastructure Health Status
`GET /api/monitoring/health`

Deeply probes all core subsystem components and returns operational state.

**Sample Response (`200 OK`):**
```json
{
  "status": "HEALTHY",
  "backend_version": "2.0.0",
  "database": {
    "status": "HEALTHY",
    "table_count": 8,
    "database_file": "backend/payguard.db"
  },
  "websocket": {
    "status": "HEALTHY",
    "active_connections": 2,
    "total_broadcasts": 1420
  },
  "near_rpc": {
    "status": "CONNECTED",
    "network": "testnet",
    "endpoint": "https://rpc.testnet.near.org",
    "latest_block_height": 184592140
  },
  "smart_contract": {
    "contract_id": "payguard-vault.testnet",
    "signer_public_key": "ed25519:64D81c3Nvyi78aR...",
    "status": "DEPLOYED_AND_ACTIVE"
  },
  "blockchain_monitor": {
    "status": "RUNNING",
    "last_checkpoint_block": 184592140
  }
}
```

