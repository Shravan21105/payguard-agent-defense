# PAYGUARD Vault Smart Contract Developer Guide

This document describes the interface, internal operations, and verification patterns of the PAYGUARD Vault contract developed in Rust using `near-sdk v5.5.0`.

**Contract Location:** `contracts/payguard-vault/`  
**Compiled Artifact:** `target/wasm32-unknown-unknown/release/payguard_vault.wasm`

---

## 1. Public Contract Interface

### Initialization
```rust
#[init]
pub fn init(
    admin_id: AccountId,
    policy_signer_pk: PublicKey,
    approvers: Vec<AccountId>,
    min_escrow_sec: Option<u64>,
    max_escrow_sec: Option<u64>,
    policy_version: Option<String>,
) -> Self;
```
- Initializes the vault. Can only be invoked once upon deployment.
- Sets the authorized Ed25519 public key corresponding to the off-chain PAYGUARD daemon.
- Configures default human approvers and timelock boundaries.

---

### Core Execution Methods

#### `execute_transfer`
```rust
#[payable]
pub fn execute_transfer(
    &mut self,
    auth: PolicyAuthorization,
    signature: String,
) -> OnChainTransactionRecord;
```
- **Prerequisites:**
  1. Contract is not paused.
  2. `auth.decision == DecisionType::Allow`.
  3. `env::block_timestamp() <= auth.expires_at`.
  4. `auth.contract_id == env::current_account_id()`.
  5. `auth.policy_version == self.policy_version`.
  6. Attached deposit $\ge$ authorized transfer amount in yoctoNEAR.
  7. Neither `auth.auth_id` nor `auth.nonce` have been consumed previously.
  8. Ed25519 signature over canonical payload verifies against `self.policy_signer_pk`.
- **Effects:**
  - Atomically marks `auth.auth_id` and `auth.nonce` as consumed.
  - Transfers authorized amount to `auth.recipient_id`.
  - Refunds any excess deposit back to `auth.sender_id`.
  - Emits `TransferExecuted` NEP-297 event.
  - Records and returns immutable `OnChainTransactionRecord`.

---

#### `create_escrow`
```rust
#[payable]
pub fn create_escrow(
    &mut self,
    auth: PolicyAuthorization,
    signature: String,
    timelock_seconds: Option<u64>,
) -> EscrowRecord;
```
- **Prerequisites:**
  1. Contract is not paused.
  2. `auth.decision == DecisionType::Warn`.
  3. `timelock_seconds` falls between `min_escrow_duration_sec` and `max_escrow_duration_sec`.
  4. Attached deposit $\ge$ authorized transfer amount.
  5. Ed25519 signature verifies.
- **Effects:**
  - Holds transfer amount inside the contract.
  - Creates an escrow record with status `PENDING_APPROVAL`.
  - Emits `EscrowCreated` NEP-297 event.

---

#### `approve_escrow`
```rust
pub fn approve_escrow(
    &mut self,
    escrow_id: String,
    reason: Option<String>,
) -> EscrowRecord;
```
- **Caller Restriction:** Must be `admin_id` or present in `authorized_approvers`.
- **Effects:**
  - Sets escrow status to `Released`.
  - Releases escrowed funds to `recipient_id`.
  - Emits `EscrowApproved` and `EscrowReleased` NEP-297 events.

---

#### `reject_escrow`
```rust
pub fn reject_escrow(
    &mut self,
    escrow_id: String,
    reason: Option<String>,
) -> EscrowRecord;
```
- **Caller Restriction:** Must be an authorized approver, OR the original `sender_id` after `timelock_until` has passed.
- **Effects:**
  - Sets escrow status to `Refunded`.
  - Refunds all escrowed funds back to `sender_id`.
  - Emits `EscrowRejected` NEP-297 event.

---

### View Methods (Read-Only)

| Method | Parameters | Return Type | Description |
| :--- | :--- | :--- | :--- |
| `get_config` | None | `VaultConfigView` | Returns admin, signer PK, pause state, and totals |
| `get_escrow` | `escrow_id: String` | `Option<EscrowRecord>` | Returns specific escrow details |
| `list_escrows` | `from_index: Option<u64>, limit: Option<u64>` | `Vec<EscrowRecord>` | Paginated listing of escrows |
| `get_transaction` | `auth_id: String` | `Option<OnChainTransactionRecord>` | Returns specific transaction record |
| `list_transactions` | `from_index: Option<u64>, limit: Option<u64>` | `Vec<OnChainTransactionRecord>` | Paginated listing of transactions |
| `is_auth_used` | `auth_id: String` | `bool` | Anti-replay check for authorization UUID |
| `is_nonce_used` | `nonce: u64` | `bool` | Anti-replay check for sequence nonce |

---

## 2. Admin Control Methods

Only the configured `admin_id` can invoke these methods:
- `pause()`: Freezes execution and escrow creation immediately.
- `unpause()`: Restores regular operation.
- `update_policy_signer(new_signer_pk: PublicKey)`: Rotates the authorized Ed25519 key.
- `add_approver(account_id: AccountId)`: Grants human operator authorization.
- `remove_approver(account_id: AccountId)`: Revokes human operator authorization.

