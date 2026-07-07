import json
import os
from typing import Any

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

from app.core.context import get_tenant_id

logger = structlog.get_logger(__name__)

SB_FQDN = os.getenv("AZURE_SERVICE_BUS_FQDN", "")

async def _send_message(queue_name: str, payload: dict[str, Any]) -> None:
    # If Service Bus is not configured, silent skip (avoids timeout on dummy endpoint)
    if not SB_FQDN or "dummy" in SB_FQDN:
        logger.debug("service_bus_not_configured_skipping", queue=queue_name)
        return
    try:
        credential = get_global_credential()
        async with ServiceBusClient(fully_qualified_namespace=SB_FQDN, credential=credential) as client:
            sender = client.get_queue_sender(queue_name=queue_name)
            message = ServiceBusMessage(json.dumps(payload))
            await sender.send_messages(message)
    except Exception as e:
        logger.warning(f"failed_to_send_service_bus_message_to_{queue_name}", error=str(e))

async def publish_to_ingestion_queue(blob_path: str, filename: str, content_type: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "blob_path": blob_path,
        "filename": filename,
        "content_type": content_type,
        "action": "extract_document"
    }
    await _send_message("document-ingestion", payload)

async def publish_to_vectorize_queue(session_id: str, message_id: str, content: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "message_id": message_id,
        "content": content,
        "action": "vectorize_chat_message"
    }
    await _send_message("memory-vectorize", payload)

async def publish_to_summarize_queue(session_id: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "action": "summarize_session"
    }
    await _send_message("summarize", payload)

async def publish_to_entity_extraction_queue(session_id: str, content: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "content": content,
        "action": "extract_entities"
    }
    await _send_message("entity-extract", payload)

async def publish_to_persona_worker(session_id: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "action": "update_persona"
    }
    await _send_message("persona", payload)

async def publish_to_recommendations_worker(session_id: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "action": "generate_recommendations"
    }
    await _send_message("recommendations", payload)
async def publish_to_reflection_worker(session_id: str) -> None:
    tenant_id = get_tenant_id()
    payload = {
        "tenant_id": tenant_id,
        "session_id": session_id,
        "action": "reflect_on_session"
    }
    await _send_message("reflection", payload)
