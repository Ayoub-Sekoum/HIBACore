import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

import structlog
import tiktoken

from app.engine.ai.client import AzureOpenAIClient

logger = structlog.get_logger(__name__)


class LLMProvider(ABC):
    """Interfaccia astratta per tutti i provider LLM."""

    @abstractmethod
    async def complete(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def complete_stream(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> AsyncGenerator[Any, None]:
        raise NotImplementedError

    @abstractmethod
    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        raise NotImplementedError


class AzureOpenAIProvider(LLMProvider):
    """Implementazione per Azure OpenAI."""

    def __init__(self, endpoint_override: str | None = None, api_key_override: str | None = None, **kwargs):
        self.client_wrapper = AzureOpenAIClient(
            endpoint_override=endpoint_override,
            api_key_override=api_key_override,
        )

    async def complete(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> Any:
        client = self.client_wrapper.client
        api_kwargs = {"model": model, "messages": messages, "stream": False, **kwargs}
        if tools:
            api_kwargs["tools"] = tools
        return await client.chat.completions.create(**api_kwargs)

    async def complete_stream(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> AsyncGenerator[Any, None]:
        client = self.client_wrapper.client
        api_kwargs = {"model": model, "messages": messages, "stream": True, **kwargs}
        if tools:
            api_kwargs["tools"] = tools
        stream = await client.chat.completions.create(**api_kwargs)
        async for chunk in stream:
            yield chunk

    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        client = self.client_wrapper.client
        response = await client.embeddings.create(input=texts, model=model)
        return [data.embedding for data in response.data]

    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        from app.engine.ai.token_counter import count_tokens
        return count_tokens(text, model)


from dataclasses import dataclass


@dataclass
class MockMessage:
    content: str
    role: str = "assistant"


@dataclass
class MockChoice:
    message: MockMessage


@dataclass
class MockUsage:
    prompt_tokens: int = 10
    completion_tokens: int = 20
    total_tokens: int = 30


@dataclass
class MockChatResponse:
    choices: list[MockChoice]
    usage: MockUsage


@dataclass
class MockDelta:
    content: str | None = None
    role: str | None = None


@dataclass
class MockStreamChoice:
    delta: MockDelta
    index: int = 0


@dataclass
class MockStreamChunk:
    choices: list[MockStreamChoice]
    id: str = "chatcmpl-mockid"
    created: int = 1700000000
    model: str = "gpt-4o"
    object: str = "chat.completion.chunk"


class MockLLMProvider(LLMProvider):
    """Fallback per sviluppo locale senza Azure credentials."""

    async def complete(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> Any:
        logger.info("mock_llm_complete_called")
        return MockChatResponse(
            choices=[MockChoice(message=MockMessage(content="Risposta simulata dal Mock LLM Provider (Modalità Sviluppo)."))],
            usage=MockUsage(),
        )

    async def complete_stream(self, messages: list[dict[str, Any]], model: str = "gpt-4o", tools: list[dict] | None = None, **kwargs) -> AsyncGenerator[Any, None]:
        logger.info("mock_llm_stream_called")
        chunks = [
            "Ciao! ", "Sono ", "il ", "tuo ", "assistente ", "in ", "modalità ", "mock. ",
            "\n\n", "Ambiente ", "di ", "sviluppo ", "locale. ",
        ]
        from unittest.mock import MagicMock
        for text in chunks:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            yield chunk
            await asyncio.sleep(0.05)

    async def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def count_tokens(self, text: str, model: str = "gpt-4o") -> int:
        return len(text.split())


class ProviderFactory:
    """Registry e Factory per selezionare il provider configurato."""

    _providers: dict[str, type[LLMProvider]] = {
        "azure_openai": AzureOpenAIProvider,
    }

    @classmethod
    def get_provider(cls, name: str = "azure_openai", **kwargs) -> LLMProvider:
        import os

        # Use Mock ONLY if there is no Azure endpoint configured (pure local dev)
        # DO NOT use SKIP_JWT_VALIDATION as a proxy for the LLM provider:
        # in Azure dev the endpoint is there even if we skip JWT.
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")

        if not endpoint or not api_key:
            logger.warning("azure_openai_not_configured_using_mock")
            return MockLLMProvider()

        provider_class = cls._providers.get(name)
        if not provider_class:
            logger.warning("provider_not_found", requested=name, fallback="azure_openai")
            provider_class = cls._providers["azure_openai"]

        return provider_class(**kwargs)
