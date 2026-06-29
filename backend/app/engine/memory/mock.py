import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

class MockMemoryService:
    """Mock service for local development without Cosmos DB."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        logger.info("mock_memory_service_initialized")

    async def create_session(self, tenant_id: str, session_id: str | None = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "id": session_id,
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "metadata": {}
        }
        logger.info("mock_session_created", session_id=session_id)
        return session_id

    async def add_message(self, session_id: str, tenant_id: str, role: str, content: str) -> None:
        if session_id not in self._sessions:
            await self.create_session(tenant_id, session_id)

        msg = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._sessions[session_id]["messages"].append(msg)
        logger.debug("mock_message_added", session_id=session_id, role=role)

    async def get_history(self, session_id: str, tenant_id: str, limit: int = 50) -> list[dict[str, str]]:
        session = self._sessions.get(session_id)
        if not session:
            return []
        messages = session.get("messages", [])
        recent = messages[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    async def list_sessions(self, tenant_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": s["id"],
                "created_at": s["created_at"],
                "message_count": len(s["messages"])
            }
            for s in self._sessions.values()
            if s["tenant_id"] == tenant_id
        ]

    async def get_latest_reflection(self, tenant_id: str) -> dict | None:
        return None

    async def save_session_reflection(self, session_id: str, tenant_id: str, reflection_data: dict) -> None:
        pass

    async def close(self):
        pass

mock_memory_service = MockMemoryService()
