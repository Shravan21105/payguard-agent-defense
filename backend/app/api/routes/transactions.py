from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import logger
from app.schemas.transaction import (
    InitiateTransactionRequest,
    TransactionAnalysisResponse,
    TransactionRecord,
    TransactionRequest,
)
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/initiate",
    response_model=TransactionRecord,
    status_code=status.HTTP_200_OK,
    summary="Initiate End-to-End Autonomous Agent Transaction (Phase 4)",
)
async def initiate_transaction(request: InitiateTransactionRequest):
    """
    Unified Phase 4 End-to-End Pipeline:
    - Input Validation & Anti-Replay
    - Multi-Agent AI Intent Auditing & Behavioral Risk Scoring
    - Deterministic Security Policy Verification
    - Ed25519 Cryptographic Authorization
    - NEAR Testnet Smart Contract Vault Execution / Escrow
    - Real-time WebSocket Telemetry Streaming
    """
    try:
        record = await transaction_service.initiate_transaction(request)
        return record
    except Exception as e:
        logger.error(f"Error initiating transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction initiation failed: {str(e)}",
        )


@router.post(
    "/analyze",
    response_model=TransactionAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Autonomous Agent Transaction through Multi-Agent LangGraph",
)
async def analyze_transaction(request: TransactionRequest):
    """
    Submits an agent-initiated transaction request to the multi-agent LangGraph workflow.
    Executes Intent Analysis, Behavioural Anomaly Detection, Security Intelligence,
    Deterministic Policy Verification, and Cryptographic Evidence Generation.
    """
    try:
        response = await transaction_service.analyze_transaction(request)
        return response
    except Exception as e:
        logger.error(f"Error evaluating transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction security evaluation failed: {str(e)}",
        )


@router.get(
    "",
    response_model=List[TransactionRecord],
    summary="List Monitored Transactions",
)
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    decision: Optional[str] = Query(default=None, description="Filter by ALLOW, WARN, or BLOCK"),
):
    """Retrieves monitored transaction records from persistent SQLite store."""
    return transaction_service.list_transactions(limit=limit, decision=decision)


@router.get(
    "/{transaction_id}",
    response_model=TransactionRecord,
    summary="Get Specific Transaction by ID",
)
async def get_transaction(transaction_id: str):
    """Retrieves a single transaction by its unique ID."""
    record = transaction_service.get_transaction(transaction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found.",
        )
    return record


@router.get(
    "/{transaction_id}/evidence",
    summary="Get Cryptographic Authorization Evidence",
)
async def get_transaction_evidence(transaction_id: str):
    """Retrieves the canonical JSON payload, SHA-256 digest, and verification record."""
    evidence = transaction_service.get_authorization_evidence(transaction_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Authorization evidence for transaction '{transaction_id}' not found.",
        )
    return evidence


@router.get(
    "/{transaction_id}/agents",
    summary="Get Agent Execution Logs for Transaction",
)
async def get_transaction_agents(transaction_id: str):
    """Retrieves telemetry logs for the 4 specialized agents that processed this transaction."""
    logs = transaction_service.get_agent_executions(transaction_id)
    return {"transaction_id": transaction_id, "agent_executions": logs}
