from app.db.database import db
from app.schemas.security import SecurityMetricsResponse


class SecurityService:
    """Aggregates real-time security analytics and threat telemetry from persistent SQLite database."""

    @classmethod
    def get_metrics(cls) -> SecurityMetricsResponse:
        metrics_dict = db.get_metrics()
        return SecurityMetricsResponse(**metrics_dict)


security_service = SecurityService()
