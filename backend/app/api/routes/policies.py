from fastapi import APIRouter, status
from app.schemas.policy import PolicyResponse, PolicyUpdateRequest
from app.services.policy_service import policy_service

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get(
    "",
    response_model=PolicyResponse,
    summary="Get Active Security Policies",
)
async def get_policies():
    """Retrieves current active deterministic security policies and threshold rules."""
    return policy_service.get_policy_response()


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Security Policies",
)
async def update_policies(update_data: PolicyUpdateRequest):
    """
    Updates active security policy limits, counterparty lists, and threshold parameters.
    Changes apply immediately to subsequent transaction evaluations.
    """
    return policy_service.update_policy(update_data)

