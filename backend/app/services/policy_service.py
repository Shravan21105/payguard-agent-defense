from datetime import datetime
from typing import Optional
from app.db.database import db
from app.schemas.policy import PolicyConfig, PolicyResponse, PolicyUpdateRequest


class PolicyService:
    """Manages active security policy state with SQLite persistence."""

    def __init__(self, initial_policy: Optional[PolicyConfig] = None):
        self._policy = initial_policy or PolicyConfig()
        self._updated_at = datetime.utcnow()
        self._version = "1.0.0"
        self._load_from_db()

    def _load_from_db(self) -> None:
        try:
            persisted = db.get_policy()
            if persisted:
                self._version = persisted["version"]
                self._updated_at = datetime.fromisoformat(persisted["updated_at"])
                self._policy = PolicyConfig(**persisted["config"])
        except Exception:
            pass

    def get_policy(self) -> PolicyConfig:
        return self._policy

    def get_policy_response(self) -> PolicyResponse:
        return PolicyResponse(
            version=self._version,
            updated_at=self._updated_at,
            config=self._policy,
        )

    def update_policy(self, update: PolicyUpdateRequest) -> PolicyResponse:
        current_data = self._policy.model_dump()
        update_data = update.model_dump(exclude_unset=True)

        merged = {**current_data, **update_data}
        self._policy = PolicyConfig(**merged)
        self._updated_at = datetime.utcnow()

        # Bump minor version
        try:
            parts = self._version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            self._version = ".".join(parts)
        except Exception:
            self._version = "1.0.1"

        # Persist to database
        db.save_policy(self._version, self._policy.model_dump())

        return self.get_policy_response()


policy_service = PolicyService()
