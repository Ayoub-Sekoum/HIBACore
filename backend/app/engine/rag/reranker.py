"""
Task 3.12 — Cross-Encoder Re-ranking.
Logica: Raffina i risultati della ricerca ibrida usando un modello Cross-Encoder più preciso.
"""

from typing import Any
import structlog
from sentence_transformers import CrossEncoder

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.rag.retriever import SearchResult

logger = structlog.get_logger(__name__)

# Global cache for the model (Lazy loading)
_model = None

def _get_model():
    global _model
    if _model is None:
        try:
            # Specific cross-encoder model
            _model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        except Exception as e:
            logger.error("reranker_model_load_failed", error=str(e))
            raise AppException(ErrorCode.RAG_305, detail="Failed to load cross-encoder model")
    return _model

async def rerank_chunks(
    tenant_id: str,
    query: str,
    chunks: list[SearchResult],
    top_k: int = 5,
    min_score: float = 0.3,
) -> list[SearchResult]:
    """
    Cross-encoder reranking.
    Usa sentence-transformers cross-encoder/ms-marco-MiniLM-L-6-v2.
    Regola 3: tenant_id come primo parametro.
    """
    # Rule 3: Tenant isolation (Check incoming data consistency)
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)
    
    if not chunks:
        return []

    try:
        model = _get_model()
        
        # Preparing pairs (query, content) for the model
        pairs = [[query, chunk.content] for chunk in chunks]
        
        # Score calculation (non-blocking thanks to model cache)
        scores = model.predict(pairs)
        
        # Score update and filtering
        reranked_results = []
        for idx, score in enumerate(scores):
            # Minimum normalization (the ms-marco model can give scores outside 0-1)
            # But the plan asks for filter < 0.3
            if score >= min_score:
                chunk = chunks[idx].model_copy()
                chunk.score = float(score)
                # Extra check: The chunk must belong to the correct tenant
                if chunk.tenant_id == tenant_id:
                    reranked_results.append(chunk)

        # Descending sort
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        
        return reranked_results[:top_k]

    except Exception as e:
        if isinstance(e, AppException):
            raise e
        logger.error("reranking_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305, detail=f"Reranking error: {str(e)}")

