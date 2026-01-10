"""
Podcast Script Generation Chain

LangChain-based podcast script generation with multiple styles.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.models.content import BrandVoice

logger = logging.getLogger(__name__)


class PodcastSection(BaseModel):
    """A section of the podcast script."""
    title: str = Field(description="Section title")
    content: str = Field(description="Section content/script")
    duration_estimate: int = Field(description="Estimated duration in seconds")
    notes: Optional[str] = Field(default=None, description="Production notes")


class PodcastScript(BaseModel):
    """Complete podcast script structure."""
    title: str = Field(description="Episode title")
    hook: str = Field(description="Opening hook to grab attention")
    sections: List[PodcastSection] = Field(description="Main sections")
    outro: str = Field(description="Closing segment")
    show_notes: str = Field(description="Show notes summary")
    key_takeaways: List[str] = Field(description="Key points for listeners")


class PodcastScriptChain:
    """
    LangChain-based podcast script generation.

    Supports multiple styles:
    - Conversational (casual, friendly)
    - Educational (informative, structured)
    - Storytelling (narrative arc)
    - Interview (Q&A format)
    - News (professional, fact-focused)
    """

    STYLE_PROMPTS = {
        "conversational": """Create a casual, friendly podcast script.
- Use natural language as if talking to a friend
- Include casual transitions and personal anecdotes
- Add moments for natural pauses and reactions
- Keep energy upbeat but authentic""",

        "educational": """Create an informative, well-structured podcast script.
- Use clear explanations and examples
- Break complex topics into digestible parts
- Include definitions for technical terms
- Add recap moments to reinforce learning""",

        "storytelling": """Create a narrative-driven podcast script.
- Build a compelling story arc
- Include tension, climax, and resolution
- Use vivid descriptions and emotional beats
- Create cliffhangers between segments""",

        "interview": """Create a Q&A format podcast script.
- Include thoughtful, probing questions
- Leave space for follow-up questions
- Add transitional commentary
- Include both expected and surprising questions""",

        "news": """Create a professional, journalistic podcast script.
- Lead with the most important information
- Use objective, factual language
- Include expert quotes and citations
- Maintain credibility and authority""",
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

        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=self.api_key,
            streaming=True,
        )

    def _calculate_word_count(self, duration_seconds: int) -> int:
        """Calculate target word count from duration (avg 150 wpm)."""
        return int((duration_seconds / 60) * 150)

    async def generate_script(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,
        brand_voice: Optional[BrandVoice] = None,
        include_intro: bool = True,
        include_outro: bool = True,
        outline: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete podcast script.

        Args:
            topic: Main topic for the episode
            style: Script style (conversational, educational, etc.)
            duration_target: Target duration in seconds
            brand_voice: Optional brand voice for styling
            include_intro: Include intro segment
            include_outro: Include outro segment
            outline: Optional outline of sections to cover

        Returns:
            Dict with script content and metadata
        """
        word_count = self._calculate_word_count(duration_target)
        style_prompt = self.STYLE_PROMPTS.get(style, self.STYLE_PROMPTS["conversational"])

        # Build the prompt
        prompt_parts = [
            f"Create a podcast script about: {topic}",
            f"\nStyle: {style_prompt}",
            f"\nTarget length: approximately {word_count} words ({duration_target // 60} minutes)",
        ]

        if brand_voice:
            prompt_parts.append(f"\nBrand voice: {brand_voice.tone}, {brand_voice.sentence_style} sentences")

        if outline:
            prompt_parts.append(f"\nCover these points in order:\n" + "\n".join(f"- {point}" for point in outline))

        prompt_parts.append("""

Structure your script as follows:

# [Episode Title]

## HOOK (30 seconds)
[Attention-grabbing opening that makes listeners want to stay]

## INTRO (60 seconds)
[Welcome listeners, introduce the topic, preview what they'll learn]

## MAIN CONTENT
### Section 1: [Title]
[Content]

### Section 2: [Title]
[Content]

### Section 3: [Title]
[Content]

(Add more sections as needed)

## KEY TAKEAWAYS
- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]

## OUTRO (60 seconds)
[Recap, call-to-action, thank listeners]

## SHOW NOTES
[Brief summary for episode description]

Use [PAUSE] to indicate natural pauses for effect.
Use [MUSIC CUE] for transition music moments.
""")

        prompt = ChatPromptTemplate.from_template("\n".join(prompt_parts))
        chain = prompt | self.llm | StrOutputParser()

        result = await chain.ainvoke({})

        # Parse the result
        sections = self._parse_script_sections(result)

        return {
            "content": result,
            "sections": sections,
            "estimated_duration": duration_target,
            "word_count": len(result.split()),
            "style": style,
            "topic": topic,
        }

    async def generate_script_stream(
        self,
        topic: str,
        style: str = "conversational",
        duration_target: int = 600,
        brand_voice: Optional[BrandVoice] = None,
    ) -> AsyncIterator[str]:
        """Stream script generation for real-time display."""
        word_count = self._calculate_word_count(duration_target)
        style_prompt = self.STYLE_PROMPTS.get(style, self.STYLE_PROMPTS["conversational"])

        prompt = ChatPromptTemplate.from_template(f"""Create a podcast script about: {{topic}}

Style: {style_prompt}

Target length: approximately {word_count} words ({duration_target // 60} minutes)

Structure with clear sections: Hook, Intro, Main Content (with subsections), Key Takeaways, Outro.
Use [PAUSE] for dramatic pauses and [MUSIC CUE] for transitions.""")

        chain = prompt | self.llm | StrOutputParser()

        async for chunk in chain.astream({"topic": topic}):
            yield chunk

    async def generate_show_notes(
        self,
        script: str,
        topic: str,
    ) -> str:
        """Generate show notes from a script."""
        prompt = ChatPromptTemplate.from_template("""Create compelling podcast show notes from this script.

Topic: {topic}

Script:
{script}

Create show notes that include:
1. A catchy episode summary (2-3 sentences)
2. Key topics covered
3. Timestamps for main sections (estimated)
4. Resources mentioned (if any)
5. Call-to-action

Show Notes:""")

        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke({"script": script[:4000], "topic": topic})

    async def find_clip_moments(
        self,
        script: str,
        count: int = 5,
        clip_duration: int = 60,
    ) -> List[Dict[str, Any]]:
        """Identify the best moments for short clips."""
        prompt = ChatPromptTemplate.from_template("""Analyze this podcast script and identify the {count} best moments for short-form clips (TikTok, Reels, Shorts).

Script:
{script}

For each moment, identify:
1. A catchy title (max 50 chars)
2. Why it's clip-worthy
3. The exact quote or segment
4. Approximate position (percentage through episode)

Look for:
- Surprising insights
- Quotable moments
- Emotional peaks
- Actionable advice
- Controversial or debate-worthy takes

Return as:
CLIP 1:
Title: [title]
Why: [reason]
Quote: [exact text]
Position: [percentage]%

Continue for all {count} clips.""")

        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({
            "script": script[:6000],
            "count": count,
        })

        # Parse clips
        clips = []
        current_clip = {}

        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("CLIP"):
                if current_clip:
                    clips.append(current_clip)
                current_clip = {}
            elif line.startswith("Title:"):
                current_clip["title"] = line[6:].strip()
            elif line.startswith("Why:"):
                current_clip["description"] = line[4:].strip()
            elif line.startswith("Quote:"):
                current_clip["quote"] = line[6:].strip()
            elif line.startswith("Position:"):
                try:
                    pos = line[9:].strip().rstrip("%")
                    current_clip["position"] = float(pos) / 100
                except ValueError:
                    current_clip["position"] = 0.5

        if current_clip:
            clips.append(current_clip)

        return clips[:count]

    def _parse_script_sections(self, script: str) -> List[Dict[str, Any]]:
        """Parse script into structured sections."""
        sections = []
        current_section = None
        current_content = []

        for line in script.split("\n"):
            # Check for section headers (##)
            if line.startswith("## "):
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": "\n".join(current_content).strip(),
                    })
                current_section = line[3:].strip()
                current_content = []
            elif line.startswith("### "):
                # Subsection - include in content
                current_content.append(line)
            elif current_section:
                current_content.append(line)

        # Add last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": "\n".join(current_content).strip(),
            })

        return sections

    async def improve_script(
        self,
        script: str,
        feedback: str,
    ) -> str:
        """Improve a script based on feedback."""
        prompt = ChatPromptTemplate.from_template("""Improve this podcast script based on the feedback provided.

Original Script:
{script}

Feedback:
{feedback}

Create an improved version that addresses the feedback while maintaining the overall structure and style.

Improved Script:""")

        chain = prompt | self.llm | StrOutputParser()
        return await chain.ainvoke({"script": script, "feedback": feedback})
