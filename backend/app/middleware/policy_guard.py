"""
policy_guard.py — Middleware di protezione per l'esecuzione dei tool.
Percorso: backend/app/middleware/policy_guard.py
"""
import structlog
from app.core.policy_engine import check_policy, PolicyDecision
from app.core.context import get_tenant_id, get_user_id
from app.services.policy.audit_log import audit_log_service
from app.services.policy.approval import approval_queue
from app.services.policy.notification_service import notification_service

logger = structlog.get_logger(__name__)

class PolicyGuard:
    @staticmethod
    async def check(tool_name: str, args: dict) -> PolicyDecision:
        """
        Verifica la policy prima di eseguire un tool.
        Recupera tenant_id e user_id dal context.
        """
        tenant_id = get_tenant_id()
        user_id = get_user_id() or "system"

        if not tenant_id:
            logger.error("policy_guard_missing_tenant_id", tool_name=tool_name)
            return PolicyDecision(decision="DENY", reason="Tenant ID missing", error_code="TENANT_101")

        # Determination of risk level (simplified)
        high_risk_tools = ["shell_exec", "webhook_send", "delete_file"]
        risk_level = "high" if tool_name in high_risk_tools else "low"

        # Check Policy
        decision = await check_policy(
            tenant_id=tenant_id,
            tool_name=tool_name,
            action_risk_level=risk_level,
            target_url=args.get("url") or args.get("endpoint")
        )

        # Log denials
        if decision.decision == "DENY":
            await audit_log_service.log_policy_denial(
                tenant_id=tenant_id,
                actor_id=user_id,
                tool_name=tool_name,
                reason=decision.reason,
                error_code=decision.error_code
            )

        # Handle Pending
        if decision.decision == "PENDING":
            # 3. Add to approval queue
            approval_id = await approval_queue.add(tenant_id, tool_name, args, decision)

        return decision
