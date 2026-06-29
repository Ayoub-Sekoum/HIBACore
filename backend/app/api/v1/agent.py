import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.config import config_manager
from app.core.auth import get_current_user

router = APIRouter()
settings = config_manager.settings

class AgentTask(BaseModel):
    prompt: str

class AgentStatusResponse(BaseModel):
    status: str
    detail: dict = {}

@router.get("/status")
async def agent_status():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ZEROCLAW_GATEWAY_URL}/health")
            return {"status": "online", "detail": r.json()}
    except Exception as e:
        return {"status": "offline", "detail": {"error": str(e)}}

@router.post("/run")
async def run_agent(task: AgentTask, user=Depends(get_current_user)):
    if not settings.ZEROCLAW_ENABLED:
        raise HTTPException(status_code=503, detail="ZeroClaw agent disabled")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{settings.ZEROCLAW_GATEWAY_URL}/webhook",
                json={"message": task.prompt},
                headers={"Content-Type": "application/json"}
            )
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="ZeroClaw timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/logs")
async def agent_logs():
    # ZeroClaw non ha endpoint /logs — restituiamo placeholder
    # In futuro: leggere da Cosmos DB o Azure Log Analytics
    return {"logs": [], "note": "log streaming not yet implemented"}
