from collections.abc import Callable
from typing import Any

import structlog

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

class ToolRegistry:
    """
    Task 5.02: Tool Registry Dinamico.
    Mantiene in memoria un dizionario di tool disponibili per l'Agent Loop.
    """
    _tools: dict[str, Callable] = {}

    # Task 5.03: Mock Cosmos DB table tenant_tool_allowlist
    # Format: { "tenant_id": ["tool_name1", "tool_name2"] }
    _tenant_allowlist: dict[str, list[str]] = {
        # Default configuration
        "default_tenant": ["web_search", "file_read"]
    }

    @classmethod
    def register(cls, name: str, func: Callable) -> None:
        cls._tools[name] = func
        logger.info("tool_registered", tool_name=name)

    @classmethod
    async def execute(cls, tenant_id: str, tool_name: str, **kwargs) -> Any:
        """
        Task 12.05: Policy Guard Middleware Integration.
        Sostituisce la vecchia allowlist statica con il controllo dinamico Policy Engine.
        """
        from app.middleware.policy_guard import PolicyGuard

        # 1. Check policy before proceeding
        decision = await PolicyGuard.check(
            tenant_id=tenant_id,
            tool_name=tool_name,
            args=kwargs
        )

        if decision.decision == "DENY":
            logger.warning("tool_execution_denied_by_policy", tenant_id=tenant_id, tool_name=tool_name)
            # Return structured error instead of throwing blocking exception (Task 12.05)
            return {
                "success": False,
                "error_code": decision.error_code,
                "message": decision.reason
            }

        if decision.decision == "PENDING":
            logger.info("tool_execution_pending_approval", tenant_id=tenant_id, tool_name=tool_name)
            # Todo: Save in real approval queue
            return {
                "success": False,
                "error_code": "POLICY_004",
                "message": "Azione in attesa di approvazione del tuo amministratore."
            }

        # 2. Proceed with execution if ALLOW
        if tool_name not in cls._tools:
            raise AppException(ErrorCode.TOOL_504, detail=f"Tool '{tool_name}' not found in registry")

        func = cls._tools[tool_name]
        try:
            return await func(**kwargs)
        except Exception as e:
            logger.error("tool_execution_failed", tool_name=tool_name, error=str(e), exc_info=True)
            raise AppException(ErrorCode.TOOL_502, detail=str(e))
