"""
Semantic Memory Service — Long-term retrieval using pgvector.
Task 4.03 & 4.04 — Multi-Tenant Enterprise Chatbot.
"""

from typing import Any

import psycopg
import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from openai import AsyncAzureOpenAI
from pgvector.psycopg import register_vector

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

class SemanticMemoryService:
    """Service to handle semantic search and indexing of chat history using pgvector."""

    def __init__(self):
        self.settings = get_settings()
        self._pool = None
        self._llm_client: AsyncAzureOpenAI | None = None

    async def _get_llm_client(self) -> AsyncAzureOpenAI:
        """Initializes the Azure OpenAI client for embeddings."""
        if self._llm_client is None:
            if self.settings.AZURE_OPENAI_API_KEY:
                self._llm_client = AsyncAzureOpenAI(
                    api_key=self.settings.AZURE_OPENAI_API_KEY,
                    azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
                    api_version="2024-05-01-preview"
                )
            else:
                from app.core.credentials import get_bearer_token_provider
                credential = get_global_credential()
                token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
                self._llm_client = AsyncAzureOpenAI( # type: ignore
                    azure_ad_token_provider=token_provider,
                    azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
                    api_version="2024-05-01-preview"
                )
        return self._llm_client

    async def _get_connection(self):
        """Returns a connection to the PostgreSQL database."""
        settings = self.settings
        if not settings.DB_HOST:
            return None

        conn_str = f"host={settings.DB_HOST} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD} sslmode=require"
        try:
            conn = await psycopg.AsyncConnection.connect(conn_str)
            await register_vector(conn)
            return conn
        except Exception as e:
            logger.error("postgres_connection_failed", error=str(e))
            return None

    async def index_message(self, tenant_id: str, session_id: str, message_id: str, content: str):
        """Generates embedding for a message and stores it in pgvector."""
        if not self.settings.DB_HOST:
            return

        client = await self._get_llm_client()
        try:
            response = await client.embeddings.create(
                input=content,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding

            conn = await self._get_connection()
            if not conn:
                return

            async with conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO message_embeddings (tenant_id, session_id, message_id, content, embedding) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (tenant_id, session_id, message_id, content, embedding)
                    )
            logger.info("message_indexed_semantically", message_id=message_id, tenant_id=tenant_id)
        except Exception as e:
            logger.error("semantic_indexing_failed", message_id=message_id, error=str(e))

    async def search_memory(self, tenant_id: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Searches long-term memory for relevant past interactions."""
        if not self.settings.DB_HOST:
            return []

        client = await self._get_llm_client()
        try:
            response = await client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding

            conn = await self._get_connection()
            if not conn:
                return []

            async with conn:
                async with conn.cursor() as cur:
                    # Using cosine similarity (<=> is negative cosine distance in pgvector)
                    await cur.execute(
                        "SELECT content, session_id, timestamp FROM message_embeddings "
                        "WHERE tenant_id = %s "
                        "ORDER BY embedding <=> %s LIMIT %s",
                        (tenant_id, query_embedding, top_k)
                    )
                    results = await cur.fetchall()

            return [{"content": r[0], "session_id": r[1], "timestamp": r[2]} for r in results]
        except Exception as e:
            logger.error("semantic_search_failed", query=query, error=str(e))
            return []

semantic_memory_service = SemanticMemoryService()
