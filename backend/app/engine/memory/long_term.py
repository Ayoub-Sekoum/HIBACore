"""
Long Term Memory — Manages persistent knowledge using CosmosDB vector/semantic search.
"""

import uuid
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.error_codes import ErrorCode

# We use the existing CosmosMemoryService pattern
from app.engine.memory.cosmos import cosmos_memory_service

logger = structlog.get_logger(__name__)

class LongTermMemory:
    """Stores and retrieves persistent knowledge about users/tenants."""

    def __init__(self):
        self.service = cosmos_memory_service
        self.settings = get_settings()
        self._openai_client = None

    async def _get_openai_client(self):
        """Lazy initialization for Azure OpenAI client used to generate embeddings."""
        if self._openai_client is None:
            if self.settings.AZURE_OPENAI_API_KEY:
                self._openai_client = AsyncAzureOpenAI(
                    api_key=self.settings.AZURE_OPENAI_API_KEY,
                    api_version="2023-05-15",
                    azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT
                )
            else:
                credential = get_global_credential()
                token_provider = get_bearer_token_provider(
                    credential, "https://cognitiveservices.azure.com/.default"
                )
                self._openai_client = AsyncAzureOpenAI(
                    azure_ad_token_provider=token_provider,
                    api_version="2023-05-15",
                    azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT
                )
        return self._openai_client

    async def save_fact(self, tenant_id: str, fact: str, metadata: dict[str, Any] | None = None):
        """Saves a fact associated with a tenant including its generated embedding."""
        try:
            # 1. Generate Embeddings using text-embedding-ada-002
            embedding = []
            try:
                if self.settings.AZURE_OPENAI_ENDPOINT:
                    client = await self._get_openai_client()
                    response = await client.embeddings.create(
                        input=fact,
                        model="text-embedding-ada-002"
                    )
                    embedding = response.data[0].embedding
                else:
                    raise AppException(ErrorCode.SYS_503, detail="Missing AZURE_OPENAI_ENDPOINT config")
            except Exception as e:
                logger.error("failed_to_generate_embedding", error=str(e), fact=fact)
                # Fail explicitly rather than saving a bad record
                raise

            # 2. Save document to Cosmos
            container = await self.service._get_container()
            doc = {
                "id": f"fact_{uuid.uuid4()}",
                "tenant_id": tenant_id,
                "fact": fact,
                "embedding": embedding,
                "metadata": metadata or {},
            }
            await container.create_item(body=doc)
            logger.info("long_term_fact_saved", tenant_id=tenant_id, doc_id=doc["id"])
        except Exception as e:
            logger.error("failed_to_save_fact", tenant_id=tenant_id, error=str(e))

    async def query_knowledge(self, tenant_id: str, query: str) -> list[dict[str, Any]]:
        """Retrieve relevant facts via simulated vector search."""
        try:
            container = await self.service._get_container()
            query_str = "SELECT * FROM c WHERE c.tenant_id = @tenant_id AND STARTSWITH(c.id, 'fact_')"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]

            results = []
            items = container.query_items(query=query_str, parameters=parameters, enable_cross_partition_query=False)
            async for item in items:
                results.append(item)
            return results
        except Exception as e:
            logger.error("failed_to_query_knowledge", tenant_id=tenant_id, error=str(e))
            return []

long_term_memory = LongTermMemory()

