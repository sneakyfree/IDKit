"""
Podcast Script Generator

AI-powered podcast script generation using LangChain.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.content import BrandVoice
from app.ai.chains.podcast_chain import PodcastScriptChain

logger = logging.getLogger(__name__)


class PodcastScriptGenerator:
    """
    AI-powered podcast script generation.

    Uses LangChain for intelligent script generation
    with multiple podcast styles and durations.
    """

    STYLES = {
        "conversational": "casual, friendly tone with natural pauses and filler words",
        "educational": "informative, structured with clear explanations and examples",
        "storytelling": "narrative arc with engaging hooks and emotional beats",
        "interview": "Q&A format with insightful questions and follow-ups",
        "news": "professional, fact-focused delivery with clear segments",
        "comedy": "humorous, entertaining with jokes and wit",
        "motivational": "inspiring, uplifting with actionable takeaways",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._podcast_chain = None

    @property
    def podcast_chain(self) -> PodcastScriptChain:
        """Get or create podcast chain."""
        if self._podcast_chain is None:
            self._podcast_chain = PodcastScriptChain()
        return self._podcast_chain

    async def generate(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,  # 10 minutes
        brand_voice_id: Optional[uuid.UUID] = None,
        outline: Optional[List[str]] = None,
        include_intro: bool = True,
        include_outro: bool = True,
        guest_name: Optional[str] = None,
    ) -> dict:
        """
        Generate a complete podcast script using LangChain.

        Args:
            topic: Main topic/subject
            style: Script style (conversational, educational, etc.)
            duration_target: Target duration in seconds
            brand_voice_id: Optional brand voice for styling
            outline: Optional outline points
            include_intro: Include intro segment
            include_outro: Include outro segment
            guest_name: Name of guest (for interview style)

        Returns:
            dict with script content and metadata
        """
        logger.info(f"Generating {style} podcast script for: {topic[:50]}...")

        # Get brand voice if specified
        brand_voice = None
        if brand_voice_id:
            result = await self.db.execute(
                select(BrandVoice).where(BrandVoice.id == brand_voice_id)
            )
            brand_voice = result.scalar_one_or_none()

        # Adjust topic for interview style
        full_topic = topic
        if guest_name and style == "interview":
            full_topic = f"Interview with {guest_name} about: {topic}"

        # Use LangChain podcast chain
        result = await self.podcast_chain.generate_script(
            topic=full_topic,
            style=style,
            duration_target=duration_target,
            brand_voice=brand_voice,
            include_intro=include_intro,
            include_outro=include_outro,
            outline=outline,
        )

        logger.info(f"Generated script with {result['word_count']} words")
        return result

    async def generate_outline(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,
    ) -> List[dict]:
        """
        Generate a podcast outline without full script.

        Useful for planning before full generation.
        """
        client = await self._get_llm_client()

        prompt = f"""Create a detailed podcast outline for a {duration_target // 60} minute episode about: {topic}

Style: {self.STYLES.get(style, 'conversational')}

Provide 5-8 main sections with:
- Section title
- Key talking points (2-3 each)
- Estimated duration

Format as a structured outline."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a podcast producer creating episode outlines.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        outline_text = response.choices[0].message.content

        # Parse outline into structured format
        sections = []
        current_section = None

        for line in outline_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check if it's a main section (starts with number or bullet)
            if line[0].isdigit() or line.startswith("-"):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": line.lstrip("0123456789.-) ").strip(),
                    "points": [],
                    "duration": 60,  # Default 1 minute
                }
            elif current_section and line.startswith(("•", "*", "-", "  ")):
                current_section["points"].append(line.lstrip("•*- ").strip())

        if current_section:
            sections.append(current_section)

        return sections

    async def generate_show_notes(
        self,
        script: str,
        topic: str,
    ) -> str:
        """Generate show notes from a podcast script using LangChain."""
        return await self.podcast_chain.generate_show_notes(
            script=script,
            topic=topic,
        )

    def _get_system_prompt(self, style: str) -> str:
        """Get system prompt for the specified style."""
        style_desc = self.STYLES.get(style, self.STYLES["conversational"])

        return f"""You are an expert podcast scriptwriter specializing in {style} podcasts.

Style guidelines: {style_desc}

Writing rules:
1. Write in natural spoken language, not written prose
2. Include natural pauses indicated by [PAUSE] or ...
3. Add emphasis cues like [EMPHASIS] for important points
4. Include verbal transitions between topics
5. Write for audio - use short sentences and clear language
6. Add personality and engagement hooks
7. Include calls to action where appropriate

Format the script with clear section headers and speaker cues if applicable."""

    def _build_prompt(
        self,
        topic: str,
        style: str,
        word_count: int,
        brand_voice: Optional[BrandVoice] = None,
        outline: Optional[List[str]] = None,
        include_intro: bool = True,
        include_outro: bool = True,
        guest_name: Optional[str] = None,
    ) -> str:
        """Build the generation prompt."""
        parts = []

        # Main instruction
        parts.append(f"Write a {word_count}-word podcast script about: {topic}")
        parts.append(f"\nStyle: {self.STYLES.get(style, 'conversational')}")

        # Outline if provided
        if outline:
            parts.append("\n\nFollow this outline:")
            for i, point in enumerate(outline, 1):
                parts.append(f"{i}. {point}")

        # Structure
        if include_intro:
            parts.append("\n\nInclude an engaging intro that hooks the listener immediately.")

        if include_outro:
            parts.append("Include an outro with a call to action (subscribe, share, etc.)")

        # Guest handling
        if guest_name:
            parts.append(f"\n\nThis is an interview episode with guest: {guest_name}")
            parts.append("Format as a conversation between HOST and GUEST.")

        # Brand voice
        if brand_voice:
            parts.append(f"\n\nBrand Voice Guidelines:")
            parts.append(f"- Tone: {brand_voice.tone}")
            parts.append(f"- Personality: {', '.join(brand_voice.personality_traits) if brand_voice.personality_traits else 'friendly'}")

            if brand_voice.use_emojis and brand_voice.emoji_frequency != "none":
                parts.append("- Include verbal equivalents of emojis (enthusiasm, laughter)")

        # Final instructions
        parts.append("\n\nMake it engaging, natural, and ready to record!")

        return "\n".join(parts)

    def _parse_sections(self, script: str) -> List[dict]:
        """Parse script into sections based on headers."""
        sections = []
        current_section = None
        current_content = []

        for line in script.split("\n"):
            # Check for section headers (## Header or all caps lines)
            is_header = (
                line.startswith("##")
                or line.startswith("**")
                or (line.isupper() and len(line) > 3 and len(line) < 50)
                or line.startswith("[SECTION")
            )

            if is_header:
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": "\n".join(current_content).strip(),
                    })
                current_section = line.strip("#* []").strip()
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": "\n".join(current_content).strip(),
            })
        elif current_content:
            # No sections found, treat entire script as one section
            sections.append({
                "title": "Full Episode",
                "content": "\n".join(current_content).strip(),
            })

        return sections
