"""
Health Check Endpoint

Non richiede autenticazione. Usato da Azure Container Apps health probes.
"""

from __future__ import annotations

import os

from fastapi import APIRouter

from app.core.schemas import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse)
async def health_check() -> APIResponse:
    """Health check — restituisce stato del servizio.

    Non richiede JWT. Usato dai load balancer e health probes ACA.
    """
    return APIResponse.ok(data={"status": "healthy", "service": "main-bot"})


@router.get("/ready", response_model=APIResponse)
async def readiness_check() -> APIResponse:
    """Readiness check — verifica stato di ogni componente.

    Non richiede JWT. Ogni componente mostra OK o DEGRADED.
    """
    components = {}

    # Cosmos DB
    cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
    if cosmos_endpoint:
        components["cosmos_db"] = "OK"
    else:
        components["cosmos_db"] = "DEGRADED"

    # Azure OpenAI
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_key = os.getenv("AZURE_OPENAI_API_KEY")
    if openai_endpoint and openai_key:
        components["azure_openai"] = "OK"
    else:
        components["azure_openai"] = "DEGRADED"

    # Redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    try:
        import redis as redis_lib
        r = redis_lib.Redis(host=redis_host, port=int(redis_port), socket_timeout=2)
        r.ping()
        components["redis"] = "OK"
        r.close()
    except Exception:
        components["redis"] = "DEGRADED"

    # Azure Search
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    if search_endpoint and search_endpoint != "https://dummy-search.search.windows.net":
        components["azure_search"] = "OK"
    else:
        components["azure_search"] = "DEGRADED"

    # Azure Blob Storage
    storage_url = os.getenv("AZURE_STORAGE_URL")
    if storage_url:
        components["blob_storage"] = "OK"
    else:
        components["blob_storage"] = "DEGRADED"

    all_ok = all(v == "OK" for v in components.values())
    overall_status = "ready" if all_ok else "degraded"

    return APIResponse.ok(data={
        "status": overall_status,
        "components": components,
        "service": "main-bot"
    })
