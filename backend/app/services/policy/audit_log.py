"""
audit_log.py — Gestione log di audit per cambi policy e dinieghi.
Percorso: backend/app/services/policy/audit_log.py
"""
import uuid
import structlog
from datetime import datetime, timezone
from typing import Any, Optional
from azure.cosmos.aio import CosmosClient, ContainerProxy
from app.core.config import get_settings
from app.core.credentials import get_global_credential

logger = structlog.get_logger(__name__)

class AuditLogService:
    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.COSMOS_ENDPOINT
        self.key = settings.COSMOS_KEY
        self.db_name = settings.COSMOS_DATABASE_NAME
        self.container_name = "audit_logs"
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

    async def log_policy_change(
        self,
        tenant_id: str,
        actor_id: str,
        actor_role: str,
        action: str,
        field_changed: str,
        old_value: Any,
        new_value: Any,
        result: str = "success"
    ) -> None:
        """Scrive un log di audit in Cosmos DB (Async/Fire-and-forget inside the loop)."""
        audit_entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "partition_key": tenant_id,
            "type": "audit_log",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "field_changed": field_changed,
            "old_value": old_value,
            "new_value": new_value,
            "result": result
        }
        try:
            container = await self._get_container()
            await container.create_item(body=audit_entry)
            logger.info("audit_log_created", tenant_id=tenant_id, action=action)
        except Exception as e:
            logger.warning("audit_log_failed_falling_back_to_structlog", error=str(e))
            # Fallback a logging strutturato se Cosmos è giù
            logger.info("policy_audit_event", **audit_entry)

    async def log_policy_denial(self, tenant_id: str, actor_id: str, tool_name: str, reason: str, error_code: str):
        """Logga i dinieghi del Policy Engine."""
        entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "partition_key": tenant_id,
            "type": "policy_denial",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "tool_name": tool_name,
            "reason": reason,
            "error_code": error_code,
            "result": "denied"
        }
        try:
            container = await self._get_container()
            await container.create_item(body=entry)
        except Exception as e:
            logger.info("policy_denied_event", **entry)

    async def get_audit_log(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Legge audit log.
        Se tenant_id=None → super admin, vede tutto.
        Se tenant_id specificato → vede solo il suo.
        """
        container = await self._get_container()
        if tenant_id:
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id ORDER BY c.timestamp DESC OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
        else:
            query = "SELECT * FROM c ORDER BY c.timestamp DESC OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit}
            ]
        
        try:
            items = container.query_items(query=query, parameters=parameters, enable_cross_partition_query=(not tenant_id))
            results = []
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("audit_log_fetch_failed", error=str(e))
            return []

audit_log_service = AuditLogService()
