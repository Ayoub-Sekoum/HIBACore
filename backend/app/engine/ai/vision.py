"""
Vision Service — Image Analysis & Multimodal Pre-processing.
Task 7.06 — Multi-Tenant Enterprise Chatbot.
"""

import structlog
from azure.ai.vision.imageanalysis.aio import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.identity.aio import DefaultAzureCredential
from app.core.credentials import get_global_credential

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

class VisionService:
    """Manages image analysis for multimodal chat."""

    async def analyze_image(self, image_url: str) -> dict:
        """
        Analyzes an image to extract captions and tags for better LLM context.
        """
        logger.info("vision_analysis_started", image_url=image_url)

        try:
            async with ImageAnalysisClient(
                endpoint=settings.VISION_ENDPOINT, # type: ignore
                credential=get_global_credential()
            ) as client:
                result = await client.analyze_from_url(
                    image_url=image_url,
                    visual_features=[
                        VisualFeatures.CAPTION,
                        VisualFeatures.TAGS,
                        VisualFeatures.READ
                    ]
                )

                analysis = {
                    "caption": result.caption.text if result.caption else "",
                    "tags": [tag.name for tag in result.tags.list] if result.tags else [],
                    "text_found": [line.text for block in result.read.blocks for line in block.lines] if result.read else []
                }

                return analysis
        except Exception as e:
            logger.error("vision_analysis_failed", error=str(e))
            return {"error": "Failed to analyze image"}

vision_service = VisionService()
