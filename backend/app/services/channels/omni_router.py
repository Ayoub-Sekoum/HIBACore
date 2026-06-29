from typing import Any

import structlog

logger = structlog.get_logger(__name__)

class ChannelMessage:
    """Modello normalizzato unificato per tutti i canali."""
    def __init__(self, tenant_id: str, user_id: str, channel: str, text: str, attachments: list[str] | None = None, metadata: dict[str, str] | None = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.channel = channel
        self.text = text
        self.attachments = attachments or []
        self.metadata = metadata or {}

def normalize_payload(payload: dict[str, Any], source_channel: str) -> ChannelMessage:
    """
    Task 6.01: Omni-Router Middleware
    Normalizza i messaggi da Web/Teams/Signal in un ChannelMessage unificato.
    """
    logger.info("normalizing_payload_for_channel", channel=source_channel)

    tenant_id = payload.get("tenant_id", "default_tenant")
    user_id = payload.get("user_id", "unknown_user")
    text = payload.get("text", "")
    attachments = payload.get("attachments", [])
    metadata = payload.get("metadata", {})

    if source_channel == "teams":
        # Simulate Teams specific extraction
        text = payload.get("text", "").replace("<at>bot</at>", "").strip()
        metadata["teams_channel_id"] = payload.get("channelData", {}).get("channel", {}).get("id")
    elif source_channel == "signal":
        # Simulate Signal specific extraction
        user_id = payload.get("source", user_id)

    return ChannelMessage(tenant_id, user_id, source_channel, text, attachments, metadata)
