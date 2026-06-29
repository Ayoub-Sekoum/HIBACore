"""
Worker component to listen for document ingestion messages from Service Bus.
"""

import asyncio
import json
import os

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.servicebus.aio import ServiceBusClient

from app.core.config import get_settings
from app.engine.ai.circuit_breaker import ResilientLLMClient
from app.engine.ai.ingestion import ingestion_service
from app.services.storage.search import index_document_chunks

logger = structlog.get_logger(__name__)

# Configuration
SB_FQDN = os.getenv("AZURE_SERVICE_BUS_FQDN")
QUEUE_NAME = "document-ingestion"


async def process_message(message_body: str):
    """Processes a single ingestion message."""
    try:
        data = json.loads(message_body)
        tenant_id = data.get("tenant_id")
        blob_path = data.get("blob_path")  # Path or full URL
        filename = data.get("filename")

        logger.info("worker_processing_start", tenant_id=tenant_id, filename=filename)

        # 1. Pipeline di ingestione (OCR + Chunking)
        # Assuming blob_path is a full URL or we construct it
        chunks = await ingestion_service.process_document(blob_path, filename, tenant_id)

        # 2. Embedding dei chunks (Task 3.11)
        # In a real setup, we'd embed each chunk using OpenAI
        llm_client = ResilientLLMClient()
        for chunk in chunks:
            try:
                vectors = await llm_client.embed([chunk["content"]])
                chunk["vector"] = vectors[0] if vectors else []
            except Exception as e:
                logger.error("chunk_embedding_failed", chunk_index=chunk["chunk_index"], error=str(e))
                chunk["vector"] = []

        # 3. Indicizzazione su AI Search
        await index_document_chunks(chunks, tenant_id)

        logger.info("worker_processing_complete", tenant_id=tenant_id, filename=filename, chunks_indexed=len(chunks))

    except Exception as e:
        logger.error("worker_processing_failed", error=str(e), exc_info=True)


async def run_worker():
    """Main loop for the ingestion worker."""
    get_settings()
    if not SB_FQDN:
        logger.warning("service_bus_not_configured", action="abort_worker")
        return

    credential = get_global_credential()

    logger.info("ingestion_worker_started", queue=QUEUE_NAME)

    try:
        async with ServiceBusClient(fully_qualified_namespace=SB_FQDN, credential=credential) as client:
            receiver = client.get_receiver(queue_name=QUEUE_NAME)
            async with receiver:
                while True:
                    messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                    for msg in messages:
                        await process_message(str(msg))
                        await receiver.complete_message(msg)
    except Exception as e:
        logger.critical("ingestion_worker_fatal_error", error=str(e))


if __name__ == "__main__":
    # For solo execution
    asyncio.run(run_worker())

