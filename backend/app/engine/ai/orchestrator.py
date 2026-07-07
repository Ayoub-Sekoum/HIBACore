"""
Task 7.07 — Thinking Levels (Multi-model Orchestrator).
Logica: Seleziona il modello (mini, gpt-4o, o1) in base alla complessità della query.
"""

from enum import Enum
from typing import Any, List, Optional
from collections.abc import AsyncGenerator
import structlog
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)

class ThinkingLevel(str, Enum):
    FAST = "fast"      # gpt-4o-mini
    NORMAL = "normal"  # gpt-4o
    DEEP = "deep"      # o1-preview

class OrchestrationResult(BaseModel):
    level: ThinkingLevel
    model_deployment: str
    response: Any

class ThinkingOrchestrator:
    """
    Orchestratore intelligente che decide quanto "pensare" prima di rispondere.
    """

    def __init__(self):
        self.settings = get_settings()
        self.llm_client = ResilientLLMClient()

    async def route_and_execute(
        self,
        tenant_id: str,
        messages: List[dict[str, Any]],
        force_level: Optional[ThinkingLevel] = None,
        **kwargs
    ) -> OrchestrationResult:
        """
        Decide il livello di "thinking" e esegue la chiamata.
        Regola 3: tenant_id come primo parametro.
        """
        if not tenant_id:
            raise AppException(ErrorCode.TENANT_101)

        # 1. Level decision
        last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        
        # We extract the tenant_max_level from the kwargs if present (e.g. policy)
        tenant_max = kwargs.pop("tenant_max_level", None)
        
        level = force_level or self._decide_level(last_user_message, messages, tenant_max)
        deployment = self._get_deployment_for_level(level)

        logger.info("orchestrator_routing", tenant_id=tenant_id, level=level, deployment=deployment)

        try:
            # 2. Execution via ResilientLLMClient (Circuit Breaker + Failover)
            # Note: o1-preview may not support some parameters such as 'stream' or 'tools' in certain contexts
            call_kwargs = kwargs.copy()
            if level == ThinkingLevel.DEEP:
                # o1-preview does not currently support streams or tools in many Azure regions
                call_kwargs.pop("stream", None)
                call_kwargs.pop("tools", None)

            response = await self.llm_client.complete(
                messages=messages,
                model=deployment,
                **call_kwargs
            )

            # BUGFIX: Prevent Reasoning Leak on non-streaming responses
            if hasattr(response, "choices") and len(response.choices) > 0:
                msg = getattr(response.choices[0], "message", None)
                if msg:
                    # We remove the reasoning_content before returning it
                    if hasattr(msg, "reasoning_content"):
                        msg.reasoning_content = None
                    if hasattr(msg, "reasoning"):
                        msg.reasoning = None

            return OrchestrationResult(
                level=level,
                model_deployment=deployment,
                response=response
            )

        except Exception as e:
            logger.error("orchestrator_execution_failed", tenant_id=tenant_id, level=level, error=str(e))
            raise AppException(ErrorCode.AI_201, detail=f"Orchestration failed at level {level}: {str(e)}")

    async def route_and_stream(
        self,
        tenant_id: str,
        messages: List[dict[str, Any]],
        force_level: Optional[ThinkingLevel] = None,
        **kwargs
    ) -> AsyncGenerator[tuple[ThinkingLevel, str, Any], None]:
        """
        Orchestra lo streaming selezionando il livello corretto.
        Ritorna (level, deployment, chunk).
        Regola 3: tenant_id come primo parametro.
        """
        if not tenant_id:
            raise AppException(ErrorCode.TENANT_101)

        last_user_message = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        
        tenant_max = kwargs.pop("tenant_max_level", None)
        level = force_level or self._decide_level(last_user_message, messages, tenant_max)
        deployment = self._get_deployment_for_level(level)

        logger.info("orchestrator_streaming_routing", tenant_id=tenant_id, level=level, deployment=deployment)

        try:
            # o1-preview does not support streams in many regions
            if level == ThinkingLevel.DEEP:
                # Fallback to non-stream for o1 if needed or handle error
                # Here we use complete and simulate a final chunk if stream is required?
                # No, we proceed with streaming if supported by the provider.
                pass

            stream = self.llm_client.complete_stream(
                messages=messages,
                model=deployment,
                **kwargs
            )

            async for chunk in stream:
                yield level, deployment, chunk

        except Exception as e:
            logger.error("orchestrator_stream_failed", tenant_id=tenant_id, level=level, error=str(e))
            yield level, deployment, {"error": str(e)}

    def _decide_level(self, query: str, messages: List[dict[str, Any]] = None, tenant_max_level: Optional[ThinkingLevel] = None) -> ThinkingLevel:
        """
        Euristica per decidere il livello di complessità, analizzando query,
        messaggi precedenti (tool calls) e rispettando il tenant_max_level.
        """
        query_lower = query.lower()
        
        # 1. Check previous tool calls
        had_tools = False
        if messages:
            # Check to see if the assistant's last message had tool_calls
            for m in reversed(messages):
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    had_tools = True
                    break
                    
        # Keywords for DEEP thinking
        deep_triggers = ["analizza", "complicato", "ragiona", "spiega nel dettaglio", "architettura", "codice", "debug"]
        
        chosen_level = ThinkingLevel.NORMAL
        
        if had_tools or any(t in query_lower for t in deep_triggers) or len(query) > 300:
            chosen_level = ThinkingLevel.DEEP
        else:
            # Keywords for FAST thinking
            fast_triggers = ["ciao", "grazie", "chi sei", "ora", "meteo"]
            if any(t in query_lower for t in fast_triggers) and len(query) < 50:
                chosen_level = ThinkingLevel.FAST
                
        # 2. Respecting the tenant_max_level
        if tenant_max_level:
            levels_order = {ThinkingLevel.FAST: 1, ThinkingLevel.NORMAL: 2, ThinkingLevel.DEEP: 3}
            if levels_order[chosen_level] > levels_order[tenant_max_level]:
                chosen_level = tenant_max_level
                
        return chosen_level

    def _get_deployment_for_level(self, level: ThinkingLevel) -> str:
        if level == ThinkingLevel.FAST:
            return self.settings.AZURE_OPENAI_MINI_DEPLOYMENT
        elif level == ThinkingLevel.DEEP:
            return self.settings.AZURE_OPENAI_O1_DEPLOYMENT
        return self.settings.AZURE_OPENAI_NORMAL_DEPLOYMENT

