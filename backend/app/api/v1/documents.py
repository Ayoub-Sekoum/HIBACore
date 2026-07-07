import os

# import magic # TODO: pip install python-magic-bin
import structlog
from fastapi import APIRouter, Depends, File, UploadFile

from app.core.auth import get_current_user
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.schemas import APIResponse
from app.services.messaging.bus import publish_to_ingestion_queue
from app.services.storage.blob import upload_document_to_blob

logger = structlog.get_logger(__name__)


router = APIRouter(dependencies=[Depends(get_current_user)])

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown"
}

@router.post("/upload", response_model=APIResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Task 3.09 & 3.10: Endpoint per il caricamento sicuro dei documenti.
    - Verifica limiti dimensione file (100MB).
    - Verifica MIME type reale tramite magic.
    - Finta scansione malware.
    - Carica su Azure Blob Storage.
    - Manda messaggio ad Azure Service Bus per elaborazione async.
    """
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # Sanitize filename to prevent path traversal
    safe_filename = os.path.basename(file.filename) if file.filename else "unknown"

    # 1. File size control
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning("file_too_large", size=file_size, filename=safe_filename)
        raise AppException(ErrorCode.UPLOAD_603, detail=f"Size: {file_size} > {MAX_FILE_SIZE_BYTES}")

    # 2. Real MIME control with python-magic
    real_mime_type = getattr(filetype.guess(file_bytes), "mime", "application/octet-stream")
    if real_mime_type not in ALLOWED_MIME_TYPES:
        logger.warning("invalid_mime_type", real_mime=real_mime_type, filename=safe_filename)
        raise AppException(ErrorCode.UPLOAD_601, detail=f"MIME {real_mime_type} non consentito")

    # 3. Dummy Malware Scan (Block if name contains 'eicar')
    if "eicar" in safe_filename.lower():
        logger.error("malware_detected", filename=safe_filename)
        raise AppException(ErrorCode.UPLOAD_602, detail=f"Malware simulation per {safe_filename}")

    # Restore file cursor after magic read
    # FastAPI UploadFile doesn't support tell(), we use a BytesIO or just pass bytes
    import io
    file_obj = io.BytesIO(file_bytes)

    # 4. Upload to Blob (Task 3.09)
    blob_path = await upload_document_to_blob(file_obj, safe_filename, real_mime_type)

    # 5. Send message to ASB (Task 3.10)
    await publish_to_ingestion_queue(blob_path, safe_filename, real_mime_type)

    return APIResponse.ok(data={"blob_path": blob_path, "status": "uploaded_and_queued"})

