"""
AI Twin Tasks

Background tasks for AI twin training and generation.
"""

import logging
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 300},
    soft_time_limit=3600,  # 1 hour
)
def train_avatar(
    self,
    user_id: str,
    twin_id: str,
    media_urls: list[str],
    options: Optional[dict] = None,
) -> dict:
    """
    Train an avatar from uploaded media.

    Args:
        user_id: User ID
        twin_id: AI Twin ID
        media_urls: List of training image/video URLs
        options: Training options

    Returns:
        Training result with avatar ID
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Training avatar for twin {twin_id}")

    async def _train():
        async with get_async_db() as db:
            from app.services.twin.service import AITwinService
            from app.websocket import ws_publisher

            service = AITwinService(db)

            # Send progress updates
            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="avatar",
                stage="downloading",
                progress=10,
                message="Downloading media files...",
            )

            # Download and process media
            processed_media = await service.process_training_media(
                media_urls=media_urls,
                media_type="avatar",
            )

            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="avatar",
                stage="training",
                progress=30,
                message="Training avatar model...",
            )

            # Train avatar
            result = await service.train_avatar(
                twin_id=UUID(twin_id),
                processed_media=processed_media,
                options=options or {},
            )

            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="avatar",
                stage="completed",
                progress=100,
                message="Avatar training complete!",
            )

            return result

    return asyncio.get_event_loop().run_until_complete(_train())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 300},
    soft_time_limit=1800,  # 30 minutes
)
def clone_voice(
    self,
    user_id: str,
    twin_id: str,
    audio_urls: list[str],
    options: Optional[dict] = None,
) -> dict:
    """
    Clone a voice from audio samples.

    Args:
        user_id: User ID
        twin_id: AI Twin ID
        audio_urls: List of audio sample URLs
        options: Cloning options

    Returns:
        Cloning result with voice ID
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Cloning voice for twin {twin_id}")

    async def _clone():
        async with get_async_db() as db:
            from app.services.twin.service import AITwinService
            from app.websocket import ws_publisher

            service = AITwinService(db)

            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="voice",
                stage="processing",
                progress=20,
                message="Processing audio samples...",
            )

            # Process audio samples
            processed_audio = await service.process_training_media(
                media_urls=audio_urls,
                media_type="voice",
            )

            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="voice",
                stage="cloning",
                progress=50,
                message="Cloning voice...",
            )

            # Clone voice
            result = await service.clone_voice(
                twin_id=UUID(twin_id),
                processed_audio=processed_audio,
                options=options or {},
            )

            await ws_publisher.send_twin_training_progress(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                job_type="voice",
                stage="completed",
                progress=100,
                message="Voice cloning complete!",
            )

            return result

    return asyncio.get_event_loop().run_until_complete(_clone())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 120},
    soft_time_limit=1800,  # 30 minutes
)
def generate_video(
    self,
    user_id: str,
    twin_id: str,
    script: str,
    video_options: Optional[dict] = None,
    voice_options: Optional[dict] = None,
) -> dict:
    """
    Generate a video with the AI twin.

    Args:
        user_id: User ID
        twin_id: AI Twin ID
        script: Script for the video
        video_options: Video generation options
        voice_options: Voice synthesis options

    Returns:
        Generated video URL and metadata
    """
    import asyncio
    import uuid
    from app.workers.utils import get_async_db

    logger.info(f"Generating video for twin {twin_id}")
    video_id = uuid.uuid4()

    async def _generate():
        async with get_async_db() as db:
            from app.services.twin.service import AITwinService
            from app.websocket import ws_publisher

            service = AITwinService(db)

            # Send initial progress
            await ws_publisher.send_job_started(
                job_id=video_id,
                user_id=UUID(user_id),
                job_type="video_generation",
                message="Starting video generation...",
            )

            # Synthesize speech
            await ws_publisher.send_job_progress(
                job_id=video_id,
                user_id=UUID(user_id),
                job_type="video_generation",
                progress=20,
                message="Synthesizing speech...",
            )

            audio_url = await service.synthesize_speech(
                twin_id=UUID(twin_id),
                text=script,
                options=voice_options or {},
            )

            # Generate video
            await ws_publisher.send_job_progress(
                job_id=video_id,
                user_id=UUID(user_id),
                job_type="video_generation",
                progress=50,
                message="Generating video...",
            )

            video_result = await service.generate_video(
                twin_id=UUID(twin_id),
                audio_url=audio_url,
                options=video_options or {},
            )

            # Post-process (enhance, add captions, etc.)
            await ws_publisher.send_job_progress(
                job_id=video_id,
                user_id=UUID(user_id),
                job_type="video_generation",
                progress=80,
                message="Post-processing video...",
            )

            final_video = await service.post_process_video(
                video_url=video_result["video_url"],
                options=video_options or {},
            )

            # Send completion
            await ws_publisher.send_twin_video_ready(
                user_id=UUID(user_id),
                twin_id=UUID(twin_id),
                video_id=video_id,
                video_url=final_video["video_url"],
                thumbnail_url=final_video.get("thumbnail_url"),
                duration_seconds=final_video.get("duration_seconds"),
            )

            return {
                "video_id": str(video_id),
                "video_url": final_video["video_url"],
                "thumbnail_url": final_video.get("thumbnail_url"),
                "duration_seconds": final_video.get("duration_seconds"),
            }

    return asyncio.get_event_loop().run_until_complete(_generate())


@celery_app.task(
    bind=True,
    soft_time_limit=7200,  # 2 hours for live session
)
def start_live_session(
    self,
    user_id: str,
    twin_id: str,
    session_config: dict,
) -> dict:
    """
    Start an AI twin live streaming session.

    Args:
        user_id: User ID
        twin_id: AI Twin ID
        session_config: Live session configuration

    Returns:
        Session details with streaming URLs
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Starting live session for twin {twin_id}")

    async def _start_live():
        async with get_async_db() as db:
            from app.services.twin.service import AITwinService

            service = AITwinService(db)

            result = await service.start_live_session(
                twin_id=UUID(twin_id),
                config=session_config,
            )

            return result

    return asyncio.get_event_loop().run_until_complete(_start_live())
