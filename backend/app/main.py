"""
FastAPI App Factory — Entry Point
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request

from app.core.config import config_manager
from app.core.exceptions import register_exception_handlers
from app.core.logging import CorrelationIdMiddleware, configure_logging
from app.core.rate_limiter import get_rate_limiter

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info("app_starting", version="1.0.0")
    print("DEBUG: Lifespan starting...")
    rate_limiter = get_rate_limiter()
    await rate_limiter.initialize()
    print("DEBUG: Rate limiter initialized.")
    yield
    from app.core.credentials import close_global_credential
    from app.engine.memory.cosmos import cosmos_memory_service
    from app.engine.rag.retriever import close_search_client
    await rate_limiter.close()
    await config_manager.close()
    await cosmos_memory_service.close()
    await close_global_credential()
    await close_search_client()
    logger.info("app_shutdown", message="Tutte le connessioni chiuse correttamente.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Multi-Tenant Chatbot Enterprise",
        description="Chatbot AI enterprise multi-tenant SaaS su Azure.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    from app.middleware.security import SecurityHeadersMiddleware
    from app.core.rate_limiter import RateLimitMiddleware
    from app.middleware.content_safety import ContentSafetyMiddleware
    from app.core.middleware import TenantMiddleware
    from fastapi.middleware.cors import CORSMiddleware

    origins = config_manager.settings.CORS_ORIGINS

    # ORDINE INVERSO: l ultimo add_middleware e il primo eseguito
    # Esecuzione reale: CORS -> CorrelationId -> Tenant -> RateLimit -> ContentSafety -> Security
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ContentSafetyMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins.split(",") if isinstance(origins, str) else origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.middleware("http")
    async def debug_headers(request: Request, call_next):
        logger.info("incoming_request", method=request.method, path=request.url.path, origin=request.headers.get("origin"))
        response = await call_next(request)
        logger.info("outgoing_response", status=response.status_code, path=request.url.path)
        return response

    @app.get("/debug-cors")
    async def debug_cors():
        return {"status": "ok", "message": "CORS is working"}

    @app.get("/")
    async def root():
        return {"status": "healthy", "message": "HOBA AI Backend is running"}

    from app.api.v1.health import router as health_router
    app.include_router(health_router, tags=["Health"])
    from app.api.v1.chat import router as chat_router
    app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
    from app.api.v1.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    from app.api.v1.admin_super import router as admin_super_router
    app.include_router(admin_super_router, prefix="/api/v1", tags=["Super Admin"])
    from app.api.v1.admin_tenant import router as admin_tenant_router
    app.include_router(admin_tenant_router, prefix="/api/v1", tags=["Tenant Admin"])
    from app.api.v1.notifications import router as notifications_router
    app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
    from app.api.v1.documents import router as documents_router
    app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
    from app.api.v1.webhooks import router as webhook_router
    app.include_router(webhook_router, prefix="/api/v1/webhooks", tags=["Webhooks"])
    from app.api.v1.conversations import router as conv_router
    app.include_router(conv_router, prefix="/api/v1/conversations", tags=["Conversations"])
    
    # DISABILITATO TEMPORANEAMENTE: pacchetto azure.ai.voicelive non installabile
    # from app.api.v1.voice import router as voice_router
    # app.include_router(voice_router, prefix="/api/v1/voice", tags=["Voice"])
    
    from app.api.v1.agents import router as agents_router
    app.include_router(agents_router, prefix="/api/v1/agents", tags=["DeepAgents"])

    from app.api.v1 import agent as zeroclaw_agent
    app.include_router(zeroclaw_agent.router, prefix="/api/v1/agent", tags=["agent"])

    return app


app = create_app()