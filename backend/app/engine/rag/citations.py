"""
Task 3.12 — Citations Engine & Context Assembly.
Logica: Costruisce il contesto per l'AI rispettando i token e estrae citazioni verificate.
"""

from typing import Any
from pydantic import BaseModel, Field
import tiktoken
import structlog

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.rag.retriever import SearchResult

logger = structlog.get_logger(__name__)

class Citation(BaseModel):
    """Schema per le citazioni verificate."""
    file_name: str
    page_number: int
    score: float
    excerpt: str

def build_rag_context(
    tenant_id: str,
    chunks: list[SearchResult],
    max_tokens: int = 8000,
) -> str:
    """
    Assembla il contesto RAG da dare al modello.
    Rispetta il budget token. Se supera: tronca dall'ultimo chunk.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    try:
        encoding = tiktoken.get_encoding("cl100k_base") # Standard for GPT-4
        
        context_parts = []
        current_tokens = 0
        
        for chunk in chunks:
            # Verifica isolamento tenant
            if chunk.tenant_id != tenant_id:
                continue
                
            formatted_chunk = f"[Fonte: {chunk.file_name}, Pagina {chunk.page_number}]\n{chunk.content}\n"
            chunk_tokens = len(encoding.encode(formatted_chunk))
            
            if current_tokens + chunk_tokens > max_tokens:
                logger.info("rag_context_token_limit_reached", current_tokens=current_tokens, limit=max_tokens)
                break
                
            context_parts.append(formatted_chunk)
            current_tokens += chunk_tokens
            
        return "\n---\n".join(context_parts)

    except Exception as e:
        logger.error("rag_context_assembly_failed", tenant_id=tenant_id, error=str(e))
        raise AppException(ErrorCode.RAG_305, detail="Error assembling RAG context")

def extract_citations(
    tenant_id: str,
    chunks: list[SearchResult],
    min_score: float = 0.5,
    max_citations: int = 3,
) -> list[Citation]:
    """
    Estrae le citazioni da includere nel final SSE chunk.
    Solo chunk con score > min_score. Max max_citations.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    citations = []
    
    # Assumiamo che chunks siano già ordinati per score dal reranker
    for chunk in chunks:
        if chunk.tenant_id != tenant_id:
            continue
            
        if chunk.score >= min_score:
            # Task: Excerpt as first 150 words (not chars)
            words = chunk.content.split()
            excerpt = " ".join(words[:150]) + ("..." if len(words) > 150 else "")
            
            citations.append(Citation(
                file_name=chunk.file_name,
                page_number=chunk.page_number,
                score=round(chunk.score, 2),
                excerpt=excerpt
            ))
            
        if len(citations) >= max_citations:
            break
            
    return citations

