"""
policy_engine.py — Il cuore decisionale della sicurezza.
Percorso: backend/app/core/policy_engine.py
"""
import structlog
from typing import Optional, Any
from dataclasses import dataclass, field
from app.services.policy.plan_definitions import PLAN_DEFINITIONS, can_plan_use_tool
# policy_store and audit_log will be implemented in subsequent steps
# from app.services.policy.policy_store import get_tenant_policy
# from app.services.policy.audit_log import log_policy_denial

logger = structlog.get_logger(__name__)

@dataclass
class PolicyDecision:
    decision: str  # "ALLOW" | "DENY" | "PENDING"
    reason: str
    error_code: Optional[str] = None
    requires_approval: bool = False
    audit_data: dict = field(default_factory=dict)


async def check_policy(
    tenant_id: str,
    tool_name: str,
    action_risk_level: str = "low",
    target_url: str | None = None,
    thinking_level: str | None = None,
) -> PolicyDecision:
    """
    Unico punto di verifica policy nel sistema.
    Fallisce CHIUSO: se non riesce a caricare la policy → DENY.
    """
    try:
        # Step 1: Carica policy (Mock per ora, verrà collegato a policy_store)
        # TODO: integrare get_tenant_policy(tenant_id)
        from app.services.policy.policy_store import get_tenant_policy
        policy = await get_tenant_policy(tenant_id)
        
        if not policy:
            return PolicyDecision(
                decision="DENY", 
                reason="Policy not found for tenant",
                error_code="POLICY_001"
            )

        # Step 2: Verifica stato tenant
        if policy.get("status") == "suspended":
            return PolicyDecision(
                decision="DENY",
                reason="Tenant is suspended",
                error_code="POLICY_001"
            )

        # Step 3: Verifica tool allowlist del tenant
        allowlist = policy.get("tool_allowlist", [])
        if tool_name not in allowlist:
            return PolicyDecision(
                decision="DENY",
                reason=f"Tool '{tool_name}' not in tenant allowlist",
                error_code="POLICY_002"
            )

        # Step 4: Verifica piano tariffario
        tenant_plan = policy.get("plan", "base")
        if not can_plan_use_tool(tenant_plan, tool_name):
            return PolicyDecision(
                decision="DENY",
                reason=f"Tool '{tool_name}' not supported by plan '{tenant_plan}'",
                error_code="POLICY_003"
            )

        # Step 5: Verifica URL (se applicabile)
        if target_url:
            net_allowlist = policy.get("network_allowlist", [])
            # Semplice check dominio per ora
            if not any(domain in target_url for domain in net_allowlist):
                return PolicyDecision(
                    decision="DENY",
                    reason=f"Target URL '{target_url}' not in allowlist",
                    error_code="POLICY_006"
                )

        # Step 6: Verifica Thinking Level
        if thinking_level:
            max_thinking = PLAN_DEFINITIONS.get(tenant_plan).max_thinking_level
            # normal < deep
            thinking_map = {"fast": 0, "normal": 1, "deep": 2}
            if thinking_map.get(thinking_level, 0) > thinking_map.get(max_thinking, 1):
                return PolicyDecision(
                    decision="DENY",
                    reason=f"Thinking level '{thinking_level}' exceeds plan limit",
                    error_code="POLICY_005"
                )

        # Step 7: Verifica Rischio Alto
        if action_risk_level == "high":
            if policy.get("require_approval_for_high_risk", True):
                return PolicyDecision(
                    decision="PENDING",
                    reason="High-risk action requires manual approval",
                    error_code="POLICY_004",
                    requires_approval=True
                )

        # Step 8: Successo
        return PolicyDecision(decision="ALLOW", reason="Policy check passed")

    except Exception as e:
        logger.error("policy_check_failed", error=str(e), tenant_id=tenant_id, exc_info=True)
        return PolicyDecision(
            decision="DENY",
            reason="Internal policy error (fail-closed)",
            error_code="POLICY_001"
        )
