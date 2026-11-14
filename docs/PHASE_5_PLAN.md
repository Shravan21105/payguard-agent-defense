# PAYGUARD — Phase 5 Implementation Plan: Real-Time Monitoring & Event Streaming

**Project:** PAYGUARD (Agent Defense Layer)  
**Track:** AI Security & Defense (SEC) | Agent Economy (AGT)  
**Hackathon:** NEAR Hackathon 2026  
**Status:** Phases 1–4 Completed (51/51 tests passing). Phase 5 Active.  
**Core Invariant:** *AI analyzes. The policy engine enforces. The smart contract protects.*

---

## 1. Repository Audit & Current State Analysis

### A. What is Already Implemented
1. **Phase 1 Deterministic Policy Engine:** Syntactic validator, policy engine, risk calculator, and decision synthesis engine (`ALLOW`, `WARN`, `BLOCK`).
2. **Phase 2 Multi-Agent AI Intelligence:** LangGraph multi-agent orchestrator (Intent, Behavioral, Security Intel, Audit agents), provider-independent LLM gateway with prompt injection sanitizer, and RFC-8785 canonical evidence.
3. **Phase 3 NEAR Smart Contract Vault:** Rust contract (`contracts/payguard-vault/`) with native Ed25519 verification, domain-separated canonical messages, atomic replay protection, and timelock escrow.
4. **Phase 4 End-to-End Blockchain Integration:** Unified `POST /api/transactions/initiate`, 11-stage transaction lifecycle, NearBlocks explorer link generation, SQLite schema migration (29 columns), and 51/51 tests passing.
5. **Basic WebSocket Skeleton:** `backend/app/websocket/manager.py` with elementary `connect`, `disconnect`, `broadcast_json`, and endpoint `@app.websocket("/ws/events")`.
6. **Frontend Dashboard:** React 19 + TypeScript + Vite + Tailwind CSS with 8 pages including `LiveMonitoring.tsx` and basic hook `useWebSocket.ts`.

### B. What Can Be Reused
- `near_rpc_client` in `backend/app/blockchain/near_client.py` for node status, account checks, and tx receipt verification.
- `blockchain_service` in `backend/app/services/blockchain_service.py` for escrow operations and contract calls.
- `db` in `backend/app/db/database.py` connection management, thread locks, and UPSERT patterns.
- Existing endpoint `@app.websocket("/ws/events")` as the canonical WebSocket URL.
- Existing frontend UI component hierarchy (`Badge`, `RiskMeter`, `Modal`, `PolicyPill`).

### C. What is Missing (Phase 5 Gaps)
1. **No Centralized Event Schema:** Events are currently created as ad-hoc dictionaries scattered across `transaction_service.py` and `blockchain_service.py`.
2. **No Event Persistence:** Events are only broadcast over WebSocket in-memory. If a client connects late or reconnects, historical events are lost. There is no `events` table in SQLite.
3. **No Subscription Filtering:** `WebSocketManager` broadcasts all messages to all connections without channel or category filtering (`transactions`, `security`, `blockchain`, `escrow`, `system`).
4. **No Blockchain Event Monitor:** There is no dedicated background loop polling NEAR Testnet for on-chain block receipts, escrow updates, or tracking checkpoints.
5. **No Event Query APIs:** Missing endpoints: `GET /api/events`, `GET /api/events/{id}`, `GET /api/events/transaction/{tx_id}`, `GET /api/events/metrics`.
6. **No Health & Monitoring Service:** Missing `GET /api/monitoring/metrics` with strict separation of SIMULATION vs ONCHAIN volumes, and `GET /api/monitoring/health` with live subsystem probes.
7. **Frontend Gaps:**
   - `useWebSocket.ts` lacks exponential backoff, category subscriptions, ping/pong heartbeats, and event deduplication.
   - `LiveMonitoring.tsx` lacks category filtering, severity filtering, search, event details inspection modal, and a transaction lifecycle visualizer.
   - `Overview.tsx`, `Transactions.tsx`, and `Approvals.tsx` do not update live metrics reactively from WebSocket events.

---

## 2. Architecture Specification

### A. Standardized Event Schema (`PayguardEvent`)

```json
{
  "event_id": "evt_5f1b2c3d4e5f6a7b",
  "event_type": "transaction.confirmed",
  "transaction_id": "tx_pg_8f2c9b4e",
  "timestamp": "2026-11-13T05:30:00.123456Z",
  "source": "near_blockchain",
  "severity": "SUCCESS",
  "category": "blockchain",
  "payload": {
    "tx_hash": "9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b",
    "block_height": 184592031,
    "explorer_url": "https://testnet.nearblocks.io/txns/9cE2vB3kL7uF1yP4wQ9zX8mN5jR2tV6hK1dG3sA5pT7b",
    "amount": 2.5,
    "execution_mode": "ONCHAIN"
  }
}
```

### Supported Event Types:
- **Transaction:** `transaction.received`, `transaction.analyzing`, `transaction.evaluated`, `transaction.allowed`, `transaction.warned`, `transaction.blocked`, `transaction.executing`, `transaction.confirmed`, `transaction.failed`
- **Escrow:** `escrow.created`, `escrow.approved`, `escrow.released`, `escrow.rejected`, `escrow.refunded`
- **AI Security:** `security.anomaly_detected`, `security.prompt_injection_detected`, `security.risk_threshold_exceeded`, `security.policy_violation`
- **Blockchain:** `blockchain.transaction_submitted`, `blockchain.transaction_confirmed`, `blockchain.transaction_failed`, `blockchain.escrow_updated`, `blockchain.connection_lost`, `blockchain.connection_restored`
- **System:** `system.websocket_connected`, `system.websocket_disconnected`, `system.metrics_updated`, `system.health_updated`

---

## 3. Implementation Milestones

### Milestone 1: Audit & Baseline Check (Completed)
- 51/51 existing tests verified passing.
- Frontend build verified clean.
- Gaps identified.

### Milestone 2: Backend Event Infrastructure
- Create `backend/app/schemas/event.py` with `PayguardEvent` model, event categories, and severity levels.
- Add `events` and `blockchain_checkpoints` tables in `backend/app/db/database.py`.
- Implement `save_event`, `list_events`, `get_event`, `get_events_for_transaction`, `get_event_metrics` with indexing and deduplication.
- Enhance `backend/app/websocket/manager.py` to support client tracking, subscription categories, ping/pong heartbeats, and health metrics.
- Create `backend/app/events/publisher.py` (singleton `event_publisher`) with automatic redaction, SQLite persistence, and category-filtered WebSocket broadcasting.
- Refactor `transaction_service.py` and `blockchain_service.py` to route events through `event_publisher`.

### Milestone 3: NEAR Event Monitoring & Checkpoints
- Create `backend/app/services/blockchain_monitor.py`.
- Background task polling NEAR Testnet RPC and contract state with exponential backoff and timeout handling.
- Checkpoint persistence in SQLite: stores `last_block_height` and `last_block_hash`.
- Emits `blockchain.*` events upon receipt confirmation.
- Safe recovery from RPC network interruptions without duplicate events.

### Milestone 4: Live Metrics & Health APIs
- Create `backend/app/services/monitoring_service.py`.
- Strict separation of `SIMULATION` vs `ONCHAIN` metrics (volume, counts, confirmed, pending).
- Implement `GET /api/monitoring/metrics`.
- Implement `GET /api/monitoring/health` with live probes (FastAPI, SQLite, WebSockets, NEAR RPC, Monitor).
- Create routes in `backend/app/api/routes/events.py` for `/api/events/*` and `/api/monitoring/*`.
- Register router in `backend/app/main.py`.

### Milestone 5: Frontend WebSocket Client Service
- Create `frontend/src/services/websocket.ts` with auto-reconnection, backoff, ping/pong, subscription categories, and event deduplication ring buffer.
- Enhance `frontend/src/hooks/useWebSocket.ts` to utilize the robust service.
- Update `frontend/src/types/index.ts` with `PayguardEvent`, event categories, monitoring metrics, and health response types.

### Milestone 6: UI Enhancements
- **`LiveMonitoring.tsx`:** Connection status bar, real-time event feed with category/severity filter pills and search, transaction lifecycle tracker, and event payload inspector modal with secret redaction.
- **`Overview.tsx`:** Reactive metric card updates on WebSocket events without full reload; distinct ONCHAIN vs SIMULATION cards.
- **`Transactions.tsx`:** Live transaction streaming + "Event Lifecycle Timeline" modal tab.
- **`Approvals.tsx`:** Real-time escrow synchronization.

### Milestone 7: Testing & Verification
- Create `backend/tests/test_phase5_realtime.py` with 20+ tests covering all Phase 5 requirements.
- Full regression run: 51 Phase 1-4 tests + Phase 5 tests (all passing).
- Run `cd frontend; npm run build` (0 TypeScript / Vite errors).

### Milestone 8: Documentation Suite
- `docs/PHASE_5_ARCHITECTURE.md`
- `docs/PHASE_5_WEBSOCKET_DOCUMENTATION.md`
- `docs/PHASE_5_BLOCKCHAIN_MONITORING.md`
- `docs/PHASE_5_API_DOCUMENTATION.md`
- `docs/PHASE_5_TEST_REPORT.md`
- Update `docs/PHASE_TRACKER.md` and `README.md`.
- Ensure zero pushes to GitHub.

