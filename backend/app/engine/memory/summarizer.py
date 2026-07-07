import structlog
from typing import Any
from app.engine.ai.token_counter import count_tokens
from app.engine.ai.orchestrator import ThinkingOrchestrator

logger = structlog.get_logger(__name__)

async def compact_context(
    messages: list[dict[str, Any]], 
    tenant_id: str,
    max_history: int = 40
) -> list[dict[str, Any]]:
    """
    Bonus 1: Context Compaction (Anchor logic).
    Se > 40 messaggi: Identifica anchor, comprime transitori, mantiene ultimi 10.
    """
    if len(messages) <= max_history:
        return messages

    logger.info("context_compaction_triggered", count=len(messages))
    
    # 1. Keep the last 10 messages intact (Masterclass Rule)
    recent_messages = messages[-10:]
    older_messages = messages[:-10]
    
    # 2. Identify “Anchors” in previous messages via AI
    # (Simplified logic for efficiency: we look for messages with tool_calls or long)
    # In a more advanced version we would use a 'summarizer_prompt' to filter them.
    
    anchors = []
    transients = []
    
    orchestrator = ThinkingOrchestrator()
    
    # Prompt to identify key points (Only if older_messages is consistent)
    if len(older_messages) > 10:
        summary_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in older_messages])
        prompt = f"""
        Analizza questa conversazione e identifica i punti chiave, le decisioni prese e i fatti importanti.
        Riassumi in modo estremamente conciso (max 200 parole) mantenendo solo le informazioni critiche.
        TESTO:
        {summary_text}
        """
        
        # We use gpt-4o-mini (fast) for compaction
        try:
            summary_content = ""
            messages_for_summary = [{"role": "user", "content": prompt}]
            async for _, _, chunk in orchestrator.route_and_stream(
                tenant_id=tenant_id,
                messages=messages_for_summary,
                force_level="fast" 
            ):
                # Robust check for chunk content
                delta = getattr(chunk.choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    summary_content += content
            
            if summary_content:
                anchors.append({
                    "role": "system",
                    "content": f"[CONTESTO COMPATTATO]: {summary_content}"
                })
        except Exception as e:
            logger.warning("compaction_ai_failed", error=str(e))
            # Fallback: Only the last 20 if the AI ​​fails
            return messages[-20:]

    return anchors + recent_messages

