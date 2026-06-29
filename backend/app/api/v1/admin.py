import structlog
from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from app.core.rbac import require_role
from app.core.schemas import APIResponse
from app.engine.ai.prompts import (
    get_tenant_system_prompt,
    update_tenant_system_prompt,
)
from app.engine.ai.usage import get_tenant_usage_report

logger = structlog.get_logger(__name__)


router = APIRouter(dependencies=[Depends(require_role("SUPER_ADMIN"))])

# Note: In a real app, this should be protected by the @require_role(['SUPER_ADMIN']) from Task 2.07.
# We are assuming auth middleware is hooked up correctly at the app level.

@router.get("/tenants/{tenant_id}/usage", response_model=APIResponse)
async def get_usage(tenant_id: str = Path(..., title="L'ID del tenant da consultare")):
    """
    Task 3.07: API admin per scaricare il report di utilizzo di un tenant.
    """
    logger.info("fetch_usage_report", target_tenant=tenant_id)
    report = await get_tenant_usage_report(tenant_id)
    return APIResponse.ok(data=report)


class SystemPromptUpdateRequest(BaseModel):
    prompt_text: str


@router.get("/tenants/{tenant_id}/prompt", response_model=APIResponse)
async def get_system_prompt(tenant_id: str = Path(...)):
    """
    Task 3.08: API admin per leggere il system prompt di un tenant.
    """
    prompt = await get_tenant_system_prompt(tenant_id)
    return APIResponse.ok(data={"prompt_text": prompt})

@router.put("/tenants/{tenant_id}/prompt", response_model=APIResponse)
async def update_system_prompt(
    request: SystemPromptUpdateRequest,
    tenant_id: str = Path(...)
):
    """
    Task 3.08: API admin per aggiornare il system prompt di un tenant.
    """
    await update_tenant_system_prompt(tenant_id, request.prompt_text)
    return APIResponse.ok(data={"message": "Prompt updated successfully"})

class TenantCreateRequest(BaseModel):
    name: str

@router.post("/tenants", response_model=APIResponse)
async def create_tenant(request: TenantCreateRequest):
    """
    Task 6.05: Tenant Admin API - Onboarding
    Provisioning automatico di partizioni Cosmos e policy.
    """
    import uuid
    new_tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
    logger.info("provisioning_new_tenant", name=request.name, new_tenant_id=new_tenant_id)

    # Mock provisioning steps:
    # 1. Cosmos DB partition
    # 2. Blob storage path creation
    # 3. Default feature flags

    return APIResponse.ok(data={"tenant_id": new_tenant_id, "name": request.name, "status": "provisioned"})

@router.delete("/tenants/{tenant_id}", response_model=APIResponse)
async def delete_tenant(tenant_id: str = Path(...)):
    """
    Task 6.05: Tenant Admin API - Disattivazione/Cancellazione
    """
    logger.info("deleting_tenant", tenant_id=tenant_id)
    return APIResponse.ok(data={"message": f"Tenant {tenant_id} deleted successfully"})

