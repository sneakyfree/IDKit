"""
Content Repurposing Chain

LangChain-based content transformation across formats.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.models.content import ContentType

logger = logging.getLogger(__name__)


class ContentRepurposeChain:
    """
    LangChain-based content repurposing chain.

    Transforms content from one format to another while
    maintaining the core message and brand voice.
    """

    # Transformation prompts
    REPURPOSE_PROMPTS = {
        ContentType.VIDEO_SCRIPT: """Transform the following content into an engaging video script.

Original Content:
{content}

Create a video script that:
1. Has a hook in the first 5 seconds
2. Includes visual cues in [brackets]
3. Has clear sections (intro, main points, CTA)
4. Is conversational and easy to deliver on camera
5. Ends with a call-to-action

Video Script:""",

        ContentType.SHORT_SCRIPT: """Transform the following content into a punchy short-form video script.

Original Content:
{content}

Create a 15-60 second script that:
1. Starts with an attention-grabbing hook
2. Gets to the main point immediately
3. Is perfect for TikTok, Reels, or Shorts
4. Includes text overlay suggestions in [brackets]
5. Has a memorable ending

Short Script:""",

        ContentType.BLOG_POST: """Transform the following content into a well-structured blog post.

Original Content:
{content}

Create a blog post that:
1. Has an SEO-friendly headline
2. Uses scannable formatting with subheadings
3. Includes bullet points for key information
4. Has an introduction, body, and conclusion
5. Ends with a call-to-action

Blog Post:""",

        ContentType.SOCIAL_POST: """Transform the following content into an engaging social media post.

Original Content:
{content}

Create a social post that:
1. Captures attention in the first line
2. Is concise and impactful
3. Includes relevant hashtags
4. Has a clear call-to-action
5. Is optimized for engagement

Social Post:""",

        ContentType.EMAIL: """Transform the following content into a compelling email.

Original Content:
{content}

Create an email that:
1. Has a subject line that gets opens
2. Has a personalized greeting
3. Uses the AIDA framework
4. Has a single, clear call-to-action
5. Is optimized for mobile reading

Email:""",

        ContentType.CAROUSEL: """Transform the following content into an Instagram/LinkedIn carousel.

Original Content:
{content}

Create a carousel with 5-10 slides:
1. Slide 1: Hook that makes people want to swipe
2. Slides 2-8: One key point per slide
3. Final slide: Strong call-to-action

Format each slide as:
[Slide N]
Title: ...
Text: ...

Carousel:""",

        ContentType.THREAD: """Transform the following content into a Twitter/X thread.

Original Content:
{content}

Create a thread with 5-10 tweets:
1. Tweet 1: Hook that stops the scroll
2. Tweets 2-8: Build the story/argument
3. Final tweet: Summary and CTA

Format each tweet as:
Tweet N/Total:
[tweet content under 280 chars]

Thread:""",

        ContentType.PODCAST_SCRIPT: """Transform the following content into a podcast script.

Original Content:
{content}

Create a podcast script that:
1. Has a conversational, natural flow
2. Includes intro music cue: [INTRO MUSIC]
3. Marks pauses for effect: [PAUSE]
4. Has smooth transitions between topics
5. Includes outro with CTA

Podcast Script:""",
    }

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.6,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or settings.openai_api_key

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.api_key,
        )

    async def repurpose(
        self,
        content: str,
        source_type: ContentType,
        target_type: ContentType,
        preserve_tone: bool = True,
    ) -> Dict[str, Any]:
        """
        Repurpose content from one type to another.

        Args:
            content: Original content to transform
            source_type: Original content type
            target_type: Target content type
            preserve_tone: Whether to maintain the original tone

        Returns:
            Dict with transformed content
        """
        # Get the repurpose prompt
        prompt_template = self.REPURPOSE_PROMPTS.get(
            target_type,
            "Transform the following content:\n\n{content}\n\nNew format:"
        )

        # Add tone preservation instruction if needed
        if preserve_tone:
            prompt_template = f"""Maintain the original tone and voice while transforming.

{prompt_template}"""

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({"content": content})

        # Parse title and content
        lines = result.strip().split("\n", 1)
        if len(lines) == 1:
            title = f"Repurposed {target_type.value}"
            body = lines[0]
        else:
            title = lines[0].strip().lstrip("#").strip()
            body = lines[1].strip()

        return {
            "title": title,
            "content": body,
            "raw": result,
            "source_type": source_type.value,
            "target_type": target_type.value,
        }

    async def repurpose_batch(
        self,
        content: str,
        source_type: ContentType,
        target_types: List[ContentType],
    ) -> List[Dict[str, Any]]:
        """
        Repurpose content to multiple formats at once.

        Args:
            content: Original content
            source_type: Original content type
            target_types: List of target types

        Returns:
            List of repurposed content dicts
        """
        results = []
        for target_type in target_types:
            result = await self.repurpose(
                content=content,
                source_type=source_type,
                target_type=target_type,
            )
            results.append(result)

        return results

    async def extract_clips(
        self,
        content: str,
        clip_count: int = 5,
        clip_format: ContentType = ContentType.SHORT_SCRIPT,
    ) -> List[Dict[str, Any]]:
        """
        Extract multiple short clips from longer content.

        Useful for creating TikTok/Reels from podcasts or long videos.
        """
        prompt = ChatPromptTemplate.from_template("""Analyze this content and extract {count} standalone clips.

Content:
{content}

For each clip:
1. Find the most engaging, shareable moments
2. Each clip should work as a standalone piece
3. Include a hook and clear ending
4. Format for short-form video

Return {count} clips in this format:
---
CLIP 1: [Catchy Title]
[Content of the clip]

CLIP 2: [Catchy Title]
[Content of the clip]
---

Clips:""")

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "content": content,
            "count": clip_count,
        })

        # Parse clips
        clips = []
        current_clip = None

        for line in result.split("\n"):
            if line.strip().startswith("CLIP"):
                if current_clip:
                    clips.append(current_clip)
                # Extract title from "CLIP N: Title" format
                parts = line.split(":", 1)
                title = parts[1].strip() if len(parts) > 1 else f"Clip {len(clips) + 1}"
                current_clip = {"title": title, "content": ""}
            elif current_clip:
                current_clip["content"] += line + "\n"

        if current_clip:
            clips.append(current_clip)

        # Clean up content
        for clip in clips:
            clip["content"] = clip["content"].strip()

        return clips[:clip_count]

    async def create_quote_cards(
        self,
        content: str,
        count: int = 5,
    ) -> List[Dict[str, str]]:
        """
        Extract quotable moments for social media quote cards.
        """
        prompt = ChatPromptTemplate.from_template("""Extract {count} powerful, quotable statements from this content.

Content:
{content}

Requirements:
1. Each quote should be impactful and shareable
2. Keep quotes under 150 characters for social media
3. Select statements that stand alone without context
4. Focus on insights, wisdom, or emotional moments

Return in this format:
QUOTE 1: [quote text]
QUOTE 2: [quote text]
...

Quotes:""")

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "content": content,
            "count": count,
        })

        # Parse quotes
        quotes = []
        for line in result.split("\n"):
            if line.strip().startswith("QUOTE"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    quote_text = parts[1].strip().strip('"').strip("'")
                    quotes.append({
                        "text": quote_text,
                        "character_count": len(quote_text),
                    })

        return quotes[:count]
