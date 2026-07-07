import re
from typing import Any

import structlog

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

# Pattern matching regex for common injections (English + Italian)
INJECTION_PATTERNS = [
    # English patterns
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+different\s+assistant", re.IGNORECASE),
    re.compile(r"bypass\s+security\s+filters", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?rules", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    # Italian patterns
    re.compile(r"ignora\s+(tutte\s+le\s+)?istruzioni\s+(precedenti|di\s+sistema)", re.IGNORECASE),
    re.compile(r"dimentica\s+(tutte\s+le\s+)?regole", re.IGNORECASE),
    re.compile(r"aggira\s+(i\s+)?filtri\s+di\s+sicurezza", re.IGNORECASE),
    re.compile(r"mostra\s+(le\s+tue\s+)?istruzioni\s+di\s+sistema", re.IGNORECASE),
    re.compile(r"rivela\s+(il\s+tuo\s+)?system\s*prompt", re.IGNORECASE),
]

def check_prompt_injection(messages: list[dict[str, Any]]) -> None:
    """
    Analizza i messaggi in ingresso per bloccare tentativi di prompt injection.
    Lancia AppException(ErrorCode.AI_204) se viene rilevata un'anomalia.
    """
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            for pattern in INJECTION_PATTERNS:
                if pattern.search(content):
                    logger.warning(
                        "prompt_injection_detected",
                        pattern=pattern.pattern,
                        content_length=len(content)
                    )
                    raise AppException(
                        ErrorCode.AI_204,
                        detail=f"Prompt injection pattern matched: {pattern.pattern}"
                    )
