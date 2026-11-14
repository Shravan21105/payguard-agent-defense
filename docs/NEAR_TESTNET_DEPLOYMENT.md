# PAYGUARD — NEAR Testnet Deployment & Operations Guide

This guide provides step-by-step instructions for deploying and interacting with the PAYGUARD Vault contract on NEAR Testnet.

---

## 1. Prerequisites

1. **Rust Toolchain:**
   - `rustc 1.80+` with target `wasm32-unknown-unknown`.
2. **NEAR CLI:**
   - Recommended: `cargo install near-cli-rs` or `npm install -g near-cli`.
3. **NEAR Testnet Account:**
   - Create a testnet account at [testnet.mynearwallet.com](https://testnet.mynearwallet.com) or using `near create-account`.
   - Ensure the account has at least 10–20 testnet NEAR for storage and deployment deposits.

---

## 2. Compiling the Smart Contract

Run from the repository root:

```powershell
cd contracts/payguard-vault
cargo build --target wasm32-unknown-unknown --release
```

The optimized WebAssembly binary will be generated at:
```text
contracts/payguard-vault/target/wasm32-unknown-unknown/release/payguard_vault.wasm
```

---

## 3. Deploying to NEAR Testnet

### Step 1: Login or Import Credentials
```bash
near login
```
or import an existing private key:
```bash
near account import-account using-private-key <PRIVATE_KEY> --account-id payguard-vault.testnet --network-id testnet
```

### Step 2: Deploy Contract Binary
```bash
near contract deploy payguard-vault.testnet \
  use-file contracts/payguard-vault/target/wasm32-unknown-unknown/release/payguard_vault.wasm \
  without-init-call \
  network-config testnet \
  sign-as payguard-vault.testnet
```

### Step 3: Initialize Contract
Retrieve the Ed25519 public key of your PAYGUARD backend daemon from `/api/blockchain/status` (e.g. `ed25519:Bkikb9xsUsYYsTFYQ1KXxgSFJT1vbGSCGE1z4WnDjcFH`).

```bash
near contract call-function as-transaction payguard-vault.testnet init \
  json-args '{
    "admin_id": "payguard-admin.testnet",
    "policy_signer_pk": "ed25519:Bkikb9xsUsYYsTFYQ1KXxgSFJT1vbGSCGE1z4WnDjcFH",
    "approvers": ["human-supervisor.testnet"],
    "min_escrow_sec": 60,
    "max_escrow_sec": 604800,
    "policy_version": "1.0.0"
  }' \
  prepaid-gas '100.0 Tgas' \
  attached-deposit '0 NEAR' \
  sign-as payguard-admin.testnet \
  network-config testnet
```

---

## 4. Operational Verification

### Check Contract Configuration
```bash
near contract call-function as-read-only payguard-vault.testnet get_config \
  text-args '' \
  network-config testnet
```

### Execute Verified Transfer (via Agent Authorization)
```bash
near contract call-function as-transaction payguard-vault.testnet execute_transfer \
  json-args '{
    "auth": {
      "auth_id": "auth_sample123",
      "sender_id": "agent-01.testnet",
      "recipient_id": "oracle.testnet",
      "amount": "1000000000000000000000000",
      "decision": "Allow",
      "risk_score": 10,
      "policy_version": "1.0.0",
      "nonce": 1,
      "issued_at": 1700000000000000000,
      "expires_at": 1800000000000000000,
      "network_id": "testnet",
      "contract_id": "payguard-vault.testnet"
    },
    "signature": "<128_HEX_CHARS_FROM_PAYGUARD_BACKEND>"
  }' \
  prepaid-gas '100.0 Tgas' \
  attached-deposit '1 NEAR' \
  sign-as agent-01.testnet \
  network-config testnet
```

### View on NEAR Explorer
Inspect the verified receipt and NEP-297 event on [NearBlocks Testnet Explorer](https://testnet.nearblocks.io).

