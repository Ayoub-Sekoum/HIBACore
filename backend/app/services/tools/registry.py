"""
Tool Registry — Dynamic Tool Loading and Management.
Task 5.02 — Multi-Tenant Enterprise Chatbot.
"""

import inspect
from collections.abc import Callable
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable

class ToolRegistry:
    """Registry for dynamic AI agent tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register_tool(self, name: str, description: str, parameters: dict[str, Any]):
        """Decorator to register a new tool."""
        def decorator(func: Callable):
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                func=func
            )
            return func
        return decorator

    def get_all_tool_schemas(self) -> list[dict[str, Any]]:
        """Returns OpenAI-compatible function schemas for all registered tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in self._tools.values()
        ]

    async def call_tool(self, name: str, **kwargs) -> Any:
        """Executes a registered tool by name."""
        if name not in self._tools:
            logger.error("tool_not_found", tool_name=name)
            raise ValueError(f"Tool {name} not found")

        tool = self._tools[name]
        try:
            if inspect.iscoroutinefunction(tool.func):
                return await tool.func(**kwargs)
            return tool.func(**kwargs)
        except Exception as e:
            logger.error("tool_execution_failed", tool_name=name, error=str(e))
            raise

tool_registry = ToolRegistry()
