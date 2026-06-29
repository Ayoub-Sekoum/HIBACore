"""
Task 4.06 — Knowledge Graph Worker.
Worker asincrono attivato da Service Bus per aggiornare il grafo.
"""

import structlog
from app.engine.memory.graph import extract_entities, upsert_graph_entities

logger = structlog.get_logger(__name__)

async def process_message_for_graph(
    tenant_id: str,
    user_id: str,
    message_text: str
) -> None:
    """
    Estrae entità e aggiorna il grafo Cosmos Gremlin.
    Richiamato asincronamente dopo ogni messaggio.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        return

    logger.info("graph_worker_starting", tenant_id=tenant_id, user_id=user_id)

    try:
        # PASSO 1 — Estrazione entità
        extraction = await extract_entities(tenant_id, message_text)
        
        # Se non ci sono entità, saltiamo
        if not extraction.entities:
            logger.info("graph_worker_no_entities", tenant_id=tenant_id)
            return

        # PASSO 2 & 3 — Upsert nel grafo
        await upsert_graph_entities(tenant_id, extraction)
        
        logger.info("graph_worker_success", tenant_id=tenant_id, entity_count=len(extraction.entities))

    except Exception as e:
        # Fallimento asincrono: non blocchiamo mai il flusso principale
        # ma segnaliamo nei log con codice MEM_403
        logger.error("graph_worker_failed", tenant_id=tenant_id, error=str(e), code="MEM_403")

