import os
import uuid
from typing import BinaryIO

import structlog

logger = structlog.get_logger(__name__)

STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_URL", "")
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", "/tmp/hoba_documents")

async def upload_document_to_blob(file_obj: BinaryIO, filename: str, content_type: str) -> str:
    """
    Task 3.09: Carica il documento nello storage Azure Blob con path basato su tenant.
    Falls back to local filesystem when Azure is not available.
    """
    from app.core.context import get_tenant_id
    from app.core.error_codes import ErrorCode
    from app.core.exceptions import AppException

    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    file_uuid = str(uuid.uuid4())
    blob_path = f"tenants/{tenant_id}/documents/{file_uuid}/{filename}"

    if not STORAGE_ACCOUNT_URL:
        # Local fallback
        local_path = os.path.join(LOCAL_STORAGE_DIR, blob_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_obj.read())
        logger.info("document_saved_locally", blob_path=blob_path, content_type=content_type)
        return blob_path

    try:
        from app.core.credentials import get_global_credential
        from azure.storage.blob.aio import BlobServiceClient
        credential = get_global_credential()
        blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
        blob_client = blob_service_client.get_blob_client(container="documents", blob=blob_path)

        await blob_client.upload_blob(file_obj, overwrite=True)
        logger.info("document_uploaded_to_blob", blob_path=blob_path, content_type=content_type)
        return blob_path
    except Exception as e:
        logger.error("blob_upload_failed", error=str(e))
        raise AppException(ErrorCode.INFRA_903, detail=str(e))
