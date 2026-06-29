"""
Task 2.08 — Feature Flag Manager + Azure App Configuration

Legge toggle da Azure App Configuration con label={tenant_id}.
Fallback a env vars per sviluppo locale.
Hot-reload senza restart (cache con TTL).
"""

from __future__ import annotations

import os
import time
from typing import Any

import structlog
from fastapi import Depends

from app.core.auth import require_tenant
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

# Cache in-memory con TTL
_flag_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL_SECONDS = 60.0


class FeatureFlagManager:
    """Gestisce feature flags da Azure App Configuration o env vars.

    In produzione: legge da Azure App Configuration con label={tenant_id}.
    In dev locale: fallback a variabili d'ambiente.
    """

    def __init__(self) -> None:
        self._client = None
        self._use_azure = os.getenv("AZURE_APP_CONFIG_ENDPOINT") is not None

    async def _get_azure_client(self):
        """Lazy init del client Azure App Configuration."""
        if self._client is None and self._use_azure:
            try:
                from azure.appconfiguration.aio import AzureAppConfigurationClient
                from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

                credential = get_global_credential()
                endpoint = os.getenv("AZURE_APP_CONFIG_ENDPOINT", "")
                self._client = AzureAppConfigurationClient(
                    base_url=endpoint,
                    credential=credential,
                )
            except Exception as exc:
                logger.warning(
                    "app_config_init_failed",
                    error=str(exc),
                    message="Fallback a env vars",
                    exc_info=True
                )
                self._use_azure = False
        return self._client

    async def get_flag(
        self,
        flag_name: str,
        tenant_id: str | None = None,
    ) -> bool:
        """Legge un feature flag.

        Args:
            flag_name: Nome del flag (es. ENABLE_RAG, ENABLE_AGENTS)
            tenant_id: Tenant ID per flag tenant-specific

        Returns:
            True se il flag è abilitato, False altrimenti.
        """
        cache_key = f"{flag_name}:{tenant_id or 'global'}"

        # Check cache
        if cache_key in _flag_cache:
            value, cached_at = _flag_cache[cache_key]
            if time.time() - cached_at < _CACHE_TTL_SECONDS:
                return bool(value)

        # Try Azure App Configuration
        if self._use_azure:
            try:
                client = await self._get_azure_client()
                if client:
                    label = tenant_id or "global"
                    setting = await client.get_configuration_setting(
                        key=flag_name,
                        label=label,
                    )
                    value = setting.value.lower() in ("true", "1", "yes", "enabled")
                    _flag_cache[cache_key] = (value, time.time())
                    return value
            except Exception:
                logger.debug("azure_app_config_get_failed", exc_info=True)
                pass  # Fallback a env vars

        # Fallback: env vars
        env_value = os.getenv(flag_name, "false")
        value = env_value.lower() in ("true", "1", "yes", "enabled")
        _flag_cache[cache_key] = (value, time.time())
        return value

    async def get_config(
        self,
        key: str,
        tenant_id: str | None = None,
        default: str = "",
    ) -> str:
        """Legge un valore di configurazione (non booleano)."""
        cache_key = f"config:{key}:{tenant_id or 'global'}"

        if cache_key in _flag_cache:
            value, cached_at = _flag_cache[cache_key]
            if time.time() - cached_at < _CACHE_TTL_SECONDS:
                return str(value)

        # Fallback a env vars
        value = os.getenv(key, default)
        _flag_cache[cache_key] = (value, time.time())
        return value


# ── Singleton ────────────────────────────────────────────────
_feature_flag_manager = FeatureFlagManager()


def get_feature_flag_manager() -> FeatureFlagManager:
    """Restituisce il singleton FeatureFlagManager."""
    return _feature_flag_manager


def require_flag(flag_name: str):
    """FastAPI Dependency Factory: blocca l'accesso se il flag è disabilitato.

    Uso:
        @router.post("/agent/run")
        async def run_agent(
            tenant_id: str = Depends(require_tenant),
            _flag=Depends(require_flag("ENABLE_AGENTS")),
        ):
            ...
    """

    async def _check_flag(
        tenant_id: str = Depends(require_tenant),
    ) -> bool:
        manager = get_feature_flag_manager()
        is_enabled = await manager.get_flag(flag_name, tenant_id)

        if not is_enabled:
            logger.info(
                "feature_flag_blocked",
                flag=flag_name,
                tenant_id=tenant_id,
            )
            raise AppException(
                ErrorCode.AUTH_004,
                detail=f"Funzionalità '{flag_name}' non disponibile per questo tenant.",
            )

        return is_enabled

    return _check_flag
