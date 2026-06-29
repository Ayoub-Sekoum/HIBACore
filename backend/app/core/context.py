"""
Task 2.06 — ContextVars per tenant_id, user_id, correlation_id

Il tenant_id viene SEMPRE dal JWT, MAI dal body della richiesta.
Thread-safe via ContextVar per async FastAPI.
"""

from __future__ import annotations

from contextvars import ContextVar

# ── Context Variables (thread-safe per asyncio) ────────────────
_tenant_id_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)
_user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_user_roles_var: ContextVar[list[str]] = ContextVar("user_roles", default=[])


# ── Getters ────────────────────────────────────────────────────

def get_tenant_id() -> str | None:
    """Restituisce il tenant_id dal context (estratto dal JWT)."""
    return _tenant_id_var.get()


def get_user_id() -> str | None:
    """Restituisce lo user_id dal context (estratto dal JWT)."""
    return _user_id_var.get()


def get_correlation_id() -> str | None:
    """Restituisce il correlation_id dal context (da X-Correlation-Id APIM)."""
    return _correlation_id_var.get()


def get_user_roles() -> list[str]:
    """Restituisce i ruoli utente dal context (dal JWT claim roles)."""
    return _user_roles_var.get()


# ── Setters (usati solo dai middleware) ─────────────────────────

def set_tenant_id(value: str) -> None:
    """Setta il tenant_id nel context. Solo per middleware."""
    _tenant_id_var.set(value)


def set_user_id(value: str) -> None:
    """Setta lo user_id nel context. Solo per middleware."""
    _user_id_var.set(value)


def set_correlation_id(value: str) -> None:
    """Setta il correlation_id nel context. Solo per middleware."""
    _correlation_id_var.set(value)


def set_user_roles(roles: list[str]) -> None:
    """Setta i ruoli utente nel context. Solo per middleware."""
    _user_roles_var.set(roles)


def clear_context() -> None:
    """Pulisce tutto il context. Chiamato a fine richiesta."""
    _tenant_id_var.set(None)
    _user_id_var.set(None)
    _correlation_id_var.set(None)
    _user_roles_var.set([])
