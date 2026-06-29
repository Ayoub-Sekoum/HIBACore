
import structlog

from app.core.context import get_tenant_id

logger = structlog.get_logger(__name__)

# Task 3.08: Mocking Cosmos DB table `system_prompts`
# Format: {tenant_id: prompt_text}
_PROMPT_DB: dict[str, str] = {}

# Default prompt se il tenant non ne ha uno personalizzato
DEFAULT_SYSTEM_PROMPT = "Sei un assistente AI aziendale utile ed educato."

async def get_tenant_system_prompt(tenant_id: str | None = None) -> str:
    """Restituisce il system prompt attivo per il tenant corrente."""
    tid = tenant_id or get_tenant_id()
    if not tid:
        return DEFAULT_SYSTEM_PROMPT

    return _PROMPT_DB.get(tid, DEFAULT_SYSTEM_PROMPT)

async def update_tenant_system_prompt(tenant_id: str, prompt_text: str) -> None:
    """Aggiorna il system prompt per un tenant (mock Cosmos DB update)."""
    _PROMPT_DB[tenant_id] = prompt_text
    logger.info("system_prompt_updated", target_tenant=tenant_id)
