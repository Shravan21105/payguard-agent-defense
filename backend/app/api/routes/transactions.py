from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.core.logging import logger
from app.schemas.transaction import (
    TransactionAnalysisResponse,
    TransactionRecord,
    TransactionRequest,
)
from app.services.transaction_service import transaction_service
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/analyze",
    response_model=TransactionAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Autonomous Agent Transaction",
)
async def analyze_transaction(request: TransactionRequest):
    """
    Submits an agent-initiated transaction request to the deterministic security engine.
    Returns structured decision (ALLOW / WARN / BLOCK) and explainable policy breakdown.
    """
    try:
        response = transaction_service.analyze_transaction(request)
        # Broadcast real-time event to connected WebSockets
        try:
            await ws_manager.broadcast_json({
                "type": "NEW_TRANSACTION_EVALUATED",
                "payload": response.model_dump(mode="json"),
            })
        except Exception as ws_err:
            logger.debug(f"WebSocket broadcast skipped: {ws_err}")

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
    """Retrieves monitored transaction records."""
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
