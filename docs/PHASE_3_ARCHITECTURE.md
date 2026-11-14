# PAYGUARD — Phase 3: NEAR Smart Contract Vault & On-Chain Enforcement Architecture

## 1. Executive Summary

**Project:** PAYGUARD (Agent Defense Layer)  
**Hackathon:** NEAR Hackathon 2026 (AI Security & Defense [SEC] / Agent Economy [AGT])  
**Central Principle:**  
> **"AI analyzes. The policy engine enforces. The smart contract protects."**

Phase 3 introduces cryptographically verified, on-chain execution protection for autonomous AI agents on NEAR Protocol. While Phase 1 provided deterministic rule enforcement and Phase 2 introduced multi-agent LLM intention auditing, Phase 3 closes the trust loop: transactions evaluated by the off-chain defense pipeline cannot be executed on-chain without an Ed25519 cryptographic authorization token signed by the PAYGUARD security daemon and verified directly inside the NEAR smart contract vault via `near_sdk::env::ed25519_verify`.

---

## 2. End-to-End System Architecture

```
+-----------------------------------------------------------------------------+
|                         Autonomous AI Agent                                 |
|   (Proposes financial payment: sender, recipient, amount, declared intent)  |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                     PAYGUARD Multi-Agent Security Engine                    |
|                                                                             |
|   [ Intent Analysis Agent ] ---> [ Behavioral Risk Agent ]                  |
|               |                             |                               |
|               v                             v                               |
|   [ Security Intelligence ] ----> [ Transaction Audit Agent ]               |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                      Deterministic Policy Engine                            |
|    - Rate limits & velocity checks                                          |
|    - Spending limits & daily caps                                           |
|    - Verified/unverified/blocked counterparty list                          |
|    - Strict invariant: AI outputs never execute directly                    |
+-----------------------------------------------------------------------------+
                                       |
            +--------------------------+--------------------------+
            |                          |                          |
       ALLOW (Score < 30)       WARN (Score 30-69)         BLOCK (Score >= 70)
            |                          |                          |
            v                          v                          v
+-----------------------+  +-----------------------+  +-----------------------+
|  Ed25519 Signer       |  |  Ed25519 Signer       |  | Signature Withheld    |
|  Signs ALLOW payload  |  |  Signs WARN payload   |  | Execution on-chain    |
|  Returns auth token   |  |  for timelock escrow  |  | is mathematically     |
+-----------------------+  +-----------------------+  | impossible            |
            |                          |              +-----------------------+
            v                          v
+-----------------------------------------------------------------------------+
|                   PAYGUARD Vault Smart Contract (Rust / NEAR)               |
|                     Account: `payguard-vault.testnet`                       |
|                                                                             |
|   1. Signature Verification: near_sdk::env::ed25519_verify(sig, msg, pk)    |
|   2. Anti-Replay Engine: Atomic checks on `used_auth_ids` & `used_nonces`   |
|   3. Temporal Window Check: block_timestamp <= expires_at                   |
|   4. Execution Branching:                                                   |
|      - ALLOW: Direct transfer to recipient + refund excess deposit          |
|      - WARN: Deposit held in Timelock Escrow pending human sign-off         |
|      - Human Operator APPROVE: Funds released to recipient                  |
|      - Human Operator REJECT / Timelock Expired: Funds refunded to sender   |
|   5. NEP-297 Standard Event Emitted: `payguard` standard v0.3.0            |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
|                          NEAR Testnet Settlement                            |
|             Receipt confirmed & viewable on NEAR Explorer                   |
|                 https://testnet.nearblocks.io/txns/{hash}                   |
+-----------------------------------------------------------------------------+
```

---

## 3. Cryptographic Authorization Specification

### 3.1 Domain-Separated Canonical Message Format
To prevent cross-contract replay, cross-network spoofing, or parameter tampering, the authorization string follows a strict canonical serialization:

```text
PAYGUARD:v1:<network_id>:<contract_id>:<auth_id>:<sender_id>:<recipient_id>:<amount_yocto>:<decision>:<risk_score>:<policy_version>:<nonce>:<issued_at>:<expires_at>
```

**Field Breakdown:**
- `PAYGUARD:v1`: Domain separator and wire format version.
- `network_id`: Network identifier (`testnet` or `mainnet`).
- `contract_id`: Vault smart contract account ID (e.g. `payguard-vault.testnet`).
- `auth_id`: Unique authorization UUID (e.g. `auth_7c3a01f92e4b`).
- `sender_id`: Authorized agent initiator account (e.g. `agent-01.testnet`).
- `recipient_id`: Approved counterparty account (e.g. `oracle.testnet`).
- `amount_yocto`: Exact transfer amount in yoctoNEAR ($10^{24}$ yoctoNEAR = 1 NEAR).
- `decision`: Upper-case policy decision (`ALLOW`, `WARN`, or `BLOCK`).
- `risk_score`: Calibrated risk score integer ($0 \le \text{risk} \le 100$).
- `policy_version`: Policy engine semantic version (e.g. `1.0.0`).
- `nonce`: Unique incremental nonce preventing transaction ordering manipulation.
- `issued_at`: Issuance timestamp in UTC nanoseconds.
- `expires_at`: Expiration timestamp in UTC nanoseconds (default TTL: 15 minutes).

### 3.2 Signature Verification Scheme
- **Algorithm:** Ed25519 (RFC 8032 / Edwards-curve Digital Signature Algorithm).
- **Public Key Representation:** 32-byte raw public key formatted as `ed25519:<Base58>` on NEAR and 64-character lowercase hexadecimal.
- **Signature Representation:** 64-byte Ed25519 signature encoded as a 128-character hexadecimal string.
- **On-Chain Host Function:** Verified at native WebAssembly speed using NEAR's gas-efficient host function:
  ```rust
  env::ed25519_verify(&sig_bytes, canonical_payload.as_bytes(), &pk_bytes)
  ```

---

## 4. Contract Storage and NEP-297 Events

### 4.1 State Structure
```rust
pub struct PayguardVault {
    pub admin_id: AccountId,
    pub policy_signer_pk: PublicKey,
    pub authorized_approvers: LookupSet<AccountId>,
    pub min_escrow_duration_sec: u64,
    pub max_escrow_duration_sec: u64,
    pub policy_version: String,
    pub is_paused: bool,
    pub used_auth_ids: LookupSet<String>,
    pub used_nonces: LookupSet<u64>,
    pub escrows: UnorderedMap<String, EscrowRecord>,
    pub transactions: UnorderedMap<String, OnChainTransactionRecord>,
    pub total_volume_yocto: U128,
    pub total_transfers_count: u64,
    pub active_escrow_count: u64,
}
```

### 4.2 Standard NEP-297 Events
All state transitions log structured JSON events adhering to NEAR NEP-297:
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "TransferExecuted", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "EscrowCreated", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "EscrowApproved", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "EscrowReleased", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "EscrowRejected", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "TransferBlocked", "data": [...]}`
- `EVENT_JSON: {"standard": "payguard", "version": "0.3.0", "event": "VaultPaused", "data": [...]}`

---

## 5. Security Invariants & Defense Guarantees

| Attack Vector | Defense Mechanism | Enforcement Layer |
| :--- | :--- | :--- |
| **Prompt Injection** | LLM Intent Auditing detects semantic deviation between declared purpose and destination wallet | Off-Chain Agent Engine |
| **Replay Attack** | Vault contract tracks `used_auth_ids` and `used_nonces` in persistent `LookupSet`; re-submissions panic atomically | On-Chain Smart Contract |
| **Signature Forgery** | RFC-8032 Ed25519 cryptographic signature verification with constant-time host function | On-Chain Smart Contract |
| **Parameter Tampering** | Changing amount, sender, or recipient invalidates the canonical string and fails Ed25519 signature check | On-Chain Smart Contract |
| **Cross-Contract Spoofing** | Domain separation prefix embeds `network_id` and contract `current_account_id` directly in the signed bytes | On-Chain Smart Contract |
| **Expired Authorization** | `block_timestamp > expires_at` panics before balance execution | On-Chain Smart Contract |
| **Unauthorized Drain** | Smart contract withholds transfers unless valid Ed25519 signature is provided; daemon never signs BLOCK decisions | Full-Stack Invariant |
| **Unapproved Escrow Release**| Only `admin_id` or accounts registered in `authorized_approvers` can call `approve_escrow` | On-Chain Smart Contract |
| **Emergency Scenario** | Admin can call `pause()` to freeze all transfer and escrow creation operations instantly | On-Chain Smart Contract |

