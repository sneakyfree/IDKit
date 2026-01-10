"""
Content Repurposing Service

Transforms content from one format to multiple platform-optimized formats.
Podcast → Clips, Quote Cards, Social Posts
Long Video → Shorts
Blog → Thread, Social Posts
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content import ContentItem, ContentType, BrandVoice
from app.models.podcast import PodcastEpisode, PodcastClip


class RepurposeResult:
    """Result of a repurposing operation."""

    def __init__(
        self,
        source_id: uuid.UUID,
        source_type: str,
        output_type: str,
        content: Any,
        metadata: Optional[Dict] = None,
        platform: Optional[str] = None,
    ):
        self.source_id = source_id
        self.source_type = source_type
        self.output_type = output_type
        self.content = content
        self.metadata = metadata or {}
        self.platform = platform
        self.created_at = datetime.utcnow()


class ContentRepurposer:
    """
    AI-powered content repurposing service.

    Transforms content across formats and platforms:
    - Podcast → Short clips, quote cards, social posts, blog posts
    - Long video → Shorts/Reels/TikToks
    - Blog → Twitter threads, LinkedIn posts, carousels
    - Any text → Platform-optimized versions
    """

    # Platform constraints
    PLATFORM_LIMITS = {
        "twitter": {"text": 280, "thread_max": 25},
        "instagram": {"caption": 2200, "carousel_max": 10},
        "tiktok": {"caption": 2200, "video_max_seconds": 180},
        "linkedin": {"text": 3000, "article_limit": 100000},
        "facebook": {"text": 63206},
        "youtube_shorts": {"title": 100, "description": 5000, "video_max_seconds": 60},
    }

    # Quote card styles
    QUOTE_CARD_STYLES = [
        "minimal",
        "gradient",
        "bold",
        "professional",
        "playful",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    # =========================================================================
    # PODCAST REPURPOSING
    # =========================================================================

    async def podcast_to_social_posts(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
        post_count: int = 5,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> List[RepurposeResult]:
        """
        Generate social media posts from a podcast episode.

        Extracts key insights, quotes, and takeaways for social sharing.
        """
        if platforms is None:
            platforms = ["twitter", "linkedin", "instagram"]

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

        content = episode.transcript or episode.script or episode.description
        if not content:
            raise ValueError("Episode has no content to repurpose")

        # Get brand voice if specified
        brand_voice = None
        if brand_voice_id:
            bv_result = await self.db.execute(
                select(BrandVoice).where(BrandVoice.id == brand_voice_id)
            )
            brand_voice = bv_result.scalar_one_or_none()

        # Generate posts for each platform
        results = []
        for platform in platforms:
            posts = await self._generate_social_posts(
                content=content,
                title=episode.title,
                platform=platform,
                count=post_count,
                brand_voice=brand_voice,
            )

            for post in posts:
                results.append(RepurposeResult(
                    source_id=episode_id,
                    source_type="podcast_episode",
                    output_type="social_post",
                    content=post,
                    platform=platform,
                    metadata={"episode_title": episode.title},
                ))

        return results

    async def podcast_to_quote_cards(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        quote_count: int = 5,
        style: str = "minimal",
    ) -> List[RepurposeResult]:
        """
        Extract quotable moments and generate quote card data.

        Returns structured data for frontend to render as images.
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

        content = episode.transcript or episode.script
        if not content:
            raise ValueError("Episode has no content to extract quotes from")

        # Extract best quotes using AI
        quotes = await self._extract_quotes(
            content=content,
            count=quote_count,
        )

        results = []
        for quote in quotes:
            card_data = {
                "quote": quote["text"],
                "attribution": quote.get("speaker", ""),
                "episode_title": episode.title,
                "style": style,
                "background_suggestion": quote.get("mood", "neutral"),
            }

            results.append(RepurposeResult(
                source_id=episode_id,
                source_type="podcast_episode",
                output_type="quote_card",
                content=card_data,
                metadata={"virality_score": quote.get("score", 5)},
            ))

        return results

    async def podcast_to_blog_post(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        include_timestamps: bool = True,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> RepurposeResult:
        """
        Convert podcast episode to a full blog post.

        Creates SEO-optimized article from episode content.
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

        content = episode.transcript or episode.script
        if not content:
            raise ValueError("Episode has no content to convert")

        # Get brand voice
        brand_voice = None
        if brand_voice_id:
            bv_result = await self.db.execute(
                select(BrandVoice).where(BrandVoice.id == brand_voice_id)
            )
            brand_voice = bv_result.scalar_one_or_none()

        # Generate blog post
        blog_post = await self._generate_blog_post(
            content=content,
            title=episode.title,
            show_notes=episode.show_notes,
            chapters=episode.chapters,
            include_timestamps=include_timestamps,
            brand_voice=brand_voice,
        )

        return RepurposeResult(
            source_id=episode_id,
            source_type="podcast_episode",
            output_type="blog_post",
            content=blog_post,
            metadata={
                "word_count": len(blog_post["content"].split()),
                "seo_title": blog_post.get("seo_title"),
                "meta_description": blog_post.get("meta_description"),
            },
        )

    async def podcast_to_newsletter(
        self,
        episode_id: uuid.UUID,
        user_id: uuid.UUID,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> RepurposeResult:
        """
        Create newsletter content from podcast episode.
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

        content = episode.transcript or episode.script or episode.show_notes
        if not content:
            raise ValueError("Episode has no content")

        client = await self._get_llm_client()

        prompt = f"""Create an email newsletter based on this podcast episode.

EPISODE TITLE: {episode.title}
CONTENT:
{content[:4000]}

Create a newsletter with:
1. Catchy subject line
2. Brief intro hook
3. 3-5 key takeaways as bullet points
4. Call to action to listen
5. Brief personal note/sign-off

Format as JSON with keys: subject, intro, takeaways (array), cta, signoff"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert email copywriter creating engaging newsletter content.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        import json
        newsletter = {}
        try:
            response_text = response.choices[0].message.content
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                newsletter = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            newsletter = {
                "subject": f"New Episode: {episode.title}",
                "intro": "Check out our latest episode!",
                "takeaways": [],
                "cta": "Listen now",
                "signoff": "Thanks for being part of our community!",
            }

        return RepurposeResult(
            source_id=episode_id,
            source_type="podcast_episode",
            output_type="newsletter",
            content=newsletter,
            metadata={"episode_title": episode.title},
        )

    # =========================================================================
    # VIDEO REPURPOSING
    # =========================================================================

    async def long_video_to_shorts(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        clip_count: int = 5,
        platforms: Optional[List[str]] = None,
    ) -> List[RepurposeResult]:
        """
        Identify best moments from long video for short-form content.

        Returns timing markers and suggested captions.
        """
        if platforms is None:
            platforms = ["youtube_shorts", "tiktok", "instagram"]

        # Get content item
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id,
            )
        )
        content_item = result.scalar_one_or_none()
        if not content_item:
            raise ValueError("Content not found")

        # Use transcript or description
        text_content = content_item.content or ""
        duration = content_item.metadata.get("duration_seconds", 600) if content_item.metadata else 600

        # Get AI suggestions for clip moments
        clips = await self._identify_video_highlights(
            content=text_content,
            duration=duration,
            count=clip_count,
        )

        results = []
        for clip in clips:
            for platform in platforms:
                max_duration = self.PLATFORM_LIMITS.get(platform, {}).get("video_max_seconds", 60)

                # Adjust clip duration for platform
                clip_duration = min(clip["duration"], max_duration)

                results.append(RepurposeResult(
                    source_id=content_id,
                    source_type="video",
                    output_type="short_clip",
                    content={
                        "start_seconds": clip["start"],
                        "end_seconds": clip["start"] + clip_duration,
                        "hook": clip["hook"],
                        "caption": self._truncate_for_platform(
                            clip["caption"],
                            platform,
                            "caption"
                        ),
                    },
                    platform=platform,
                    metadata={"virality_score": clip.get("score", 5)},
                ))

        return results

    # =========================================================================
    # TEXT/BLOG REPURPOSING
    # =========================================================================

    async def blog_to_twitter_thread(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        max_tweets: int = 10,
    ) -> RepurposeResult:
        """
        Convert blog post to Twitter/X thread.
        """
        # Get content
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id,
            )
        )
        content_item = result.scalar_one_or_none()
        if not content_item:
            raise ValueError("Content not found")

        if not content_item.content:
            raise ValueError("Content has no text to convert")

        client = await self._get_llm_client()

        prompt = f"""Convert this blog post into a Twitter thread (max {max_tweets} tweets).

BLOG POST:
{content_item.content[:5000]}

Requirements:
1. First tweet must be a strong hook
2. Each tweet max 280 characters
3. Use thread numbering (1/, 2/, etc.)
4. End with a call to action
5. Make it engaging and shareable

Return as JSON array of tweet strings."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral Twitter thread writer who creates engaging, shareable content.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        import json
        tweets = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                tweets = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        # Ensure tweets are within limit
        tweets = [t[:280] for t in tweets[:max_tweets]]

        return RepurposeResult(
            source_id=content_id,
            source_type="blog_post",
            output_type="twitter_thread",
            content={"tweets": tweets, "tweet_count": len(tweets)},
            platform="twitter",
            metadata={"original_title": content_item.title},
        )

    async def blog_to_linkedin_post(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        style: str = "professional",
    ) -> RepurposeResult:
        """
        Convert blog post to LinkedIn-optimized post.
        """
        # Get content
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id,
            )
        )
        content_item = result.scalar_one_or_none()
        if not content_item:
            raise ValueError("Content not found")

        if not content_item.content:
            raise ValueError("Content has no text to convert")

        client = await self._get_llm_client()

        prompt = f"""Convert this blog post into a LinkedIn post.

BLOG POST:
{content_item.content[:4000]}

Style: {style}

LinkedIn post requirements:
1. Strong opening hook (first 2-3 lines visible before "see more")
2. Use line breaks for readability
3. Include 3-5 relevant hashtags at the end
4. Professional but personable tone
5. Max 3000 characters
6. End with engagement question or CTA

Return as JSON with keys: content, hashtags (array)"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a LinkedIn content strategist who creates viral professional posts.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        import json
        post_data = {}
        try:
            response_text = response.choices[0].message.content
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                post_data = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            post_data = {
                "content": content_item.content[:3000],
                "hashtags": [],
            }

        return RepurposeResult(
            source_id=content_id,
            source_type="blog_post",
            output_type="linkedin_post",
            content=post_data,
            platform="linkedin",
            metadata={"original_title": content_item.title},
        )

    async def blog_to_carousel(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        slide_count: int = 10,
        platform: str = "instagram",
    ) -> RepurposeResult:
        """
        Convert blog post to carousel slides (Instagram/LinkedIn).
        """
        # Get content
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id,
            )
        )
        content_item = result.scalar_one_or_none()
        if not content_item:
            raise ValueError("Content not found")

        if not content_item.content:
            raise ValueError("Content has no text to convert")

        max_slides = self.PLATFORM_LIMITS.get(platform, {}).get("carousel_max", 10)
        slide_count = min(slide_count, max_slides)

        client = await self._get_llm_client()

        prompt = f"""Convert this blog post into {slide_count} carousel slides for {platform}.

BLOG POST:
{content_item.content[:4000]}

For each slide provide:
1. Headline (max 50 chars)
2. Body text (max 150 chars)
3. Suggested visual type (text-only, icon, photo, chart)

First slide: Hook/title
Last slide: Call to action

Return as JSON array of objects with keys: headline, body, visual_type"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {platform} carousel expert who creates engaging, swipeable content.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        import json
        slides = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                slides = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        return RepurposeResult(
            source_id=content_id,
            source_type="blog_post",
            output_type="carousel",
            content={"slides": slides[:slide_count]},
            platform=platform,
            metadata={
                "original_title": content_item.title,
                "slide_count": len(slides[:slide_count]),
            },
        )

    # =========================================================================
    # BATCH REPURPOSING
    # =========================================================================

    async def repurpose_to_all_platforms(
        self,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
        content_type: str,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, List[RepurposeResult]]:
        """
        One-click repurpose content to all supported platforms.

        Returns dict of platform -> list of repurposed content.
        """
        results = {
            "twitter": [],
            "linkedin": [],
            "instagram": [],
            "tiktok": [],
            "facebook": [],
            "youtube_shorts": [],
            "blog": [],
            "newsletter": [],
        }

        if content_type == "podcast_episode":
            # Social posts for all platforms
            social_posts = await self.podcast_to_social_posts(
                episode_id=content_id,
                user_id=user_id,
                platforms=["twitter", "linkedin", "instagram", "facebook"],
                brand_voice_id=brand_voice_id,
            )
            for post in social_posts:
                if post.platform:
                    results[post.platform].append(post)

            # Quote cards for Instagram
            quote_cards = await self.podcast_to_quote_cards(
                episode_id=content_id,
                user_id=user_id,
            )
            results["instagram"].extend(quote_cards)

            # Blog post
            blog_post = await self.podcast_to_blog_post(
                episode_id=content_id,
                user_id=user_id,
                brand_voice_id=brand_voice_id,
            )
            results["blog"].append(blog_post)

            # Newsletter
            newsletter = await self.podcast_to_newsletter(
                episode_id=content_id,
                user_id=user_id,
                brand_voice_id=brand_voice_id,
            )
            results["newsletter"].append(newsletter)

        elif content_type == "blog_post":
            # Twitter thread
            thread = await self.blog_to_twitter_thread(
                content_id=content_id,
                user_id=user_id,
            )
            results["twitter"].append(thread)

            # LinkedIn post
            linkedin = await self.blog_to_linkedin_post(
                content_id=content_id,
                user_id=user_id,
            )
            results["linkedin"].append(linkedin)

            # Instagram carousel
            carousel = await self.blog_to_carousel(
                content_id=content_id,
                user_id=user_id,
                platform="instagram",
            )
            results["instagram"].append(carousel)

            # LinkedIn carousel
            linkedin_carousel = await self.blog_to_carousel(
                content_id=content_id,
                user_id=user_id,
                platform="linkedin",
            )
            results["linkedin"].append(linkedin_carousel)

        elif content_type == "video":
            # Short clips for all platforms
            shorts = await self.long_video_to_shorts(
                content_id=content_id,
                user_id=user_id,
            )
            for short in shorts:
                if short.platform:
                    results[short.platform].append(short)

        return results

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _generate_social_posts(
        self,
        content: str,
        title: str,
        platform: str,
        count: int,
        brand_voice: Optional[BrandVoice] = None,
    ) -> List[Dict]:
        """Generate platform-specific social posts."""
        client = await self._get_llm_client()

        char_limit = self.PLATFORM_LIMITS.get(platform, {}).get("text", 2200)

        brand_instructions = ""
        if brand_voice:
            brand_instructions = f"\nBrand voice: {brand_voice.tone}, personality: {', '.join(brand_voice.personality_traits or [])}"

        prompt = f"""Create {count} social media posts for {platform} based on this content.

TITLE: {title}
CONTENT:
{content[:3000]}
{brand_instructions}

Requirements for {platform}:
- Max {char_limit} characters per post
- Include relevant hashtags
- Each post should focus on a different key point/insight
- Make posts engaging and shareable
- Optimize for the platform's algorithm (engagement-focused)

Return as JSON array of objects with keys: text, hashtags (array)"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {platform} content strategist creating viral posts.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.8,
        )

        import json
        posts = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                posts = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        return posts[:count]

    async def _extract_quotes(
        self,
        content: str,
        count: int,
    ) -> List[Dict]:
        """Extract quotable moments from content."""
        client = await self._get_llm_client()

        prompt = f"""Extract the {count} most quotable moments from this content.

CONTENT:
{content[:4000]}

For each quote identify:
1. The exact quote text (max 200 characters)
2. Speaker name if mentioned
3. Mood/emotion (inspiring, controversial, funny, insightful)
4. Virality score (1-10)

Return as JSON array with keys: text, speaker, mood, score"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at identifying viral-worthy quotes and soundbites.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        import json
        quotes = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                quotes = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        return quotes[:count]

    async def _generate_blog_post(
        self,
        content: str,
        title: str,
        show_notes: Optional[str],
        chapters: Optional[List],
        include_timestamps: bool,
        brand_voice: Optional[BrandVoice] = None,
    ) -> Dict:
        """Generate full blog post from transcript/script."""
        client = await self._get_llm_client()

        brand_instructions = ""
        if brand_voice:
            brand_instructions = f"\nBrand voice: {brand_voice.tone}"

        chapters_str = ""
        if chapters and include_timestamps:
            chapters_str = "\nChapters: " + str(chapters)

        prompt = f"""Convert this podcast content into a full blog post.

TITLE: {title}
CONTENT:
{content[:6000]}
{chapters_str}
{brand_instructions}

Create a comprehensive blog post with:
1. SEO-optimized title
2. Meta description (150 chars)
3. Introduction hook
4. Main content with H2 headers
5. Key takeaways section
6. Conclusion with CTA

Format the content in Markdown.

Return as JSON with keys: seo_title, meta_description, content (markdown)"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an SEO expert and blog writer creating engaging, searchable content.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=4000,
            temperature=0.7,
        )

        import json
        blog_post = {}
        try:
            response_text = response.choices[0].message.content
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                blog_post = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            blog_post = {
                "seo_title": title,
                "meta_description": content[:150],
                "content": content,
            }

        return blog_post

    async def _identify_video_highlights(
        self,
        content: str,
        duration: int,
        count: int,
    ) -> List[Dict]:
        """Identify best moments in video for clips."""
        client = await self._get_llm_client()

        prompt = f"""Analyze this video content and identify the {count} best moments for short-form clips.

VIDEO TRANSCRIPT/DESCRIPTION:
{content[:4000]}

Total video duration: {duration} seconds

For each highlight provide:
1. Approximate start time (seconds)
2. Suggested duration (15-60 seconds)
3. Hook text (first line to grab attention)
4. Caption for the clip
5. Virality score (1-10)

Look for:
- Surprising statements
- Emotional moments
- Actionable tips
- Quotable soundbites
- Controversial takes

Return as JSON array with keys: start, duration, hook, caption, score"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral video editor who identifies the most engaging moments.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        import json
        highlights = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                highlights = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        # Ensure valid timestamps
        for h in highlights:
            h["start"] = max(0, min(h.get("start", 0), duration - 15))
            h["duration"] = max(15, min(h.get("duration", 30), 60))

        return highlights[:count]

    def _truncate_for_platform(
        self,
        text: str,
        platform: str,
        field: str = "text",
    ) -> str:
        """Truncate text to platform limits."""
        limits = self.PLATFORM_LIMITS.get(platform, {})
        limit = limits.get(field, limits.get("text", 2200))

        if len(text) <= limit:
            return text

        # Truncate with ellipsis
        return text[:limit - 3] + "..."
