"""
Voice Service — Real-time Voice & Streaming STT/TTS.
Task 7.01 — Multi-Tenant Enterprise Chatbot.
"""

import asyncio
import json

import structlog
from azure.ai.voicelive.aio import connect
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class VoiceService:
    """Manages real-time bidirectional voice communication."""

    async def handle_realtime_session(self, websocket: WebSocket, tenant_id: str):
        """
        Handles a WebSocket connection for real-time voice interaction.
        Proxies audio between the client and Azure AI Voice Live.
        """
        await websocket.accept()
        logger.info("voice_websocket_accepted", tenant_id=tenant_id)

        try:
            async with connect(
                endpoint=settings.AZURE_COGNITIVE_SERVICES_ENDPOINT, # type: ignore
                credential=get_global_credential(),
                model="gpt-4o-realtime-preview",
                credential_scopes=["https://cognitiveservices.azure.com/.default"]
            ) as conn:
                # 1. Update session config
                await conn.session.update(session={
                    "instructions": f"Sei un assistente AI aziendale per il tenant {tenant_id}. Rispondi in modo professionale.",
                    "modalities": ["text", "audio"],
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16"
                })

                # 2. Start bidirectional proxying
                async def receive_from_client():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            msg = json.loads(data)
                            if msg["type"] == "audio":
                                # Append audio to buffer
                                await conn.input_audio_buffer.append(audio=msg["audio"])
                            elif msg["type"] == "commit":
                                await conn.input_audio_buffer.commit()
                                await conn.response.create()
                    except WebSocketDisconnect:
                        logger.info("voice_client_disconnected")
                    except Exception as e:
                        logger.error("voice_receive_error", error=str(e))

                async def send_to_client():
                    async for event in conn:
                        if event.type == "response.audio.delta":
                            # Send audio delta to client
                            await websocket.send_json({
                                "type": "audio",
                                "audio": event.delta
                            })
                        elif event.type == "response.audio_transcript.delta":
                            await websocket.send_json({
                                "type": "transcript",
                                "text": event.delta
                            })
                        elif event.type == "error":
                            logger.error("voice_azure_error", error=event.error.message)
                            await websocket.send_json({"type": "error", "message": event.error.message})

                # Run proxy tasks
                await asyncio.gather(receive_from_client(), send_to_client())

        except Exception as e:
            logger.error("voice_session_failed", error=str(e))
            await websocket.close(code=1011)

voice_service = VoiceService()
