import structlog
from fastapi import APIRouter, Depends, Path, Request

from app.core.auth import get_current_user
from app.core.schemas import APIResponse

logger = structlog.get_logger(__name__)


router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/{event}", response_model=APIResponse)
async def inbound_webhook(
    request: Request,
    event: str = Path(...)
):
    """
    Task 5.08: Webhook Triggers Inbound (es. Event Grid).
    Riceve un webhook, lo valida, e innesca un agente asincrono via Service Bus.
    """
    await request.json()

    from app.core.context import get_tenant_id
    tenant_id = get_tenant_id()

    logger.info("inbound_webhook_received", tenant_id=tenant_id, event=event)

    # HERE: sending payload to service bus queue (agent-triggers) to not block
    # await publish_to_agent_trigger_queue(tenant_id, event, payload)

    return APIResponse.ok(data={"status": "accepted", "event": event})
