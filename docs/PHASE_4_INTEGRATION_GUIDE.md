# PAYGUARD — Phase 4: Autonomous AI Agent Integration Guide

**Project:** PAYGUARD (Agent Defense Layer)  
**Hackathon:** NEAR Hackathon 2026  
**Tracks:** AI Security & Defense (SEC) | Agent Economy (AGT)

---

## 1. Introduction

As autonomous AI agents gain wallet autonomy to transact on blockchain networks, granting them unrestricted private key access creates immense financial exposure. Agents can fall victim to:
- Prompt injection and jailbreaks.
- Sybil counterparties and address poisoning.
- Erroneous decimal / amount hallucinations.
- Rapid runaway spending loops.

**PAYGUARD solves this by serving as an intelligent cryptographic firewall.**  
Instead of signing and submitting transactions directly, the AI agent passes every proposed payment to PAYGUARD's defense layer. PAYGUARD evaluates the agent's natural-language intent, enforces deterministic security policies, and issues an Ed25519 authorization signature only when verified safe.

---

## 2. Integration Pattern

```
+--------------------------------------------------------------------------------+
|                             AUTONOMOUS AI AGENT                                |
|                                                                                |
|  1. Agent formulates financial goal:                                           |
|     "I need to pay 3.5 NEAR to oracle-feed.testnet for weather data access"    |
|                                                                                |
|  2. Agent calls PAYGUARD before executing on-chain:                            |
|     response = payguard.initiate_transaction(...)                              |
|                                                                                |
|  3. Agent inspects response.decision:                                          |
|                                                                                |
|     ├── If 'ALLOW' & 'CONFIRMED':                                              |
|     │     Agent logs tx_hash & explorer_url; proceeds with downstream task.    |
|     │                                                                          |
|     ├── If 'WARN' & 'ESCROW_CREATED':                                          |
|     │     Funds safely locked in vault escrow; agent pauses task or            |
|     │     notifies human operator for sign-off.                                |
|     │                                                                          |
|     └── If 'BLOCK':                                                            |
|           Agent aborts operation; alerts security supervisor with reasons.    |
+--------------------------------------------------------------------------------+
```

---

## 3. Python Integration Example

Here is a complete, production-ready Python client for any autonomous agent:

```python
"""
payguard_client.py - Drop-in security client for Python AI agents.
"""

import uuid
import requests
from typing import Dict, Any, Optional

class PayGuardClient:
    def __init__(self, base_url: str = "http://localhost:8000", agent_id: str = "ai-agent-v1"):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id

    def submit_payment(
        self,
        sender_account: str,
        recipient_account: str,
        amount: float,
        declared_intent: str,
        currency: str = "NEAR",
        dry_run: bool = False,
        timelock_seconds: int = 86400,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submits a transaction proposal to PAYGUARD for security evaluation & execution.
        """
        payload = {
            "transaction_id": f"tx-{uuid.uuid4()}",
            "agent_id": self.agent_id,
            "sender_account": sender_account,
            "recipient_account": recipient_account,
            "amount": amount,
            "currency": currency,
            "declared_intent": declared_intent,
            "dry_run": dry_run,
            "timelock_seconds": timelock_seconds,
            "metadata": metadata or {}
        }

        url = f"{self.base_url}/api/transactions/initiate"
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

# --- Example Agent Usage ---
if __name__ == "__main__":
    client = PayGuardClient(agent_id="data-collector-agent-07")

    print("[*] Proposing payment to PAYGUARD defense engine...")
    result = client.submit_payment(
        sender_account="agent-vault.testnet",
        recipient_account="oracle-node.testnet",
        amount=1.5,
        declared_intent="Subscribing to high-frequency price feed stream for 24 hours"
    )

    decision = result.get("decision")
    status = result.get("status")

    if decision == "ALLOW":
        print(f"[+] Payment ALLOWED & {status}!")
        print(f"    Transaction Hash: {result.get('tx_hash')}")
        print(f"    Explorer Link:    {result.get('explorer_url')}")
    elif decision == "WARN":
        print(f"[!] Payment held in ESCROW (Status: {status})")
        print(f"    Escrow ID:   {result.get('escrow_id')}")
        print(f"    Reasons:     {result.get('reasons')}")
    else:  # BLOCK
        print(f"[-] Payment BLOCKED by security policy!")
        print(f"    Risk Score:  {result.get('risk_score')}")
        print(f"    Reasons:     {result.get('reasons')}")
```

---

## 4. LangChain Tool Integration

You can easily wrap PAYGUARD as a standard LangChain Tool for any ReAct or Plan-and-Solve agent:

```python
from langchain.tools import tool
import requests

@tool
def secure_blockchain_transfer(
    recipient: str,
    amount: float,
    intent_reason: str
) -> str:
    """
    Safely executes a NEAR cryptocurrency transfer through the PAYGUARD security vault.
    Always provide the exact recipient, amount in NEAR, and a natural language explanation of why this transfer is needed.
    """
    url = "http://localhost:8000/api/transactions/initiate"
    payload = {
        "agent_id": "langchain-reasoning-agent",
        "sender_account": "agent-core.testnet",
        "recipient_account": recipient,
        "amount": amount,
        "declared_intent": intent_reason,
        "dry_run": False
    }

    resp = requests.post(url, json=payload).json()
    decision = resp.get("decision")

    if decision == "ALLOW":
        return f"Transfer SUCCESSFUL. Tx Hash: {resp.get('tx_hash')}. Explorer: {resp.get('explorer_url')}"
    elif decision == "WARN":
        return f"Transfer held in ESCROW for human approval. Escrow ID: {resp.get('escrow_id')}. Reason: {resp.get('reasons')}"
    else:
        return f"Transfer BLOCKED by PAYGUARD firewall. Violations: {resp.get('reasons')}. Action aborted."
```

---

## 5. TypeScript / Node.js Integration Example

For agents running in JavaScript or TypeScript (e.g. ElizaOS, AutoGPT, or autonomous bots):

```typescript
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

interface InitiateResponse {
  transaction_id: string;
  decision: 'ALLOW' | 'WARN' | 'BLOCK';
  status: string;
  risk_score: number;
  reasons: string[];
  tx_hash?: string;
  explorer_url?: string;
  escrow_id?: string;
}

export async function executeSafeAgentPayment(
  recipient: string,
  amount: number,
  intent: string
): Promise<InitiateResponse> {
  const payload = {
    transaction_id: `tx-${uuidv4()}`,
    agent_id: 'elizaos-trading-bot',
    sender_account: 'agent-trading.testnet',
    recipient_account: recipient,
    amount,
    currency: 'NEAR',
    declared_intent: intent,
    dry_run: false,
  };

  const response = await axios.post<InitiateResponse>(
    'http://localhost:8000/api/transactions/initiate',
    payload
  );

  return response.data;
}
```

---

## 6. Best Practices for Agent Developers

1. **Be Specific in `declared_intent`:** Provide clear context regarding the purpose and service provider in the intent string. PAYGUARD's LLM Intent Agent verifies whether the declared recipient and amount align with the task description.
2. **Handle `WARN` Gracefully:** Treat `WARN` as an asynchronous approval state. If your agent operates on a continuous schedule, record the `escrow_id` and query `GET /api/blockchain/escrow/{id}` until the human operator signs off.
3. **Never Attempt to Bypass `BLOCK`:** If PAYGUARD returns `BLOCK`, never instruct the agent to retry with minor variations. Deterministic policy blocks represent hard boundaries (e.g., blacklisted exploit contracts or daily spending caps).
4. **Subscribe to Real-Time Telemetry:** Connect to `ws://localhost:8000/api/ws/monitoring` to listen for immediate transaction confirmation or escrow events without polling.

