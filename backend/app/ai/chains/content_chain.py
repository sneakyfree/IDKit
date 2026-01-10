"""
Content Generation Chain

LangChain-based content generation with brand voice integration.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.content import BrandVoice, ContentTemplate, ContentType

logger = logging.getLogger(__name__)


class ContentGenerationChain:
    """
    LangChain-based content generation chain.

    Supports:
    - Multiple content types (video scripts, social posts, blogs, etc.)
    - Brand voice integration
    - Template-based generation
    - Streaming output
    """

    # System prompts for each content type
    SYSTEM_PROMPTS = {
        ContentType.VIDEO_SCRIPT: """You are an expert video scriptwriter for YouTube and similar platforms.
Create engaging, well-structured video scripts that:
- Hook viewers in the first 5 seconds
- Have clear sections (intro, main content, call-to-action)
- Include visual cues and b-roll suggestions in [brackets]
- Use conversational language that's easy to deliver on camera
- End with a strong call-to-action""",

        ContentType.SHORT_SCRIPT: """You are an expert short-form video creator for TikTok, Reels, and Shorts.
Create punchy, hook-driven scripts that:
- Start with an irresistible hook (pattern interrupt, controversial take, or surprising fact)
- Get to the point immediately - no fluff
- Use trending formats and structures
- Are optimized for 15-60 second videos
- Include text overlay suggestions in [brackets]""",

        ContentType.BLOG_POST: """You are an expert blog writer and SEO specialist.
Create informative, engaging blog posts that:
- Have compelling headlines and subheadings
- Use the inverted pyramid structure (key info first)
- Include relevant keywords naturally
- Have scannable formatting with bullet points and short paragraphs
- End with a clear conclusion or call-to-action""",

        ContentType.SOCIAL_POST: """You are a social media expert who drives engagement.
Create posts that:
- Are optimized for the target platform's algorithm
- Include relevant hashtags
- Use power words and emotional triggers
- Have a clear call-to-action
- Are concise and impactful""",

        ContentType.EMAIL: """You are an email marketing expert with high conversion rates.
Create emails that:
- Have compelling subject lines
- Use the AIDA framework (Attention, Interest, Desire, Action)
- Are personalized and conversational
- Have a single, clear call-to-action
- Are optimized for mobile reading""",

        ContentType.PODCAST_SCRIPT: """You are a podcast producer creating engaging audio content.
Create podcast scripts that:
- Have natural, conversational flow
- Include clear transitions between sections
- Mark [PAUSE] for dramatic effect where appropriate
- Are easy to read aloud without stumbling
- Include intro and outro segments""",

        ContentType.CAROUSEL: """You are a carousel content creator for Instagram and LinkedIn.
Create slide-by-slide content that:
- Has a hook on slide 1 that makes people swipe
- Tells a story or provides value across 5-10 slides
- Uses one key point per slide
- Ends with a strong CTA on the last slide
- Includes text suggestions for each slide in numbered format""",

        ContentType.THREAD: """You are a Twitter/X thread expert who goes viral.
Create engaging threads that:
- Start with a killer hook tweet that demands attention
- Build curiosity and momentum tweet by tweet
- Use numbers, lists, and clear structure
- Include a recap or key takeaway at the end
- End with engagement prompts (saves, retweets, follows)""",
    }

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or settings.openai_api_key

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.api_key,
            streaming=True,
        )

    def _build_brand_voice_instructions(self, brand_voice: BrandVoice) -> str:
        """Build brand voice instructions for the prompt."""
        instructions = ["\n## Brand Voice Guidelines"]
        instructions.append(f"- **Tone**: {brand_voice.tone}")
        instructions.append(f"- **Sentence Style**: {brand_voice.sentence_style}")
        instructions.append(f"- **Vocabulary Level**: {brand_voice.vocabulary_level}")

        if brand_voice.personality_traits:
            traits = ", ".join(brand_voice.personality_traits)
            instructions.append(f"- **Personality**: {traits}")

        if brand_voice.use_emojis:
            instructions.append(f"- **Emoji Usage**: {brand_voice.emoji_frequency}")
        else:
            instructions.append("- **Emojis**: Do not use emojis")

        if brand_voice.avoid_words:
            avoid = ", ".join(brand_voice.avoid_words)
            instructions.append(f"- **Avoid These Words**: {avoid}")

        if brand_voice.key_phrases:
            phrases = ", ".join(brand_voice.key_phrases)
            instructions.append(f"- **Key Phrases to Include**: {phrases}")

        if brand_voice.examples:
            instructions.append(f"- **Example of Voice**: {brand_voice.examples[0]}")

        return "\n".join(instructions)

    def _build_template_instructions(self, template: ContentTemplate) -> str:
        """Build template instructions for the prompt."""
        return f"\n## Template Structure\nFollow this template:\n{template.template_body}"

    def _build_platform_instructions(self, platforms: List[str]) -> str:
        """Build platform-specific instructions."""
        platform_tips = {
            "youtube": "Optimize for YouTube SEO with keyword-rich titles and descriptions",
            "tiktok": "Use trending sounds/format references, keep it punchy",
            "instagram": "Include relevant hashtags, optimize for Reels/carousel format",
            "twitter": "Keep tweets under 280 chars, use threads for longer content",
            "linkedin": "Professional tone, thought leadership angle, tag relevant people/companies",
            "facebook": "Encourage shares and comments, include questions",
        }

        instructions = ["\n## Platform Optimization"]
        for platform in platforms:
            if platform.lower() in platform_tips:
                instructions.append(f"- **{platform.title()}**: {platform_tips[platform.lower()]}")

        return "\n".join(instructions)

    def build_chain(
        self,
        content_type: ContentType,
        brand_voice: Optional[BrandVoice] = None,
        template: Optional[ContentTemplate] = None,
        target_platforms: Optional[List[str]] = None,
        max_tokens: int = 2000,
    ):
        """Build the generation chain for a specific content type."""
        # Get system prompt for content type
        system_prompt = self.SYSTEM_PROMPTS.get(
            content_type,
            "You are an expert content creator. Generate high-quality content."
        )

        # Build complete system message
        system_parts = [system_prompt]

        if brand_voice:
            system_parts.append(self._build_brand_voice_instructions(brand_voice))

        if template:
            system_parts.append(self._build_template_instructions(template))

        if target_platforms:
            system_parts.append(self._build_platform_instructions(target_platforms))

        system_parts.append("\n## Output Format")
        system_parts.append("Start with a clear, compelling title on the first line.")
        system_parts.append("Then provide the main content below.")

        full_system = "\n".join(system_parts)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", full_system),
            ("human", "{topic}"),
        ])

        # Build chain with output parser
        chain = prompt | self.llm | StrOutputParser()

        return chain

    async def generate(
        self,
        topic: str,
        content_type: ContentType,
        brand_voice: Optional[BrandVoice] = None,
        template: Optional[ContentTemplate] = None,
        target_platforms: Optional[List[str]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate content using the chain.

        Returns:
            Dict with 'title' and 'content' keys.
        """
        chain = self.build_chain(
            content_type=content_type,
            brand_voice=brand_voice,
            template=template,
            target_platforms=target_platforms,
        )

        # Build input
        input_text = topic
        if additional_context:
            input_text = f"{topic}\n\nAdditional context: {additional_context}"

        # Generate
        result = await chain.ainvoke({"topic": input_text})

        # Parse title and content
        lines = result.strip().split("\n", 1)
        if len(lines) == 1:
            title = lines[0][:100]
            content = lines[0]
        else:
            title = lines[0].strip().lstrip("#").strip()
            content = lines[1].strip()

        return {
            "title": title,
            "content": content,
            "raw": result,
            "content_type": content_type.value,
        }

    async def generate_stream(
        self,
        topic: str,
        content_type: ContentType,
        brand_voice: Optional[BrandVoice] = None,
        template: Optional[ContentTemplate] = None,
        target_platforms: Optional[List[str]] = None,
        additional_context: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream content generation for real-time display.

        Yields chunks of generated text.
        """
        chain = self.build_chain(
            content_type=content_type,
            brand_voice=brand_voice,
            template=template,
            target_platforms=target_platforms,
        )

        # Build input
        input_text = topic
        if additional_context:
            input_text = f"{topic}\n\nAdditional context: {additional_context}"

        # Stream
        async for chunk in chain.astream({"topic": input_text}):
            yield chunk

    async def generate_variations(
        self,
        topic: str,
        content_type: ContentType,
        count: int = 3,
        brand_voice: Optional[BrandVoice] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple variations of content.

        Useful for A/B testing.
        """
        # Create a higher temperature LLM for variations
        variation_llm = ChatOpenAI(
            model=self.model,
            temperature=0.9,  # Higher temperature for diversity
            api_key=self.api_key,
        )

        results = []
        for i in range(count):
            result = await self.generate(
                topic=f"{topic} (Variation {i + 1}: Be creative and unique)",
                content_type=content_type,
                brand_voice=brand_voice,
            )
            result["variation_number"] = i + 1
            results.append(result)

        return results
