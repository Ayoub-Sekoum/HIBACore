"""
Task 4.06 — Knowledge Graph (Cosmos Gremlin).
Logica: Estrae entità e relazioni per costruire una memoria relazionale.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, List, Optional
import structlog
from pydantic import BaseModel, Field
from gremlin_python.driver import client, serializer

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)

class Entity(BaseModel):
    name: str
    type: str  # Persona, Azienda, Progetto, Prodotto, Luogo, Data, Numero

class Relation(BaseModel):
    from_entity: str = Field(..., alias="from")
    relation: str
    to_entity: str = Field(..., alias="to")

class EntityExtractionResult(BaseModel):
    entities: List[Entity] = []
    relations: List[Relation] = []

# Cache per il client Gremlin
_gremlin_client = None

def _get_gremlin_client():
    global _gremlin_client
    if _gremlin_client is None:
        settings = get_settings()
        endpoint = settings.COSMOS_ENDPOINT
        if not endpoint:
            return None
        
        # Trasformiamo l'endpoint https in gremlin e aggiungiamo la porta 443
        gremlin_endpoint = endpoint.replace("https://", "wss://").replace(".documents.azure.com", ".gremlin.cosmos.azure.com")
        if ":443" not in gremlin_endpoint:
            gremlin_endpoint = f"{gremlin_endpoint}:443/"
            
        try:
            _gremlin_client = client.Client(
                gremlin_endpoint,
                'g',
                username=f"/dbs/{settings.COSMOS_DATABASE_NAME}/colls/graph",
                password=settings.COSMOS_KEY,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
        except Exception as e:
            logger.error("gremlin_client_init_failed", error=str(e))
            return None
    return _gremlin_client

import re

def _sanitize_gremlin_string(text: str) -> str:
    """Applica una whitelist stringente per prevenire Gremlin Injection."""
    # Consente solo lettere, numeri, spazi, trattini, undescore, punti e virgole
    clean = re.sub(r'[^a-zA-Z0-9\s\-_.,]', '', text).strip()
    return clean

async def extract_entities(
    tenant_id: str,
    text: str,
) -> EntityExtractionResult:
    """
    Usa GPT-4o-mini per estrarre entità e relazioni dal testo.
    Ritorna EntityExtractionResult con entities[] e relations[].
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    prompt = f"""Estrai entità e relazioni dal testo seguente.
Tipi entità: Persona, Azienda, Progetto, Prodotto, Luogo, Data, Numero
Formato risposta JSON:
{{
  "entities": [{{ "name": "Marco Rossi", "type": "Persona" }}],
  "relations": [{{ "from": "Marco Rossi", "relation": "è_CEO_di", "to": "Acme Corp" }}]
}}

Testo: {text}"""

    llm_client = ResilientLLMClient()
    try:
        response = await llm_client.complete(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
            response_format={ "type": "json_object" }
        )
        import json
        data = json.loads(response)
        return EntityExtractionResult.model_validate(data)
    except Exception as e:
        logger.warning("entity_extraction_failed", tenant_id=tenant_id, error=str(e))
        return EntityExtractionResult()

async def upsert_graph_entities(
    tenant_id: str,
    result: EntityExtractionResult,
) -> None:
    """
    Salva entità e relazioni nel grafo Cosmos Gremlin.
    Usa upsert (crea se non esiste, aggiorna se esiste).
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id or not result.entities:
        return

    gremlin_client = _get_gremlin_client()
    if not gremlin_client:
        logger.warning("gremlin_unavailable", code="MEM_403")
        return

    try:
        now = datetime.now(timezone.utc).isoformat()
        
        # PASSO 2 — Upsert nodi
        for entity in result.entities:
            # Protezione injection Gremlin stringente
            name = _sanitize_gremlin_string(entity.name)
            etype = _sanitize_gremlin_string(entity.type)
            
            query = (
                f"g.V().has('name', '{name}').has('tenant_id', '{tenant_id}')"
                f".fold().coalesce("
                f"  unfold().property('last_seen', '{now}'),"
                f"  addV('{etype}').property('name', '{name}').property('tenant_id', '{tenant_id}').property('created_at', '{now}').property('last_seen', '{now}')"
                f")"
            )
            # Eseguiamo in modo asincrono (simulato per il client sincrono di gremlin-python)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, gremlin_client.submit, query)

        # PASSO 3 — Upsert archi
        for rel in result.relations:
            f_name = _sanitize_gremlin_string(rel.from_entity)
            t_name = _sanitize_gremlin_string(rel.to_entity)
            relation = _sanitize_gremlin_string(rel.relation)
            
            query = (
                f"g.V().has('name', '{f_name}').has('tenant_id', '{tenant_id}').as('a')"
                f".V().has('name', '{t_name}').has('tenant_id', '{tenant_id}').as('b')"
                f".coalesce("
                f"  select('a').outE('{relation}').where(inV().as('b')),"
                f"  addE('{relation}').from('a').to('b').property('tenant_id', '{tenant_id}').property('last_seen', '{now}')"
                f")"
            )
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, gremlin_client.submit, query)

    except Exception as e:
        logger.error("graph_upsert_failed", tenant_id=tenant_id, error=str(e), code="MEM_403")

async def get_graph_context(
    tenant_id: str,
    query: str,
    max_tokens: int = 500,
) -> str:
    """
    Recupera il contesto relazionale dal grafo per una query.
    Ritorna testo naturale leggibile dal modello AI.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        return ""

    try:
        # (1) Estrazione entità dalla query
        extraction = await extract_entities(tenant_id, query)
        if not extraction.entities:
            return ""

        gremlin_client = _get_gremlin_client()
        if not gremlin_client:
            return ""

        context_facts = []
        for entity in extraction.entities:
            name = entity.name.replace("'", "\\'")
            # Query Gremlin per prendere i vicini a 1 salto
            gremlin_query = f"g.V().has('tenant_id', '{tenant_id}').has('name', '{name}').bothE().as('e').otherV().as('v').select('e','v').limit(20)"
            
            loop = asyncio.get_running_loop()
            callback = await loop.run_in_executor(None, gremlin_client.submit, gremlin_query)
            results = callback.all().result()
            
            for res in results:
                edge = res['e']
                other_v = res['v']
                # Costruiamo una frase in linguaggio naturale
                # Nota: le proprietà del vertex/edge dipendono dalla GraphSON serialization
                # Qui semplifichiamo assumendo una certa struttura
                if 'label' in edge and 'properties' in other_v:
                    other_name = other_v['properties']['name'][0]['value']
                    context_facts.append(f"{entity.name} {edge['label']} {other_name}.")

        if not context_facts:
            return ""

        context_text = "Dati relazionali trovati:\n" + "\n".join(set(context_facts))
        return context_text[:max_tokens * 4] # Approssimazione grossolana tokens-chars

    except Exception as e:
        logger.warning("graph_context_failed", tenant_id=tenant_id, error=str(e))
        return ""

