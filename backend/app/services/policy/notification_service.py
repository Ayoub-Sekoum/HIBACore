"""
notification_service.py — Gestore delle notifiche real-time via SSE.
Percorso: backend/app/services/policy/notification_service.py
"""
import asyncio
import json
import structlog
from typing import AsyncGenerator

logger = structlog.get_logger(__name__)

class NotificationService:
    def __init__(self):
        # Map tenant_id -> set of queues (one for each connected admin)
        self.queues: dict[str, set[asyncio.Queue]] = {}

    async def subscribe(self, tenant_id: str) -> AsyncGenerator[str, None]:
        """Sottoscrive un client (admin) alle notifiche del tenant."""
        queue = asyncio.Queue()
        if tenant_id not in self.queues:
            self.queues[tenant_id] = set()
        
        self.queues[tenant_id].add(queue)
        logger.info("admin_subscribed_to_notifications", tenant_id=tenant_id)
        
        try:
            while True:
                # Wait for new notifications
                data = await queue.get()
                yield f"event: notification\ndata: {json.dumps(data)}\n\n"
        finally:
            self.queues[tenant_id].remove(queue)
            if not self.queues[tenant_id]:
                del self.queues[tenant_id]
            logger.info("admin_unsubscribed_from_notifications", tenant_id=tenant_id)

    async def broadcast(self, tenant_id: str, event_type: str, message: str, data: dict | None = None):
        """Invia una notifica a tutti gli admin connessi per quel tenant."""
        if tenant_id not in self.queues:
            return

        payload = {
            "type": event_type,
            "message": message,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }

        # Deploy to all active queues
        for queue in self.queues[tenant_id]:
            await queue.put(payload)
        
        logger.debug("notification_broadcasted", tenant_id=tenant_id, type=event_type)

    async def broadcast_super(self, event_type: str, message: str, data: dict | None = None):
        """Invia una notifica globale ai Super Admin (usa tenant_id='global')."""
        await self.broadcast("global", event_type, message, data)

notification_service = NotificationService()
