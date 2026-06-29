"""
Observability AI — Logging agent steps, reasoning, and tools.
"""


import structlog

logger = structlog.get_logger(__name__)

class AgentLogger:
    """Provides structured logging for agent operations."""

    def log_agent_step(self, thought: str, action: str | None, result: str | None):
        """Logs the agent's internal reasoning loop."""
        logger.info(
            "agent_step_executed",
            thought=thought,
            action=action,
            result=result
        )

    def log_tool_usage(self, tool_name: str, tenant_id: str, success: bool, error: str | None = None):
        """Logs when a tool is called."""
        logger.info(
            "tool_usage",
            tool=tool_name,
            tenant_id=tenant_id,
            success=success,
            error=error
        )

    def log_token_usage(self, tenant_id: str, tokens_prompt: int, tokens_completion: int):
        """Logs the tokens consumed during an LLM interaction."""
        logger.info(
            "token_usage",
            tenant_id=tenant_id,
            prompt_tokens=tokens_prompt,
            completion_tokens=tokens_completion,
            total_tokens=tokens_prompt + tokens_completion
        )

agent_logger = AgentLogger()
