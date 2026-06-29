"""
Short Term Memory — Manages chat context using Redis.
"""

import json

import redis.asyncio as redis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

class ShortTermMemory:
    """Manages conversational short-term context backed by Redis."""

    def __init__(self):
        self.settings = get_settings()
        self._redis_client = None

    async def _get_client(self):
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                password=self.settings.REDIS_PASSWORD,
                ssl=self.settings.REDIS_USE_SSL,
                decode_responses=True
            )
        return self._redis_client

    async def add_message(self, session_id: str, message: dict[str, str], max_history: int = 10):
        """Append a message to the session's context, truncating if necessary."""
        client = await self._get_client()
        key = f"chat_context:{session_id}"

        # We push to the right (tail) of the list
        await client.rpush(key, json.dumps(message))

        # Keep only the last max_history items (trimming the head)
        await client.ltrim(key, -max_history, -1)

        # Set expiry for short term memory (e.g. 24 hours)
        await client.expire(key, 86400)

        logger.info("short_term_memory_added", session_id=session_id)

    async def get_context(self, session_id: str) -> list[dict[str, str]]:
        """Retrieve the short-term context for a session."""
        client = await self._get_client()
        key = f"chat_context:{session_id}"

        items = await client.lrange(key, 0, -1)
        return [json.loads(item) for item in items]

short_term_memory = ShortTermMemory()
