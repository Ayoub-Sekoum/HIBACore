"""
notifications.py — Endpoint SSE per le notifiche amministrative.
Percorso: backend/app/api/v1/notifications.py
"""
import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.core.auth import require_role
from app.core.context import get_tenant_id
from app.services.policy.notification_service import notification_service

router = APIRouter(prefix="/admin/notifications", tags=["Notifications"])
logger = structlog.get_logger(__name__)

@router.get("/stream")
async def stream_notifications(
    request: Request,
    admin_claims: dict = Depends(require_role(["TENANT_ADMIN", "SUPER_ADMIN"]))
):
    """
    Endpoint SSE per ricevere notifiche in tempo reale.
    I Super Admin ricevono notifiche globali, i Tenant Admin solo del loro tenant.
    """
    is_super = "SUPER_ADMIN" in admin_claims.get("roles", [])
    tenant_id = "global" if is_super else get_tenant_id()
    
    logger.info("sse_connection_opened", tenant_id=tenant_id, user=admin_claims.get("oid"))
    
    return StreamingResponse(
        notification_service.subscribe(tenant_id),
        media_type="text/event-stream"
    )
