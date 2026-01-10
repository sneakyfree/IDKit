"""
Podcast Tasks

Background tasks for podcast generation, clip extraction, and distribution.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
)
def check_scheduled_podcast_distributions(self) -> dict:
    """
    Check for scheduled podcast episode distributions and execute them.

    This task runs periodically (every minute via beat schedule) to find
    episodes that are scheduled to be distributed and triggers distribution.

    Returns:
        Summary of processed distributions
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info("Checking for scheduled podcast distributions")

    async def _check_scheduled():
        async with get_async_db() as db:
            from sqlalchemy import select, and_
            from app.models.podcast import PodcastEpisode

            # Find episodes scheduled for distribution within the next minute
            # (to account for task execution time)
            now = datetime.now(timezone.utc)
            window_end = now + timedelta(minutes=1)

            result = await db.execute(
                select(PodcastEpisode).where(
                    and_(
                        PodcastEpisode.publish_date.isnot(None),
                        PodcastEpisode.publish_date <= window_end,
                        PodcastEpisode.publish_date > now - timedelta(minutes=5),  # Don't re-process old ones
                        PodcastEpisode.is_published == False,
                        PodcastEpisode.status == "ready",
                    )
                )
            )
            episodes = result.scalars().all()

            if not episodes:
                logger.debug("No scheduled podcast distributions found")
                return {"processed": 0, "episodes": []}

            processed = []
            for episode in episodes:
                logger.info(f"Triggering distribution for scheduled episode {episode.id}")

                # Queue the distribution task
                distribute_episode.delay(
                    user_id=str(episode.user_id),
                    episode_id=str(episode.id),
                    platforms=["spotify", "apple", "google", "youtube", "rss"],
                    options={},
                )

                processed.append({
                    "episode_id": str(episode.id),
                    "title": episode.title,
                    "scheduled_time": episode.publish_date.isoformat() if episode.publish_date else None,
                })

            return {
                "processed": len(processed),
                "episodes": processed,
            }

    return asyncio.get_event_loop().run_until_complete(_check_scheduled())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 300},
    soft_time_limit=3600,  # 1 hour
)
def generate_episode(
    self,
    user_id: str,
    podcast_id: str,
    topic: str,
    style: str = "conversational",
    duration_target: int = 600,
    use_ai_twin: bool = True,
    options: Optional[dict] = None,
) -> dict:
    """
    Generate a complete podcast episode from a topic.

    Args:
        user_id: User ID
        podcast_id: Podcast ID
        topic: Episode topic/subject
        style: Script style (conversational, educational, etc.)
        duration_target: Target duration in seconds
        use_ai_twin: Whether to use AI twin for voice
        options: Additional generation options

    Returns:
        Generated episode details
    """
    import asyncio
    import uuid
    from app.workers.utils import get_async_db

    logger.info(f"Generating podcast episode for podcast {podcast_id}")
    episode_id = uuid.uuid4()

    async def _generate():
        async with get_async_db() as db:
            from app.services.podcast.generator import PodcastGenerator
            from app.websocket import ws_publisher

            generator = PodcastGenerator(db)

            # Send progress: Starting
            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=episode_id,
                content_type="podcast_episode",
                stage="initializing",
                progress=5,
                message="Starting episode generation...",
            )

            # Step 1: Generate script
            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=episode_id,
                content_type="podcast_episode",
                stage="script",
                progress=15,
                message="Generating script...",
            )

            script = await generator.generate_script(
                topic=topic,
                style=style,
                duration_target=duration_target,
                podcast_id=UUID(podcast_id),
            )

            # Step 2: Generate audio
            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=episode_id,
                content_type="podcast_episode",
                stage="audio",
                progress=40,
                message="Synthesizing audio...",
            )

            audio_result = await generator.generate_audio(
                script=script,
                podcast_id=UUID(podcast_id),
                use_ai_twin=use_ai_twin,
            )

            # Step 3: Generate video (if applicable)
            video_result = None
            if use_ai_twin and options and options.get("generate_video", True):
                await ws_publisher.send_content_progress(
                    user_id=UUID(user_id),
                    content_id=episode_id,
                    content_type="podcast_episode",
                    stage="video",
                    progress=65,
                    message="Generating video...",
                )

                video_result = await generator.generate_video(
                    audio_url=audio_result["audio_url"],
                    script=script,
                    podcast_id=UUID(podcast_id),
                )

            # Step 4: Generate metadata
            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=episode_id,
                content_type="podcast_episode",
                stage="metadata",
                progress=85,
                message="Generating metadata...",
            )

            metadata = await generator.generate_metadata(
                script=script,
                audio_url=audio_result["audio_url"],
            )

            # Step 5: Create episode record
            episode = await generator.create_episode(
                podcast_id=UUID(podcast_id),
                episode_id=episode_id,
                title=metadata.get("title", f"Episode: {topic}"),
                description=metadata.get("description", ""),
                script=script,
                audio_url=audio_result["audio_url"],
                video_url=video_result["video_url"] if video_result else None,
                duration_seconds=audio_result.get("duration_seconds"),
                chapters=metadata.get("chapters", []),
            )

            # Send completion
            await ws_publisher.send_content_completed(
                user_id=UUID(user_id),
                content_id=episode_id,
                content_type="podcast_episode",
                preview_url=audio_result["audio_url"],
            )

            return {
                "episode_id": str(episode_id),
                "title": episode.title,
                "audio_url": episode.audio_url,
                "video_url": episode.video_url,
                "duration_seconds": episode.duration_seconds,
            }

    return asyncio.get_event_loop().run_until_complete(_generate())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 120},
    soft_time_limit=1800,  # 30 minutes
)
def extract_clips(
    self,
    user_id: str,
    episode_id: str,
    clip_count: int = 5,
    clip_duration: int = 60,
    options: Optional[dict] = None,
) -> dict:
    """
    Extract short clips from a podcast episode.

    Args:
        user_id: User ID
        episode_id: Episode ID
        clip_count: Number of clips to extract
        clip_duration: Target duration per clip (seconds)
        options: Additional extraction options

    Returns:
        List of extracted clips
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Extracting clips from episode {episode_id}")

    async def _extract():
        async with get_async_db() as db:
            from app.services.podcast.clip_extractor import ClipExtractor
            from app.websocket import ws_publisher

            extractor = ClipExtractor(db)

            # Get episode
            episode = await extractor.get_episode(UUID(episode_id))
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            # Send progress
            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=UUID(episode_id),
                content_type="podcast_clips",
                stage="analyzing",
                progress=10,
                message="Analyzing episode for highlights...",
            )

            # Find highlights
            highlights = await extractor.find_highlights(
                transcript=episode.transcript,
                audio_url=episode.audio_url,
                count=clip_count,
                target_duration=clip_duration,
            )

            clips = []
            for i, highlight in enumerate(highlights):
                progress = 20 + (i / len(highlights)) * 70

                await ws_publisher.send_content_progress(
                    user_id=UUID(user_id),
                    content_id=UUID(episode_id),
                    content_type="podcast_clips",
                    stage="extracting",
                    progress=progress,
                    message=f"Extracting clip {i + 1}/{len(highlights)}...",
                )

                clip = await extractor.create_clip(
                    episode_id=UUID(episode_id),
                    start_time=highlight["start"],
                    end_time=highlight["end"],
                    title=highlight.get("title", f"Clip {i + 1}"),
                    quote_text=highlight.get("best_quote"),
                )

                # Generate clip video with captions
                clip_video = await extractor.generate_clip_video(
                    clip=clip,
                    add_captions=options.get("add_captions", True) if options else True,
                )

                clips.append({
                    "clip_id": str(clip.id),
                    "title": clip.title,
                    "start_time": clip.start_time_seconds,
                    "end_time": clip.end_time_seconds,
                    "audio_url": clip.audio_url,
                    "video_url": clip_video.get("video_url"),
                    "quote_text": clip.quote_text,
                })

            # Send completion
            await ws_publisher.send_content_completed(
                user_id=UUID(user_id),
                content_id=UUID(episode_id),
                content_type="podcast_clips",
            )

            return {
                "episode_id": episode_id,
                "clips": clips,
                "clip_count": len(clips),
            }

    return asyncio.get_event_loop().run_until_complete(_extract())


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    soft_time_limit=600,  # 10 minutes
    rate_limit="5/m",
)
def distribute_episode(
    self,
    user_id: str,
    episode_id: str,
    platforms: list[str],
    options: Optional[dict] = None,
) -> dict:
    """
    Distribute a podcast episode to multiple platforms.

    Args:
        user_id: User ID
        episode_id: Episode ID
        platforms: List of platforms to distribute to
        options: Platform-specific options

    Returns:
        Distribution results per platform
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Distributing episode {episode_id} to {platforms}")

    async def _distribute():
        async with get_async_db() as db:
            from app.services.podcast.distributor import PodcastDistributor
            from app.websocket import ws_publisher

            distributor = PodcastDistributor(db)

            # Get episode
            episode = await distributor.get_episode(UUID(episode_id))
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            results = {}

            for i, platform in enumerate(platforms):
                progress = (i / len(platforms)) * 100

                await ws_publisher.send_job_progress(
                    job_id=UUID(episode_id),
                    user_id=UUID(user_id),
                    job_type="podcast_distribution",
                    progress=progress,
                    message=f"Publishing to {platform}...",
                )

                try:
                    if platform == "spotify":
                        result = await distributor.publish_to_spotify(
                            episode=episode,
                            options=options.get("spotify", {}) if options else {},
                        )
                    elif platform == "apple":
                        result = await distributor.publish_to_apple(
                            episode=episode,
                            options=options.get("apple", {}) if options else {},
                        )
                    elif platform == "google":
                        result = await distributor.publish_to_google(
                            episode=episode,
                            options=options.get("google", {}) if options else {},
                        )
                    elif platform == "youtube":
                        result = await distributor.publish_to_youtube(
                            episode=episode,
                            options=options.get("youtube", {}) if options else {},
                        )
                    elif platform == "rss":
                        result = await distributor.update_rss_feed(episode=episode)
                    else:
                        result = {"status": "error", "error": f"Unknown platform: {platform}"}

                    results[platform] = result

                except Exception as e:
                    logger.error(f"Failed to distribute to {platform}: {e}")
                    results[platform] = {"status": "error", "error": str(e)}

            # Send completion
            await ws_publisher.send_job_completed(
                job_id=UUID(episode_id),
                user_id=UUID(user_id),
                job_type="podcast_distribution",
                result=results,
                message="Episode distributed successfully",
            )

            return {
                "episode_id": episode_id,
                "results": results,
                "successful": [p for p, r in results.items() if r.get("status") != "error"],
                "failed": [p for p, r in results.items() if r.get("status") == "error"],
            }

    return asyncio.get_event_loop().run_until_complete(_distribute())


@celery_app.task(
    bind=True,
    soft_time_limit=300,
)
def generate_show_notes(
    self,
    user_id: str,
    episode_id: str,
) -> dict:
    """
    Generate show notes for a podcast episode.

    Args:
        user_id: User ID
        episode_id: Episode ID

    Returns:
        Generated show notes
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Generating show notes for episode {episode_id}")

    async def _generate():
        async with get_async_db() as db:
            from app.services.podcast.generator import PodcastGenerator

            generator = PodcastGenerator(db)

            episode = await generator.get_episode(UUID(episode_id))
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            show_notes = await generator.generate_show_notes(
                transcript=episode.transcript,
                script=episode.script,
            )

            # Update episode with show notes
            await generator.update_episode(
                episode_id=UUID(episode_id),
                show_notes=show_notes,
            )

            return {
                "episode_id": episode_id,
                "show_notes": show_notes,
            }

    return asyncio.get_event_loop().run_until_complete(_generate())


@celery_app.task(
    bind=True,
    soft_time_limit=600,
)
def transcribe_episode(
    self,
    user_id: str,
    episode_id: str,
) -> dict:
    """
    Transcribe a podcast episode audio.

    Args:
        user_id: User ID
        episode_id: Episode ID

    Returns:
        Transcription result
    """
    import asyncio
    from app.workers.utils import get_async_db

    logger.info(f"Transcribing episode {episode_id}")

    async def _transcribe():
        async with get_async_db() as db:
            from app.services.podcast.generator import PodcastGenerator
            from app.websocket import ws_publisher

            generator = PodcastGenerator(db)

            episode = await generator.get_episode(UUID(episode_id))
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            await ws_publisher.send_content_progress(
                user_id=UUID(user_id),
                content_id=UUID(episode_id),
                content_type="podcast_transcription",
                stage="transcribing",
                progress=20,
                message="Transcribing audio...",
            )

            transcript = await generator.transcribe_audio(
                audio_url=episode.audio_url,
            )

            # Update episode with transcript
            await generator.update_episode(
                episode_id=UUID(episode_id),
                transcript=transcript["text"],
            )

            await ws_publisher.send_content_completed(
                user_id=UUID(user_id),
                content_id=UUID(episode_id),
                content_type="podcast_transcription",
            )

            return {
                "episode_id": episode_id,
                "transcript": transcript["text"],
                "segments": transcript.get("segments", []),
            }

    return asyncio.get_event_loop().run_until_complete(_transcribe())
