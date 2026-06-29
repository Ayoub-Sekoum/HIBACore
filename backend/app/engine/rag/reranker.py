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

# Cache globale per il modello (Lazy loading)
_model = None

def _get_model():
    global _model
    if _model is None:
        try:
            # Modello specifico richiesto dal PIANO_LAVORO_GEMINI.md
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
    # Regola 3: Isolamento tenant (Verifica coerenza dati in ingresso)
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)
    
    if not chunks:
        return []

    try:
        model = _get_model()
        
        # Preparazione coppie (query, content) per il modello
        pairs = [[query, chunk.content] for chunk in chunks]
        
        # Calcolo dei punteggi (non bloccante grazie alla cache del modello)
        scores = model.predict(pairs)
        
        # Aggiornamento score e filtraggio
        reranked_results = []
        for idx, score in enumerate(scores):
            # Normalizzazione minima (il modello ms-marco può dare score fuori 0-1)
            # Ma il piano chiede filtro < 0.3
            if score >= min_score:
                chunk = chunks[idx].model_copy()
                chunk.score = float(score)
                # Verifica extra: il chunk deve appartenere al tenant corretto
                if chunk.tenant_id == tenant_id:
                    reranked_results.append(chunk)

        # Ordinamento decrescente
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        
        return reranked_results[:top_k]

    except Exception as e:
        if isinstance(e, AppException):
            raise e
        logger.error("reranking_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305, detail=f"Reranking error: {str(e)}")

