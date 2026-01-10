"""
AI Orchestrator

Central orchestration layer for all AI operations.
Manages chains, caching, and fallbacks.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content import BrandVoice, ContentTemplate, ContentType
from app.ai.chains.content_chain import ContentGenerationChain
from app.ai.chains.repurpose_chain import ContentRepurposeChain
from app.ai.chains.podcast_chain import PodcastScriptChain

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Central AI orchestration service.

    Manages all AI chains and provides a unified interface
    for content generation across the platform.
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        model: str = "gpt-4-turbo-preview",
    ):
        self.db = db
        self.model = model

        # Initialize chains
        self.content_chain = ContentGenerationChain(model=model)
        self.repurpose_chain = ContentRepurposeChain(model=model)
        self.podcast_chain = PodcastScriptChain(model=model)

    async def _get_brand_voice(
        self,
        brand_voice_id: uuid.UUID,
    ) -> Optional[BrandVoice]:
        """Fetch brand voice from database."""
        if not self.db or not brand_voice_id:
            return None

        result = await self.db.execute(
            select(BrandVoice).where(BrandVoice.id == brand_voice_id)
        )
        return result.scalar_one_or_none()

    async def _get_template(
        self,
        template_id: uuid.UUID,
    ) -> Optional[ContentTemplate]:
        """Fetch template from database."""
        if not self.db or not template_id:
            return None

        result = await self.db.execute(
            select(ContentTemplate).where(ContentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    # ==================== Content Generation ====================

    async def generate_content(
        self,
        topic: str,
        content_type: ContentType,
        brand_voice_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        target_platforms: Optional[List[str]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate content using LangChain.

        Args:
            topic: Main topic/subject
            content_type: Type of content to generate
            brand_voice_id: Optional brand voice ID
            template_id: Optional template ID
            target_platforms: Target platforms for optimization
            additional_context: Extra context

        Returns:
            Dict with title, content, and metadata
        """
        # Fetch brand voice and template
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None
        template = await self._get_template(template_id) if template_id else None

        logger.info(
            f"Generating {content_type.value} content for topic: {topic[:50]}..."
        )

        result = await self.content_chain.generate(
            topic=topic,
            content_type=content_type,
            brand_voice=brand_voice,
            template=template,
            target_platforms=target_platforms,
            additional_context=additional_context,
        )

        logger.info(f"Generated content: {result['title'][:50]}...")
        return result

    async def generate_content_stream(
        self,
        topic: str,
        content_type: ContentType,
        brand_voice_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        target_platforms: Optional[List[str]] = None,
    ) -> AsyncIterator[str]:
        """Stream content generation."""
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None
        template = await self._get_template(template_id) if template_id else None

        async for chunk in self.content_chain.generate_stream(
            topic=topic,
            content_type=content_type,
            brand_voice=brand_voice,
            template=template,
            target_platforms=target_platforms,
        ):
            yield chunk

    async def generate_variations(
        self,
        topic: str,
        content_type: ContentType,
        count: int = 3,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple content variations for A/B testing."""
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None

        return await self.content_chain.generate_variations(
            topic=topic,
            content_type=content_type,
            count=count,
            brand_voice=brand_voice,
        )

    # ==================== Content Repurposing ====================

    async def repurpose_content(
        self,
        content: str,
        source_type: ContentType,
        target_type: ContentType,
        preserve_tone: bool = True,
    ) -> Dict[str, Any]:
        """Transform content from one format to another."""
        return await self.repurpose_chain.repurpose(
            content=content,
            source_type=source_type,
            target_type=target_type,
            preserve_tone=preserve_tone,
        )

    async def repurpose_to_all(
        self,
        content: str,
        source_type: ContentType,
        exclude_types: Optional[List[ContentType]] = None,
    ) -> List[Dict[str, Any]]:
        """Repurpose content to all available formats."""
        exclude = exclude_types or []

        target_types = [
            t for t in ContentType
            if t != source_type and t not in exclude
        ]

        return await self.repurpose_chain.repurpose_batch(
            content=content,
            source_type=source_type,
            target_types=target_types,
        )

    async def extract_clips(
        self,
        content: str,
        clip_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Extract short clips from long-form content."""
        return await self.repurpose_chain.extract_clips(
            content=content,
            clip_count=clip_count,
        )

    async def create_quote_cards(
        self,
        content: str,
        count: int = 5,
    ) -> List[Dict[str, str]]:
        """Extract quotable moments for social media."""
        return await self.repurpose_chain.create_quote_cards(
            content=content,
            count=count,
        )

    # ==================== Podcast Generation ====================

    async def generate_podcast_script(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,
        brand_voice_id: Optional[uuid.UUID] = None,
        include_intro: bool = True,
        include_outro: bool = True,
        outline: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a complete podcast script."""
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None

        return await self.podcast_chain.generate_script(
            topic=topic,
            style=style,
            duration_target=duration_target,
            brand_voice=brand_voice,
            include_intro=include_intro,
            include_outro=include_outro,
            outline=outline,
        )

    async def generate_podcast_script_stream(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> AsyncIterator[str]:
        """Stream podcast script generation."""
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None

        async for chunk in self.podcast_chain.generate_script_stream(
            topic=topic,
            style=style,
            duration_target=duration_target,
            brand_voice=brand_voice,
        ):
            yield chunk

    async def generate_show_notes(
        self,
        script: str,
        topic: str,
    ) -> str:
        """Generate show notes from a podcast script."""
        return await self.podcast_chain.generate_show_notes(
            script=script,
            topic=topic,
        )

    async def find_clip_moments(
        self,
        script: str,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find the best clip-worthy moments in a podcast."""
        return await self.podcast_chain.find_clip_moments(
            script=script,
            count=count,
        )

    async def improve_script(
        self,
        script: str,
        feedback: str,
    ) -> str:
        """Improve a script based on feedback."""
        return await self.podcast_chain.improve_script(
            script=script,
            feedback=feedback,
        )

    # ==================== Batch Operations ====================

    async def batch_generate(
        self,
        topics: List[str],
        content_type: ContentType,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Generate content for multiple topics."""
        brand_voice = await self._get_brand_voice(brand_voice_id) if brand_voice_id else None

        results = []
        for topic in topics:
            result = await self.content_chain.generate(
                topic=topic,
                content_type=content_type,
                brand_voice=brand_voice,
            )
            results.append(result)

        return results

    # ==================== Content Calendar ====================

    async def generate_content_calendar(
        self,
        theme: str,
        days: int = 7,
        content_types: Optional[List[ContentType]] = None,
        brand_voice_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate a week's worth of content ideas.

        Returns a list of content suggestions with topics and types.
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_openai import ChatOpenAI

        types_str = ", ".join([t.value for t in (content_types or list(ContentType)[:4])])

        prompt = ChatPromptTemplate.from_template("""Create a {days}-day content calendar for the theme: {theme}

Content types to use: {types}

For each day, provide:
1. Content type
2. Topic/angle
3. Hook/headline
4. Key points to cover

Format:
DAY 1:
Type: [type]
Topic: [topic]
Hook: [hook]
Points: [bullet points]

Continue for all {days} days. Vary the content types and make each day unique and engaging.""")

        llm = ChatOpenAI(model=self.model, api_key=settings.openai_api_key)
        chain = prompt | llm | StrOutputParser()

        result = await chain.ainvoke({
            "days": days,
            "theme": theme,
            "types": types_str,
        })

        # Parse the calendar
        calendar = []
        current_day = None

        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("DAY"):
                if current_day:
                    calendar.append(current_day)
                current_day = {"day": len(calendar) + 1}
            elif current_day:
                if line.startswith("Type:"):
                    current_day["content_type"] = line[5:].strip()
                elif line.startswith("Topic:"):
                    current_day["topic"] = line[6:].strip()
                elif line.startswith("Hook:"):
                    current_day["hook"] = line[5:].strip()
                elif line.startswith("Points:"):
                    current_day["points"] = line[7:].strip()

        if current_day:
            calendar.append(current_day)

        return calendar[:days]
