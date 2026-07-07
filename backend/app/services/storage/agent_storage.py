import os
import structlog

logger = structlog.get_logger(__name__)


async def backup_chat_memory(session_id: str, tenant_id: str, data: dict) -> None:
    """Stub: backs up chat memory to storage."""
    logger.info("backup_chat_memory_stub", session_id=session_id, tenant_id=tenant_id)


async def get_agent_memory(session_id: str, tenant_id: str) -> dict:
    """Stub: retrieves agent memory from storage."""
    logger.info("get_agent_memory_stub", session_id=session_id, tenant_id=tenant_id)
    return {}


try:
    from azure.storage.blob.aio import BlobServiceClient
    from azure.identity.aio import DefaultAzureCredential
    from app.core.credentials import get_global_credential
    from app.core.config import get_settings
    settings = get_settings()
    _AZURE_AVAILABLE = True
except Exception:
    _AZURE_AVAILABLE = False
    settings = None

async def sync_workspace_to_azure():
    """
    Sincronizza il workspace locale con Azure Blob Storage.
    Usa Managed Identity (DefaultAzureCredential) per sicurezza Enterprise.
    Task: Workspace Persistence logic.
    """
    if not _AZURE_AVAILABLE or settings is None:
        logger.warning("azure_not_available_sync_skipped")
        return

    endpoint = settings.AZURE_STORAGE_CONNECTION_STRING # In v2 might be endpoint URL
    container_name = settings.AGENT_STORAGE_CONTAINER
    workspace = settings.AGENT_WORKSPACE_PATH

    if not endpoint:
        logger.warning("azure_storage_not_configured_for_sync")
        return

    try:
        # Task: Managed Identity Integration
        if "DefaultEndpointsProtocol" in endpoint:
            # Connection string mode
            client = BlobServiceClient.from_connection_string(endpoint)
        else:
            # Managed Identity / Endpoint mode
            client = BlobServiceClient(account_url=endpoint, credential=get_global_credential())

        async with client:
            container_client = client.get_container_client(container_name)
            
            # Guarantees the existence of the container
            if not await container_client.exists():
                await container_client.create_container()

            # Scan and upload (Sequential/Async)
            for root, _, files in os.walk(workspace):
                for file_name in files:
                    local_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(local_path, workspace).replace("\\", "/")
                    
                    blob_client = container_client.get_blob_client(relative_path)
                    
                    # Best-effort upload
                    try:
                        with open(local_path, "rb") as data:
                            await blob_client.upload_blob(data, overwrite=True)
                            logger.info("agent_file_synced", path=relative_path)
                    except Exception as fe:
                        logger.warning("file_sync_failed", path=relative_path, error=str(fe))

    except Exception as e:
        logger.error("workspace_persistence_failed", error=str(e), code="INFRA_905")
