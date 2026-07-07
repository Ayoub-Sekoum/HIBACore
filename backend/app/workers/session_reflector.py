import structlog
import json
from datetime import datetime
from typing import Any
from app.engine.ai.orchestrator import ThinkingOrchestrator
from app.engine.memory.cosmos import cosmos_memory_service

logger = structlog.get_logger(__name__)

async def reflect_on_session(
    session_id: str,
    tenant_id: str,
    messages: list[dict[str, Any]]
) -> None:
    """
    Bonus 3: Continuity Framework (Session reflections).
    Riflette sulla sessione appena conclusa per estrarre fatti e decisioni.
    """
    if not messages:
        return

    logger.info("session_reflection_started", session_id=session_id)
    
    orchestrator = ThinkingOrchestrator()
    
    # 1. Session analysis with GPT-4o-mini
    history_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in messages])
    
    prompt = f"""
    Sei un 'Continuity Engine'. Analizza la conversazione e rispondi SOLO in JSON.
    Estrai:
    - principali argomenti trattati (topics)
    - decisioni prese (decisions)
    - fatti appresi sull'utente o sul progetto (facts)
    - una brevissima sintesi (summary)
    
    JSON FORMAT:
    {{
      "topics": [],
      "decisions": [],
      "facts": [],
      "summary": ""
    }}
    
    CONVERSAZIONE:
    {history_text}
    """
    
    try:
        reflection_json = ""
        messages_for_reflection = [{"role": "user", "content": prompt}]
        async for _, _, chunk in orchestrator.route_and_stream(
            tenant_id=tenant_id,
            messages=messages_for_reflection,
            force_level="fast"
        ):
            # Robust check for chunk content
            delta = getattr(chunk.choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta else None
            if content:
                reflection_json += content
        
        # JSON cleanup
        if "```json" in reflection_json:
            reflection_json = reflection_json.split("```json")[1].split("```")[0].strip()
        
        reflection_data = json.loads(reflection_json)
        reflection_data["session_id"] = session_id
        reflection_data["tenant_id"] = tenant_id
        reflection_data["updated_at"] = datetime.utcnow().isoformat()
        
        # 2. Save to Cosmos DB (We use a dedicated container 'Continuity' or similar)
        # For now we store as session metadata or in a new container via cosmos_service.
        # Let's imagine that cosmos_service has a method for saving reflections.
        await cosmos_memory_service.save_session_reflection(session_id, tenant_id, reflection_data)
        
        logger.info("session_reflection_saved", session_id=session_id)
        
    except Exception as e:
        logger.error("session_reflection_failed", error=str(e), code="MEM_410")

