from app.core.config import config_manager
"""
Task 4.08 — Self-Evolving User Persona.
Logica: Analizza lo stile e gli argomenti dell'utente per personalizzare le risposte.
Evolve il profilo usando una media mobile pesata (config_manager.settings.AI_PERSONA_OLD_WEIGHT vecchio / config_manager.settings.AI_PERSONA_NEW_WEIGHT nuovo).
"""

import json
from typing import Any, Optional
import structlog
from pydantic import BaseModel, Field
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

from app.core.config import get_settings
from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)

class UserPersona(BaseModel):
    """Schema per il profilo utente persistente."""
    technical_level: float = Field(0.5, ge=0, le=1)  # 0: basic, 1: expert
    communication_style: float = Field(0.5, ge=0, le=1) # 0: casual, 1: formal
    preferred_language: str = "it"
    top_interests: dict[str, float] = Field(default_factory=dict)
    last_updated: str | None = None

class PersonaExtraction(BaseModel):
    """Schema per l'estrazione temporanea da una sessione."""
    technical_level: float
    communication_style: float
    detected_interests: list[str]

# Cosmos SQL client cache
_cosmos_client = None

async def _get_persona_container():
    """Helper per ottenere il container Cosmos SQL per i profili."""
    settings = get_settings()
    endpoint = settings.COSMOS_ENDPOINT
    key = settings.COSMOS_KEY
    db_name = settings.COSMOS_DATABASE_NAME
    
    if not endpoint:
        return None

    global _cosmos_client
    if _cosmos_client is None:
        if key:
            _cosmos_client = CosmosClient(endpoint, credential=key)
        else:
            _cosmos_client = CosmosClient(endpoint, credential=get_global_credential())
            
    db = _cosmos_client.get_database_client(db_name)
    container = await db.create_container_if_not_exists(
        id="user_profiles",
        partition_key="/tenant_id",
        offer_throughput=400
    )
    return container

async def get_user_persona(
    tenant_id: str,
    user_id: str,
) -> UserPersona:
    """
    Recupera il profilo utente dal DB.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    try:
        container = await _get_persona_container()
        if not container:
            return UserPersona()

        # Query for id (which will be user_id) and partition key (tenant_id)
        try:
            item = await container.read_item(item=user_id, partition_key=tenant_id)
            return UserPersona.model_validate(item)
        except Exception:
            # If it does not exist, it returns default
            return UserPersona()

    except Exception as e:
        logger.warning("get_persona_failed", tenant_id=tenant_id, user_id=user_id, error=str(e))
        return UserPersona()

async def update_user_persona(
    tenant_id: str,
    user_id: str,
    session_text: str,
) -> UserPersona:
    """
    Evolve il profilo utente basandosi sull'ultima interazione.
    Usa pesatura config_manager.settings.AI_PERSONA_OLD_WEIGHT/config_manager.settings.AI_PERSONA_NEW_WEIGHT come da Masterclass.
    Regola 3: tenant_id come primo parametro.
    """
    if not tenant_id:
        raise AppException(ErrorCode.TENANT_101)

    # 1. Extraction from the current text via LLM
    new_data = await _extract_persona_from_text(tenant_id, session_text)
    if not new_data:
        return await get_user_persona(tenant_id, user_id)

    # 2. Recover old profile
    current_persona = await get_user_persona(tenant_id, user_id)

    # 3. Weighted Moving Average and Topic Decay
    new_interests = {}
    
    # - Each session applies topic_score *= 0.95 for topics NOT mentioned
    for topic, score in current_persona.top_interests.items():
        new_score = score * 0.95
        if new_score >= 0.05:
            new_interests[topic] = new_score
            
    # - Each session adds +0.2 per topic mentioned (capped at 1.0)
    for topic in new_data.detected_interests:
        t = topic.lower()
        new_interests[t] = min(1.0, new_interests.get(t, 0.5) + 0.2)
        
    evolved_persona = UserPersona(
        technical_level=(current_persona.technical_level * config_manager.settings.AI_PERSONA_OLD_WEIGHT) + (new_data.technical_level * config_manager.settings.AI_PERSONA_NEW_WEIGHT),
        communication_style=(current_persona.communication_style * config_manager.settings.AI_PERSONA_OLD_WEIGHT) + (new_data.communication_style * config_manager.settings.AI_PERSONA_NEW_WEIGHT),
        preferred_language=current_persona.preferred_language,
        top_interests=new_interests,
        last_updated=None
    )

    # 4. Persistent saving
    try:
        container = await _get_persona_container()
        if container:
            from datetime import datetime, timezone
            data = evolved_persona.model_dump()
            data["id"] = user_id
            data["tenant_id"] = tenant_id
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            await container.upsert_item(data)
            logger.info("persona_evolved", tenant_id=tenant_id, user_id=user_id)
            
        return evolved_persona
    except Exception as e:
        logger.error("save_persona_failed", tenant_id=tenant_id, error=str(e), code="MEM_403")
        return evolved_persona

async def _extract_persona_from_text(
    tenant_id: str,
    text: str,
) -> Optional[PersonaExtraction]:
    """Usa GPT-4o-mini per analizzare lo stile utente."""
    prompt = f"""Analizza i messaggi dell'utente e valuta su una scala da 0.0 a 1.0:
1. Livello Tecnico (0: principiante, 1: esperto/sviluppatore)
2. Stile di Comunicazione (0: informale/amichevole, 1: formale/professionale)
3. Interessi principali (lista di parole chiave)

Rispondi SOLO in JSON:
{{
  "technical_level": 0.8,
  "communication_style": 0.4,
  "detected_interests": ["python", "azure", "sicurezza"]
}}

Testo Utente:
{text}"""

    llm_client = ResilientLLMClient()
    try:
        response = await llm_client.complete(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",
            response_format={ "type": "json_object" }
        )
        data = json.loads(response)
        return PersonaExtraction.model_validate(data)
    except Exception as e:
        logger.warning("persona_extraction_failed", tenant_id=tenant_id, error=str(e))
        return None

