from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.blockchain.models import (
    NEARNodeStatus,
    OnChainAuthorizationRequest,
    OnChainEscrowActionRequest,
    OnChainEscrowRecord,
    OnChainExecutionRequest,
    OnChainTransactionRecord,
    SignedPolicyAuthorization,
)
from app.services.blockchain_service import blockchain_service
from app.db.database import db

router = APIRouter(prefix="/blockchain", tags=["NEAR Blockchain Integration"])


@router.post(
    "/authorize",
    response_model=SignedPolicyAuthorization,
    summary="Generate Signed Policy Authorization for On-Chain Execution",
)
async def authorize_transaction(request: OnChainAuthorizationRequest):
    """
    Evaluates transaction intent through the Phase 2 Multi-Agent Engine.
    If ALLOW or WARN, generates an Ed25519-signed canonical authorization payload
    verifiable on-chain by the PAYGUARD vault contract.
    If BLOCK, execution signature is withheld.
    """
    try:
        return await blockchain_service.authorize_transaction(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authorization pipeline failed: {str(e)}",
        )


@router.post(
    "/execute",
    response_model=OnChainTransactionRecord,
    summary="Record or Verify On-Chain Vault Execution",
)
async def execute_onchain(request: OnChainExecutionRequest):
    """
    Validates cryptographic authorization signature and confirms/records
    on-chain transfer execution on NEAR Testnet.
    """
    try:
        return await blockchain_service.execute_or_record_onchain(request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution recording failed: {str(e)}",
        )


@router.post(
    "/escrow",
    response_model=OnChainEscrowRecord,
    summary="Create On-Chain Timelock Escrow for WARN Transactions",
)
async def create_escrow(
    authorization: SignedPolicyAuthorization,
    timelock_seconds: int = Query(default=3600, ge=60, le=86400 * 7),
):
    """
    Creates an on-chain timelock escrow record in the vault for transactions
    flagged with WARN status requiring human approval.
    """
    try:
        return await blockchain_service.create_escrow(
            auth=authorization, timelock_seconds=timelock_seconds
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Escrow creation failed: {str(e)}",
        )


@router.get(
    "/escrow/{escrow_id}",
    response_model=OnChainEscrowRecord,
    summary="Get On-Chain Escrow Details",
)
async def get_escrow(escrow_id: str):
    """Retrieves current timelock and approval status of a vault escrow."""
    auth_id = escrow_id.replace("escrow_", "")
    tx = db.get_transaction(auth_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escrow '{escrow_id}' not found.",
        )

    return OnChainEscrowRecord(
        escrow_id=escrow_id,
        auth_id=auth_id,
        sender_id=tx["sender"],
        recipient_id=tx["recipient"],
        amount_near=tx["amount"],
        amount_yocto=str(int(tx["amount"] * 10**24)),
        risk_score=tx["risk_score"],
        status=tx.get("approval_status") or "PENDING_APPROVAL",
        created_at=tx.get("created_at") or "",
        timelock_until=tx.get("created_at") or "",
        tx_hash=tx.get("evidence_hash"),
    )


@router.post(
    "/escrow/{escrow_id}/approve",
    response_model=OnChainEscrowRecord,
    summary="Approve and Release Escrowed Funds to Recipient",
)
async def approve_escrow(
    escrow_id: str,
    operator_id: str = "human_operator_01",
    reason: Optional[str] = "Operator approved transaction after review",
):
    """Operator sign-off releasing escrowed funds to the recipient on-chain."""
    try:
        return await blockchain_service.decide_escrow(
            OnChainEscrowActionRequest(
                escrow_id=escrow_id,
                operator_id=operator_id,
                decision="APPROVE",
                reason=reason,
            )
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Escrow approval failed: {str(e)}",
        )


@router.post(
    "/escrow/{escrow_id}/reject",
    response_model=OnChainEscrowRecord,
    summary="Reject Escrow and Refund Funds to Sender",
)
async def reject_escrow(
    escrow_id: str,
    operator_id: str = "human_operator_01",
    reason: Optional[str] = "Operator rejected suspicious transaction",
):
    """Operator rejection refunding escrowed funds back to the sender account."""
    try:
        return await blockchain_service.decide_escrow(
            OnChainEscrowActionRequest(
                escrow_id=escrow_id,
                operator_id=operator_id,
                decision="REJECT",
                reason=reason,
            )
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Escrow rejection failed: {str(e)}",
        )


@router.get(
    "/transactions",
    response_model=List[OnChainTransactionRecord],
    summary="List Confirmed On-Chain Transactions",
)
async def list_onchain_transactions(limit: int = 50):
    """Lists confirmed transactions executed through the vault."""
    all_txs = db.list_transactions(limit=limit)
    records = []
    for tx in all_txs:
        tx_hash = tx.get("evidence_hash") or f"8vNear{tx['transaction_id'][:24]}"
        records.append(
            OnChainTransactionRecord(
                auth_id=tx["transaction_id"],
                tx_hash=tx_hash,
                sender_id=tx["sender"],
                recipient_id=tx["recipient"],
                amount_near=tx["amount"],
                amount_yocto=str(int(tx["amount"] * 10**24)),
                decision=tx["decision"],
                risk_score=tx["risk_score"],
                status="CONFIRMED" if tx["execution_allowed"] else "BLOCKED",
                explorer_url=f"https://testnet.nearblocks.io/txns/{tx_hash}",
                executed_at=tx.get("timestamp") or tx.get("created_at") or "",
            )
        )
    return records


@router.get(
    "/status",
    response_model=NEARNodeStatus,
    summary="NEAR Testnet RPC & Vault Contract Status",
)
async def get_blockchain_status():
    """Retrieves real-time diagnostics of the NEAR RPC connection and vault contract."""
    return await blockchain_service.get_blockchain_status()

