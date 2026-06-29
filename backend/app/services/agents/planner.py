"""
Agent Planner — Decision engine using Azure AI Projects SDK.
"""

import structlog

from app.services.agents.agent_loop import agent_orchestrator

logger = structlog.get_logger(__name__)

class AgentPlanner:
    """Decision engine that plans actions using the Azure AI Projects SDK."""

    def __init__(self, tool_registry, tool_permissions, logger_system):
        self.tool_registry = tool_registry
        self.tool_permissions = tool_permissions
        self.logger_system = logger_system

    async def plan_and_execute(self, user_request: str, tenant_id: str, user_role: str, session_id: str) -> str:
        """
        Executes a loop using Azure AI Agents:
        The agent_orchestrator handles the reasoning, tool calling, and observation.
        """
        self.logger_system.log_agent_step(
            thought="Starting plan and execute loop via Azure AI Projects SDK.",
            action=None,
            result=None
        )

        # We collect the response stream
        final_response = []

        try:
            # We assume agent_orchestrator handles internal permission checks or we would inject them into the tools it has.
            # In Phase 5, tools are attached to the agent directly.

            async for chunk in agent_orchestrator.run_agent(
                tenant_id=tenant_id,
                user_query=user_request,
                session_id=session_id
            ):
                if chunk.get("type") == "content":
                    final_response.append(chunk.get("delta", ""))

                # We could log intermediate tool calls if they were yielded
                elif chunk.get("type") == "status":
                    self.logger_system.log_agent_step("Received status", chunk.get("message"), None)

            full_response = "".join(final_response)
            self.logger_system.log_agent_step("Finished execution", "finish", full_response)
            return full_response

        except Exception as e:
            error_msg = str(e)
            self.logger_system.log_agent_step("Error in agent loop", "error", error_msg)
            return f"Error processing request: {error_msg}"
