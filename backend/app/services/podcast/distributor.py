"""
Podcast Distributor Service

Multi-platform podcast distribution including RSS feed generation,
podcast directory submissions, and social media clip publishing.
"""

import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.podcast import (
    Podcast,
    PodcastEpisode,
    PodcastClip,
    PodcastStatus,
)
from app.models.social import SocialAccount
from app.adapters.youtube.adapter import YouTubeAdapter
from app.adapters.tiktok.adapter import TikTokAdapter
from app.adapters.instagram.adapter import InstagramAdapter
from app.adapters.twitter.adapter import TwitterAdapter
from app.adapters.interfaces.base import PublishContent, ContentType

logger = logging.getLogger(__name__)


class DistributionResult:
    """Result of a distribution operation."""

    def __init__(
        self,
        platform: str,
        success: bool,
        url: Optional[str] = None,
        platform_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.platform = platform
        self.success = success
        self.url = url
        self.platform_id = platform_id
        self.error = error


class PodcastDistributor:
    """
    Multi-platform podcast distribution service.

    Handles RSS feed generation, directory submissions,
    and social media publishing of clips.
    """

    # Supported podcast directories
    DIRECTORIES = {
        "spotify": "Spotify for Podcasters",
        "apple": "Apple Podcasts",
        "google": "Google Podcasts",
        "amazon": "Amazon Music",
        "stitcher": "Stitcher",
        "overcast": "Overcast",
        "pocketcasts": "Pocket Casts",
    }

    # Supported video platforms
    VIDEO_PLATFORMS = {
        "youtube": "YouTube (full episode)",
        "tiktok": "TikTok (clips)",
        "instagram": "Instagram Reels (clips)",
        "shorts": "YouTube Shorts (clips)",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._adapters = {
            "youtube": YouTubeAdapter(),
            "tiktok": TikTokAdapter(),
            "instagram": InstagramAdapter(),
            "twitter": TwitterAdapter(),
        }

    async def _get_social_account(
        self,
        user_id: uuid.UUID,
        platform: str,
    ) -> Optional[SocialAccount]:
        """Get connected social account for a platform."""
        result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == platform,
                SocialAccount.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def generate_rss_feed(
        self,
        podcast_id: uuid.UUID,
        user_id: uuid.UUID,
        base_url: str,
    ) -> str:
        """
        Generate a podcast RSS feed.

        Args:
            podcast_id: Podcast to generate feed for
            user_id: Owner user ID
            base_url: Base URL for media files

        Returns:
            RSS XML string
        """
        # Get podcast with episodes
        result = await self.db.execute(
            select(Podcast).where(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id,
            )
        )
        podcast = result.scalar_one_or_none()
        if not podcast:
            raise ValueError("Podcast not found")

        # Get published episodes
        episodes_result = await self.db.execute(
            select(PodcastEpisode)
            .where(
                PodcastEpisode.podcast_id == podcast_id,
                PodcastEpisode.is_published == True,
            )
            .order_by(PodcastEpisode.publish_date.desc())
        )
        episodes = episodes_result.scalars().all()

        # Build RSS feed
        rss = ET.Element("rss", {
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        })

        channel = ET.SubElement(rss, "channel")

        # Channel metadata
        ET.SubElement(channel, "title").text = podcast.title
        ET.SubElement(channel, "description").text = podcast.description or ""
        ET.SubElement(channel, "language").text = podcast.language
        ET.SubElement(channel, "link").text = f"{base_url}/podcasts/{podcast.id}"

        # iTunes specific
        ET.SubElement(channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}author").text = "IDKit"
        ET.SubElement(channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}summary").text = podcast.description or ""
        ET.SubElement(channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit").text = "false"

        if podcast.cover_art_url:
            image = ET.SubElement(channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
            image.set("href", podcast.cover_art_url)

            # Standard RSS image
            rss_image = ET.SubElement(channel, "image")
            ET.SubElement(rss_image, "url").text = podcast.cover_art_url
            ET.SubElement(rss_image, "title").text = podcast.title
            ET.SubElement(rss_image, "link").text = f"{base_url}/podcasts/{podcast.id}"

        if podcast.category:
            category = ET.SubElement(channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}category")
            category.set("text", podcast.category)

        # Atom self-reference
        atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
        atom_link.set("href", f"{base_url}/podcasts/{podcast.id}/feed.xml")
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")

        # Episodes
        for episode in episodes:
            item = ET.SubElement(channel, "item")

            ET.SubElement(item, "title").text = episode.title
            ET.SubElement(item, "description").text = episode.description or ""
            ET.SubElement(item, "link").text = f"{base_url}/episodes/{episode.id}"
            ET.SubElement(item, "guid").text = str(episode.id)

            if episode.publish_date:
                ET.SubElement(item, "pubDate").text = episode.publish_date.strftime(
                    "%a, %d %b %Y %H:%M:%S %z"
                )

            # Enclosure (audio file)
            if episode.audio_url:
                enclosure = ET.SubElement(item, "enclosure")
                enclosure.set("url", episode.audio_url)
                enclosure.set("type", "audio/mpeg")
                enclosure.set("length", str(episode.file_size_bytes or 0))

            # iTunes episode data
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration"
            ).text = self._format_duration(episode.duration_seconds or 0)

            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}summary"
            ).text = episode.description or ""

            if episode.episode_number:
                ET.SubElement(
                    item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}episode"
                ).text = str(episode.episode_number)

            if episode.season_number:
                ET.SubElement(
                    item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}season"
                ).text = str(episode.season_number)

            # Show notes as content:encoded
            if episode.show_notes:
                content_encoded = ET.SubElement(
                    item, "{http://purl.org/rss/1.0/modules/content/}encoded"
                )
                content_encoded.text = f"<![CDATA[{episode.show_notes}]]>"

        # Generate XML string
        return ET.tostring(rss, encoding="unicode", xml_declaration=True)

    def _format_duration(self, seconds: int) -> str:
        """Format duration as HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    async def distribute_episode(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
    ) -> Dict[str, DistributionResult]:
        """
        Distribute an episode to multiple platforms.

        Args:
            episode_id: Episode to distribute
            user_id: Owner user ID
            platforms: Target platforms (None = all available)

        Returns:
            Dict of platform -> DistributionResult
        """
        # Get episode
        result = await self.db.execute(
            select(PodcastEpisode).where(
                PodcastEpisode.id == episode_id,
                PodcastEpisode.user_id == user_id,
            )
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Episode not found")

        if not episode.audio_url:
            raise ValueError("Episode has no audio to distribute")

        # Get podcast for settings
        podcast_result = await self.db.execute(
            select(Podcast).where(Podcast.id == episode.podcast_id)
        )
        podcast = podcast_result.scalar_one_or_none()

        results = {}

        # Audio platforms (via RSS - these update automatically)
        # Just mark as published since RSS feed will pick up the episode
        if not episode.is_published:
            episode.is_published = True
            episode.publish_date = datetime.now(timezone.utc)
            await self.db.commit()

        # RSS-based platforms are automatically updated
        for platform in ["spotify", "apple", "google", "amazon"]:
            if platforms is None or platform in platforms:
                results[platform] = DistributionResult(
                    platform=platform,
                    success=True,
                    url=podcast.rss_feed_url if podcast else None,
                )

        # YouTube (full video)
        if (platforms is None or "youtube" in platforms) and episode.video_url:
            youtube_result = await self._publish_to_youtube(
                episode=episode,
                podcast=podcast,
            )
            results["youtube"] = youtube_result

        return results

    async def distribute_clip(
        self,
        clip_id: uuid.UUID,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
    ) -> Dict[str, DistributionResult]:
        """
        Distribute a clip to social media platforms.

        Args:
            clip_id: Clip to distribute
            user_id: Owner user ID
            platforms: Target platforms (None = clip's target_platforms)

        Returns:
            Dict of platform -> DistributionResult
        """
        # Get clip
        result = await self.db.execute(
            select(PodcastClip).where(
                PodcastClip.id == clip_id,
                PodcastClip.user_id == user_id,
            )
        )
        clip = result.scalar_one_or_none()
        if not clip:
            raise ValueError("Clip not found")

        if not clip.video_url and not clip.audio_url:
            raise ValueError("Clip has no media to distribute")

        # Use clip's target platforms if none specified
        if platforms is None:
            platforms = clip.target_platforms or ["tiktok", "reels", "shorts"]

        results = {}
        published = []

        # TikTok
        if "tiktok" in platforms and clip.video_url:
            tiktok_result = await self._publish_to_tiktok(clip)
            results["tiktok"] = tiktok_result
            if tiktok_result.success:
                published.append("tiktok")

        # Instagram Reels
        if "reels" in platforms and clip.video_url:
            reels_result = await self._publish_to_instagram_reels(clip)
            results["reels"] = reels_result
            if reels_result.success:
                published.append("instagram")

        # YouTube Shorts
        if "shorts" in platforms and clip.video_url:
            shorts_result = await self._publish_to_youtube_shorts(clip)
            results["shorts"] = shorts_result
            if shorts_result.success:
                published.append("youtube_shorts")

        # Twitter/X
        if "twitter" in platforms and clip.video_url:
            twitter_result = await self._publish_to_twitter(clip)
            results["twitter"] = twitter_result
            if twitter_result.success:
                published.append("twitter")

        # Update clip's published platforms
        if published:
            current_published = clip.published_platforms or []
            clip.published_platforms = list(set(current_published + published))
            await self.db.commit()

        return results

    async def _publish_to_youtube(
        self,
        episode: PodcastEpisode,
        podcast: Optional[Podcast],
    ) -> DistributionResult:
        """
        Publish full episode to YouTube.

        Uses YouTube Data API v3 via YouTubeAdapter.
        """
        # Get connected YouTube account
        social_account = await self._get_social_account(episode.user_id, "youtube")
        if not social_account:
            return DistributionResult(
                platform="youtube",
                success=False,
                error="No YouTube account connected. Please connect your account in settings.",
            )

        # Build publish content
        description = episode.description or ""
        if episode.show_notes:
            description += f"\n\n{episode.show_notes}"

        content = PublishContent(
            content_type=ContentType.VIDEO,
            title=episode.title,
            text=description,
            video_url=episode.video_url,
            thumbnail_url=episode.thumbnail_url,
            hashtags=["podcast", "idkit"],
            extras={
                "category_id": "22",  # People & Blogs
                "privacy": "public",
            },
        )

        try:
            adapter = self._adapters["youtube"]
            result = await adapter.publish(social_account.access_token, content)

            if result.success:
                logger.info(f"Published episode {episode.id} to YouTube: {result.platform_id}")
                return DistributionResult(
                    platform="youtube",
                    success=True,
                    url=result.url,
                    platform_id=result.platform_id,
                )
            else:
                logger.error(f"YouTube publish failed: {result.error_message}")
                return DistributionResult(
                    platform="youtube",
                    success=False,
                    error=result.error_message,
                )

        except Exception as e:
            logger.error(f"YouTube publish error: {e}")
            return DistributionResult(
                platform="youtube",
                success=False,
                error=str(e),
            )

    async def _publish_to_youtube_shorts(
        self,
        clip: PodcastClip,
    ) -> DistributionResult:
        """Publish clip as YouTube Short."""
        # Get connected YouTube account
        social_account = await self._get_social_account(clip.user_id, "youtube")
        if not social_account:
            return DistributionResult(
                platform="shorts",
                success=False,
                error="No YouTube account connected. Please connect your account in settings.",
            )

        # Build publish content with SHORT type
        content = PublishContent(
            content_type=ContentType.SHORT,
            title=clip.title or "Podcast Clip",
            text=clip.description or clip.quote_text or "",
            video_url=clip.video_url,
            thumbnail_url=clip.thumbnail_url,
            hashtags=["shorts", "podcast", "idkit"],
            extras={
                "category_id": "22",
                "privacy": "public",
            },
        )

        try:
            adapter = self._adapters["youtube"]
            result = await adapter.publish(social_account.access_token, content)

            if result.success:
                logger.info(f"Published clip {clip.id} to YouTube Shorts: {result.platform_id}")
                return DistributionResult(
                    platform="shorts",
                    success=True,
                    url=result.url,
                    platform_id=result.platform_id,
                )
            else:
                return DistributionResult(
                    platform="shorts",
                    success=False,
                    error=result.error_message,
                )

        except Exception as e:
            logger.error(f"YouTube Shorts publish error: {e}")
            return DistributionResult(
                platform="shorts",
                success=False,
                error=str(e),
            )

    async def _publish_to_tiktok(
        self,
        clip: PodcastClip,
    ) -> DistributionResult:
        """Publish clip to TikTok."""
        # Get connected TikTok account
        social_account = await self._get_social_account(clip.user_id, "tiktok")
        if not social_account:
            return DistributionResult(
                platform="tiktok",
                success=False,
                error="No TikTok account connected. Please connect your account in settings.",
            )

        # Build publish content
        caption = clip.description or clip.quote_text or clip.title or ""
        content = PublishContent(
            content_type=ContentType.VIDEO,
            text=caption,
            video_url=clip.video_url,
            hashtags=["podcast", "podcastclip", "idkit"],
        )

        try:
            adapter = self._adapters["tiktok"]
            result = await adapter.publish(social_account.access_token, content)

            if result.success:
                logger.info(f"Published clip {clip.id} to TikTok: {result.platform_id}")
                return DistributionResult(
                    platform="tiktok",
                    success=True,
                    url=result.url,
                    platform_id=result.platform_id,
                )
            else:
                return DistributionResult(
                    platform="tiktok",
                    success=False,
                    error=result.error_message,
                )

        except Exception as e:
            logger.error(f"TikTok publish error: {e}")
            return DistributionResult(
                platform="tiktok",
                success=False,
                error=str(e),
            )

    async def _publish_to_instagram_reels(
        self,
        clip: PodcastClip,
    ) -> DistributionResult:
        """Publish clip as Instagram Reel."""
        # Get connected Instagram account
        social_account = await self._get_social_account(clip.user_id, "instagram")
        if not social_account:
            return DistributionResult(
                platform="reels",
                success=False,
                error="No Instagram account connected. Please connect your account in settings.",
            )

        # Build publish content for Reel
        caption = clip.description or clip.quote_text or clip.title or ""
        content = PublishContent(
            content_type=ContentType.REEL,
            text=caption,
            video_url=clip.video_url,
            thumbnail_url=clip.thumbnail_url,
            hashtags=["podcast", "podcastclip", "reels", "idkit"],
        )

        try:
            adapter = self._adapters["instagram"]
            result = await adapter.publish(social_account.access_token, content)

            if result.success:
                logger.info(f"Published clip {clip.id} to Instagram Reels: {result.platform_id}")
                return DistributionResult(
                    platform="reels",
                    success=True,
                    url=result.url,
                    platform_id=result.platform_id,
                )
            else:
                return DistributionResult(
                    platform="reels",
                    success=False,
                    error=result.error_message,
                )

        except Exception as e:
            logger.error(f"Instagram Reels publish error: {e}")
            return DistributionResult(
                platform="reels",
                success=False,
                error=str(e),
            )

    async def _publish_to_twitter(
        self,
        clip: PodcastClip,
    ) -> DistributionResult:
        """Publish clip to Twitter/X."""
        # Get connected Twitter account
        social_account = await self._get_social_account(clip.user_id, "twitter")
        if not social_account:
            return DistributionResult(
                platform="twitter",
                success=False,
                error="No Twitter/X account connected. Please connect your account in settings.",
            )

        # Build tweet text (max 280 chars)
        tweet_text = clip.quote_text or clip.description or clip.title or "Check out this podcast clip!"
        if len(tweet_text) > 260:  # Leave room for hashtags
            tweet_text = tweet_text[:257] + "..."

        content = PublishContent(
            content_type=ContentType.POST,
            text=tweet_text,
            video_url=clip.video_url,
            hashtags=["podcast", "podcastclip"],
        )

        try:
            adapter = self._adapters["twitter"]
            result = await adapter.publish(social_account.access_token, content)

            if result.success:
                logger.info(f"Published clip {clip.id} to Twitter: {result.platform_id}")
                return DistributionResult(
                    platform="twitter",
                    success=True,
                    url=result.url,
                    platform_id=result.platform_id,
                )
            else:
                return DistributionResult(
                    platform="twitter",
                    success=False,
                    error=result.error_message,
                )

        except Exception as e:
            logger.error(f"Twitter publish error: {e}")
            return DistributionResult(
                platform="twitter",
                success=False,
                error=str(e),
            )

    async def get_distribution_status(
        self,
        podcast_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict:
        """
        Get distribution status for a podcast.

        Returns info about connected platforms and submission status.
        """
        result = await self.db.execute(
            select(Podcast).where(
                Podcast.id == podcast_id,
                Podcast.user_id == user_id,
            )
        )
        podcast = result.scalar_one_or_none()
        if not podcast:
            raise ValueError("Podcast not found")

        return {
            "rss_feed_url": podcast.rss_feed_url,
            "directories": {
                "spotify": {
                    "connected": bool(podcast.spotify_url),
                    "url": podcast.spotify_url,
                },
                "apple": {
                    "connected": bool(podcast.itunes_url),
                    "url": podcast.itunes_url,
                },
                "youtube": {
                    "connected": bool(podcast.youtube_playlist_id),
                    "playlist_id": podcast.youtube_playlist_id,
                },
            },
            "stats": {
                "episode_count": podcast.episode_count,
                "subscriber_count": podcast.subscriber_count,
                "total_plays": podcast.total_plays,
            },
        }

    async def submit_to_directory(
        self,
        podcast_id: uuid.UUID,
        user_id: uuid.UUID,
        directory: str,
        rss_url: str,
    ) -> DistributionResult:
        """
        Submit podcast RSS feed to a directory.

        Most directories accept RSS URLs and verify ownership.
        """
        if directory not in self.DIRECTORIES:
            raise ValueError(f"Unknown directory: {directory}")

        # Podcast directories typically require manual submission
        # through their portals. We can provide the URLs and instructions.

        directory_urls = {
            "spotify": "https://podcasters.spotify.com/",
            "apple": "https://podcasts.apple.com/submit",
            "google": "https://podcasts.google.com/publish",
            "amazon": "https://podcasters.amazon.com/",
        }

        return DistributionResult(
            platform=directory,
            success=True,
            url=directory_urls.get(directory),
            error=f"Please submit your RSS feed ({rss_url}) at the directory portal",
        )

    async def schedule_distribution(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        scheduled_time: datetime,
        platforms: Optional[List[str]] = None,
    ) -> Dict:
        """
        Schedule episode distribution for a future time.

        In production, this would create a task in the job queue.
        """
        # Get episode
        result = await self.db.execute(
            select(PodcastEpisode).where(
                PodcastEpisode.id == episode_id,
                PodcastEpisode.user_id == user_id,
            )
        )
        episode = result.scalar_one_or_none()
        if not episode:
            raise ValueError("Episode not found")

        # Update publish date and ensure status is ready for distribution
        episode.publish_date = scheduled_time
        episode.status = "ready"  # Ensure it's marked ready for the scheduler
        await self.db.commit()

        # The check_scheduled_podcast_distributions Celery beat task runs every minute
        # and will pick up this episode when the scheduled_time is reached.
        # It queries for episodes where:
        #   - publish_date is not None
        #   - publish_date <= now + 1 minute
        #   - is_published == False
        #   - status == "ready"

        return {
            "episode_id": str(episode_id),
            "scheduled_time": scheduled_time.isoformat(),
            "platforms": platforms or ["spotify", "apple", "google", "youtube", "rss"],
            "status": "scheduled",
            "note": "Distribution will be triggered automatically at the scheduled time",
        }
