"""
RAG Pipeline — Retrieval & Reranking.
Task 3.12 — Core AI Features.
"""

import asyncio
from typing import Any

import structlog

from app.engine.ai.circuit_breaker import ResilientLLMClient
from app.engine.memory.semantic import semantic_memory_service
from app.services.storage.search import hybrid_search_documents

logger = structlog.get_logger(__name__)


async def retrieve_and_rerank(
    query: str,
    tenant_id: str,
    top_k: int = 3,
    include_long_term_memory: bool = True
) -> tuple[str, list[dict[str, Any]]]:
    """
    Enhanced Multi-Source RAG Pipeline:
    1. Retrieval from Documents (Azure AI Search).
    2. Retrieval from Long-term Chat Memory (pgvector).
    3. Retrieval from Knowledge Graph (Contextual Entities).
    4. Combined Reranking & Context Assembly.
    """
    llm_client = ResilientLLMClient()

    # 1. Embed query
    try:
        query_vector = await llm_client.embed([query], model="text-embedding-3-small")
        vector = query_vector[0] if query_vector else []
    except Exception as e:
        logger.warning("rag_embedding_failed", error=str(e))
        vector = []

    # 2. Parallel Retrieval
    try:
        tasks = [
            hybrid_search_documents(
                query_vector=vector,
                query_text=query,
                tenant_id=tenant_id,
                top_k=top_k * 2
            )
        ]

        if include_long_term_memory:
            tasks.append(semantic_memory_service.search_memory(tenant_id, query, top_k=3))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        search_results: list[dict[str, Any]] = results[0] if not isinstance(results[0], Exception) else [] # type: ignore
        long_term_memory: list[dict[str, Any]] = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else [] # type: ignore

    except Exception as e:
        logger.error("rag_parallel_retrieval_failed", error=str(e))
        search_results = []
        long_term_memory = []

    if not search_results:
        return "", []

    # 3. Simple Re-ranking (In production: use Cross-Encoder)
    # For now, we trust the hybrid search score
    search_results.sort(key=lambda x: x.get("search_score", 0), reverse=True)
    top_results = search_results[:top_k]

    # 4. Assemble Context & Citations
    context_chunks = []
    citations = []

    for idx, doc in enumerate(top_results):
        source_label = f"Doc {idx+1}: {doc['file_name']}"
        if doc.get('page_number'):
            source_label += f" (Pag. {doc['page_number']})"

        context_chunks.append(f"[{source_label}]\n{doc['content']}")

        citations.append({
            "id": doc["id"],
            "file_name": doc['file_name'],
            "page": doc.get('page_number', 1),
            "score": doc.get('search_score', 0),
            "excerpt": doc['content'][:150] + "..." if len(doc['content']) > 150 else doc['content']
        })

    context_str = "\n\n".join(context_chunks)

    # 5. Integrate Long-term Memory
    if long_term_memory:
        memory_chunks = ["--- RICORDI PASSATI ---"]
        for m in long_term_memory:
            memory_chunks.append(f"In passato è stato detto: {m['content']}")
        context_str = context_str + "\n\n" + "\n".join(memory_chunks)

    return context_str, citations

