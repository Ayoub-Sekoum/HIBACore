"""
Task 2.05 — PII Masking Middleware nei Log

Processor structlog che maschera dati sensibili prima di emetterli.
GDPR compliance: email, telefoni, codici fiscali, JWT, IP.
"""

from __future__ import annotations

import re
from typing import Any

# ── PII pattern to mask ────────────────────────────────

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email: mario@example.com → ***@***.com
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "***@***.***"),
    # Italian telephone: +39... → +39***
    (re.compile(r"\+?\d{2,3}[\s.-]?\d{6,10}"), "+XX***"),
    # Italian tax code: 16 alphanumeric chars
    (re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"), "CF_REDACTED"),
    # JWT token: eyJ... → [REDACTED_JWT]
    (re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"), "[REDACTED_JWT]"),
    # IP address: 192.168.1.1 → X.X.X.X
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "X.X.X.X"),
    # Bearer token in header
    (re.compile(r"Bearer\s+[a-zA-Z0-9._-]+"), "Bearer [REDACTED]"),
    # Sensitive keys and Connection Strings
    (re.compile(r"(?:api[_-]?key|api[_-]?secret|password|secret|AccountKey|SharedAccessKey)[\"']?\s*[:=]\s*[\"']?[\w/-]+=*", re.IGNORECASE), "[REDACTED_SECURE_VAL]"),
    (re.compile(r"Endpoint=https://[^;]+;[^\"]+", re.IGNORECASE), "Endpoint=https://[REDACTED];[REDACTED]"),
]


def mask_pii_value(value: str) -> str:
    """Maschera tutti i pattern PII trovati in una stringa."""
    result = value
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def mask_pii_recursive(obj: Any) -> Any:
    """Maschera PII ricorsivamente in dict, list, string."""
    if isinstance(obj, str):
        return mask_pii_value(obj)
    if isinstance(obj, dict):
        return {k: mask_pii_recursive(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(mask_pii_recursive(item) for item in obj)
    return obj


def pii_masking_processor(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor: maschera PII da tutti i campi del log.

    Aggiunto nella processor chain di structlog PRIMA del rendering.
    """
    return mask_pii_recursive(event_dict)
