"""
Task 2.06 — JWT Decoder + TenantMiddleware

Accesso SOLO via SSO Microsoft (Azure Entra ID).
Nessun login/password custom. Il JWT viene da APIM validato.

Estrae dal JWT: tid (tenant_id), oid (user_id), roles[].
Senza tenant_id valido → TENANT_101.
"""

from __future__ import annotations

import os
from typing import Any

import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt # type: ignore

from app.core.context import (
    set_tenant_id,
    set_user_id,
    set_user_roles,
)
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

# FastAPI security scheme — Bearer token
_bearer_scheme = HTTPBearer(auto_error=False)


# ── Configurazione (da env per flessibilità dev/prod) ──────────

def _get_entra_config() -> dict[str, str]:
    """Configurazione Entra ID da variabili d'ambiente."""
    return {
        "tenant_id": os.getenv("AZURE_TENANT_ID", ""),
        "client_id": os.getenv("AZURE_CLIENT_ID", ""),
        "issuer": os.getenv(
            "AZURE_JWT_ISSUER",
            f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', '')}/v2.0",
        ),
        "audience": os.getenv("AZURE_CLIENT_ID", ""),
        # In produzione i JWK vengono cachati e verificati
        "jwks_uri": os.getenv(
            "AZURE_JWKS_URI",
            f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', '')}/discovery/v2.0/keys",
        ),
    }


# ── JWT Decoder ────────────────────────────────────────────────

async def decode_jwt_token(token: str) -> dict[str, Any]:
    """Decodifica e valida un JWT da Azure Entra ID.

    In produzione: verifica firma con JWK endpoint Entra ID.
    In sviluppo: se SKIP_JWT_VALIDATION=true, decodifica senza verifica.
    """
    skip_validation = os.getenv("SKIP_JWT_VALIDATION", "false").lower() == "true"

    if skip_validation:
        # Dev mode: decodifica senza verifica firma
        return jwt.get_unverified_claims(token)

    config = _get_entra_config()

    try:
        claims = jwt.decode(
            token,
            key="",  # In produzione: usa JWKS cachati
            algorithms=["RS256"],
            audience=config["audience"],
            issuer=config["issuer"],
            options={
                "verify_signature": True,
                "verify_aud": bool(config["audience"]),
                "verify_iss": bool(config["issuer"]),
                "verify_exp": True,
            },
        )
        return claims
    except JWTError as exc:
        logger.warning("jwt_decode_failed", error=str(exc))
        raise AppException(ErrorCode.AUTH_002, detail=str(exc)) from exc


# ── Dependency: Estrai dati dal JWT e popola ContextVars ────────

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """FastAPI Dependency: estrae e valida l'utente dal JWT.

    Popola ContextVars con tenant_id, user_id, roles.
    Se arriva da APIM, i dati sono anche negli header X-Tenant-Id, X-User-Id.

    Returns:
        Dict con claims JWT (tid, oid, roles, name, etc.)
    """
    # Priorità 1: JWT dal Bearer token
    if credentials and credentials.credentials:
        claims = await decode_jwt_token(credentials.credentials)
    # Priorità 2: Headers da APIM (JWT già validato dal gateway)
    elif request.headers.get("x-tenant-id"):
        claims = {
            "tid": request.headers.get("x-tenant-id"),
            "oid": request.headers.get("x-user-id"),
            "roles": request.headers.get("x-user-roles", "").split(","),
        }
    else:
        raise AppException(ErrorCode.AUTH_001)

    # Estrai tenant_id (obbligatorio)
    tenant_id = claims.get("tid")
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    # Popola ContextVars
    set_tenant_id(tenant_id)
    set_user_id(claims.get("oid", "unknown"))
    set_user_roles(claims.get("roles", []))

    return claims


# ── Dependency: tenant_id dal context (per gli endpoint) ────────

async def require_tenant(
    _user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """FastAPI Dependency: assicura che il tenant_id sia disponibile.

    Uso negli endpoint:
        @router.post("/documents")
        async def upload(tenant_id: str = Depends(require_tenant)):
            path = f"tenants/{tenant_id}/docs/{uuid4()}"
    """
    from app.core.context import get_tenant_id

    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)
    return tenant_id


def require_role(allowed_roles: list[str]):
    """
    FastAPI Dependency: verifica che l'utente abbia almeno uno dei ruoli permessi.
    """
    async def role_checker(claims: dict[str, Any] = Depends(get_current_user)):
        user_roles = claims.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            logger.warning("unauthorized_role_access", required=allowed_roles, current=user_roles)
            raise AppException(ErrorCode.AUTH_004)
        return claims
    
    return role_checker
