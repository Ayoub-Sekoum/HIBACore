"""
policy_store.py — Gestione persistenza delle policy su Cosmos DB + Cache Redis.
Percorso: backend/app/services/policy/policy_store.py
"""
import uuid
import structlog
from datetime import datetime, timezone
from typing import Optional, Any
from azure.cosmos.aio import CosmosClient, ContainerProxy
from app.core.config import get_settings
from app.core.credentials import get_global_credential
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.services.policy.plan_definitions import PLAN_DEFINITIONS
from app.services.policy.notification_service import notification_service

logger = structlog.get_logger(__name__)

# Simple in-memory cache as a fallback if Redis is not configured/accessible
_policy_cache: dict[str, dict[str, Any]] = {}

class PolicyStore:
    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.COSMOS_ENDPOINT
        self.key = settings.COSMOS_KEY
        self.db_name = settings.COSMOS_DATABASE_NAME
        self.container_name = "policies"
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

    async def get_tenant_policy(self, tenant_id: str) -> Optional[dict[str, Any]]:
        """Legge la policy da Cosmos DB con cache locale (60s simulation)."""
        if tenant_id in _policy_cache:
            # TODO: Implement real or Redis deadline logic
            return _policy_cache[tenant_id]

        try:
            container = await self._get_container()
            policy = await container.read_item(item=f"policy-{tenant_id}", partition_key=tenant_id)
            _policy_cache[tenant_id] = policy
            return policy
        except Exception as e:
            logger.warning("policy_fetch_failed", tenant_id=tenant_id, error=str(e))
            return None

    async def create_tenant_policy(self, tenant_id: str, plan: str, created_by: str) -> dict[str, Any]:
        """Crea la policy di default per un nuovo tenant basata sul piano."""
        plan_def = PLAN_DEFINITIONS.get(plan.lower())
        if not plan_def:
            raise AppException(ErrorCode.POLICY_003, detail=f"Invalid plan: {plan}")

        policy_doc = {
            "id": f"policy-{tenant_id}",
            "tenant_id": tenant_id,
            "partition_key": tenant_id,
            "type": "tenant_policy",
            "status": "active",
            "plan": plan.lower(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": created_by,
            "tool_allowlist": plan_def.allowed_tools,
            "require_approval_for_high_risk": plan_def.require_approval_for_high_risk,
            "max_thinking_level": plan_def.max_thinking_level,
            "max_file_size_mb": plan_def.max_file_size_mb,
            "sandbox_timeout_seconds": plan_def.sandbox_timeout_seconds,
            "network_allowlist": [],
            "shell_commands_allowlist": ["ls", "cat", "grep"] if plan == "enterprise" else [],
            "admin_can_modify": plan_def.admin_can_modify
        }

        try:
            container = await self._get_container()
            await container.upsert_item(body=policy_doc)
            _policy_cache[tenant_id] = policy_doc
            
            # Real-time notification
            await notification_service.broadcast(
                tenant_id, "policy_created", f"Nuova policy per tenant {tenant_id} creata."
            )
            
            return policy_doc
        except Exception as e:
            logger.error("policy_creation_failed", tenant_id=tenant_id, error=str(e))
            raise AppException(ErrorCode.MEM_401, detail="Failed to create tenant policy")

    async def update_tenant_policy(
        self, tenant_id: str, updates: dict, updated_by: str, is_super_admin: bool
    ) -> dict[str, Any]:
        """Aggiorna la policy verificando i permessi di admin_can_modify."""
        policy = await self.get_tenant_policy(tenant_id)
        if not policy:
            raise AppException(ErrorCode.TENANT_104)

        if not is_super_admin:
            allowed_fields = policy.get("admin_can_modify", [])
            for field in updates.keys():
                if field not in allowed_fields:
                    logger.warning("unauthorized_policy_update_attempt", 
                                   tenant_id=tenant_id, field=field, actor=updated_by)
                    raise AppException(ErrorCode.POLICY_002)

        policy.update(updates)
        policy["updated_at"] = datetime.now(timezone.utc).isoformat()
        policy["updated_by"] = updated_by

        try:
            container = await self._get_container()
            await container.replace_item(item=policy["id"], body=policy)
            _policy_cache[tenant_id] = policy
            
            # Real-time notification
            await notification_service.broadcast(
                tenant_id, "policy_updated", f"Policy aggiornata da {updated_by}", {"fields": list(updates.keys())}
            )
            if is_super_admin:
                await notification_service.broadcast_super("tenant_policy_changed", f"Policy del tenant {tenant_id} modificata.")
            
            return policy
        except Exception as e:
            logger.error("policy_update_failed", tenant_id=tenant_id, error=str(e))
            raise AppException(ErrorCode.MEM_401, detail="Failed to update policy")

    async def suspend_tenant(self, tenant_id: str, reason: str, by: str) -> None:
        """Sospende il tenant invalidando immediatamente la cache."""
        await self.update_tenant_policy(tenant_id, {"status": "suspended"}, by, True)
        if tenant_id in _policy_cache:
            del _policy_cache[tenant_id]

    async def list_all_tenants(self) -> list[dict[str, Any]]:
        """Lista tutti i tenant con la loro configurazione base (Super Admin only)."""
        container = await self._get_container()
        query = "SELECT c.tenant_id, c.status, c.plan, c.tool_allowlist, c.max_thinking_level FROM c WHERE c.type = 'tenant_policy'"
        try:
            items = container.query_items(query=query, enable_cross_partition_query=True)
            results = []
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("cosmos_list_all_tenants_failed", error=str(e))
            return []

policy_store = PolicyStore()
async def get_tenant_policy(tenant_id: str): return await policy_store.get_tenant_policy(tenant_id)
