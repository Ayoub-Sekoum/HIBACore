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
    
    # 1. Mantieni intatti gli ultimi 10 messaggi (Regola Masterclass)
    recent_messages = messages[-10:]
    older_messages = messages[:-10]
    
    # 2. Identifica "Ancore" nei messaggi precedenti via AI
    # (Logica semplificata per efficienza: cerchiamo messaggi con tool_calls o lunghi)
    # In una versione più avanzata useremmo un 'summarizer_prompt' per filtrarli.
    
    anchors = []
    transients = []
    
    orchestrator = ThinkingOrchestrator()
    
    # Prompt per identificare punti chiave (Solo se older_messages è consistente)
    if len(older_messages) > 10:
        summary_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in older_messages])
        prompt = f"""
        Analizza questa conversazione e identifica i punti chiave, le decisioni prese e i fatti importanti.
        Riassumi in modo estremamente conciso (max 200 parole) mantenendo solo le informazioni critiche.
        TESTO:
        {summary_text}
        """
        
        # Usiamo gpt-4o-mini (fast) per la compattazione
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
            # Fallback: Solo gli ultimi 20 se fallisce l'AI
            return messages[-20:]

    return anchors + recent_messages

