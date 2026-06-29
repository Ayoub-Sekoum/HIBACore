"""
Task 2.07 — RBAC Middleware + @require_role

Ruoli dal JWT claim 'roles[]'. Solo SSO Microsoft Entra ID.
Route /admin/* richiedono SUPER_ADMIN.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Depends

from app.core.auth import get_current_user
from app.core.context import get_user_roles
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)


def require_role(*allowed_roles: str):
    """FastAPI Dependency Factory: verifica che l'utente abbia almeno uno dei ruoli richiesti.

    Uso:
        @router.get("/admin/tenants")
        async def list_tenants(user=Depends(require_role("SUPER_ADMIN"))):
            ...

        @router.post("/chat")
        async def chat(user=Depends(require_role("USER", "ADMIN"))):
            ...
    """

    async def _check_roles(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_roles = get_user_roles()

        # Verifica se l'utente ha almeno uno dei ruoli richiesti
        if not any(role in user_roles for role in allowed_roles):
            logger.warning(
                "access_denied",
                required_roles=list(allowed_roles),
                user_roles=user_roles,
                user_id=user.get("oid"),
            )
            raise AppException(
                ErrorCode.AUTH_004,
                detail=f"Ruoli richiesti: {', '.join(allowed_roles)}",
            )

        return user

    return _check_roles
