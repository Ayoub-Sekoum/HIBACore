import os
from typing import Any, Optional

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

class AzureOpenAIClient:
    """
    Wrapper per AsyncAzureOpenAI usando DefaultAzureCredential o API Key.
    Gestisce istanze multiple in base all'endpoint.
    """
    _instances: dict[str, 'AzureOpenAIClient'] = {}

    def __new__(cls, endpoint_override: str | None = None, api_key_override: str | None = None) -> 'AzureOpenAIClient':
        key = f"{endpoint_override}_{api_key_override}"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._initialize(endpoint_override, api_key_override)
            cls._instances[key] = instance
        return cls._instances[key]

    def _initialize(self, endpoint_override: str | None = None, api_key_override: str | None = None) -> None:
        try:
            endpoint = endpoint_override or os.getenv("AZURE_OPENAI_ENDPOINT")
            if not endpoint:
                endpoint = "https://dummy-endpoint.openai.azure.com/"
                logger.warning("azure_openai_endpoint_not_set", message="using dummy endpoint")

            api_key = api_key_override or os.getenv("AZURE_OPENAI_API_KEY")

            if api_key:
                self._client = AsyncAzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                )
            else:
                credential = get_global_credential()
                scope = "https://cognitiveservices.azure.com/.default"
                token_provider = get_bearer_token_provider(credential, scope)
                
                self._client = AsyncAzureOpenAI( # type: ignore
                    azure_ad_token_provider=token_provider,
                    azure_endpoint=endpoint,
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                )
            logger.info("azure_openai_client_initialized", endpoint=endpoint)
        except Exception as e:
            logger.error(
                "azure_openai_initialization_failed",
                exc_info=True,
                detail=str(e)
            )
            raise AppException(ErrorCode.INFRA_901, detail=f"Failed to initialize AsyncAzureOpenAI: {str(e)}")

    @property
    def client(self) -> AsyncAzureOpenAI | Any:
        if self._client is None:
            self._initialize()
        return self._client

def log_retry_attempt(retry_state):
    """Callback di logging per i retry"""
    if retry_state.attempt_number > 0:
        logger.warning(
            "azure_openai_call_retrying",
            attempt_number=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
        )

# Retry Policy: Max 3 attempts, exponential backoff 2, 4 seconds.
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=log_retry_attempt,
    reraise=True
)
async def _execute_with_retry(
    client_instance: AsyncAzureOpenAI,
    messages: list[dict[str, Any]],
    model: str = "gpt-4o",
    stream: bool = False,
    **kwargs: Any
) -> Any:
    # Make the real call (tenacity will retry this fn)
    return await client_instance.chat.completions.create(
        model=model,
        messages=messages, # type: ignore
        stream=stream,
        **kwargs
    )

async def generate_completion(
    messages: list[dict[str, Any]],
    model: str = "gpt-4o",
    stream: bool = False,
    **kwargs: Any
) -> Any:
    """
    Genera una chat completion chiamando il Singleton AsyncAzureOpenAI con retry.
    Se fallisce dopo 3 tentativi solleva AppException(ErrorCode.AI_201).
    """
    client_wrapper = AzureOpenAIClient()

    try:
        response = await _execute_with_retry(
            client_wrapper.client,
            messages=messages, # type: ignore
            model=model,
            stream=stream,
            **kwargs
        )
        return response

    except Exception as e:
        # If we are here, tenacity attempts are exhausted or a non-retryable exception has occurred.
        logger.error(
            "azure_openai_call_failed",
            error_code=ErrorCode.AI_201.value,
            model=model,
            error=str(e),
            exc_info=True
        )
        # We always convert to custom error to comply with the rule
        raise AppException(
            ErrorCode.AI_201,
            detail=f"Azure OpenAI timeout/failure after retries: {str(e)}"
        ) from e
