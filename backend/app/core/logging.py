"""
Centralized Logging Configuration — structlog + Azure Monitor + PII Masking.
Task 2.04 + 2.05 — Multi-Tenant Enterprise Chatbot.
"""

import logging
from typing import MutableMapping
import re
import sys
import time
from typing import Any
from uuid import uuid4

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import get_settings
from app.core.context import (
    get_correlation_id,
    get_tenant_id,
    get_user_id,
    set_correlation_id,
)

# ── PII Masking Patterns ────────────────────────────────────────────────────

_PII_PATTERNS = [
    # Email: mario.rossi@example.com → ***@***.com
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
     lambda m: f"***@{m.group().split('@')[1].split('.')[0]}***.{m.group().split('.')[-1]}"),

    # Telefono italiano
    (re.compile(r"(\+39[\s\-]?)[\d\s\-]{6,15}"), "\\1***"),

    # Codice fiscale
    (re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b"), "[CF_REDACTED]"),

    # JWT Bearer token
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer [TOKEN_REDACTED]"),

    # IP address
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "X.X.X.X"),
]

_SENSITIVE_KEYS = {
    "password", "secret", "api_key", "token", "authorization",
    "connection_string", "private_key", "client_secret",
}


def _mask_string(value: str) -> str:
    """Applies PII masking to a string."""
    for pattern, replacement in _PII_PATTERNS:
        if callable(replacement):
            value = pattern.sub(replacement, str(value)) # type: ignore
        else:
            value = pattern.sub(replacement, str(value)) # type: ignore
    return value


def _mask_dict(data: dict[str, Any] | MutableMapping[str, Any]) -> dict[str, Any] | MutableMapping[str, Any]:
    """Recursively masks settings and PII in a dictionary."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            result[key] = "[REDACTED]"
        elif isinstance(value, str):
            result[key] = _mask_string(value)
        elif isinstance(value, dict):
            result[key] = _mask_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _mask_dict(item) if isinstance(item, dict)
                else _mask_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def pii_masking_processor(
    logger: WrappedLogger, method: str, event_dict: EventDict
) -> EventDict:
    """Structlog processor to mask PII."""
    return _mask_dict(event_dict)


def add_request_context(
    logger: WrappedLogger, method: str, event_dict: EventDict
) -> EventDict:
    """Injects tenant_id, correlation_id, and user_id from context vars."""
    if "tenant_id" not in event_dict:
        tenant_id = get_tenant_id()
        if tenant_id:
            event_dict["tenant_id"] = tenant_id

    if "correlation_id" not in event_dict:
        corr_id = get_correlation_id()
        if corr_id:
            event_dict["correlation_id"] = corr_id

    if "user_id" not in event_dict:
        user_id = get_user_id()
        if user_id:
            event_dict["user_id"] = user_id

    return event_dict


def configure_logging() -> None:
    """
    Configures structlog with a full processing chain.
    Called once during app startup.
    """
    settings = get_settings()
    level = "DEBUG" if settings.DEBUG else "INFO"
    json_output = settings.ENVIRONMENT == "production"

    shared_processors: list[Any] = [
        pii_masking_processor,
        add_request_context,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    if json_output:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors[:-1],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level))

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure Azure Monitor if available
    _configure_azure_monitor(settings.APPLICATIONINSIGHTS_CONNECTION_STRING)


def _configure_azure_monitor(connection_string: str | None) -> None:
    """Configures Azure Monitor OpenTelemetry export."""
    if not connection_string:
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor as _az_configure
        _az_configure(connection_string=connection_string)
    except Exception as exc:
        structlog.get_logger().warning(
            "azure_monitor_init_failed",
            error=str(exc),
            message="Azure Monitor telemetry disabled"
        )


class CorrelationIdMiddleware:
    """Pure ASGI Middleware to handle X-Correlation-Id and log requests safely."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        correlation_id_bytes = headers.get(b"x-correlation-id")
        correlation_id = correlation_id_bytes.decode() if correlation_id_bytes else str(uuid4())

        set_correlation_id(correlation_id)

        start_time = time.perf_counter()
        logger = structlog.get_logger()

        await logger.ainfo(
            "request_started",
            method=scope["method"],
            path=scope["path"]
        )

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-correlation-id", correlation_id.encode()))

                status_code = message.get("status")
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                await logger.ainfo(
                    "request_completed",
                    method=scope["method"],
                    path=scope["path"],
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
