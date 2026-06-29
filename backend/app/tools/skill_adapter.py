import os
from typing import Any

import httpx
from langchain_core.tools import tool

SKILL_ENGINE_URL = os.getenv("SKILL_ENGINE_URL", "http://localhost:3000")

@tool
async def call_external_skill(skill_name: str, payload: dict[str, Any]) -> Any:
    """
    Calls an existing skill from the HOBA Skill Engine (Node.js).
    Use this for specialized tools like CRM integration, custom APIs, or advanced RAG.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SKILL_ENGINE_URL}/skills/execute",
                json={"skillName": skill_name, "payload": payload},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Skill execution failed: {str(e)}"}

@tool
async def search_available_skills() -> dict[str, Any]:
    """Returns a list of all custom skills available in the engine."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SKILL_ENGINE_URL}/skills/index", timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {"error": "Failed to fetch skill index"}
