"""
TenantMiddleware — deve essere il PRIMO middleware dopo CORS.

Estrae dal JWT (già validato da Azure API Management / App Service):
  - tid  → tenant_id
  - oid  → user_id
  - X-Correlation-Id header → correlation_id

Ogni request senza tenant_id valido viene bloccata con TENANT_101.
Se SKIP_JWT_VALIDATION=true usa un tenant_id di sviluppo.
"""
import os
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.context import set_correlation_id, set_tenant_id, set_user_id
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.schemas import APIResponse

logger = structlog.get_logger(__name__)

# Route che non richiedono tenant_id
EXEMPT_PATHS = {
    "/", "/health", "/ready", "/docs", "/openapi.json",
    "/redoc", "/debug-cors", "/metrics",
}

# Tenant di sviluppo — usato quando SKIP_JWT_VALIDATION=true
DEV_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "79fea776-1896-4256-b418-2cca88af08ae")
DEV_USER_ID   = "dev-user-local"
SKIP_JWT      = os.getenv("SKIP_JWT_VALIDATION", "false").lower() == "true"


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:

        # 1. Bypass per route pubbliche
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        # Bypass anche per path che iniziano con /_
        if request.url.path.startswith("/_"):
            return await call_next(request)

        # 2. Correlation ID
        correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
        set_correlation_id(correlation_id)

        # 3. Estrazione tenant_id
        tenant_id = request.headers.get("X-Tenant-Id")
        user_id   = request.headers.get("X-User-Id")

        if not tenant_id:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload   = jwt.get_unverified_claims(token)
                    tenant_id = payload.get("tid")
                    user_id   = payload.get("oid") or payload.get("sub")
                except JWTError as e:
                    logger.error("jwt_decode_failed", error=str(e), path=request.url.path)
                except Exception as e:
                    logger.error("jwt_unexpected_error", error=str(e), path=request.url.path)

        # 4. Fallback dev — se SKIP_JWT_VALIDATION=true non bloccare
        if not tenant_id:
            if SKIP_JWT:
                tenant_id = DEV_TENANT_ID
                user_id   = user_id or DEV_USER_ID
                logger.warning(
                    "tenant_id_missing_using_dev_fallback",
                    path=request.url.path,
                    dev_tenant=tenant_id,
                )
            else:
                logger.warning(
                    "tenant_id_missing",
                    path=request.url.path,
                    correlation_id=correlation_id,
                    has_auth_header=bool(request.headers.get("Authorization"))
                )
                error_response = APIResponse.fail(
                    error_code=ErrorCode.TENANT_101.name,
                    message=ErrorCode.TENANT_101.default_message,
                )
                return JSONResponse(
                    status_code=ErrorCode.TENANT_101.http_status,
                    content=error_response.model_dump(mode="json"),
                    headers={"X-Correlation-Id": correlation_id}
                )

        # 5. Imposta contesti
        set_tenant_id(tenant_id)
        if user_id:
            set_user_id(user_id)

        structlog.contextvars.bind_contextvars(
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id,
            path=request.url.path,
        )

        # 6. Passa la richiesta
        try:
            response = await call_next(request)
        except AppException as exc:
            app_err_response = APIResponse.fail(
                error_code=exc.error_code.name,
                message=exc.detail,
            )
            response = JSONResponse(
                status_code=exc.error_code.http_status,
                content=app_err_response.model_dump(mode="json")
            )

        # 7. Header in uscita e pulizia
        response.headers["X-Correlation-Id"] = correlation_id
        structlog.contextvars.clear_contextvars()

        return response
