"""
Centralized Configuration Manager using Pydantic Settings and Azure App Configuration.
Loads settings from environment variables first, then optionally from Azure App Configuration.
Supports multi-tenancy via labels in Azure App Configuration.
"""

from typing import Any

import structlog
from azure.appconfiguration.aio import AzureAppConfigurationClient
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Core App Info
    APP_NAME: str = "HOBA AI"
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    # ZeroClaw AI Agent Configuration
    ZEROCLAW_GATEWAY_URL: str = "http://4.209.34.69:42617"
    ZEROCLAW_ENABLED: bool = True

    # Azure Infrastructure
    AZURE_APP_CONFIG_ENDPOINT: str | None = None
    APPLICATIONINSIGHTS_CONNECTION_STRING: str | None = None
    AZURE_KEYVAULT_ENDPOINT: str | None = None

    # Storage & DB
    COSMOS_ENDPOINT: str | None = None
    COSMOS_KEY: str | None = None
    COSMOS_DATABASE_NAME: str = "chatdb"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_USE_SSL: bool = False

    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    
    # PostgreSQL/pgvector (Semantic Memory)
    DB_HOST: str | None = None
    DB_NAME: str = "postgres"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None

    # AI Services
    AI_RETRIEVER_TOP_K: int = 20
    AI_RRF_K: int = 60
    AI_MAX_CITATION_TOKENS: int = 8000
    AI_PERSONA_OLD_WEIGHT: float = 0.7
    AI_PERSONA_NEW_WEIGHT: float = 0.3
    AI_CHAT_HISTORY_LIMIT: int = 60
    AI_MAX_CONTEXT_BUDGET: int = 8000
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_SECONDARY_ENDPOINT: str | None = None
    AZURE_OPENAI_SECONDARY_API_KEY: str | None = None
    AZURE_OPENAI_MINI_DEPLOYMENT: str = "gpt-4o-mini"
    AZURE_OPENAI_NORMAL_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_O1_DEPLOYMENT: str = "o1-preview"

    CONTENT_SAFETY_ENDPOINT: str | None = None
    CONTENT_SAFETY_KEY: str | None = None

    CONTENTUNDERSTANDING_ENDPOINT: str | None = None

    AZURE_SEARCH_ENDPOINT: str | None = "https://dummy-search.search.windows.net"
    AZURE_SEARCH_KEY: str | None = None
    AZURE_SEARCH_INDEX: str = "documents"

    # Auth
    AZURE_AD_TENANT_ID: str | None = None
    AZURE_AD_CLIENT_ID: str | None = None

    # Agent Project
    AZURE_AI_PROJECT_ENDPOINT: str | None = None

    # Phase 7: Voice & Vision
    TRANSCRIPTION_ENDPOINT: str | None = None
    TRANSCRIPTION_KEY: str | None = None
    AZURE_COGNITIVE_SERVICES_ENDPOINT: str | None = None
    AZURE_COGNITIVE_SERVICES_KEY: str | None = None
    VISION_ENDPOINT: str | None = None
    VISION_KEY: str | None = None

    # Agent & DeepAgents Configuration
    # Scoped directory for agent operations
    AGENT_WORKSPACE_PATH: str = Field(default="agent_workspace", alias="AGENT_WORKSPACE_PATH")
    # Azure Blob Storage container for agent file backups
    AGENT_STORAGE_CONTAINER: str = "agent-artifacts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


class ConfigManager:
    """Manager to handle dynamic configuration from Azure App Configuration."""

    def __init__(self):
        self._settings = Settings()
        self._client: AzureAppConfigurationClient | None = None
        self._cache: dict[str, dict[str, Any]] = {}  # tenant_id -> config

    @property
    def settings(self) -> Settings:
        """Access the static/base settings."""
        return self._settings

    async def get_azure_client(self) -> AzureAppConfigurationClient | None:
        """Lazy initialization of the Azure App Configuration client."""
        if self._client is None and self._settings.AZURE_APP_CONFIG_ENDPOINT:
            try:
                credential = get_global_credential()
                self._client = AzureAppConfigurationClient(
                    base_url=self._settings.AZURE_APP_CONFIG_ENDPOINT,
                    credential=credential
                )
            except Exception as e:
                logger.error("app_config_client_init_failed", error=str(e))
        return self._client

    async def get_tenant_config(self, tenant_id: str) -> dict[str, Any]:
        """
        Fetches tenant-specific configuration from Azure App Configuration.
        Uses the tenant_id as the label.
        """
        if tenant_id in self._cache:
            return self._cache[tenant_id]

        client = await self.get_azure_client()
        if not client:
            return {}

        try:
            config = {}
            # List settings for this specific tenant label
            items = client.list_configuration_settings(label_filter=tenant_id)
            async for item in items:
                # Assuming keys are like 'app:settings:foo'
                # We strip the prefix if necessary or just store the key
                config[item.key] = item.value

            self._cache[tenant_id] = config
            return config
        except Exception as e:
            logger.warning("tenant_config_fetch_failed", tenant_id=tenant_id, error=str(e))
            return {}

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.close()


# Singleton instance
config_manager = ConfigManager()


def get_settings() -> Settings:
    """Provider function for FastAPI dependencies."""
    return config_manager.settings
