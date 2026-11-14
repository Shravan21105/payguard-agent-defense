from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.transaction import TransactionRecord
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'APPROVE' or 'REJECT'")
    operator_id: str = Field(default="human_operator_01")
    reason: Optional[str] = Field(default=None, description="Operator justification for decision")


@router.get("", response_model=List[TransactionRecord], summary="List Pending Transactions Awaiting Human Sign-off")
async def list_pending_approvals():
    """Retrieves all transactions flagged with WARN status requiring human operator review."""
    return transaction_service.list_pending_approvals()


@router.post("/{transaction_id}/decide", response_model=TransactionRecord, summary="Record Human Operator Decision")
async def decide_approval(transaction_id: str, payload: ApprovalDecisionRequest):
    """
    Submits an operator decision (APPROVE or REJECT) for a flagged transaction.
    If approved, generates updated cryptographic authorization evidence and updates execution state.
    """
    dec = payload.decision.upper()
    if dec not in ("APPROVE", "REJECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'APPROVE' or 'REJECT'.",
        )

    try:
        updated_tx = await transaction_service.record_human_approval(
            transaction_id=transaction_id,
            decision=dec,
            operator_id=payload.operator_id,
            reason=payload.reason,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )

    if not updated_tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found.",
        )

    return updated_tx

