# PAYGUARD Vault — Smart Contract Architecture (Phase 2+ Design)

## Overview

The `payguard-vault` smart contract will act as the decentralized, on-chain execution barrier on NEAR Protocol.

```
+-------------------------------------------------------------------+
| Autonomous AI Agent                                               |
+-------------------------------------------------------------------+
                                  │
                                  ▼
+-------------------------------------------------------------------+
| PAYGUARD Off-Chain Security Engine (FastAPI + Deterministic Rules)|
+-------------------------------------------------------------------+
                                  │ (Signed Intent / Policy Proof)
                                  ▼
+-------------------------------------------------------------------+
| NEAR Smart Contract (payguard-vault.testnet)                      |
| - Validates Operator Signature & Policy Nonce                     |
| - Checks Vault Daily Thresholds On-Chain                          |
| - Releases Escrowed NEAR to Verified Recipient                    |
+-------------------------------------------------------------------+
```

## Core Security Invariant

**AI analyzes. The policy engine enforces. The smart contract protects.**

Autonomous AI agents NEVER hold direct private keys to unconstrained vault funds. Instead:
1. Funds are locked in `payguard-vault.testnet`.
2. Agent payment requests require approval by PAYGUARD's deterministic policy engine.
3. Upon ALLOW verdict (or manual human-in-the-loop sign-off for WARN), a cryptographic authorization token is generated.
4. The smart contract verifies the authorization token, executes the transfer, and emits an immutable event.
5. In Phase 1, all contract interactions are simulated within the local deterministic security engine.

## Status

- **Phase 1 (Current):** Interface specification, security invariants, simulated execution models.
- **Phase 2 (Upcoming):** Rust `near-sdk` contract implementation, testnet deployment, multi-signature timelock.

