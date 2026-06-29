"""
approval.py — Gestione della coda di approvazione per azioni ad alto rischio.
Percorso: backend/app/services/policy/approval.py
"""
import uuid
import structlog
from datetime import datetime, timezone
from typing import Any, Optional
from azure.cosmos.aio import CosmosClient, ContainerProxy
from app.core.config import get_settings
from app.core.credentials import get_global_credential

logger = structlog.get_logger(__name__)

class ApprovalQueue:
    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.COSMOS_ENDPOINT
        self.key = settings.COSMOS_KEY
        self.db_name = settings.COSMOS_DATABASE_NAME
        self.container_name = "approvals"
        self._client: Optional[CosmosClient] = None

    async def _get_container(self) -> ContainerProxy:
        if self._client is None:
            credential = get_global_credential()
            self._client = CosmosClient(
                url=self.endpoint,
                credential=self.key if self.key else credential
            )
        database = self._client.get_database_client(self.db_name)
        return database.get_container_client(self.container_name)

    async def add(self, tenant_id: str, tool_name: str, args: dict, decision: Any) -> str:
        """Aggiunge una richiesta di approvazione alla coda."""
        approval_id = str(uuid.uuid4())
        doc = {
            "id": approval_id,
            "tenant_id": tenant_id,
            "partition_key": tenant_id,
            "type": "approval_request",
            "status": "pending",
            "tool_name": tool_name,
            "args": args,
            "reason": decision.reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            container = await self._get_container()
            await container.create_item(body=doc)
            logger.info("approval_request_queued", tenant_id=tenant_id, approval_id=approval_id)
            return approval_id
        except Exception as e:
            logger.error("approval_queue_failed", error=str(e))
            return approval_id

    async def get_all_pending(self, tenant_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Lista richieste pendenti (Super Admin o specifico Tenant)."""
        container = await self._get_container()
        if tenant_id:
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id AND c.status = 'pending'"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]
        else:
            query = "SELECT * FROM c WHERE c.status = 'pending'"
            parameters = []
        
        try:
            items = container.query_items(query=query, parameters=parameters, enable_cross_partition_query=(not tenant_id))
            results = []
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("approval_fetch_failed", error=str(e))
            return []

approval_queue = ApprovalQueue()
