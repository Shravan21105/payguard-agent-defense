# PAYGUARD — Developer Setup & Testing Guide

## 1. System Requirements

- **Operating System:** Windows (PowerShell 5.1+) / macOS / Linux
- **Python:** 3.11.9
- **Node.js:** v24+ (or v20+)
- **npm:** 11+
- **Git:** 2.40+

---

## 2. Environment Activation & Verification

All Python operations must use the dedicated virtual environment located at `backend/venv`.

### Check Python & Pip Environment:
```powershell
# Windows PowerShell
.\backend\venv\Scripts\python.exe --version
.\backend\venv\Scripts\python.exe -m pip --version
```
Expected output:
```text
Python 3.11.9
pip 26.3+ from ...\backend\venv\Lib\site-packages\pip
```

---

## 3. Running the Backend Server

Start the FastAPI application using the active virtual environment:

```powershell
# From project root
.\backend\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

- **Health Check Endpoint:** `http://127.0.0.1:8000/api/health`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`
- **WebSocket Telemetry Stream:** `ws://127.0.0.1:8000/ws/events`

---

## 4. Running the Frontend Application

Start the React + TypeScript Vite development server:

```powershell
# From project root
cd frontend
npm run dev
```

The frontend dashboard will be available at:
`http://localhost:5173/`

To build the frontend for production:
```powershell
cd frontend
npm run build
```

---

## 5. Running the Test Suite

Execute the comprehensive 20-test Pytest test suite:

```powershell
# From project root
.\backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

### Covered Test Cases:
1. `test_valid_transaction_allowed` (ALLOW)
2. `test_trusted_recipient_low_risk` (ALLOW)
3. `test_unknown_recipient_triggers_warn` (WARN)
4. `test_blocked_recipient_triggers_hard_block` (BLOCK)
5. `test_spending_limit_exceeded_triggers_block` (BLOCK)
6. `test_daily_limit_exceeded_triggers_block` (BLOCK)
7. `test_duplicate_transaction_triggers_block` (BLOCK)
8. `test_invalid_amount_rejected` (Validation Failure)
9. `test_warn_decision_requires_human_approval` (WARN)
10. `test_hard_block_is_never_overridden` (BLOCK)
11. `test_determinism_identical_inputs_produce_identical_outputs` (Deterministic verification)
12. `test_health_endpoint` (HTTP 200)
13. `test_analyze_transaction_allowed` (HTTP 200)
14. `test_analyze_transaction_blocked_by_blocklist` (HTTP 200)
15. `test_analyze_transaction_warn_unknown_recipient` (HTTP 200)
16. `test_get_transactions_list` (HTTP 200)
17. `test_get_transaction_by_id` (HTTP 200)
18. `test_get_transaction_not_found` (HTTP 404)
19. `test_get_and_update_policies` (HTTP 200)
20. `test_get_security_metrics` (HTTP 200)
