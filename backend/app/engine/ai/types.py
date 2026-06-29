"""
F.3 — Tipi strutturati per le risposte LLM.
Evita l'uso di `-> Any` nelle signature dei provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatChoice:
    message: ChatMessage
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatCompletionResponse:
    choices: list[ChatChoice] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""

    @property
    def content(self) -> str:
        """Shortcut per accedere alla risposta testuale del primo choice."""
        if self.choices:
            return self.choices[0].message.content
        return ""


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]] = field(default_factory=list)
    model: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)
