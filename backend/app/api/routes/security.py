from fastapi import APIRouter
from app.schemas.security import SecurityMetricsResponse
from app.services.security_service import security_service

router = APIRouter(prefix="/security", tags=["Security Telemetry"])


@router.get(
    "/metrics",
    response_model=SecurityMetricsResponse,
    summary="Get Security Overview Metrics",
)
async def get_security_metrics():
    """
    Returns aggregate security statistics: total monitored, approval counts,
    blocked exploits, prevented drain volume, and recent alerts.
    """
    return security_service.get_metrics()

