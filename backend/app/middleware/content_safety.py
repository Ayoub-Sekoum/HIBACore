"""
Middleware for Azure AI Content Safety.
Analyzes user prompts for harmful content and prompt injection.
"""

from typing import Any

import structlog
try:
    from azure.ai.contentsafety import ContentSafetyClient
except ImportError:
    ContentSafetyClient = None  # modulo non installato, middleware disabilitato
from azure.core.credentials import AzureKeyCredential
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)


class ContentSafetyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check user input for safety using Azure AI Content Safety.
    Only checks Chat and Document endpoints to avoid unnecessary calls.
    """

    def __init__(self, app: Any):
        super().__init__(app)
        settings = get_settings()
        self.enabled = settings.CONTENT_SAFETY_ENDPOINT is not None
        self._client: ContentSafetyClient | None = None

        # Thresholds (0-7 scale, 0 is safe)
        self.threshold = 4

    def get_client(self) -> ContentSafetyClient | None:
        """Lazy initialization of Content Safety client."""
        if self._client is None and self.enabled:
            settings = get_settings()
            try:
                self._client = ContentSafetyClient(
                    endpoint=settings.CONTENT_SAFETY_ENDPOINT,
                    credential=AzureKeyCredential(settings.CONTENT_SAFETY_KEY) # type: ignore
                )
            except Exception as e:
                logger.error("content_safety_client_init_failed", error=str(e))
                self.enabled = False
        return self._client

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Only analyze POST/PUT on chat and document routes
        if not self.enabled or request.method not in ["POST", "PUT"]:
            return await call_next(request)
        if not (
            request.url.path.startswith("/api/v1/chat")
            or request.url.path.startswith("/api/v1/documents")
        ):
            return await call_next(request)

        try:
            # Read the body without consuming it — rebuild the receive callable after reading
            body = await request.body()

            async def _receive():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = _receive  # type: ignore[attr-defined]

            import json
            try:
                data = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                data = {}

            user_text = data.get("text", "") or data.get("query", "") or ""
            if user_text:
                await self.analyze_text(str(user_text))
        except AppException:
            raise
        except Exception as e:
            logger.warning("content_safety_check_skipped", error=str(e))

        return await call_next(request)

    async def analyze_text(self, text: str):
        """Helper to analyze text for harmful content."""
        client = self.get_client()
        if not client:
            return

        try:
            request = AnalyzeTextOptions(text=text)
            response = client.analyze_text(request)

            for result in response.categories_analysis:
                if result.severity >= self.threshold:
                    logger.warning(
                        "content_safety_violation",
                        category=result.category,
                        severity=result.severity,
                        text_snippet=text[:50] + "..."
                    )
                    raise AppException(
                        ErrorCode.AI_204,
                        detail=f"Contenuto non ammesso: rilevata categoria {result.category} con severità {result.severity}."
                    )
        except AppException:
            raise
        except Exception as e:
            logger.error("content_safety_analysis_failed", error=str(e))
