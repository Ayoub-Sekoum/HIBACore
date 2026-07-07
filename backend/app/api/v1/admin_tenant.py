"""
admin_tenant.py — API per l'amministratore del cliente.
Percorso: backend/app/api/v1/admin_tenant.py
"""
from fastapi import APIRouter, Depends, Query, Request
import structlog
from app.core.auth import require_role
from app.core.context import get_tenant_id
from app.services.policy.policy_store import policy_store
from app.services.policy.audit_log import audit_log_service
from app.core.exceptions import AppException
from app.core.error_codes import ErrorCode

router = APIRouter(prefix="/admin/tenant", tags=["Tenant Admin"])
logger = structlog.get_logger(__name__)

@router.get("/policy")
async def get_my_policy(
    admin_claims: dict = Depends(require_role(["TENANT_ADMIN"]))
):
    """Legge la policy del proprio tenant (senza campi riservati)."""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    policy = await policy_store.get_tenant_policy(tenant_id)
    if not policy:
        raise AppException(ErrorCode.TENANT_104)
    
    # Remove reserved fields
    reserved = ["admin_can_modify", "id", "partition_key", "type"]
    public_policy = {k: v for k, v in policy.items() if k not in reserved}
    
    return {"status": "success", "data": public_policy}

@router.patch("/policy")
async def update_my_policy(
    updates: dict,
    request: Request,
    admin_claims: dict = Depends(require_role(["TENANT_ADMIN"]))
):
    """Aggiorna policy (solo campi in admin_can_modify)."""
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    old_policy = await policy_store.get_tenant_policy(tenant_id)
    if not old_policy:
         raise AppException(ErrorCode.TENANT_104)

    # The update is verified within policy_store.update_tenant_policy
    # if is_super_admin=False
    updated = await policy_store.update_tenant_policy(
        tenant_id=tenant_id,
        updates=updates,
        updated_by=admin_claims.get("oid", "tenant-admin"),
        is_super_admin=False
    )

    # Audit logs
    for field, new_val in updates.items():
        await audit_log_service.log_policy_change(
            tenant_id=tenant_id,
            actor_id=admin_claims.get("oid", "tenant-admin"),
            actor_role="TENANT_ADMIN",
            action="update_policy",
            field_changed=field,
            old_value=old_policy.get(field),
            new_value=new_val
        )

    return {"status": "success", "data": updated}

@router.get("/audit")
async def get_my_audit(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: dict = Depends(require_role(["TENANT_ADMIN"]))
):
    """Audit log del proprio tenant."""
    tenant_id = get_tenant_id()
    audit = await audit_log_service.get_audit_log(tenant_id=tenant_id, limit=limit, offset=offset)
    return {"status": "success", "data": audit}
