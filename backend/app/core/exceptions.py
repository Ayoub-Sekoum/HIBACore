"""
Task 2.02 — Global Exception Handler + AppException.
Nessuna eccezione Python raggiunge MAI il client in forma grezza.
Tutto viene convertito in APIResponse con ErrorCode dal catalogo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.context import get_correlation_id, get_tenant_id, get_user_id
from app.core.error_codes import ErrorCode
from app.core.schemas import APIResponse

logger = structlog.get_logger(__name__)


class AppException(Exception):
    """
    Eccezione applicativa tipizzata.
    Usa SEMPRE ErrorCode dal catalogo, mai stringhe libere.
    """

    def __init__(
        self,
        error_code: ErrorCode,
        detail: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.error_code = error_code
        self.detail = detail or error_code.default_message
        self.extra = extra or {}
        self.timestamp = datetime.now(timezone.utc)
        super().__init__(self.detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra tutti gli exception handler globali sull'app FastAPI."""

    @app.exception_handler(AppException)
    async def handle_app_exception(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Gestisce AppException → APIResponse con error_code dal catalogo."""
        log_data = {
            "error_code": exc.error_code.name,
            "detail": exc.detail,
            "category": exc.error_code.category,
            "path": request.url.path,
            "method": request.method,
            "tenant_id": get_tenant_id(),
            "user_id": get_user_id(),
            "correlation_id": get_correlation_id(),
            **exc.extra
        }

        # Different level logs based on category
        if exc.error_code.category in ["Infrastructure", "AI Security", "Tenant Isolation"]:
            logger.error("app_exception_critical", **log_data, exc_info=True)
        else:
            logger.warning("app_exception", **log_data)

        response = APIResponse.fail(
            error_code=exc.error_code.name,
            message=exc.error_code.default_message,
        )
        return JSONResponse(
            status_code=exc.error_code.http_status,
            content=response.model_dump(mode="json")
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Gestisce HTTPException standard di FastAPI/Starlette."""
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=str(exc.detail),
            path=request.url.path,
            method=request.method,
        )

        error_code = _map_http_status_to_error_code(exc.status_code)

        response = APIResponse.fail(
            error_code=error_code.name,
            message=str(exc.detail) if exc.detail else error_code.default_message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(mode="json")
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Gestisce errori di validazione Pydantic."""
        logger.warning(
            "validation_error",
            errors=str(exc.errors()),
            path=request.url.path,
            method=request.method,
        )

        response = APIResponse.fail(
            error_code="VALIDATION_ERROR",
            message="I dati inviati non sono validi. Controlla i campi richiesti.",
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(mode="json")
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Catch-all per eccezioni non gestite."""
        logger.error(
            "unhandled_exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        response = APIResponse.fail(
            error_code=ErrorCode.INFRA_903.name,
            message="Si è verificato un errore interno. Contatta il supporto.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(mode="json")
        )


def _map_http_status_to_error_code(status_code: int) -> ErrorCode:
    """Mappa HTTP status code al codice errore più appropriato."""
    mapping = {
        401: ErrorCode.AUTH_001,
        403: ErrorCode.AUTH_004,
        404: ErrorCode.TENANT_104,
        429: ErrorCode.TENANT_103,
    }
    return mapping.get(status_code, ErrorCode.INFRA_903)
