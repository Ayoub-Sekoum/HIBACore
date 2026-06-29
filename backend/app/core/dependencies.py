from fastapi import Request

from app.engine.ai.orchestrator import ThinkingOrchestrator
from app.engine.memory.cosmos import CosmosMemoryService

def get_cosmos_service() -> CosmosMemoryService:
    from app.engine.memory.cosmos import cosmos_memory_service
    return cosmos_memory_service

def get_orchestrator() -> ThinkingOrchestrator:
    return ThinkingOrchestrator()

