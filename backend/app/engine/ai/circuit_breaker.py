from collections.abc import AsyncGenerator
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.providers import AzureOpenAIProvider

logger = structlog.get_logger(__name__)

def log_retry_attempt(retry_state):
    """Callback di logging per i retry del circuit breaker."""
    if retry_state.attempt_number > 0:
        logger.warning(
            "llm_provider_call_retrying",
            attempt_number=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
        )

# Task 3.04: Failover Cascade (Primary -> Secondary -> Exception AI_203)
# For this implementation, we simulate the cascade using Tenacity to handle
# retries on the primary provider, then we catch the final exception and attempt a failover.

@retry(
    stop=stop_after_attempt(3), # 3 attempts per provider
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=log_retry_attempt,
    reraise=True
)
async def _call_provider_with_retry(provider, method: str, *args, **kwargs):
    func = getattr(provider, method)
    return await func(*args, **kwargs)

class ResilientLLMClient:
    """Wrapper that implements Circuit Breaker and Failover Cascade."""

    def __init__(self):
        settings = get_settings()
        self._azure_available = bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY)
        self.primary_provider = None
        self.secondary_provider = None
        if self._azure_available:
            self.primary_provider = AzureOpenAIProvider(
                endpoint_override=settings.AZURE_OPENAI_ENDPOINT,
                api_key_override=settings.AZURE_OPENAI_API_KEY
            )
            self.secondary_provider = AzureOpenAIProvider(
                endpoint_override=settings.AZURE_OPENAI_SECONDARY_ENDPOINT or settings.AZURE_OPENAI_ENDPOINT,
                api_key_override=settings.AZURE_OPENAI_SECONDARY_API_KEY or settings.AZURE_OPENAI_API_KEY
            )
        else:
            from app.engine.ai.providers import MockLLMProvider
            logger.warning("azure_openai_not_configured_using_mock")
            self.primary_provider = MockLLMProvider()
            self.secondary_provider = MockLLMProvider()

    async def _execute_with_cascade(self, method: str, *args, **kwargs):
        try:
            return await _call_provider_with_retry(self.primary_provider, method, *args, **kwargs)
        except Exception as e_primary:
            logger.error(
                "primary_llm_provider_failed",
                error=str(e_primary),
                action="falling_back_to_secondary"
            )
            try:
                return await _call_provider_with_retry(self.secondary_provider, method, *args, **kwargs)
            except Exception as e_secondary:
                logger.critical(
                    "all_llm_providers_failed",
                    error_code=ErrorCode.AI_203.value,
                    primary_error=str(e_primary),
                    secondary_error=str(e_secondary)
                )
                raise AppException(ErrorCode.AI_203, detail="Failover fallito su tutti i provider") from e_secondary

    async def complete(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> Any:
        return await self._execute_with_cascade("complete", messages=messages, model=model, tools=tools, **kwargs)

    async def complete_stream(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> AsyncGenerator[Any, None]:
        # For stream we can't easily wrap the generator in the same generic function due to async iteration
        # Need a dedicated cascade for stream
        try:
            # We don't use @retry on generators easily without accumulating, so we just attempt failover on initial connection
            provider = self.primary_provider
            stream = provider.complete_stream(messages=messages, model=model, tools=tools, **kwargs)
            async for chunk in stream:
                yield chunk
        except Exception as e_primary:
             logger.error("primary_llm_provider_stream_failed", error=str(e_primary), action="falling_back_to_secondary")
             try:
                 provider = self.secondary_provider
                 stream = provider.complete_stream(messages=messages, model=model, tools=tools, **kwargs)
                 async for chunk in stream:
                     yield chunk
             except Exception as e_secondary:
                 logger.critical(
                    "all_llm_providers_stream_failed",
                    error_code=ErrorCode.AI_203.value
                 )
                 raise AppException(ErrorCode.AI_203, detail="Failover stream fallito") from e_secondary

    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        return await self._execute_with_cascade("embed", texts=texts, model=model)

