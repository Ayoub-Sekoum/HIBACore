"""
Document Ingestion Service using Azure AI Content Understanding.
Handles OCR, layout extraction, and semantic chunking.
"""

from typing import Any
from uuid import uuid4

import structlog
from azure.ai.contentunderstanding.aio import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalyzeInput
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)


class IngestionService:
    """Service to process documents and prepare them for indexing."""

    def __init__(self):
        settings = get_settings()
        self.endpoint = settings.CONTENTUNDERSTANDING_ENDPOINT
        self._client: ContentUnderstandingClient | None = None

    async def get_client(self) -> ContentUnderstandingClient:
        """Lazy initialization of the async client."""
        if self._client is None:
            if not self.endpoint:
                logger.error("content_understanding_endpoint_missing")
                raise AppException(ErrorCode.INFRA_903, detail="CONTENTUNDERSTANDING_ENDPOINT not configured")

            credential = get_global_credential()
            self._client = ContentUnderstandingClient(
                endpoint=self.endpoint,
                credential=credential
            )
        return self._client

    async def extract_markdown(self, blob_url: str) -> str:
        """Extracts markdown content from a document using prebuilt-documentSearch."""
        client = await self.get_client()
        try:
            logger.info("document_analysis_started", blob_url=blob_url)

            poller = await client.begin_analyze(
                analyzer_id="prebuilt-documentSearch",
                inputs=[AnalyzeInput(url=blob_url)]
            )
            result = await poller.result()

            if not result.contents:
                logger.warning("document_analysis_empty", blob_url=blob_url)
                return ""

            # Content Understanding returns a list of results
            content = result.contents[0]
            logger.info("document_analysis_completed", blob_url=blob_url)
            return content.markdown or ""

        except Exception as e:
            logger.error("document_analysis_failed", blob_url=blob_url, error=str(e))
            raise AppException(ErrorCode.RAG_305, detail=f"Failed to analyze document: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
        """
        Splits text into chunks with overlap.
        Using a simple character-based split for now, 
        could be improved with semantic splitting or tiktoken.
        """
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += (chunk_size - overlap)

        return chunks

    async def process_document(self, blob_url: str, filename: str, tenant_id: str) -> list[dict[str, Any]]:
        """
        Full pipeline: Analyze -> Extract -> Chunk.
        Returns a list of chunks ready for indexing.
        """
        markdown = await self.extract_markdown(blob_url)
        raw_chunks = self.chunk_text(markdown)

        processed_chunks = []
        for i, content in enumerate(raw_chunks):
            processed_chunks.append({
                "id": str(uuid4()),
                "tenant_id": tenant_id,
                "file_name": filename,
                "content": content,
                "chunk_index": i,
                # In production, we'd also store page numbers if provided by the SDK
                "metadata": {
                    "source": filename,
                    "blob_url": blob_url
                }
            })

        return processed_chunks

    async def close(self):
        """Cleanup resources."""
        if self._client:
            await self._client.close()


ingestion_service = IngestionService()
