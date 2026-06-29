"""
Teams Adapter — Integration layer for external events.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)

class TeamsAdapter:
    """Translates Teams webhook events into internal agent requests."""

    def __init__(self, agent_planner):
        self.agent_planner = agent_planner

    async def handle_message(self, payload: dict[str, Any]) -> str:
        """
        Process an incoming Teams message payload.
        Maps the webhook payload to our internal routing structure.
        """
        message_type = payload.get("type")
        if message_type != "message":
            logger.info("teams_adapter_ignored_event", event_type=message_type)
            return "Event ignored"

        text = payload.get("text", "")
        tenant_id = payload.get("tenantId", "unknown_tenant")
        user_info = payload.get("from", {})
        user_id = user_info.get("id", "unknown_user")

        # Real extraction of session_id from conversation object
        conversation_info = payload.get("conversation", {})
        session_id = conversation_info.get("id", f"session_{user_id}")

        # Real extraction or mapping of user_role.
        # In a real Teams app, you might look at AAD token claims or bot framework context.
        # Here we map directly if they send specific roles in the from object metadata.
        user_role = user_info.get("role", "user")

        logger.info("teams_adapter_processing", user=user_id, tenant=tenant_id, text=text, session=session_id)

        try:
            response = await self.agent_planner.plan_and_execute(
                user_request=text,
                tenant_id=tenant_id,
                user_role=user_role,
                session_id=session_id
            )
            return response
        except Exception as e:
            logger.error("teams_adapter_error", error=str(e))
            return "Error processing request via Teams Adapter."
