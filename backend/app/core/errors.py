from typing import Any, Dict, Optional
from fastapi import Request
from fastapi.responses import JSONResponse


class PayguardError(Exception):
    """Base exception for PAYGUARD security domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PolicyViolationError(PayguardError):
    """Raised when a hard security policy violation occurs."""
    pass


class ValidationError(PayguardError):
    """Raised when transaction data fails schema or sanity validation."""
    pass


class ResourceNotFoundError(PayguardError):
    """Raised when an entity is not found."""
    pass


async def payguard_exception_handler(request: Request, exc: PayguardError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred during security processing.",
            "path": str(request.url.path),
        },
    )
