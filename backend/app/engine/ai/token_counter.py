from typing import Any

import structlog
import tiktoken

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

# gpt-4o limits
MAX_CONTEXT_TOKENS = 120000
TRUNCATE_TARGET_TOKENS = 100000

import functools

@functools.lru_cache(maxsize=32)
def _get_encoding(model_name: str):
    return tiktoken.encoding_for_model(model_name)

def count_tokens(text: str, model_name: str = "gpt-4o") -> int:
    """Restituisce il numero di token per la stringa specificata."""
    try:
        # Some Azure model names might not exactly match openai's tiktoken names
        # Default to cl100k_base which is used by gpt-4o
        encoding = _get_encoding(model_name)
        return len(encoding.encode(text))
    except (KeyError, Exception) as e:
        # Fallback for environments with no internet/connection errors
        logger.warning("tiktoken_failure_using_fallback", error=str(e), model=model_name)
        # Approximation: 1 token ~= 4 chars for Italian/English
        return len(text) // 4

def count_messages_tokens(messages: list[dict[str, Any]], model_name: str = "gpt-4o") -> int:
    """Stima il numero di token per una lista di messaggi."""
    total_tokens = 0
    for msg in messages:
        # Approximation: +4 tokens for message overhead
        total_tokens += 4
        content = msg.get("content")
        if isinstance(content, str):
            total_tokens += count_tokens(content, model_name)
    return total_tokens

def manage_context_window(messages: list[dict[str, Any]], model_name: str = "gpt-4o") -> list[dict[str, Any]]:
    """
    Se i messaggi superano il MAX_CONTEXT_TOKENS, tronca la history intelligente
    mantenendo il system prompt, l'ultimo messaggio dell'utente e i RAG chunks.
    Se anche dopo il troncamento si supera il limite, lancia AI_205.
    """
    total_tokens = count_messages_tokens(messages, model_name)

    if total_tokens <= MAX_CONTEXT_TOKENS:
        return messages

    logger.warning("context_window_exceeded", total_tokens=total_tokens, limit=MAX_CONTEXT_TOKENS)

    # We must keep system messages (usually index 0)
    system_msgs = [m for m in messages if m.get("role") == "system"]

    # We must keep the latest user query
    user_queries = [m for m in messages if m.get("role") == "user"]
    last_user_msg = user_queries[-1] if user_queries else None

    # Identify history messages that can be dropped
    history_msgs = [
        m for m in messages
        if m.get("role") not in ["system"] and m != last_user_msg
    ]

    # Pre-calculate tokens for each segment to avoid O(N^2) complexity
    system_tokens = count_messages_tokens(system_msgs, model_name)
    user_tokens = count_messages_tokens([last_user_msg], model_name) if last_user_msg else 0
    history_msg_tokens = [count_messages_tokens([m], model_name) for m in history_msgs]
    current_history_tokens = sum(history_msg_tokens)

    # Iteratively remove oldest history messages until we fit within TRUNCATE_TARGET_TOKENS
    while history_msgs and (system_tokens + current_history_tokens + user_tokens) > TRUNCATE_TARGET_TOKENS:
        history_msgs.pop(0)
        removed_tokens = history_msg_tokens.pop(0)
        current_history_tokens -= removed_tokens

    truncated_messages = system_msgs + history_msgs
    if last_user_msg:
        truncated_messages.append(last_user_msg)

    final_tokens = count_messages_tokens(truncated_messages, model_name)

    # If it still exceeds after clearing all history, the prompt/RAG chunks itself are too large.
    if final_tokens > MAX_CONTEXT_TOKENS:
        logger.error("prompt_too_large_after_truncation", final_tokens=final_tokens)
        raise AppException(
            ErrorCode.AI_205,
            detail=f"Prompt still too large after truncation: {final_tokens} tokens"
        )

    logger.info("context_window_truncated", original_tokens=total_tokens, final_tokens=final_tokens)
    return truncated_messages
