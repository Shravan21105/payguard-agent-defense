# PAYGUARD — Intelligent Security Infrastructure for Autonomous AI Agents

> **NEAR Hackathon 2026**  
> **Primary Track:** AI Security & Defense (SEC)  
> **Secondary Track:** Agent Economy (AGT)

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.11.9-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![React](https://img.shields.io/badge/React-19-61DAFB.svg)
![NEAR](https://img.shields.io/badge/NEAR-Testnet-black.svg)
![Security](https://img.shields.io/badge/Security-Deterministic%20Defense-emerald.svg)

---

## 1. Executive Summary

Autonomous AI agents are increasingly entrusted with financial capabilities, such as paying for computation, querying decentralized oracles, and rebalancing liquidity on blockchain networks like NEAR. However, granting unconstrained wallet private keys to autonomous LLMs creates severe vulnerabilities:

- **Adversarial Prompt Injection:** Attackers manipulating agents into executing unauthorized drain transfers.
- **Rogue / Malicious Counterparties:** Agents interacting with unverified or phishing contracts.
- **Infinite Spending Loops:** Agent runtime bugs triggering rapid successive token transfers.
- **Duplicate / Replay Exploits:** Replaying transactions to deplete agent vault balances.
- **Excessive Resource Allocation:** Agents exceeding intended budgetary limits.

### The PAYGUARD Solution

PAYGUARD introduces a deterministic, intelligent security layer positioned directly between autonomous AI agents and blockchain execution layers.

### The Core Security Principle:

$$\text{\textbf{AI analyzes.}} \quad \longrightarrow \quad \text{\textbf{The policy engine enforces.}} \quad \longrightarrow \quad \text{\textbf{The smart contract protects.}}$$

> **Important Security Invariant:** AI models and risk heuristics provide explainable threat telemetry, but an AI recommendation can **never** independently authorize or execute a payment, nor can it override a deterministic policy **BLOCK**.

---

## 2. Architecture & Decision Hierarchy

```
+--------------------------------------------------------------------------+
|                        AUTONOMOUS AI AGENT LAYER                         |
+--------------------------------------------------------------------------+
                                     │
                     HTTP POST /api/transactions/analyze
                                     ▼
+--------------------------------------------------------------------------+
|                       PAYGUARD SECURITY BACKEND                          |
|                                                                          |
|  • TransactionValidator: Structural and address sanity verification      |
|  • PolicyEngine: Deterministic security rules                            |
|     ├── Per-transaction spending ceiling (e.g. 50 NEAR)                  |
|     ├── Rolling 24-hour cumulative limit (e.g. 200 NEAR)                 |
|     ├── Counterparty blocklist & trusted list checking                   |
|     ├── Duplicate transaction detection within 120s window               |
|     └── Frequency / velocity burst protection (>10 tx/min)               |
|  • RiskCalculator: Heuristic additive 0-100 explainable risk scoring     |
|  • DecisionEngine: Synthesizes final verdict                             |
|  • BehaviouralAnomalyDetector: Baseline Scikit-learn Isolation Forest    |
|  • WebSocket Broadcast: Real-time event streaming                       |
+--------------------------------------------------------------------------+
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
      [ALLOW]                     [WARN]                      [BLOCK]
Passed all policies &        Elevated risk score /       Violates hard policy /
low risk (<30). Safe to      unverified counterparty.   blocked address / exploit.
execute on-chain.            Requires human sign-off.    IRREVOCABLY HALTED.
```

---

## 3. Technology Stack

- **Backend:**
  - Python 3.11.9
  - FastAPI
  - Uvicorn (ASGI)
  - Pydantic v2 & Pydantic Settings
  - WebSockets (Real-time telemetry)
  - Pytest (20/20 Passing unit & integration tests)
  - HTTPX
- **AI & Machine Learning:**
  - Scikit-learn (Isolation Forest baseline anomaly detection)
  - NumPy & Pandas
  - Rule-based explainable risk calculation
- **Frontend:**
  - React 19 + TypeScript
  - Vite 8
  - Tailwind CSS (Cybersecurity Fintech SaaS dark theme)
  - Recharts (Interactive telemetry and volume graphs)
  - Lucide React
  - Axios
- **Blockchain (Future Phases):**
  - NEAR Protocol Testnet
  - Rust `near-sdk` vault contract (`contracts/payguard-vault/`)

---

## 4. Project Structure

```
PAYGUARD/
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── components/
│   │   │   └── common/
│   │   │       ├── Badge.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── PolicyPill.tsx
│   │   │       └── RiskMeter.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── layouts/
│   │   │   └── DashboardLayout.tsx
│   │   ├── pages/
│   │   │   ├── AiSecurity.tsx
│   │   │   ├── Approvals.tsx
│   │   │   ├── LiveMonitoring.tsx
│   │   │   ├── Overview.tsx
│   │   │   ├── Policies.tsx
│   │   │   ├── Settings.tsx
│   │   │   ├── ThreatIntelligence.tsx
│   │   │   └── Transactions.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   └── cn.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   └── anomaly_detector.py
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── policies.py
│   │   │       ├── security.py
│   │   │       └── transactions.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── errors.py
│   │   │   └── logging.py
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── decision_engine.py
│   │   │   ├── policy_engine.py
│   │   │   ├── risk_calculator.py
│   │   │   └── transaction_validator.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── policy.py
│   │   │   ├── security.py
│   │   │   └── transaction.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── policy_service.py
│   │   │   ├── security_service.py
│   │   │   └── transaction_service.py
│   │   ├── websocket/
│   │   │   ├── __init__.py
│   │   │   └── manager.py
│   │   └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   └── test_policy_engine.py
│   ├── venv/
│   └── requirements.txt
│
├── contracts/
│   └── payguard-vault/
│       └── README.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── PHASE_TRACKER.md
│   └── SECURITY.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.11.9
- Node.js v24+ (or v20+)
- Existing activated virtual environment at `backend/venv`

### Step 1: Clone and Inspect
```powershell
git clone <repo_url>
cd PAYGUARD
```

### Step 2: Backend Dependencies & Tests
The virtual environment `backend/venv` is pre-configured. To run the automated test suite:
```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Step 3: Launch Backend Server
```powershell
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- API Health Check: `http://127.0.0.1:8000/api/health`
- Swagger Documentation: `http://127.0.0.1:8000/docs`

### Step 4: Launch Frontend Dashboard
In a separate terminal:
```powershell
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173/`.

---

## 6. Phase 1 Implementation Status

- [x] Python 3.11.9 virtual environment strictly maintained.
- [x] Deterministic Security Policy Engine (`ALLOW`, `WARN`, `BLOCK`).
- [x] All 8 required policy checks implemented & verified.
- [x] Configurable risk calculator (0-100) with explainability.
- [x] REST API endpoints (`/health`, `/transactions/analyze`, `/transactions`, `/policies`, `/security/metrics`).
- [x] Real-time WebSocket connection telemetry (`/ws/events`).
- [x] Scikit-learn Isolation Forest behavioral anomaly detector baseline.
- [x] Cyber-fintech React 19 UI with 8 pages, simulation controls, and dynamic charts.
- [x] 20/20 Pytest unit & integration tests passing with 100% success rate.
- [x] Zero hardcoded secrets, complete `.env.example`, and clean gitignore.

---

## 7. License

MIT License — Developed for the NEAR Hackathon 2026.
