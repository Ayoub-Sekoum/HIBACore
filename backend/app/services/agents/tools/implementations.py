from typing import Any

import structlog

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.services.agents.tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)

async def web_search(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Task 5.04: Web Search Tool (Azure Bing Search API).
    Mocked version.
    """
    logger.info("tool_web_search_executed", query=query)

    # In a real environment, query Azure Bing Search using the key from Key Vault
    # and return results.
    return [
        {
            "title": f"Result for {query}",
            "url": "https://example.com",
            "snippet": f"This is a mocked snippet for the search query: {query}"
        }
    ]

async def file_read(path: str) -> str:
    """
    Task 5.06: File Operations Tool.
    Read-only operations from blob storage. Incorporates path traversal protection.
    """
    if ".." in path:
        logger.warning("path_traversal_attempt_blocked", path=path)
        raise AppException(ErrorCode.TOOL_504, detail="Path traversal blocked")

    logger.info("tool_file_read_executed", path=path)
    # Mock reading file content from blob storage
    return f"Contenuto finto del file {path}"

async def code_execution(code: str, language: str = "python") -> str:
    """
    Task 5.05 & 5.07: Secure Code Execution Sandbox / Shell Command Execution.
    Simulates sending code to an isolated Azure Container Instance (ACI).
    """
    logger.info("tool_code_execution_executed", language=language)

    if language != "python":
        raise AppException(ErrorCode.TOOL_504, detail="Only python is supported in the sandbox")

    # Simulate execution delay and result
    return "Mocked code execution output: Hello World"

async def webhook_send(url: str, payload: dict[str, Any]) -> str:
    """
    Task 5.08: Outbound Webhook Tool.
    Invia un payload a un URL in allowlist con firma HMAC.
    """
    logger.info("tool_webhook_send_executed", url=url)

    if "example.com" not in url:  # Simulated allowlist check
        raise AppException(ErrorCode.TOOL_504, detail="URL non in allowlist")

    import httpx
    async with httpx.AsyncClient():
        try:
            # Simulate real sending
            # response = await client.post(url, json=payload, headers={"X-Hub-Signature": "..."})
            return f"Webhook inviato con successo a {url}"
        except Exception as e:
            raise AppException(ErrorCode.TOOL_502, detail=f"Webhook fallito: {e}")

# Registering tools at startup
ToolRegistry.register("web_search", web_search)
ToolRegistry.register("file_read", file_read)
ToolRegistry.register("code_execution", code_execution)
ToolRegistry.register("webhook_send", webhook_send)
