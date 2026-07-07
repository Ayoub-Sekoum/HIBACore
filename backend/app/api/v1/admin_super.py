from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
import structlog

from app.core.auth import require_role
from app.services.policy.policy_store import policy_store
from app.services.policy.audit_log import audit_log_service
from app.core.exceptions import AppException
from app.core.error_codes import ErrorCode

from app.services.policy.approval import approval_queue

router = APIRouter(prefix="/admin/super", tags=["Super Admin"])
logger = structlog.get_logger(__name__)

@router.get("/tenants")
async def list_tenants(
     _admin: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    """Lista tutti i tenant con la loro configurazione base."""
    data = await policy_store.list_all_tenants()
    return {"status": "success", "data": data}

@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    _admin: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    """Dettaglio singolo tenant con policy completa."""
    policy = await policy_store.get_tenant_policy(tenant_id)
    if not policy:
        raise AppException(ErrorCode.TENANT_104)
    
    # Recent audit
    audit = await audit_log_service.get_audit_log(tenant_id=tenant_id, limit=10)
    
    return {
        "status": "success",
        "data": {
            "policy": policy,
            "recent_audit": audit
        }
    }

@router.patch("/tenants/{tenant_id}/policy")
async def update_tenant_policy(
    tenant_id: str,
    updates: dict,
    request: Request,
    admin_claims: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    """Aggiorna policy di un tenant (super admin può cambiare tutto)."""
    old_policy = await policy_store.get_tenant_policy(tenant_id)
    if not old_policy:
         raise AppException(ErrorCode.TENANT_104)

    updated = await policy_store.update_tenant_policy(
        tenant_id=tenant_id,
        updates=updates,
        updated_by=admin_claims.get("oid", "super-admin"),
        is_super_admin=True
    )

    # Audit logs
    for field, new_val in updates.items():
        await audit_log_service.log_policy_change(
            tenant_id=tenant_id,
            actor_id=admin_claims.get("oid", "super-admin"),
            actor_role="SUPER_ADMIN",
            action="update_policy",
            field_changed=field,
            old_value=old_policy.get(field),
            new_value=new_val
        )

    return {"status": "success", "data": updated}

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason_data: dict, # {"reason": "..."}
    admin_claims: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    await policy_store.suspend_tenant(
        tenant_id=tenant_id,
        reason=reason_data.get("reason", "No reason provided"),
        by=admin_claims.get("oid", "super-admin")
    )
    return {"status": "success", "message": "Tenant sospeso."}

@router.get("/audit")
async def get_global_audit(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    """Audit log globale."""
    audit = await audit_log_service.get_audit_log(limit=limit, offset=offset)
    return {"status": "success", "data": audit}

@router.get("/approvals")
async def get_super_approvals(
    _admin: dict = Depends(require_role(["SUPER_ADMIN"]))
):
    """Richieste di approvazione in attesa (tutti i tenant)."""
    approvals = await approval_queue.get_all_pending()
    return {"status": "success", "data": approvals}
