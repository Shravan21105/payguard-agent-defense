from typing import Any, Dict, List
from fastapi import APIRouter
from app.db.database import db

router = APIRouter(prefix="/threats", tags=["Threat Intelligence"])


@router.get("", summary="Get Threat Intelligence Findings")
async def get_threat_findings(limit: int = 50):
    """Retrieves real detected exploit attempts, prompt injections, and suspicious counterparties."""
    findings = db.list_security_findings(limit=limit)
    return {
        "total_threats_logged": len(findings),
        "threats": findings,
    }

