# PAYGUARD — Hackathon Submission Dossier Index
## Complete Evaluation Package for the NEAR Hackathon 2026

**Project:** PAYGUARD — Autonomous Agent Financial Defense Layer  
**Tracks:** AI Security & Defense (SEC) | Agent Economy (AGT)  
**Submission Version:** `v1.0.0-hackathon`  
**Core Invariant:** *"AI analyzes. The policy engine enforces. The smart contract protects."*

---

## 1. Submission Dossier Navigation

This folder contains the complete, verified submission deliverables for technical judges, security auditors, and hackathon reviewers:

| Document | Purpose & Summary |
| :--- | :--- |
| [**PROJECT_DESCRIPTION.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/PROJECT_DESCRIPTION.md) | Standardized pitches (Short, Standard, Detailed Technical), problem statement, innovation, NEAR integration, and roadmap. |
| [**TECHNICAL_ARCHITECTURE.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/TECHNICAL_ARCHITECTURE.md) | In-depth architectural specification containing all 6 Mermaid diagrams (System, Multi-Agent, Lifecycle, Cryptographic Auth, Escrow Flow, SOC Telemetry). |
| [**DEMO_SCRIPT.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/DEMO_SCRIPT.md) | Step-by-step operator runbook for DEMO 1 (ALLOW), DEMO 2 (WARN), and DEMO 3 (BLOCK), fallback procedures, and spoken presentation scripts (30s elevator to 5-minute live demo). |
| [**JUDGE_QA.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/JUDGE_QA.md) | 42 comprehensive technical and conceptual questions with concise answers, deeper explanations, and practical codebase examples across 7 categories. |
| [**SECURITY_SUMMARY.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/SECURITY_SUMMARY.md) | Threat model, STRIDE analysis, prompt injection defense, TOCTOU prevention, replay windows, and production secret management. |
| [**TEST_RESULTS.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/TEST_RESULTS.md) | Exact automated test outputs: 129/129 backend Pytest tests (100%), 354KB compiled Rust smart contract WASM, 2.23s frontend code-split build, and zero-vulnerability supply chain audit. |
| [**PRESENTATION_OUTLINE.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/PRESENTATION_OUTLINE.md) | 12-slide executive pitch deck structure with visual design specifications, slide-by-slide notes, and speaker cues. |
| [**RELEASE_CHECKLIST.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/RELEASE_CHECKLIST.md) | Pre-flight secret hygiene verification, release notes, suggested GitHub tags, and developer publication commands. |
| [**FINAL_READINESS_AUDIT.md**](file:///c:/VII%20Sem%20Projects/NEAR-HACKATHON/PAYGUARD/submission/FINAL_READINESS_AUDIT.md) | Comprehensive evidence-based readiness audit, Testnet verification results, and publication readiness verdict. |

---

## 2. Quick Evaluation Guide for Judges

1. **Verify Backend Health & Telemetry:**
   ```bash
   curl http://127.0.0.1:8000/api/health
   curl http://127.0.0.1:8000/api/security/metrics
   ```
2. **Access Security Operations Center (SOC) Dashboard:**
   Open [http://localhost:5173](http://localhost:5173) in your browser.
   - Test presets in **Overview** (Safe Transfer, Unknown Recipient, Blocked Malicious).
   - Toggle between **Dark** and **Light** themes in the navigation bar.
   - Inspect live agent consensus in **AI Security**.
   - Review pending escrows in **Approvals**.
3. **Execute Full Automated Regression Suite:**
   ```bash
   backend/venv/Scripts/python.exe -m pytest backend/tests -v
   ```
   *Expected Result: 129 passed in ~62s.*
4. **Inspect Compiled Rust Smart Contract:**
   ```bash
   cargo build --target wasm32-unknown-unknown --release --manifest-path contracts/payguard-vault/Cargo.toml
   ```
   *Output: 354KB `payguard_vault.wasm` in `contracts/payguard-vault/target/wasm32-unknown-unknown/release/`.*

