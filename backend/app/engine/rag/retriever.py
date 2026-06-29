"""
Task 3.11 — Hybrid Search + Semantic Ranker (RRF Fusion).
Logica ispirata da OpenClaw: bilancia rilevanza semantica e keyword con RRF.
"""

import asyncio
import re
from collections import OrderedDict
from typing import Any

import structlog
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from pydantic import BaseModel, Field

from app.core.config import config_manager, get_settings
from app.core.credentials import get_global_credential
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)


class SearchResult(BaseModel):
    """Schema per i risultati del Task 3.11."""
    content: str
    file_name: str
    page_number: int
    chunk_index: int
    score: float
    tenant_id: str
    id: str | None = None


# ── Embedding Cache (E.2) ─────────────────────────────────────
_embedding_cache: OrderedDict[str, list[float]] = OrderedDict()
MAX_EMBD_CACHE = 100


async def _get_cached_embedding(query: str, tenant_id: str) -> list[float]:
    """LRU-style cache per gli embedding delle query — evita costi doppi. (E.2)"""
    if query in _embedding_cache:
        # MRU move
        emb = _embedding_cache.pop(query)
        _embedding_cache[query] = emb
        return emb

    llm_client = ResilientLLMClient()
    try:
        query_vector = await llm_client.embed([query], model="text-embedding-3-small")
        if not query_vector:
            raise AppException(ErrorCode.RAG_304, detail="Empty embedding result")
        embedding = query_vector[0]

        _embedding_cache[query] = embedding
        if len(_embedding_cache) > MAX_EMBD_CACHE:
            _embedding_cache.popitem(last=False)

        return embedding
    except AppException:
        raise
    except Exception as e:
        logger.error("rag_embedding_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_304)


# ── Search Client Singleton (E.3) ─────────────────────────────
_search_client_instance: SearchClient | None = None


def _get_search_client(settings) -> SearchClient:
    """Inizializza il client search una sola volta (connection pooling). (E.3)"""
    global _search_client_instance
    if _search_client_instance is None:
        endpoint = settings.AZURE_SEARCH_ENDPOINT
        key = settings.AZURE_SEARCH_KEY
        index_name = settings.AZURE_SEARCH_INDEX

        if key:
            credential = AzureKeyCredential(key)
        else:
            credential = get_global_credential()

        _search_client_instance = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )
    return _search_client_instance


async def close_search_client() -> None:
    """Chiudi il SearchClient al shutdown dell'app. (E.3)"""
    global _search_client_instance
    if _search_client_instance:
        await _search_client_instance.close()
        _search_client_instance = None


# ── Public API ────────────────────────────────────────────────

async def hybrid_search(
    query: str,
    tenant_id: str,
    top_k: int = 5,
    use_semantic_ranker: bool = True,
) -> list[SearchResult]:
    """
    Hybrid search: vettoriale + BM25 + RRF fusion + semantic ranker.
    Sempre filtra per tenant_id — mai senza.
    """
    # Isolamento tenant SEMPRE + Sanitizzazione (D.1)
    if not tenant_id or not re.match(r'^[a-zA-Z0-9\-_]+$', tenant_id):
        logger.error("invalid_tenant_id_injection_attempt", tenant_id=tenant_id)
        raise AppException(ErrorCode.TENANT_101)

    # PASSO 1 — Genera embedding della query utente (Cached — E.2)
    embedding = await _get_cached_embedding(query, tenant_id)

    # PASSO 2 & 3 — Parallel Retrieval (Vettoriale + Keyword)
    try:
        retrieval_top_k = config_manager.settings.AI_RETRIEVER_TOP_K
        vector_task = _vector_search(embedding, tenant_id, top_k=retrieval_top_k)
        keyword_task = _keyword_search(query, tenant_id, top_k=retrieval_top_k)

        vector_results, keyword_results = await asyncio.gather(vector_task, keyword_task)
    except AppException:
        raise
    except Exception as e:
        logger.error("rag_parallel_search_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305)

    # PASSO 4 — Reciprocal Rank Fusion (RRF)
    # Formula: score = (1 / (60 + rank_vettoriale)) + (1 / (60 + rank_bm25))
    fused_results = _reciprocal_rank_fusion(vector_results, keyword_results)

    # PASSO 5 — Semantic Ranker Azure (opzionale)
    if use_semantic_ranker:
        try:
            settings = get_settings()
            client = _get_search_client(settings)
            
            # Eseguiamo una chiamata specifica per il re-ranking semantico sui top risultati fusi
            # Azure AI Search richiede 'semantic' query type
            semantic_results = await client.search(
                search_text=query,
                filter=f"tenant_id eq '{tenant_id}'",
                query_type="semantic",
                semantic_configuration_name="default", # Assumiamo configurazione 'default'
                top=top_k,
                select=["id", "tenant_id", "file_name", "page_number", "chunk_index", "content"]
            )
            
            final_results = []
            async for r in semantic_results:
                final_results.append(SearchResult(
                    id=r["id"],
                    content=r["content"],
                    file_name=r["file_name"],
                    page_number=r.get("page_number", 0),
                    chunk_index=r.get("chunk_index", 0),
                    score=r.get("@search.reranker_score", 0.0),
                    tenant_id=r["tenant_id"]
                ))
            if final_results:
                return final_results

        except Exception as e:
            logger.warning("semantic_ranker_failed", tenant_id=tenant_id, error=str(e))
            # Fallback al RRF se il semantic ranker fallisce (Configurazione o Limiti)
            pass

    # PASSO 6 — Restituisci risultato top_k richiesto
    return fused_results[:top_k]


# ── Private Helpers ───────────────────────────────────────────

async def _vector_search(
    embedding: list[float],
    tenant_id: str,
    top_k: int,
) -> list[SearchResult]:
    """Ricerca vettoriale pura su Azure AI Search."""
    settings = get_settings()
    client = _get_search_client(settings)

    results = []
    try:
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="vector"
        )

        search_results = await client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=f"tenant_id eq '{tenant_id}'",
            select=["id", "tenant_id", "file_name", "page_number", "chunk_index", "content"],
            top=top_k
        )
        async for r in search_results:
            results.append(SearchResult(
                id=r["id"],
                content=r["content"],
                file_name=r["file_name"],
                page_number=r.get("page_number", 0),
                chunk_index=r.get("chunk_index", 0),
                score=r.get("@search.score", 0.0),
                tenant_id=r["tenant_id"]
            ))
        return results
    except Exception as e:
        logger.error("vector_search_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305)


async def _keyword_search(
    query: str,
    tenant_id: str,
    top_k: int,
) -> list[SearchResult]:
    """Ricerca BM25 keyword su Azure AI Search."""
    settings = get_settings()
    client = _get_search_client(settings)

    results = []
    try:
        search_results = await client.search(
            search_text=query,
            filter=f"tenant_id eq '{tenant_id}'",
            select=["id", "tenant_id", "file_name", "page_number", "chunk_index", "content"],
            top=top_k
        )
        async for r in search_results:
            results.append(SearchResult(
                id=r["id"],
                content=r["content"],
                file_name=r["file_name"],
                page_number=r.get("page_number", 0),
                chunk_index=r.get("chunk_index", 0),
                score=r.get("@search.score", 0.0),
                tenant_id=r["tenant_id"]
            ))
        return results
    except Exception as e:
        logger.error("keyword_search_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305)


def _reciprocal_rank_fusion(
    vector_results: list[SearchResult],
    keyword_results: list[SearchResult],
    k: int = 60,
) -> list[SearchResult]:
    """
    RRF: combina due liste di risultati senza bisogno di normalizzare gli score.
    Logica da OpenClaw: bilancia i segnali diversi con una costante di ranking.
    """
    vector_ranks = {res.id: i for i, res in enumerate(vector_results, 1) if res.id}
    keyword_ranks = {res.id: i for i, res in enumerate(keyword_results, 1) if res.id}

    all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

    final_list = []
    for doc_id in all_ids:
        r_v = vector_ranks.get(doc_id, 999)
        r_k = keyword_ranks.get(doc_id, 999)
        score = (1.0 / (k + r_v)) + (1.0 / (k + r_k))

        doc = (
            next((r for r in vector_results if r.id == doc_id), None)
            or next((r for r in keyword_results if r.id == doc_id), None)
        )
        if doc:
            new_doc = doc.model_copy()
            new_doc.score = score
            final_list.append(new_doc)

    final_list.sort(key=lambda x: x.score, reverse=True)
    return final_list

