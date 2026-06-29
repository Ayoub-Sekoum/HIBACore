"""
plan_definitions.py — Definizione dei piani tariffari e dei limiti associati.
Percorso: backend/app/services/policy/plan_definitions.py
"""
from dataclasses import dataclass, field
from typing import List

@dataclass
class PlanDefinition:
    name: str
    allowed_tools: List[str]
    max_thinking_level: str
    max_file_size_mb: int
    sandbox_timeout_seconds: int
    can_customize_network_allowlist: bool
    require_approval_for_high_risk: bool
    admin_can_modify: List[str] = field(default_factory=list)

PLAN_DEFINITIONS = {
    "base": PlanDefinition(
        name="Base",
        allowed_tools=["web_search", "file_read"],
        max_thinking_level="normal",
        max_file_size_mb=50,
        sandbox_timeout_seconds=30,
        can_customize_network_allowlist=False,
        require_approval_for_high_risk=True,
        admin_can_modify=["require_approval_for_high_risk"],
    ),
    "standard": PlanDefinition(
        name="Standard",
        allowed_tools=["web_search", "file_read", "code_execution", "webhook_send"],
        max_thinking_level="normal",
        max_file_size_mb=100,
        sandbox_timeout_seconds=30,
        can_customize_network_allowlist=False,
        require_approval_for_high_risk=True,
        admin_can_modify=["tool_allowlist", "require_approval_for_high_risk"],
    ),
    "enterprise": PlanDefinition(
        name="Enterprise",
        allowed_tools=["web_search", "file_read", "code_execution",
                       "shell_exec", "webhook_send"],
        max_thinking_level="deep",
        max_file_size_mb=100,
        sandbox_timeout_seconds=60,
        can_customize_network_allowlist=True,
        require_approval_for_high_risk=False,
        admin_can_modify=["tool_allowlist", "network_allowlist",
                          "shell_commands_allowlist", "require_approval_for_high_risk",
                          "max_thinking_level"],
    ),
}

def can_plan_use_tool(plan: str, tool_name: str) -> bool:
    """Risponde: questo piano supporta questo tool?"""
    plan_def = PLAN_DEFINITIONS.get(plan.lower())
    if not plan_def:
        return False
    return tool_name in plan_def.allowed_tools

def get_admin_editable_fields(plan: str) -> List[str]:
    """Quali campi può modificare l'admin del cliente per questo piano?"""
    plan_def = PLAN_DEFINITIONS.get(plan.lower())
    if not plan_def:
        return []
    return plan_def.admin_can_modify
