"""
Content Generation Service

AI-powered content generation using LangChain.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content import (
    BrandVoice,
    ContentItem,
    ContentStatus,
    ContentTemplate,
    ContentType,
    GenerationJob,
)
from app.ai.orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    AI-powered content generation service.

    Supports multiple content types with brand voice integration
    and template-based generation.
    """

    # Content type configurations
    TYPE_CONFIGS = {
        ContentType.VIDEO_SCRIPT: {
            "max_tokens": 2000,
            "system_prompt": "You are an expert video scriptwriter. Create engaging, well-structured video scripts.",
        },
        ContentType.SHORT_SCRIPT: {
            "max_tokens": 500,
            "system_prompt": "You are an expert short-form video creator. Write punchy, hook-driven scripts for TikTok/Reels/Shorts.",
        },
        ContentType.BLOG_POST: {
            "max_tokens": 3000,
            "system_prompt": "You are an expert blog writer. Create informative, SEO-friendly blog posts.",
        },
        ContentType.SOCIAL_POST: {
            "max_tokens": 300,
            "system_prompt": "You are a social media expert. Write engaging posts that drive engagement.",
        },
        ContentType.EMAIL: {
            "max_tokens": 1000,
            "system_prompt": "You are an email marketing expert. Write compelling emails with clear CTAs.",
        },
        ContentType.PODCAST_SCRIPT: {
            "max_tokens": 4000,
            "system_prompt": "You are a podcast producer. Create conversational, engaging podcast scripts.",
        },
        ContentType.CAROUSEL: {
            "max_tokens": 1500,
            "system_prompt": "You are a carousel content creator. Write slide-by-slide content for Instagram carousels.",
        },
        ContentType.THREAD: {
            "max_tokens": 2000,
            "system_prompt": "You are a Twitter/X thread expert. Write compelling multi-tweet threads.",
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._orchestrator = None

    @property
    def orchestrator(self) -> AIOrchestrator:
        """Get or create AI orchestrator."""
        if self._orchestrator is None:
            self._orchestrator = AIOrchestrator(db=self.db)
        return self._orchestrator

    async def generate_content(
        self,
        user_id: uuid.UUID,
        content_type: ContentType,
        topic: str,
        brand_voice_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        additional_context: Optional[str] = None,
        target_platforms: Optional[List[str]] = None,
        **kwargs,
    ) -> ContentItem:
        """
        Generate content using AI.

        Args:
            user_id: Owner of the content
            content_type: Type of content to generate
            topic: Main topic/subject
            brand_voice_id: Optional brand voice for styling
            template_id: Optional template to use
            additional_context: Extra context for generation
            target_platforms: Target platforms for optimization

        Returns:
            Generated ContentItem
        """
        # Create job for tracking
        job = GenerationJob(
            user_id=user_id,
            job_type="content",
            status="processing",
            input_params={
                "content_type": content_type.value,
                "topic": topic,
                "brand_voice_id": str(brand_voice_id) if brand_voice_id else None,
                "template_id": str(template_id) if template_id else None,
            },
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()

        try:
            # Use LangChain orchestrator for generation
            logger.info(f"Generating {content_type.value} content for topic: {topic[:50]}...")

            result = await self.orchestrator.generate_content(
                topic=topic,
                content_type=content_type,
                brand_voice_id=brand_voice_id,
                template_id=template_id,
                target_platforms=target_platforms,
                additional_context=additional_context,
            )

            title = result["title"]
            body = result["content"]

            # Create content item
            content = ContentItem(
                user_id=user_id,
                content_type=content_type.value,
                status=ContentStatus.READY.value,
                title=title,
                body=body,
                ai_generated=True,
                generation_prompt=topic,
                generation_params={
                    "content_type": content_type.value,
                    "brand_voice_id": str(brand_voice_id) if brand_voice_id else None,
                    "template_id": str(template_id) if template_id else None,
                },
                brand_voice_id=brand_voice_id,
                template_id=template_id,
                target_platforms=target_platforms or [],
            )

            self.db.add(content)

            # Update job
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            job.content_id = content.id
            job.output_data = {"content_id": str(content.id)}

            await self.db.commit()
            await self.db.refresh(content)

            return content

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise

    async def generate_content_stream(
        self,
        user_id: uuid.UUID,
        content_type: ContentType,
        topic: str,
        brand_voice_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        target_platforms: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream content generation for real-time display.

        Yields chunks of generated text as they're produced.
        """
        async for chunk in self.orchestrator.generate_content_stream(
            topic=topic,
            content_type=content_type,
            brand_voice_id=brand_voice_id,
            template_id=template_id,
            target_platforms=target_platforms,
        ):
            yield chunk

    async def generate_batch(
        self,
        user_id: uuid.UUID,
        content_type: ContentType,
        topics: List[str],
        brand_voice_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> List[ContentItem]:
        """
        Generate multiple content items in batch.
        """
        results = []
        for topic in topics:
            content = await self.generate_content(
                user_id=user_id,
                content_type=content_type,
                topic=topic,
                brand_voice_id=brand_voice_id,
                **kwargs,
            )
            results.append(content)
        return results

    async def repurpose_content(
        self,
        content_id: uuid.UUID,
        target_types: List[ContentType],
        user_id: uuid.UUID,
    ) -> List[ContentItem]:
        """
        Repurpose existing content into other formats.

        E.g., Blog post -> Social posts, threads, etc.
        Uses LangChain repurpose chain for intelligent transformation.
        """
        # Get original content
        result = await self.db.execute(
            select(ContentItem).where(
                ContentItem.id == content_id,
                ContentItem.user_id == user_id,
            )
        )
        original = result.scalar_one_or_none()
        if not original:
            raise ValueError("Content not found")

        logger.info(f"Repurposing content {content_id} to {len(target_types)} formats")

        # Get original content type
        source_type = ContentType(original.content_type)
        original_content = f"Title: {original.title}\n\n{original.body}"

        repurposed = []
        for target_type in target_types:
            # Use orchestrator for repurposing
            repurpose_result = await self.orchestrator.repurpose_content(
                content=original_content,
                source_type=source_type,
                target_type=target_type,
                preserve_tone=True,
            )

            content = ContentItem(
                user_id=user_id,
                content_type=target_type.value,
                status=ContentStatus.READY.value,
                title=repurpose_result["title"],
                body=repurpose_result["content"],
                ai_generated=True,
                generation_prompt=f"Repurposed from {original.id}",
                parent_id=original.id,
                brand_voice_id=original.brand_voice_id,
            )
            self.db.add(content)
            repurposed.append(content)

        await self.db.commit()
        for content in repurposed:
            await self.db.refresh(content)

        logger.info(f"Created {len(repurposed)} repurposed content items")
        return repurposed

    def _build_prompt(
        self,
        content_type: ContentType,
        topic: str,
        brand_voice: Optional[BrandVoice] = None,
        template: Optional[ContentTemplate] = None,
        additional_context: Optional[str] = None,
        target_platforms: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """Build the generation prompt."""
        parts = []

        # Topic instruction
        parts.append(f"Create {content_type.value} content about: {topic}")

        # Brand voice instructions
        if brand_voice:
            parts.append(f"\n\nBrand Voice Guidelines:")
            parts.append(f"- Tone: {brand_voice.tone}")
            parts.append(f"- Style: {brand_voice.sentence_style} sentences")
            parts.append(f"- Vocabulary: {brand_voice.vocabulary_level}")

            if brand_voice.personality_traits:
                parts.append(f"- Personality: {', '.join(brand_voice.personality_traits)}")

            if brand_voice.use_emojis:
                parts.append(f"- Emoji usage: {brand_voice.emoji_frequency}")
            else:
                parts.append("- No emojis")

            if brand_voice.avoid_words:
                parts.append(f"- Avoid these words: {', '.join(brand_voice.avoid_words)}")

        # Template instructions
        if template:
            parts.append(f"\n\nFollow this template structure:\n{template.template_body}")

        # Platform optimization
        if target_platforms:
            parts.append(f"\n\nOptimize for these platforms: {', '.join(target_platforms)}")

        # Additional context
        if additional_context:
            parts.append(f"\n\nAdditional context: {additional_context}")

        # Format instructions
        parts.append("\n\nFormat your response with a clear title on the first line, followed by the main content.")

        return "\n".join(parts)

    async def _call_llm(
        self,
        prompt: str,
        content_type: ContentType,
    ) -> str:
        """Call the LLM API."""
        config = self.TYPE_CONFIGS.get(content_type, {})
        client = await self._get_llm_client()

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": config.get("system_prompt", "")},
                {"role": "user", "content": prompt},
            ],
            max_tokens=config.get("max_tokens", 1000),
            temperature=0.7,
        )

        return response.choices[0].message.content

    def _parse_generated_content(
        self,
        text: str,
        content_type: ContentType,
    ) -> tuple[str, str]:
        """Parse generated text into title and body."""
        lines = text.strip().split("\n", 1)

        if len(lines) == 1:
            # No clear title/body separation
            title = lines[0][:100]
            body = lines[0]
        else:
            # First line is title, rest is body
            title = lines[0].strip().lstrip("#").strip()
            body = lines[1].strip()

        return title, body
