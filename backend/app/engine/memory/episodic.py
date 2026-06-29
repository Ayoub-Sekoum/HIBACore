"""
Episodic Memory — Manages task history and agent episodes using CosmosDB.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.engine.memory.cosmos import cosmos_memory_service

logger = structlog.get_logger(__name__)

class EpisodicMemory:
    """Stores history of task executions and complex agent episodes."""

    def __init__(self):
        self.service = cosmos_memory_service

    async def record_episode(self, tenant_id: str, session_id: str, action_log: list[dict[str, Any]], final_result: str):
        """Record an entire multi-step episode."""
        try:
            container = await self.service._get_container()
            doc = {
                "id": f"episode_{uuid.uuid4()}",
                "tenant_id": tenant_id,
                "session_id": session_id,
                "actions": action_log,
                "result": final_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await container.create_item(body=doc)
            logger.info("episodic_memory_recorded", tenant_id=tenant_id, session_id=session_id)
        except Exception as e:
            logger.error("failed_to_record_episode", tenant_id=tenant_id, error=str(e))

    async def get_history(self, tenant_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Retrieve past episodes for the tenant."""
        try:
            container = await self.service._get_container()
            query_str = "SELECT TOP @limit * FROM c WHERE c.tenant_id = @tenant_id AND STARTSWITH(c.id, 'episode_') ORDER BY c.timestamp DESC"
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@limit", "value": limit}
            ]

            results = []
            items = container.query_items(query=query_str, parameters=parameters, enable_cross_partition_query=False)
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("failed_to_get_history", tenant_id=tenant_id, error=str(e))
            return []

episodic_memory = EpisodicMemory()

