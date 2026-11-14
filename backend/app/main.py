from collections import defaultdict
from contextlib import asynccontextmanager
import time
from typing import Dict, List
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.agents import router as agents_router
from app.api.routes.ai import router as ai_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.blockchain import router as blockchain_router
from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.policies import router as policies_router
from app.api.routes.security import router as security_router
from app.api.routes.threats import router as threats_router
from app.api.routes.transactions import router as transactions_router
from app.blockchain.signer import policy_signer
from app.core.config import settings
from app.core.errors import PayguardError, global_exception_handler, payguard_exception_handler
from app.core.logging import logger
from app.services.blockchain_monitor import blockchain_monitor
from app.websocket.manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT} mode)")
    logger.info(f"CORS origins configured: {settings.CORS_ORIGINS}")
    logger.info(f"Multi-Agent LangGraph Orchestrator initialized. LLM Provider: {settings.LLM_PROVIDER}")

    # Production Cryptographic Security Check
    if settings.ENVIRONMENT.lower() in ("production", "prod") and getattr(policy_signer, "is_ephemeral", False):
        raise RuntimeError(
            "Production startup halted: PolicySigner is running in ephemeral development mode. "
            "In production, POLICY_SIGNER_PRIVATE_KEY must be explicitly configured in the environment."
        )

    try:
        await blockchain_monitor.start()
    except Exception as e:
        logger.warning(f"Could not start background blockchain monitor: {e}")
    yield
    try:
        await blockchain_monitor.stop()
    except Exception as e:
        logger.warning(f"Error stopping blockchain monitor: {e}")
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Security Infrastructure for Autonomous AI Agents — Phase 3 NEAR Smart Contract Vault & On-Chain Enforcement (NEAR Hackathon 2026)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(PayguardError, payguard_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Security & Rate Limiting State
_rate_limit_records: Dict[str, List[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60.0  # seconds
_RATE_LIMIT_MAX_REQUESTS = 180  # per minute per client IP for evaluation endpoints

@app.middleware("http")
async def security_hardening_middleware(request: Request, call_next):
    # 1. Enforce maximum payload size (1 MB limit)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 1_048_576:
                return JSONResponse(
                    status_code=413,
                    content={"error": "PayloadTooLarge", "message": "Request payload exceeds 1MB limit."},
                )
        except ValueError:
            pass

    # 2. Rate limiting on sensitive evaluation & authorization endpoints
    path = request.url.path
    if path.startswith(("/api/transactions/initiate", "/api/transactions/analyze", "/api/blockchain/authorize")):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - _RATE_LIMIT_WINDOW
        # Prune old timestamps
        history = [ts for ts in _rate_limit_records[client_ip] if ts > window_start]
        if len(history) >= _RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"error": "RateLimitExceeded", "message": "Too many requests. Please throttle your transaction evaluation rate."},
            )
        history.append(now)
        _rate_limit_records[client_ip] = history

    response: Response = await call_next(request)

    # 3. Security Headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    return response

# CORS configuration for local React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api
app.include_router(health_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(policies_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(threats_router, prefix="/api")
app.include_router(blockchain_router, prefix="/api")
app.include_router(events_router, prefix="/api")


# WebSocket Telemetry endpoint for real-time dashboard events
@app.websocket("/ws/events")
@app.websocket("/api/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    client_id = await ws_manager.connect(websocket)
    if not client_id:
        return
    try:
        # Send initial connection acknowledgment with client ID and supported categories
        await websocket.send_json({
            "event_id": f"evt_welcome_{client_id}",
            "type": "system.websocket_connected",
            "event_type": "system.websocket_connected",
            "category": "system",
            "severity": "INFO",
            "source": "websocket_server",
            "message": "Connected to PAYGUARD Real-Time Security Telemetry Stream",
            "version": settings.APP_VERSION,
            "payload": {
                "client_id": client_id,
                "supported_categories": ["transactions", "security", "blockchain", "escrow", "system", "all"],
                "active_subscriptions": ["all"],
            },
        })
        while True:
            raw_text = await websocket.receive_text()
            if raw_text == "ping":
                ws_manager.record_heartbeat(websocket)
                await websocket.send_text("pong")
                continue

            try:
                import json
                msg_data = json.loads(raw_text)
                action = msg_data.get("action") or msg_data.get("type")
                if action == "subscribe":
                    cats = msg_data.get("categories", ["all"])
                    updated = ws_manager.update_subscriptions(websocket, cats)
                    await websocket.send_json({
                        "type": "system.subscription_updated",
                        "event_type": "system.subscription_updated",
                        "client_id": client_id,
                        "active_subscriptions": list(updated),
                    })
                elif action == "ping":
                    ws_manager.record_heartbeat(websocket)
                    await websocket.send_json({"type": "pong", "client_id": client_id})
            except json.JSONDecodeError:
                # Non-JSON message received
                pass

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error ({client_id}): {e}")
        ws_manager.disconnect(websocket)


@app.get("/", include_in_schema=False)
async def root_redirect():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 5: Real-Time Monitoring & Event Streaming",
        "docs": "/docs",
        "health": "/api/health",
        "monitoring_health": "/api/monitoring/health",
        "monitoring_metrics": "/api/monitoring/metrics",
        "events": "/api/events",
        "agents": "/api/agents/status",
        "blockchain": "/api/blockchain/status",
        "websocket": "ws://127.0.0.1:8000/ws/events",
        "description": "PAYGUARD Real-Time Event Streaming & Blockchain Monitoring are operational.",
    }
