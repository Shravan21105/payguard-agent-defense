# PAYGUARD — Test Architecture & Verification Runbook
## Comprehensive Test Suites, Adversarial Scenarios, and Baseline Execution Results

**Project:** PAYGUARD — Autonomous Agent Financial Defense Layer  
**Test Suite Coverage:** 129 Backend Pytest Cases | Rust Smart Contract WASM | Frontend Strict TypeScript & Oxlint  
**Baseline Result:** 100% Passing (129/129 Python tests passed in 62.65s)

---

## 1. Testing Philosophy & Separation of Concerns

PAYGUARD adheres to a zero-compromise testing philosophy:
1. **Deterministic Supremacy:** Policy rules must be 100% deterministic functions. Given identical inputs and policy states, tests must assert identical verdicts.
2. **Adversarial Resilience:** The system is explicitly tested against prompt injection, role hijacking, signature tampering, replay attacks, parameter manipulation, and race conditions.
3. **No Mocks for Critical Policy Logic:** Deterministic policy checks, risk calculations, Ed25519 signing, and RFC-8785 canonical hashing run against real algorithmic implementations. Network-dependent NEAR RPC calls and remote LLM providers feature verified mock fallbacks for hermetic local testing.

---

## 2. Test Suite Organization

```
backend/tests/
├── test_api_endpoints.py               # Core REST API endpoints (Health, Policies, Tx CRUD, Metrics)
├── test_policy_engine.py                # Deterministic rule checks (Limits, Allowlist, Blocklist, Duplicates)
├── test_phase2_multiagent.py            # LangGraph multi-agent orchestration, intent audit, prompt injection
├── test_phase3_blockchain.py            # Ed25519 policy signer, canonical hashes, escrow lifecycle, nonces
├── test_phase4_end_to_end.py            # Full lifecycle: Safe transfer, dry-run, blocked threat, escrow approval
├── test_phase5_realtime.py              # WebSocket hub, broadcast channels, client subscription, deduplication
├── test_phase6_ai_intelligence.py       # Behavioral anomaly profiling, LLM outage fallback, explainability
├── test_phase7_security_hardening.py    # 20 adversarial security tests (tampering, TOCTOU, Unicode evasion)
└── test_phase9_signing_safety.py        # 9 production Ed25519 key safety, startup guards, and rotation tests
```

---

## 3. Detailed Test Module Breakdown

### Module 1: Deterministic Policy Engine (`test_policy_engine.py`)
- `test_valid_transaction_allowed`: Clean transaction under limits passes with `ALLOW` and 0 risk score.
- `test_trusted_recipient_low_risk`: Whitelisted ecosystem nodes receive zero-risk classification.
- `test_unknown_recipient_triggers_warn`: Unverified counterparties trigger `WARN` with escrow requirement.
- `test_blocked_recipient_triggers_hard_block`: Known malicious actors trigger immutable `BLOCK`.
- `test_spending_limit_exceeded_triggers_block`: Transfers above maximum single-tx limit trigger hard block.
- `test_daily_limit_exceeded_triggers_block`: Cumulative 24h spending above threshold triggers block.
- `test_duplicate_transaction_triggers_block`: Identical transactions within 120s sliding window trigger block.
- `test_determinism_identical_inputs_produce_identical_outputs`: Proves mathematical repeatability.

### Module 2: Multi-Agent Intelligence (`test_phase2_multiagent.py` & `test_phase6_ai_intelligence.py`)
- `test_safe_transaction_multiagent`: Verifies consensus between Intent, Behavioral, and Audit agents.
- `test_malicious_recipient_intercepted`: Threat Intelligence agent detects stealth blocklist aliases.
- `test_intent_recipient_mismatch`: Detects discrepancies between natural language intent and recipient parameter.
- `test_prompt_injection_defense`: Intercepts direct prompt injection attacks attempting to drain balances.
- `test_behavioral_anomaly_detection`: Isolation Forest identifies velocity outliers and abnormal burst patterns.
- `test_llm_provider_timeout_and_outage_fallback`: Graceful fallback to deterministic NLP during provider timeouts.
- `test_ai_failure_not_becoming_automatic_allow`: Verifies fail-safe principle: an AI failure never causes an accidental `ALLOW`.

### Module 3: Cryptographic Authorization & Blockchain (`test_phase3_blockchain.py`)
- `test_policy_signer_initialization_and_keys`: Verifies Ed25519 keypair generation and public key formatting.
- `test_yocto_conversion`: Precision verification for NEAR to yoctoNEAR (10^24) conversions.
- `test_policy_signer_canonical_message_and_signature`: Asserts RFC-8785 JSON canonicalization.
- `test_blockchain_execute_and_replay_protection`: Verifies nonce uniqueness and replay prevention.
- `test_blockchain_escrow_lifecycle`: Full cycle of `WARN` -> Escrow Creation -> Operator Approval -> Vault Release.
- `test_blockchain_escrow_rejection`: Full cycle of `WARN` -> Escrow Creation -> Operator Rejection -> Vault Refund.

### Module 4: Adversarial Security Hardening (`test_phase7_security_hardening.py`)
- `test_tampered_signature_rejection`: Corrupting a single bit of the Ed25519 signature triggers immediate rejection.
- `test_tampered_canonical_payload_rejection`: Altering payload amounts or recipients invalidates the signature.
- `test_expired_authorization_token_rejected`: Tokens past expiration window are rejected.
- `test_replay_attack_prevention_on_execution`: Re-submitting identical authorization tokens is blocked by nonce cache.
- `test_zero_and_negative_amount_rejection`: Fuzzes zero, negative, NaN, and infinity values.
- `test_self_transfer_rejection`: Prevents circular loop drains where sender equals recipient.
- `test_recipient_unicode_and_zero_width_sanitization`: Strips zero-width spaces (`\u200B`, `\uFEFF`) and homoglyphs.
- `test_toctou_daily_limit_race_condition_prevention`: Concurrent transaction requests cannot bypass the daily limit.
- `test_api_security_headers_and_payload_size_enforcement`: Asserts 1MB payload ceiling and secure HTTP headers.

### Module 5: Production Ed25519 Signing Key Safety (`test_phase9_signing_safety.py`)
- `test_production_startup_without_signing_key_fails`: Prohibits ephemeral fallback keys when `ENVIRONMENT=production`.
- `test_production_startup_with_valid_hex_key`: Validates 64-character hex Ed25519 private key parsing.
- `test_production_startup_with_valid_base58_key`: Validates 32-byte Base58 (NEAR standard) secret key parsing.
- `test_invalid_key_format_fails_in_production`: Rejects malformed or corrupted key strings with clear exceptions.
- `test_public_private_key_mismatch_fails`: Ensures configured `POLICY_SIGNER_PUBLIC_KEY` matches derived private key.
- `test_signing_and_verification_compatibility`: Cryptographically verifies generated signature against on-chain public key.
- `test_key_rotation`: Confirms atomic in-memory signer rotation without service downtime.
- `test_development_mode_identifies_ephemeral_key`: Confirms dev mode explicitly tags generated keys with `is_ephemeral=True`.
- `test_block_decision_never_receives_executable_authorization_signature`: Invariant check that BLOCK never receives valid auth payload.

---

## 4. Execution Commands & Automated Validation

### A. Run Full Backend Test Suite
```bash
# Run all 129 tests with verbose output
backend/venv/Scripts/pytest -v --tb=short backend/tests

# Run only Phase 9 signing safety tests
backend/venv/Scripts/pytest -v backend/tests/test_phase9_signing_safety.py

# Run with test coverage report
backend/venv/Scripts/pytest --cov=backend/app --cov-report=term-missing backend/tests
```

### B. Smart Contract WASM Build Verification
```bash
cargo build --target wasm32-unknown-unknown --release --manifest-path contracts/payguard-vault/Cargo.toml
```

### C. Frontend Linter & Strict TypeScript Verification
```bash
cd frontend
npm run lint
npm run build
```

---

## 5. Actual Baseline Execution Results (Verified)

### Backend Pytest Output Summary
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.4.2, pluggy-1.7.0
rootdir: C:\VII Sem Projects\NEAR-HACKATHON\PAYGUARD
collected 129 items

backend/tests/test_api_endpoints.py::test_health_endpoint PASSED         [  0%]
backend/tests/test_api_endpoints.py::test_analyze_transaction_allowed PASSED [  1%]
...
backend/tests/test_phase7_security_hardening.py::test_api_security_headers_and_payload_size_enforcement PASSED [ 89%]
backend/tests/test_phase9_signing_safety.py::test_production_startup_without_signing_key_fails PASSED [ 90%]
backend/tests/test_phase9_signing_safety.py::test_production_startup_with_valid_hex_key PASSED [ 91%]
backend/tests/test_phase9_signing_safety.py::test_production_startup_with_valid_base58_key PASSED [ 92%]
backend/tests/test_phase9_signing_safety.py::test_invalid_key_format_fails_in_production PASSED [ 93%]
backend/tests/test_phase9_signing_safety.py::test_public_private_key_mismatch_fails PASSED [ 94%]
backend/tests/test_phase9_signing_safety.py::test_signing_and_verification_compatibility PASSED [ 95%]
backend/tests/test_phase9_signing_safety.py::test_key_rotation PASSED    [ 96%]
backend/tests/test_phase9_signing_safety.py::test_development_mode_identifies_ephemeral_key PASSED [ 97%]
backend/tests/test_phase9_signing_safety.py::test_block_decision_never_receives_executable_authorization_signature PASSED [ 98%]
backend/tests/test_policy_engine.py::test_determinism_identical_inputs_produce_identical_outputs PASSED [100%]

======================= 129 passed, 1 warning in 62.65s =======================
```

### Frontend Build Output Summary (Code-Split & Optimized)
```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.6 building client environment for production...
transforming...
✓ 2529 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     1.33 kB │ gzip:   0.69 kB
dist/assets/index-DkH8eB5R.css    100.24 kB │ gzip:  13.97 kB
dist/assets/vendor-icons-B2yR474F.js 17.52 kB │ gzip:   5.64 kB
dist/assets/vendor-REACT-Dffy29Gf.js 241.31 kB │ gzip:  78.42 kB
dist/assets/vendor-charts-By_k289e.js 257.65 kB │ gzip:  79.20 kB
dist/assets/vendor-D8z0QoO8.js    227.14 kB │ gzip:  71.95 kB
dist/assets/Overview-D2k98gqX.js   45.18 kB │ gzip:  11.23 kB
... [all chunks under 300 kB - 0 build warnings]
✓ built in 2.41s
```
rendering chunks...
computing gzip size...
dist/index.html                   1.32 kB │ gzip:   0.69 kB
dist/assets/index-DJvNN00h.css  100.24 kB │ gzip:  13.97 kB
dist/assets/index-DKXrt__y.js   955.80 kB │ gzip: 266.18 kB
✓ built in 3.06s
```

### Contract WASM Output Summary
```
    Finished `release` profile [optimized] target(s) in 10.15s
    Artifact: contracts/payguard-vault/target/wasm32-unknown-unknown/release/payguard_vault.wasm (354,034 bytes)
```

