from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.policies import router as policies_router
from app.api.routes.security import router as security_router
from app.api.routes.transactions import router as transactions_router
from app.core.config import settings
from app.core.errors import PayguardError, global_exception_handler, payguard_exception_handler
from app.core.logging import logger
from app.websocket.manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT} mode)")
    logger.info(f"CORS origins configured: {settings.CORS_ORIGINS}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Security Infrastructure for Autonomous AI Agents (NEAR Hackathon 2026)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(PayguardError, payguard_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

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


# WebSocket Telemetry endpoint for real-time dashboard events
@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to PAYGUARD Real-Time Security Telemetry Stream",
            "timestamp": "now",
        })
        while True:
            # Keep-alive loop; receive incoming messages or ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        ws_manager.disconnect(websocket)


@app.get("/", include_in_schema=False)
async def root_redirect():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "description": "PAYGUARD AI Security Engine is operational.",
    }
