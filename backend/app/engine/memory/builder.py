import asyncio
import os
from typing import Any

import structlog

from app.core.config import config_manager
from app.engine.ai.token_counter import count_tokens

logger = structlog.get_logger(__name__)


def _get_memory_service():
    """Returns mock or cosmos memory service based on configuration."""
    cosmos_endpoint = config_manager.settings.COSMOS_ENDPOINT
    if not cosmos_endpoint:
        from app.engine.memory.mock import mock_memory_service
        return mock_memory_service
    from app.engine.memory.cosmos import cosmos_memory_service
    return cosmos_memory_service


async def _safe_retrieve_and_rerank(query: str, tenant_id: str, top_k: int = 5):
    """Wrapper that gracefully degrades when Azure Search is unavailable."""
    try:
        from app.engine.ai.rag import retrieve_and_rerank
        return await retrieve_and_rerank(query, tenant_id, top_k=top_k)
    except Exception as e:
        logger.warning("rag_retriever_unavailable", error=str(e))
        return ("", [])


async def _safe_retrieve_semantic_memory(query: str, tenant_id: str):
    """Wrapper that gracefully degrades when pgvector is unavailable."""
    try:
        from app.engine.memory.pgvector import retrieve_semantic_memory
        return await retrieve_semantic_memory(query, tenant_id)
    except Exception as e:
        logger.warning("semantic_memory_unavailable", error=str(e))
        return []


async def _safe_get_graph_context(tenant_id: str, query: str):
    """Wrapper that gracefully degrades when Gremlin is unavailable."""
    try:
        from app.engine.memory.graph import get_graph_context
        return await get_graph_context(tenant_id, query)
    except Exception as e:
        logger.warning("graph_context_unavailable", error=str(e))
        return ""


async def _safe_compact_context(messages: list, tenant_id: str):
    """Wrapper for context compaction."""
    try:
        from app.engine.memory.summarizer import compact_context
        return await compact_context(messages, tenant_id)
    except Exception:
        return messages


# Budget allocation: 8000 tokens for the generated context (history + RAG)
MAX_CONTEXT_BUDGET = config_manager.settings.AI_MAX_CONTEXT_BUDGET

async def build_memory_context(
    session_id: str,
    tenant_id: str,
    current_query: str
) -> dict[str, Any]:
    """
    Task 4.02: Combina ultimi N messaggi Cosmos DB + top-K chunk pgvector/AI Search
    (filtro tenant_id) + entità Knowledge Graph. Calcola token budget per sorgente.
    """
    context_data: dict[str, Any] = {
        "history": [],
        "rag_context": "",
        "citations": [],
        "knowledge_graph": ""
    }

    memory_service = _get_memory_service()

    # 1. Parallel Fetching (Check 4 - Low Latency)
    async def get_history_safe():
        if session_id:
            return await memory_service.get_history(session_id, tenant_id, limit=config_manager.settings.AI_CHAT_HISTORY_LIMIT)
        return []

    async def get_reflection_safe():
        return await memory_service.get_latest_reflection(tenant_id)

    tasks = [
        get_history_safe(),
        get_reflection_safe(),
        _safe_retrieve_semantic_memory(current_query, tenant_id),
        _safe_retrieve_and_rerank(current_query, tenant_id, top_k=5),
        _safe_get_graph_context(tenant_id, current_query)
    ]

    # Executing all fetches in parallel (FIX 2 - Robust Handling)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Unpack with Reliability
    history_raw = results[0]
    latest_reflection = results[1]
    semantic_memory = results[2]
    rag_result = results[3]
    kg_context = results[4]

    # Critical failures -> graceful fallback instead of raise
    if isinstance(history_raw, Exception):
        logger.warning("history_fetch_failed_fallback", error=str(history_raw))
        history_raw = []

    if isinstance(rag_result, Exception):
        logger.warning("rag_fetch_failed_fallback", error=str(rag_result))
        rag_result = ("", [])

    # Non-critical failures -> Fallback
    if isinstance(latest_reflection, Exception):
        logger.warning("reflection_fetch_failed", error=str(latest_reflection))
        latest_reflection = None

    if isinstance(semantic_memory, Exception):
        logger.warning("semantic_memory_failed", error=str(semantic_memory))
        semantic_memory = []

    if isinstance(kg_context, Exception):
        logger.warning("graph_context_failed", error=str(kg_context))
        kg_context = ""

    # Final unpacking of RAG
    if isinstance(rag_result, tuple) and len(rag_result) == 2:
        rag_context, citations = rag_result
    else:
        rag_context, citations = "", []

    # 2. Process History & Compaction
    if history_raw:
        context_data["history"] = await _safe_compact_context(list(history_raw), tenant_id)

    # 3. Continuity Framework (Bonus 3)
    if latest_reflection and isinstance(latest_reflection, dict):
        reflection_msg = {
            "role": "system",
            "content": f"[CONTINUITY]: Ultima riflessione: {latest_reflection.get('summary', '')}"
        }
        context_data["history"].insert(0, reflection_msg)

    # 4. Integrate Semantic Memory
    if semantic_memory and isinstance(semantic_memory, list):
        current_history = context_data["history"]
        if isinstance(current_history, list):
            context_data["history"] = semantic_memory + current_history

    context_data["rag_context"] = rag_context if isinstance(rag_context, str) else ""
    context_data["citations"] = list(citations) if citations else []
    context_data["knowledge_graph"] = kg_context if isinstance(kg_context, str) else ""

    # 5. Sequential Context Processing (Token-aware)
    final_rag_context = ""
    final_history = []
    current_tokens = 0

    kg_text = kg_context if isinstance(kg_context, str) else ""
    kg_tokens = count_tokens(kg_text)
    if kg_tokens < MAX_CONTEXT_BUDGET:
        context_data["knowledge_graph"] = kg_text
        current_tokens += kg_tokens

    if isinstance(context_data["history"], list):
        for msg in reversed(context_data["history"]):
            msg_tokens = count_tokens(msg.get("content", "") if isinstance(msg, dict) else "")
            if current_tokens + msg_tokens < (MAX_CONTEXT_BUDGET * 0.7):
                final_history.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
    context_data["history"] = final_history

    remaining_budget = MAX_CONTEXT_BUDGET - current_tokens
    rag_text = rag_context if isinstance(rag_context, str) else ""
    if remaining_budget > 0:
        if count_tokens(rag_text) > remaining_budget:
            logger.info("rag_context_truncated", needed=count_tokens(rag_text), limit=remaining_budget)
            rag_text = rag_text[:(remaining_budget * 4)]
        final_rag_context = rag_text

    context_data["rag_context"] = final_rag_context
    context_data["citations"] = list(citations) if citations else []

    return context_data

