from typing import Any

import structlog

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)

async def retrieve_semantic_memory(query: str, tenant_id: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Task 4.04: Semantic Memory Retriever (pgvector).
    Simula la ricerca su PostgreSQL/pgvector usando operatore <=> con soglia 0.75 e filtro tenant_id.
    """
    if not tenant_id:
        logger.error("semantic_memory_search_without_tenant_id")
        raise AppException(ErrorCode.TENANT_101)

    llm_client = ResilientLLMClient()

    try:
        await llm_client.embed([query])
        # In a real environment, query PostgreSQL:
        # SELECT content FROM message_embeddings
        # WHERE tenant_id = $1 AND embedding <=> $2 < 0.25 (which means similarity > 0.75)
        # ORDER BY embedding <=> $2 LIMIT $3
        logger.info("executing_pgvector_search", tenant_id=tenant_id, query_len=len(query))
    except Exception as e:
        logger.warning("semantic_memory_embedding_failed", error=str(e))

    # Mocked results
    return [
        {"role": "user", "content": "Il CEO dell'azienda si chiama Mario Rossi."},
        {"role": "assistant", "content": "Capito, ho memorizzato che il CEO è Mario Rossi."}
    ][:top_k]

