import os

import structlog
from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import PlainTextResponse

from app.core.auth import get_current_user
from app.core.context import get_tenant_id
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.schemas import APIResponse
from app.engine.memory.cosmos import cosmos_memory_service
from app.engine.memory.mock import mock_memory_service


# Helper to get the active memory service
def get_memory_service():
    if os.getenv("SKIP_JWT_VALIDATION", "false").lower() == "true":
        return mock_memory_service
    return cosmos_memory_service

logger = structlog.get_logger(__name__)


router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/", response_model=APIResponse)
async def list_conversations():
    """
    Task 4.01+: Recupera la lista delle sessioni per il tenant corrente.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    memory_service = get_memory_service()
    sessions = await memory_service.list_sessions(tenant_id)
    return APIResponse.ok(data=sessions)

@router.get("/{session_id}/export")
async def export_conversation(
    session_id: str = Path(...),
    format: str = Query("markdown", description="Formato esportazione (es. markdown)")
):
    """
    Task 4.09: Markdown Memory Export API
    Genera un file .md con tutti i messaggi della conversazione.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    if format.lower() != "markdown":
        raise AppException(ErrorCode.INFRA_903, detail="Formato non supportato")

    # Fetch max 1000 messages to simulate full export
    memory_service = get_memory_service()
    history = await memory_service.get_history(session_id, tenant_id, limit=1000)

    if not history:
        raise AppException(ErrorCode.MEM_401, detail="Session not found or empty")

    markdown_lines = [f"# Export Conversazione: {session_id}", ""]

    for msg in history:
        role = "Utente" if msg["role"] == "user" else "Assistente AI"
        content = msg["content"]
        markdown_lines.append(f"### {role}")
        markdown_lines.append(f"{content}\n")

    markdown_content = "\n".join(markdown_lines)

    # In a real environment, this could be uploaded to Blob Storage and a SAS token returned.
    # Here we return the raw markdown file directly as a download

    logger.info("conversation_exported", session_id=session_id, format=format)

    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=\"{session_id}.md\""}
    )

