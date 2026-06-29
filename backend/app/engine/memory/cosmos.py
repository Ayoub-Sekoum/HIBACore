"""
Cosmos DB Chat Memory Service — Session & History Management.
Task 4.01 — Multi-Tenant Enterprise Chatbot.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

from azure.cosmos.aio import ContainerProxy
from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)


class CosmosMemoryService:
    """Service to handle chat history and session persistence in Cosmos DB."""

    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.COSMOS_ENDPOINT
        self.key = settings.COSMOS_KEY
        self.db_name = settings.COSMOS_DATABASE_NAME
        self.container_name = "conversations"
        self._client: CosmosClient | None = None

    async def _get_container(self) -> ContainerProxy:
        """
        Inizializzazione lazy del client Cosmos e restituzione del container.
        Supporta Managed Identity e Chiavi di Accesso.
        """
        if self._client is None:
            if not self.endpoint:
                logger.error("cosmos_endpoint_missing")
                raise AppException(ErrorCode.INFRA_901, detail="COSMOS_ENDPOINT not configured")

            credential = get_global_credential()
            # If key is provided (local dev), use it; otherwise use Managed Identity
            self._client = CosmosClient(
                url=self.endpoint,
                credential=self.key if self.key else credential
            )

        database = self._client.get_database_client(self.db_name)
        return database.get_container_client(self.container_name)

    async def create_session(self, tenant_id: str) -> str:
        """Creates a new chat session for a tenant."""
        if not tenant_id:
            raise AppException(ErrorCode.TENANT_101)

        container = await self._get_container()
        session_id = str(uuid.uuid4())

        document = {
            "id": session_id,
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "metadata": {}
        }

        try:
            await container.create_item(body=document)
            logger.info("chat_session_created", session_id=session_id, tenant_id=tenant_id)
            return session_id
        except Exception as e:
            logger.error("cosmos_create_session_failed", tenant_id=tenant_id, error=str(e))
            raise AppException(ErrorCode.MEM_401, detail=f"Failed to create session: {str(e)}")

    async def add_message(self, session_id: str, tenant_id: str, role: str, content: str) -> None:
        """Adds a message to an existing session and triggers async workers."""
        if not tenant_id:
            raise AppException(ErrorCode.TENANT_101)

        container = await self._get_container()

        try:
            # Read item (must specify partition key for efficient access)
            item = await container.read_item(item=session_id, partition_key=tenant_id)

            msg_id = str(uuid.uuid4())
            msg = {
                "id": msg_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            item["messages"].append(msg)

            # Update item (Optimistic Concurrency Control could be added here if needed)
            await container.replace_item(item=session_id, body=item)
            logger.debug("chat_message_added", session_id=session_id, role=role)

            # 3. Trigger Asynchronous Processing via Service Bus
            try:
                from app.services.messaging.bus import (
                    publish_to_entity_extraction_queue,
                    publish_to_persona_worker,
                    publish_to_summarize_queue,
                    publish_to_vectorize_queue,
                    publish_to_reflection_worker,
                )

                await publish_to_vectorize_queue(session_id, msg_id, content)
                await publish_to_entity_extraction_queue(session_id, content)
                await publish_to_persona_worker(session_id)
                await publish_to_reflection_worker(session_id)

                if len(item["messages"]) > 50:
                    await publish_to_summarize_queue(session_id)
            except ImportError:
                logger.warning("messaging_bus_not_found_skipping_hooks")

        except Exception as e:
            logger.error("cosmos_add_message_failed", session_id=session_id, error=str(e))
            raise AppException(ErrorCode.MEM_401, detail=f"Failed to add message: {str(e)}")

    async def get_history(self, session_id: str, tenant_id: str, limit: int = 50) -> list[dict[str, str]]:
        """Retrieves recent chat history for a session."""
        if not tenant_id:
            raise AppException(ErrorCode.TENANT_101)

        container = await self._get_container()
        try:
            item = await container.read_item(item=session_id, partition_key=tenant_id)
            messages = item.get("messages", [])
            recent_msgs = messages[-limit:]
            return [{"role": m["role"], "content": m["content"]} for m in recent_msgs]
        except Exception as e:
            logger.warning("cosmos_get_history_missing", session_id=session_id, error=str(e))
            return []

    async def list_sessions(self, tenant_id: str) -> list[dict[str, Any]]:
        """Lists all chat sessions for a specific tenant."""
        container = await self._get_container()
        query = "SELECT c.id, c.created_at, ARRAY_LENGTH(c.messages) AS message_count FROM c WHERE c.tenant_id = @tenant_id"
        parameters = [{"name": "@tenant_id", "value": tenant_id}]

        try:
            results = []
            items = container.query_items(query=query, parameters=parameters, enable_cross_partition_query=False)
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("cosmos_list_sessions_failed", tenant_id=tenant_id, error=str(e))
            raise AppException(ErrorCode.MEM_401, detail=f"Failed to list sessions: {str(e)}")

    async def save_session_reflection(self, session_id: str, tenant_id: str, reflection_data: dict[str, Any]) -> None:
        """Saves a session reflection (Bonus 3)."""
        container = await self._get_container()
        reflection_doc = {
            "id": f"reflection_{session_id}",
            "type": "reflection",
            "session_id": session_id,
            "tenant_id": tenant_id,
            "data": reflection_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        try:
            await container.upsert_item(body=reflection_doc)
        except Exception as e:
            logger.error("cosmos_save_reflection_failed", session_id=session_id, error=str(e))

    async def get_latest_reflection(self, tenant_id: str) -> dict[str, Any] | None:
        """Retrieves the most recent reflection for a tenant (Bonus 3)."""
        container = await self._get_container()
        query = "SELECT TOP 1 * FROM c WHERE c.tenant_id = @tenant_id AND c.type = 'reflection' ORDER BY c.updated_at DESC"
        parameters = [{"name": "@tenant_id", "value": tenant_id}]
        try:
            items = container.query_items(query=query, parameters=parameters, enable_cross_partition_query=False)
            async for item in items:
                return item.get("data")
            return None
        except Exception as e:
            logger.warning("cosmos_get_reflection_failed", tenant_id=tenant_id, error=str(e))
            return None

    async def close(self):
        """Closes the Cosmos client."""
        if self._client:
            await self._client.close()


cosmos_memory_service = CosmosMemoryService()
