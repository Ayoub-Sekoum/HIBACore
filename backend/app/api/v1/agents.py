from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agents.builder import AgentState, create_agent_executor
from app.core.auth import get_current_user
from app.tools.filesystem import list_files, read_file, write_file
from app.tools.skill_adapter import call_external_skill, search_available_skills

logger = structlog.get_logger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])

class AgentRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    stream: bool = False

class AgentResponse(BaseModel):
    response: str
    steps: list[dict[str, Any]] = []

@router.post("/chat")
async def agent_chat(request: AgentRequest):
    """
    Main endpoint for interacting with the DeepAgent.
    Handles the planning loop and tool execution.
    """
    # 1. Initialize Tools
    tools = [list_files, read_file, write_file, call_external_skill, search_available_skills]

    # 2. Define System Prompt for the DeepAgent
    system_prompt = (
        "Sei l'Assistante Avanzato HOBA (DeepAgent). "
        "Hai accesso al filesystem tramite i tool forniti. "
        "Pianifica i tuoi task, comunica con l'utente e usa le skill se necessario. "
        "Mantieni un tono professionale e tecnico."
    )

    # 3. Create the Graph Executor
    agent_app = create_agent_executor(tools, system_prompt)

    # 4. Initialize State
    initial_state = AgentState(
        messages=[HumanMessage(content=request.prompt)]
    )

    try:
        # 5. Execute the Graph
        final_state = await agent_app.ainvoke(initial_state)

        # 6. Extract the final response
        last_message = final_state["messages"][-1]

        return {
            "response": last_message.content,
            "messages": [m.dict() for m in final_state["messages"]]
        }

    except Exception as e:
        logger.error("agent_execution_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Errore durante l'esecuzione dell'agente")
