"""
Voice API — Real-time Voice WebSocket Endpoint.
Task 7.02 — Multi-Tenant Enterprise Chatbot.
"""

import structlog
from fastapi import APIRouter, Depends, WebSocket

from app.core.auth import get_current_user
from app.core.context import get_tenant_id
from app.engine.ai.voice import voice_service

logger = structlog.get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.websocket("/realtime")
async def voice_realtime_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional voice chat.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        from app.core.error_codes import ErrorCode
        from app.core.exceptions import AppException
        raise AppException(ErrorCode.TENANT_101)

    await voice_service.handle_realtime_session(websocket, tenant_id)

@router.get("/status")
async def voice_status():
    return {"status": "voice_service_ready"}

