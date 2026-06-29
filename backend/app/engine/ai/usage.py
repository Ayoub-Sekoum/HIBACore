from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.context import get_tenant_id

logger = structlog.get_logger(__name__)

# Mock database until Cosmos DB is fully wired up in Phase 4
_USAGE_DB: dict[str, list] = {}

# Approximate pricing per 1K tokens for Azure OpenAI
PRICING = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "text-embedding-3-small": {"prompt": 0.00002, "completion": 0.0}
}

async def record_usage(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """
    Task 3.07: Registra i token consumati e calcola il costo stimato in USD.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("record_usage_no_tenant")
        return

    rates = PRICING.get(model, {"prompt": 0.0, "completion": 0.0})
    cost_usd = (prompt_tokens / 1000.0) * rates["prompt"] + (completion_tokens / 1000.0) * rates["completion"]

    record = {
        "tenant_id": tenant_id,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": cost_usd,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Simulate Cosmos DB save
    if tenant_id not in _USAGE_DB:
        _USAGE_DB[tenant_id] = []
    _USAGE_DB[tenant_id].append(record)

    logger.info("usage_recorded", **record)

async def get_tenant_usage_report(tenant_id: str) -> dict[str, Any]:
    """Recupera il report mensile di utilizzo per il tenant (mock Cosmos DB)."""
    records = _USAGE_DB.get(tenant_id, [])

    total_prompt = sum(r["prompt_tokens"] for r in records)
    total_completion = sum(r["completion_tokens"] for r in records)
    total_cost = sum(r["estimated_cost_usd"] for r in records)

    return {
        "tenant_id": tenant_id,
        "total_requests": len(records),
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_cost_usd": round(total_cost, 6)
    }
