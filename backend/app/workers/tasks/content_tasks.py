"""
Content Generation Tasks

Background tasks for AI content generation.
"""

import logging
from typing import Optional
from uuid import UUID

from celery import shared_task

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=600,
)
def generate_content(
    self,
    user_id: str,
    content_type: str,
    prompt: str,
    brand_voice_id: Optional[str] = None,
    template_id: Optional[str] = None,
    options: Optional[dict] = None,
) -> dict:
    """
    Generate AI content (scripts, posts, etc.).

    Args:
        user_id: User ID
        content_type: Type of content (script, post, caption, etc.)
        prompt: Generation prompt
        brand_voice_id: Optional brand voice for style
        template_id: Optional template to use
        options: Additional generation options

    Returns:
        Generated content with metadata
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Generating {content_type} for user {user_id}")

    async def _generate():
        async with get_async_db() as db:
            from app.services.content.generator import ContentGenerator

            generator = ContentGenerator(db)

            # Send progress via WebSocket
            from app.websocket import ws_publisher

            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=UUID(self.request.id or "00000000-0000-0000-0000-000000000000"),
                content_type=content_type,
                stage="generating",
                progress=10,
                message="Starting generation...",
            )

            # Generate content
            result = await generator.generate(
                user_id=UUID(user_id),
                content_type=content_type,
                prompt=prompt,
                brand_voice_id=UUID(brand_voice_id) if brand_voice_id else None,
                template_id=UUID(template_id) if template_id else None,
                options=options or {},
            )

            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=UUID(self.request.id or "00000000-0000-0000-0000-000000000000"),
                content_type=content_type,
                stage="completed",
                progress=100,
                message="Generation complete",
            )

            return result

    return asyncio.get_event_loop().run_until_complete(_generate())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=900,
)
def repurpose_content(
    self,
    user_id: str,
    content_id: str,
    target_formats: list[str],
    options: Optional[dict] = None,
) -> dict:
    """
    Repurpose existing content into new formats.

    Args:
        user_id: User ID
        content_id: Source content ID
        target_formats: List of formats to generate
        options: Repurposing options

    Returns:
        Dict of format -> generated content
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Repurposing content {content_id} for user {user_id}")

    async def _repurpose():
        async with get_async_db() as db:
            from app.services.content.repurposer import ContentRepurposer

            repurposer = ContentRepurposer(db)
            results = {}

            for i, target_format in enumerate(target_formats):
                progress = int(((i + 1) / len(target_formats)) * 100)

                from app.websocket import ws_publisher
                await ws_publisher.send_content_progress(
                    user_id=UUID(user_id),
                    content_id=UUID(content_id),
                    content_type="repurpose",
                    stage=f"generating_{target_format}",
                    progress=progress,
                    message=f"Creating {target_format}...",
                )

                result = await repurposer.repurpose(
                    content_id=UUID(content_id),
                    target_format=target_format,
                    options=options or {},
                )
                results[target_format] = result

            return results

    return asyncio.get_event_loop().run_until_complete(_repurpose())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=300,
)
def generate_script(
    self,
    user_id: str,
    topic: str,
    script_type: str = "video",
    duration_target: int = 60,
    style: str = "conversational",
    brand_voice_id: Optional[str] = None,
) -> dict:
    """
    Generate a script for video/podcast.

    Args:
        user_id: User ID
        topic: Script topic
        script_type: Type of script (video, podcast, etc.)
        duration_target: Target duration in seconds
        style: Script style
        brand_voice_id: Optional brand voice

    Returns:
        Generated script with metadata
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Generating {script_type} script for user {user_id}: {topic}")

    async def _generate_script():
        async with get_async_db() as db:
            from app.services.content.generator import ContentGenerator

            generator = ContentGenerator(db)

            result = await generator.generate_script(
                user_id=UUID(user_id),
                topic=topic,
                script_type=script_type,
                duration_target=duration_target,
                style=style,
                brand_voice_id=UUID(brand_voice_id) if brand_voice_id else None,
            )

            return result

    return asyncio.get_event_loop().run_until_complete(_generate_script())
