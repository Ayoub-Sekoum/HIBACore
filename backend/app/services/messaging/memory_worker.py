"""
Unified Memory Worker for Chat History.
Handles: Semantic Vectorization, Entity Extraction, and Summarization.
"""

import asyncio
import json
import os
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.servicebus.aio import ServiceBusClient

from app.core.config import get_settings
from app.engine.ai.circuit_breaker import ResilientLLMClient
from app.engine.memory.cosmos import cosmos_memory_service
from app.engine.memory.semantic import semantic_memory_service

logger = structlog.get_logger(__name__)

# Configuration
SB_FQDN = os.getenv("AZURE_SERVICE_BUS_FQDN")
VECTORIZE_QUEUE = "memory-vectorize"
SUMMARIZE_QUEUE = "summarize"
ENTITY_EXTRACT_QUEUE = "entity-extract"


async def process_vectorize(message_data: dict[str, Any]):
    """Generates embedding for a message and stores it in pgvector."""
    session_id = message_data.get("session_id")
    message_id = message_data.get("message_id")
    content = message_data.get("content")
    tenant_id = message_data.get("tenant_id") # We need to ensure tenant_id is in the message

    if not all([session_id, message_id, content, tenant_id]):
        logger.error("vectorize_missing_data", data=message_data)
        return

    await semantic_memory_service.index_message(str(tenant_id), str(session_id), str(message_id), str(content))


async def process_summarize(message_data: dict[str, Any]):
    """Summarizes old history if context window is getting full."""
    session_id = message_data.get("session_id")
    tenant_id = message_data.get("tenant_id")

    if not session_id or not tenant_id:
        return

    logger.info("summarization_start", session_id=session_id)

    # 1. Get history
    history = await cosmos_memory_service.get_history(session_id, tenant_id, limit=100)
    if len(history) < 40:
        return

    # 2. Call LLM to summarize
    llm = ResilientLLMClient()
    prompt = f"Riassumi i seguenti messaggi di una chat in modo conciso, mantenendo i fatti chiave e le preferenze dell'utente:\n\n{json.dumps(history[:-10])}"

    try:
        summary = await llm.complete([{"role": "system", "content": "Sei un assistente esperto in summarization."}, {"role": "user", "content": prompt}])

        # 3. Update Cosmos (This logic needs careful implementation in cosmos.py to prune old messages)
        # For now, we just log it as a placeholder for a complete pruning logic
        logger.info("summarization_complete", session_id=session_id, summary_length=len(summary))
    except Exception as e:
        logger.error("summarization_failed", session_id=session_id, error=str(e))


async def worker_loop(queue_name: str, processor_func):
    """Generic worker loop for a specific queue."""
    get_settings()
    if not SB_FQDN:
        return

    credential = get_global_credential()

    try:
        async with ServiceBusClient(fully_qualified_namespace=SB_FQDN, credential=credential) as client:
            receiver = client.get_queue_receiver(queue_name=queue_name)
            async with receiver:
                logger.info("worker_started", queue=queue_name)
                while True:
                    messages = await receiver.receive_messages(max_message_count=1, max_wait_time=5)
                    for msg in messages:
                        try:
                            data = json.loads(str(msg))
                            await processor_func(data)
                            await receiver.complete_message(msg)
                        except Exception as e:
                            logger.error("worker_message_error", queue=queue_name, error=str(e))
                            # Depending on severity, we might abandon or dead-letter
    except Exception as e:
        logger.critical("worker_fatal_error", queue=queue_name, error=str(e))


async def run_all_memory_workers():
    """Runs all memory-related workers in parallel."""
    await asyncio.gather(
        worker_loop(VECTORIZE_QUEUE, process_vectorize),
        worker_loop(SUMMARIZE_QUEUE, process_summarize),
        # worker_loop(ENTITY_EXTRACT_QUEUE, process_entity_extract) # To be implemented
    )

if __name__ == "__main__":
    asyncio.run(run_all_memory_workers())

