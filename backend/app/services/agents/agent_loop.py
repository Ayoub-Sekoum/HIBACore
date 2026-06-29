"""
Agent Loop Engine — Orchestration and Tool Calling.
Task 5.01 — Multi-Tenant Enterprise Chatbot.
"""

from collections.abc import AsyncGenerator
from typing import Any

import structlog
from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool # type: ignore
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

logger = structlog.get_logger(__name__)

class AgentOrchestrator:
    """Orchestrates autonomous agent runs using Azure AI Projects SDK."""

    def __init__(self):
        self.settings = get_settings()
        self._project_client: AIProjectClient | None = None

    async def _get_client(self) -> AIProjectClient:
        """Lazy initialization of AIProjectClient."""
        if self._project_client is None:
            endpoint = self.settings.AZURE_AI_PROJECT_ENDPOINT
            if not endpoint:
                logger.error("azure_ai_project_endpoint_missing")
                raise AppException(ErrorCode.INFRA_901, detail="AZURE_AI_PROJECT_ENDPOINT not configured")

            credential = get_global_credential()
            self._project_client = AIProjectClient(
                endpoint=endpoint,
                credential=credential
            )
        return self._project_client

    async def run_agent(
        self,
        tenant_id: str,
        user_query: str,
        session_id: str,
        instructions: str = "You are a helpful enterprise assistant."
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Runs an autonomous agent loop and yields progress/result chunks."""
        client = await self._get_client()

        try:
            # 1. Get or Create Agent
            # In production, we would use create_memory_store() and attach it
            agent = await client.agents.create_agent( # type: ignore
                model=self.settings.AZURE_OPENAI_NORMAL_DEPLOYMENT,
                name=f"agent-{tenant_id}",
                instructions=instructions,
                tools=[CodeInterpreterTool(), FileSearchTool()], # type: ignore
            )

            # 2. Create Thread
            thread = await client.agents.threads.create() # type: ignore

            # 3. Add Message
            await client.agents.messages.create( # type: ignore
                thread_id=thread.id,
                role="user",
                content=user_query,
            )

            # 4. Create and Stream Run
            logger.info("agent_run_started", tenant_id=tenant_id, session_id=session_id)

            # Using streaming for real-time feedback
            async with await client.agents.runs.create_and_stream_run( # type: ignore
                thread_id=thread.id,
                agent_id=agent.id
            ) as stream:
                async for event in stream:
                    # Map SDK events to our SSE format
                    if event.type == "thread.message.delta":
                        yield {"type": "content", "delta": event.data.delta.content[0].text.value}
                    elif event.type == "thread.run.step.delta":
                        if event.data.delta.step_details.type == "tool_calls":
                            yield {"type": "status", "message": "Esecuzione tool in corso..."}
                    elif event.type == "thread.run.completed":
                        yield {"type": "status", "message": "Completato"}

        except Exception as e:
            logger.error("agent_run_failed", error=str(e))
            yield {"type": "error", "code": "AGENT_500", "message": str(e)}
        finally:
            # Clean up (optional, depending on persistence requirements)
            # await client.agents.delete_agent(agent.id)
            pass

    async def close(self):
        """Closes the project client."""
        if self._project_client:
            await self._project_client.close()

agent_orchestrator = AgentOrchestrator()
