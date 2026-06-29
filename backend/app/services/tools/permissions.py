"""
Tool Permission System — Controls tool access by tenant and role.
"""


import structlog

logger = structlog.get_logger(__name__)

class PermissionError(Exception):
    """Raised when a user is not authorized to use a tool."""
    pass

class ToolPermission:
    """Manages permissions for AI agent tools."""

    def __init__(self):
        # In a real app, this might come from a DB or App Configuration
        self._tool_roles = {}

    def set_tool_roles(self, tool_name: str, allowed_roles: list[str]):
        """Define which roles can access a tool."""
        self._tool_roles[tool_name] = allowed_roles

    def check_permission(self, tool_name: str, tenant_id: str, user_role: str) -> bool:
        """
        Check if the given user role in the tenant can execute the tool.
        Raises PermissionError if unauthorized.
        """
        allowed_roles = self._tool_roles.get(tool_name)

        # If no specific roles are defined, we might assume it's open, or restricted.
        # Let's assume open by default for unconfigured tools, or change logic as needed.
        if allowed_roles is None:
            return True

        if user_role not in allowed_roles:
            logger.warning("tool_permission_denied", tool=tool_name, tenant=tenant_id, role=user_role)
            raise PermissionError(f"Role '{user_role}' is not authorized to use tool '{tool_name}'")

        return True

tool_permissions = ToolPermission()
