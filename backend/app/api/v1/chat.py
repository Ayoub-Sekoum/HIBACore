import asyncio
import json
import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field

from app.agents.builder import AgentState, create_agent_executor
from app.core.auth import get_current_user
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.core.schemas import APIResponse
from app.core.utils import retry
from app.engine.ai.vision import vision_service
from app.engine.ai.orchestrator import ThinkingOrchestrator, ThinkingLevel
from app.engine.memory.cosmos import cosmos_memory_service
from app.engine.memory.mock import mock_memory_service
from app.tools.filesystem import list_files, read_file, write_file
from app.tools.skill_adapter import call_external_skill, search_available_skills

from app.engine.ai.prompts import get_tenant_system_prompt
from app.engine.memory.builder import build_memory_context
from app.core.context import get_tenant_id
from app.engine.ai.stylist import determine_writing_style, get_style_instructions
from app.engine.ai.security import check_prompt_injection
from app.engine.ai.token_counter import manage_context_window
from app.engine.ai.usage import record_usage
from app.services.messaging.bus import publish_to_recommendations_worker
from app.services.storage.agent_storage import backup_chat_memory, get_agent_memory


logger = structlog.get_logger(__name__)


# Helper to get the active memory service
def get_memory_service():
    import os
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    skip_jwt = os.getenv("SKIP_JWT_VALIDATION", "false").lower() == "true"
    if skip_jwt or not cosmos_endpoint:
        return mock_memory_service
    return cosmos_memory_service

router = APIRouter(dependencies=[Depends(get_current_user)])

class ChatRequest(BaseModel):
    text: str = Field(..., description="Il messaggio dell'utente")
    isPensieroProfondoAttivo: bool = Field(False, description="Se True, usa il Deep Thinking con Skill Engine")
    session_id: str | None = Field(None, description="ID della sessione chat per il recupero history")
    image_url: str | None = Field(None, description="Task 7.05: URL immagine per GPT-4o Vision")
    thinking_level: str = Field("normal", description="Task 7.07: fast (mini), normal (4o), deep (o1)")
    isCitationsEnabled: bool = Field(True, description="Se True, usa il recupero RAG")
    used_skills: list[str] | None = Field(default_factory=list, description="Lista di skill/funzioni abilitate dall'utente")

class ChatResponse(BaseModel):
    response: str
    used_skills: list[str] | None = None

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str

class ModelsResponse(BaseModel):
    models: list[ModelInfo]

class SkillInfo(BaseModel):
    id: str
    name: str
    description: str
    path: str
    category: str | None = None

class SkillsResponse(BaseModel):
    skills: list[SkillInfo]

# Azure OpenAI and external tool hooks
SKILL_ENGINE_URL = os.getenv("SKILL_ENGINE_URL", "http://localhost:3000")

@retry(max_attempts=3, is_async=True)
async def get_skill_tools() -> list[dict]:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SKILL_ENGINE_URL}/skills/index", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Fallback for testing/if engine is down
            logger.error("fetch_tools_failed", error=str(e), exc_info=True)
            return []

@retry(max_attempts=2, is_async=True)
async def execute_skill(name: str, arguments: str) -> Any:
    payload = json.loads(arguments)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SKILL_ENGINE_URL}/skills/execute",
                json={"skillName": name, "payload": payload},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("execute_skill_failed", name=name, error=str(e), exc_info=True)
            return {"error": str(e)}


@router.get("/models", response_model=APIResponse[ModelsResponse])
async def list_models():
    """
    Returns the list of available AI models/deployments.
    Task 11.01: Dynamic model synchronization.
    """
    from app.core.config import get_settings
    get_settings()

    # In a production scenario, we'd list real deployments from Azure AI Search or Foundry
    # For now, we return the real models mapped to our internal buckets
    models = [
        ModelInfo(id="fast", name="HOBA Mini", description="Veloce ed economico (GPT-4o Mini)"),
        ModelInfo(id="normal", name="HOBA Pro", description="Bilanciato e potente (GPT-4o)"),
        ModelInfo(id="deep", name="HOBA O1", description="Ragionamento profondo (o1)")
    ]

    return APIResponse.ok(data=ModelsResponse(models=models))


@router.get("/skills", response_model=APIResponse[SkillsResponse])
async def list_skills():
    """
    Scans the slkills directory and returns the list of available modules.
    Task 13: Skill Hub Architecture.
    """
    import os
    # Task 13: Skill Hub Architecture (Dynamic scanning)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skills_root = os.path.join(base_dir, "skills") 
    skills = []

    # Add Core Engine Functions from README
    system_skills = [
        SkillInfo(
            id="rag-citations",
            name="RAG / Citazioni",
            description="Recupero documenti e citazioni inline dalle fonti aziendali.",
            path="core/engine/rag",
            category="Core"
        ),
        SkillInfo(
            id="web-search",
            name="Web Search",
            description="Ricerca sul Web in tempo reale per informazioni aggiornate.",
            path="core/engine/web",
            category="Core"
        ),
        SkillInfo(
            id="code-interpreter",
            name="Code Interpreter",
            description="Esecuzione di codice (Python/JS) in ambiente sandbox isolato.",
            path="core/engine/code",
            category="Core"
        ),
        SkillInfo(
            id="long-term-memory",
            name="Long Term Memory",
            description="Memoria semantica e storica basata su pgvector e Cosmos DB.",
            path="core/engine/memory",
            category="Core"
        ),
        SkillInfo(
            id="voice-mode",
            name="Voice Mode",
            description="Interazione vocale full-duplex tramite WebRTC e Azure Speech.",
            path="core/engine/voice",
            category="Core"
        ),
        SkillInfo(
            id="vision-multimodal",
            name="Vision",
            description="Analisi multimodale di immagini e screenshot tramite GPT-4o Vision.",
            path="core/engine/vision",
            category="Core"
        )
    ]
    skills.extend(system_skills)

    if os.path.exists(skills_root):
        # Scan subdirectories as individual skills
        for entry in os.scandir(skills_root):
            if entry.is_dir() and not entry.name.startswith('.'):
                # Basic normalization for displays
                name = entry.name.replace('-', ' ').title()
                skills.append(SkillInfo(
                    id=entry.name,
                    name=name,
                    description=f"AI Capability: {name}",
                    path=entry.path,
                    category="Agent Tool" if "azure" in entry.name else "Custom"
                ))

    return APIResponse.ok(data=SkillsResponse(skills=skills))


from app.core.dependencies import get_orchestrator

@router.post("/chat", response_model=APIResponse[ChatResponse])
async def chat_endpoint(
    request: ChatRequest,
    orchestrator: ThinkingOrchestrator = Depends(get_orchestrator)
):
    try:
                        # Use our helper
        memory_service = get_memory_service()
                
        # RULE: tenant_id ALWAYS from context
        tenant_id = get_tenant_id()
        if not tenant_id:
             raise AppException(ErrorCode.TENANT_101)

        session_id = request.session_id or await memory_service.create_session(tenant_id)

        # Log the user message to memory
        await memory_service.add_message(session_id, tenant_id, "user", request.text)

        # Task 4.02: Memory Context Builder (includes RAG and History)
        memory_context = await build_memory_context(session_id, tenant_id, request.text)

        system_prompt = await get_tenant_system_prompt()

        # Determine style automatically "under the hood"
        writing_style = await determine_writing_style(request.text, memory_context.get("history", []))
        style_instructions = get_style_instructions(writing_style)
        system_prompt += f"\n\nSTILE DI RISPOSTA: {style_instructions}"

        if memory_context.get("rag_context"):
            system_prompt += f"\n\nContesto recuperato dai documenti aziendali:\n{memory_context['rag_context']}"

        messages = [{"role": "system", "content": system_prompt}]

        # Prepend history
        if memory_context.get("history"):
            messages.extend(memory_context["history"])

        # Format multimodal input if there is an image (Task 7.05)
        if request.image_url:
            # Task 7.06: Pre-process with Vision API
            analysis = await vision_service.analyze_image(request.image_url)
            vision_context = f"\n[Vision Analysis: {analysis.get('caption', '')}. Tags: {', '.join(analysis.get('tags', []))}]"

            user_msg_content: Any = [
                {"type": "text", "text": f"{request.text}{vision_context}"},
                {"type": "image_url", "image_url": {"url": request.image_url, "detail": "auto"}}
            ]
        else:
            user_msg_content = request.text

        # Add current user message
        messages.append({"role": "user", "content": user_msg_content}) # type: ignore

        # Task 7.07: Thinking Levels via Orchestrator
        
        # Task 3.05: Security check
        check_prompt_injection(messages)

        # Task 3.06: Token count & context window management
        # Note: We use NORMAL as the basis for cautionary token counting
        messages = manage_context_window(messages, model_name="gpt-4o")

        if not request.isPensieroProfondoAttivo:
            # Deep Thought OFF: Return response via Orchestrator
            orch_result = await orchestrator.route_and_execute(
                tenant_id=tenant_id,
                messages=messages,
                force_level=ThinkingLevel(request.thinking_level) if request.thinking_level in [l.value for l in ThinkingLevel] else None
            )

            response = orch_result.response
            target_model = orch_result.model_deployment

            # Task 3.07: Usage tracker hook
            if response and hasattr(response, "usage") and response.usage:
                await record_usage(target_model, response.usage.prompt_tokens, response.usage.completion_tokens)

            content = response.choices[0].message.content if response.choices else ""

            # Log the assistant response to Cosmos DB
            memory_service = get_memory_service()
            await memory_service.add_message(session_id, tenant_id, "assistant", content)

            # Task 6.06: Trigger smart recommendations and Continuity Reflection (Block 7.1)
            from app.workers.session_reflector import reflect_on_session
            asyncio.create_task(reflect_on_session(session_id, tenant_id, messages))
            
            await publish_to_recommendations_worker(session_id)

            return APIResponse.ok(data=ChatResponse(
                response=content,
                used_skills=[]
            ))

        # Deep Thinking ON: DeepAgents Integration
        # Combine existing tools and new DeepAgents tools
        tools = [list_files, read_file, write_file, call_external_skill, search_available_skills]

        # Build the dynamic system prompt
        full_system_prompt = system_prompt
        if memory_context.get("rag_context"):
            full_system_prompt += f"\n\nContext: {memory_context['rag_context']}"

        # Initialize the DeepAgent executor
        agent_app = create_agent_executor(tools, full_system_prompt)

        # Map history to LangChain messages
        history_msgs: list[BaseMessage] = []
        for m in (memory_context.get("history") or []):
            if m["role"] == "user":
                history_msgs.append(HumanMessage(content=m["content"]))
            else:
                history_msgs.append(AIMessage(content=m["content"]))

        # Add current message
        history_msgs.append(HumanMessage(content=request.text))

        # Execute the agent loop
        initial_state = AgentState(messages=history_msgs)
        final_state = await agent_app.ainvoke(initial_state)

        # Sync workspace to Azure in background (Task: Persistence)
        import asyncio

        from app.services.storage.agent_storage import sync_workspace_to_azure
        asyncio.create_task(sync_workspace_to_azure())

        # Extract the final answer and used tools
        last_msg = final_state["messages"][-1]
        final_content = last_msg.content

        used_skills = []
        for m in final_state["messages"]:
            if hasattr(m, "tool_calls") and m.tool_calls:
                 used_skills.extend([tc["name"] for tc in m.tool_calls])

        await memory_service.add_message(session_id, tenant_id, "assistant", final_content)

        return APIResponse.ok(data=ChatResponse(
            response=final_content,
            used_skills=list(set(used_skills))
        ))

    except Exception as e:
        if isinstance(e, AppException):
            raise e

        logger.error("unhandled_chat_error", error=str(e), exc_info=True)
        # Wrap generic error in AppException with central code
        raise AppException(ErrorCode.INFRA_903, detail="Errore durante l'elaborazione della chat")

@router.post("/stream")
async def chat_stream_endpoint(
    request: Request,
    chat_req: ChatRequest
):
    """
    Streaming SSE Endpoint (Task 3.02)
    Note: StreamingResponse bypasses the normal APIResponse wrapper 
    but we still follow security and tenant rules.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)
    
    # 0. Session and Context (Consistency with chat_endpoint)
    memory_service = get_memory_service()
    session_id = chat_req.session_id or await memory_service.create_session(tenant_id)
    await memory_service.add_message(session_id, tenant_id, "user", chat_req.text)
    
    # Task 4.02: Memory Context Builder (Compaction, KG, Semantic)
    memory_context = await build_memory_context(session_id, tenant_id, chat_req.text)
    
    system_prompt = await get_tenant_system_prompt()
    # Determine style automatically via History (Task 7.07 + Bonus)
    writing_style = await determine_writing_style(chat_req.text, memory_context.get("history", []))
    style_instructions = get_style_instructions(writing_style)
    system_prompt += f"\n\nSTILE DI RISPOSTA: {style_instructions}"

    if memory_context.get("knowledge_graph"):
        system_prompt += f"\n\nKnowledge Graph context:\n{memory_context['knowledge_graph']}"

    if memory_context.get("rag_context"):
        system_prompt += f"\n\nContesto recuperato dai documenti aziendali:\n{memory_context['rag_context']}"
    
    citations = memory_context.get("citations", [])

    messages = [{"role": "system", "content": system_prompt}]
    if memory_context.get("history"):
        messages.extend(memory_context["history"])
    
    messages.append({"role": "user", "content": chat_req.text})

    from app.engine.ai.security import check_prompt_injection
    check_prompt_injection(messages)

    messages = manage_context_window(messages, model_name="gpt-4o")

    # Security check — prompt injection detection
    check_prompt_injection(messages)

    async def event_generator() -> AsyncGenerator[str, None]:
        orchestrator = ThinkingOrchestrator()
        try:
            stream_response = orchestrator.route_and_stream(
                tenant_id=tenant_id,
                messages=messages,
                force_level=ThinkingLevel(chat_req.thinking_level) if chat_req.thinking_level in [l.value for l in ThinkingLevel] else None
            )

            # We need to track time from the first event by thinking in deep mode
            import time
            start_time = time.time()
            last_progress = start_time
            thinking_started = False
            
            async for level, deployment, chunk in stream_response:
                # If it's in Deep and we didn't send thinking_start, let's send it now
                if level == ThinkingLevel.DEEP and not thinking_started:
                    yield f"event: thinking_start\ndata: {json.dumps({'level': 'deep', 'model': deployment})}\n\n"
                    thinking_started = True

                # Progress every 5 seconds
                if thinking_started:
                    now = time.time()
                    if now - last_progress >= 5.0:
                        yield f"event: thinking_progress\ndata: {json.dumps({'elapsed_seconds': int(now - start_time)})}\n\n"
                        last_progress = now

                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("client_disconnected_during_stream")
                    break

                if isinstance(chunk, dict) and "error" in chunk:
                    yield f"event: error\ndata: {json.dumps({'error': chunk['error']})}\n\n"
                    break

                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    message_info = getattr(chunk.choices[0], "message", None)
                    
                    # BUGFIX OpenClaw: Prevent "Reasoning Leak" (Thinking trace) in ALL formats
                    is_reasoning = False
                    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        is_reasoning = True
                    if hasattr(delta, "reasoning") and delta.reasoning:
                        is_reasoning = True
                    if message_info and hasattr(message_info, "reasoning_content") and message_info.reasoning_content:
                        is_reasoning = True
                        
                    if is_reasoning:
                        # We log internally if useful, but DO NOT report to the user
                        continue
                    
                    if delta and delta.content:
                        # If we had started thinking, we send thinking_end before the first response piece
                        if thinking_started:
                            yield f"event: thinking_end\ndata: {json.dumps({'elapsed_seconds': int(time.time() - start_time)})}\n\n"
                            thinking_started = False
                            
                        # Emitting an SSE text chunk
                        yield f"event: message\ndata: {json.dumps({'text': delta.content})}\n\n"
                        
            # Safe closing for corner case (e.g. error before starting the real answer)
            if thinking_started:
                yield f"event: thinking_end\ndata: {json.dumps({'elapsed_seconds': int(time.time() - start_time)})}\n\n"
                
            # Task 3.12: Send final chunk with quotes from RAG
            if citations:
                yield f"event: citations\ndata: {json.dumps({'citations': citations})}\n\n"


            # Task 7.1: Trigger Continuity Reflection after stream is done (asynchronous)
            from app.workers.session_reflector import reflect_on_session
            asyncio.create_task(reflect_on_session(session_id, tenant_id, messages))

            yield f"event: done\ndata: {json.dumps({'status': 'finished'})}\n\n"

        except Exception as e:
            logger.error("streaming_error", error=str(e), exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error_code': 'AI_206', 'message': 'Errore nello streaming'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

