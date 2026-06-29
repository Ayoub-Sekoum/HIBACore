"""
Secure Code Execution Sandbox using Azure Container Instances (ACI).
Task 5.05 — Multi-Tenant Enterprise Chatbot.
"""

import os

import structlog
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from azure.mgmt.containerinstance.aio import ContainerInstanceManagementClient

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

class ACISandbox:
    """Sandbox for secure code execution in isolated ACI containers."""

    def __init__(self):
        self.settings = get_settings()
        self._mgmt_client: ContainerInstanceManagementClient | None = None

    async def _get_client(self) -> ContainerInstanceManagementClient:
        """Lazy initialization of the management client."""
        if self._mgmt_client is None:
            credential = get_global_credential()
            subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
            if not subscription_id:
                raise AppException(ErrorCode.INFRA_901, detail="AZURE_SUBSCRIPTION_ID not configured")

            self._mgmt_client = ContainerInstanceManagementClient(credential, subscription_id)
        return self._mgmt_client

    async def execute_python(self, tenant_id: str, code: str) -> dict[str, str]:
        """
        Executes Python code in a sandboxed ACI.
        Note: This is a high-latency operation (seconds to minutes for cold start).
        Managed Code Interpreter (Phase 5.01) is preferred for low latency.
        """
        logger.info("aci_sandbox_execution_requested", tenant_id=tenant_id)

        return {
            "stdout": "Risultato esecuzione (Placeholder ACI)",
            "stderr": "",
            "exit_code": "0"
        }

aci_sandbox = ACISandbox()
