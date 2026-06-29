"""
Azure AI Search Integration — Hybrid Search & Indexing.
Task 3.11 — Multi-Tenant Enterprise Chatbot.
"""

from typing import Any

import structlog
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)


def _get_search_client() -> SearchClient:
    """Initializes the Azure AI Search client."""
    settings = get_settings()
    endpoint = settings.AZURE_SEARCH_ENDPOINT
    key = settings.AZURE_SEARCH_KEY
    index_name = settings.AZURE_SEARCH_INDEX

    if not endpoint:
        logger.error("azure_search_endpoint_missing")
        raise AppException(ErrorCode.INFRA_903, detail="AZURE_SEARCH_ENDPOINT not configured")

    if key:
        credential = AzureKeyCredential(key)
    else:
        credential: Any = get_global_credential() # type: ignore

    return SearchClient(endpoint=endpoint, index_name=index_name, credential=credential) # type: ignore


async def hybrid_search_documents(
    query_vector: list[float],
    query_text: str,
    tenant_id: str,
    top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Hybrid search (vector + keyword) with mandatory tenant_id filter.
    """
    if not tenant_id:
        logger.error("search_failed_no_tenant_id")
        raise AppException(ErrorCode.TENANT_101)

    try:
        client = _get_search_client()
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="vector"
        ) if query_vector else None

        results = []
        async with client:
            search_results = await client.search(
                search_text=query_text,
                vector_queries=[vector_query] if vector_query else None,
                filter=f"tenant_id eq '{tenant_id}'",
                top=top_k,
                select=["id", "tenant_id", "file_name", "page_number", "content"]
            )

            async for result in search_results:
                results.append({
                    "id": result["id"],
                    "tenant_id": result["tenant_id"],
                    "file_name": result["file_name"],
                    "page_number": result.get("page_number", 0),
                    "content": result["content"],
                    "search_score": result["@search.score"]
                })
        return results

    except Exception as e:
        logger.error("search_failed", error=str(e))
        raise AppException(ErrorCode.RAG_305, detail=f"Search failed: {str(e)}")


async def index_document_chunks(chunks: list[dict[str, Any]], tenant_id: str) -> None:
    """Uploads document chunks to Azure AI Search."""
    if not chunks:
        return

    try:
        client = _get_search_client()
        async with client:
            await client.upload_documents(documents=chunks)
            logger.info("indexing_success", count=len(chunks), tenant_id=tenant_id)
    except Exception as e:
        logger.error("indexing_failed", error=str(e))
        raise AppException(ErrorCode.RAG_305, detail=f"Indexing failed: {str(e)}")
