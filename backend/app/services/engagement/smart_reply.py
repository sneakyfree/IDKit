"""
Smart Reply Assistant Service

AI-powered contextual reply suggestions with tone matching,
conversation history analysis, and personalization.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ReplyTone(str, Enum):
    """Tone options for replies."""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    EMPATHETIC = "empathetic"
    HUMOROUS = "humorous"
    GRATEFUL = "grateful"
    INFORMATIVE = "informative"


@dataclass
class ConversationThread:
    """Represents a conversation thread for context."""
    thread_id: str
    messages: List[Dict[str, Any]]
    platform: str
    participant_name: str
    participant_id: str
    is_dm: bool = False
    topic: Optional[str] = None


@dataclass
class ReplyContext:
    """Context for generating smart replies."""
    original_message: str
    sender_name: str
    sender_id: str
    platform: str
    message_type: str  # 'comment', 'dm', 'mention', 'reply'
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    language: str = "en"
    thread: Optional[ConversationThread] = None
    post_content: Optional[str] = None  # Content of the post being commented on
    brand_voice: Optional[Dict[str, Any]] = None
    user_profile: Optional[Dict[str, Any]] = None


@dataclass
class ReplySuggestion:
    """A suggested reply with metadata."""
    suggestion_id: str
    text: str
    tone: ReplyTone
    confidence: float
    reasoning: str
    character_count: int
    estimated_engagement: float  # 0-1 scale
    includes_question: bool
    includes_cta: bool
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SmartReplyAssistant:
    """
    AI-powered smart reply assistant.

    Features:
    - Multiple reply suggestions with different tones
    - Conversation context analysis
    - Sentiment-aware responses
    - Brand voice matching
    - Engagement optimization
    - Multi-language support
    """

    # Tone characteristics for prompt engineering
    TONE_CHARACTERISTICS = {
        ReplyTone.FRIENDLY: "warm, approachable, uses conversational language",
        ReplyTone.PROFESSIONAL: "polished, respectful, maintains boundaries",
        ReplyTone.CASUAL: "relaxed, informal, uses slang appropriately",
        ReplyTone.ENTHUSIASTIC: "excited, energetic, uses exclamation marks",
        ReplyTone.EMPATHETIC: "understanding, supportive, acknowledges feelings",
        ReplyTone.HUMOROUS: "witty, playful, uses appropriate humor",
        ReplyTone.GRATEFUL: "appreciative, thankful, acknowledges support",
        ReplyTone.INFORMATIVE: "helpful, educational, provides value",
    }

    # Platform-specific constraints
    PLATFORM_LIMITS = {
        "twitter": 280,
        "instagram": 2200,
        "tiktok": 150,
        "youtube": 10000,
        "facebook": 8000,
        "linkedin": 3000,
    }

    def __init__(self):
        self._llm_client = None
        self._cache: Dict[str, List[ReplySuggestion]] = {}

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            from app.config import settings
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    async def get_suggestions(
        self,
        context: ReplyContext,
        num_suggestions: int = 3,
        preferred_tones: Optional[List[ReplyTone]] = None,
        max_length: Optional[int] = None,
        include_question: bool = False,
        include_cta: bool = False,
    ) -> List[ReplySuggestion]:
        """
        Generate smart reply suggestions based on context.

        Args:
            context: Full context for the reply
            num_suggestions: Number of suggestions to generate
            preferred_tones: Specific tones to use (defaults to auto-selection)
            max_length: Maximum character length (defaults to platform limit)
            include_question: Whether to include a follow-up question
            include_cta: Whether to include a call-to-action

        Returns:
            List of reply suggestions ranked by confidence
        """
        # Determine max length
        char_limit = max_length or self.PLATFORM_LIMITS.get(context.platform, 500)

        # Auto-select tones if not specified
        if not preferred_tones:
            preferred_tones = await self._suggest_tones(context)

        # Build prompt
        prompt = self._build_suggestion_prompt(
            context=context,
            tones=preferred_tones[:num_suggestions],
            char_limit=char_limit,
            include_question=include_question,
            include_cta=include_cta,
        )

        # Generate suggestions
        client = await self._get_llm_client()

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(context),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.8,
        )

        # Parse suggestions
        suggestions = self._parse_suggestions(
            response.choices[0].message.content,
            preferred_tones,
            char_limit,
        )

        return suggestions

    async def quick_reply(
        self,
        message: str,
        platform: str,
        tone: ReplyTone = ReplyTone.FRIENDLY,
    ) -> str:
        """
        Generate a single quick reply.

        Simplified interface for fast reply generation.
        """
        context = ReplyContext(
            original_message=message,
            sender_name="User",
            sender_id="unknown",
            platform=platform,
            message_type="comment",
        )

        suggestions = await self.get_suggestions(
            context=context,
            num_suggestions=1,
            preferred_tones=[tone],
        )

        return suggestions[0].text if suggestions else ""

    async def analyze_message(
        self,
        message: str,
        platform: str,
    ) -> Dict[str, Any]:
        """
        Analyze a message to understand intent and suggest response strategy.
        """
        client = await self._get_llm_client()

        prompt = f"""Analyze this social media message and provide insights:

MESSAGE: {message}
PLATFORM: {platform}

Provide analysis in this exact JSON format:
{{
    "sentiment": "positive|negative|neutral|mixed",
    "intent": "question|praise|complaint|collaboration|general|spam",
    "urgency": "high|medium|low",
    "topics": ["topic1", "topic2"],
    "key_points": ["point1", "point2"],
    "suggested_response_type": "answer|thank|apologize|redirect|engage|ignore",
    "recommended_tone": "friendly|professional|empathetic|enthusiastic",
    "follow_up_needed": true|false,
    "notes": "any additional observations"
}}"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media analyst. Return only valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.3,
        )

        try:
            import json
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "sentiment": "neutral",
                "intent": "general",
                "urgency": "medium",
                "topics": [],
                "key_points": [],
                "suggested_response_type": "engage",
                "recommended_tone": "friendly",
                "follow_up_needed": False,
                "notes": "Analysis failed to parse",
            }

    async def generate_thread_reply(
        self,
        thread: ConversationThread,
        tone: ReplyTone = ReplyTone.FRIENDLY,
    ) -> ReplySuggestion:
        """
        Generate a reply that considers the full conversation thread.
        """
        if not thread.messages:
            raise ValueError("Thread has no messages")

        # Get last message
        last_message = thread.messages[-1]

        # Build conversation history
        history = "\n".join([
            f"[{m.get('sender', 'Unknown')}]: {m.get('content', '')}"
            for m in thread.messages[-5:]  # Last 5 messages
        ])

        context = ReplyContext(
            original_message=last_message.get("content", ""),
            sender_name=thread.participant_name,
            sender_id=thread.participant_id,
            platform=thread.platform,
            message_type="dm" if thread.is_dm else "comment",
            thread=thread,
        )

        suggestions = await self.get_suggestions(
            context=context,
            num_suggestions=1,
            preferred_tones=[tone],
        )

        return suggestions[0] if suggestions else None

    async def personalize_template(
        self,
        template: str,
        context: ReplyContext,
    ) -> str:
        """
        Personalize a template reply using AI.

        Takes a generic template and makes it contextual and personal.
        """
        client = await self._get_llm_client()

        prompt = f"""Personalize this reply template for the specific message:

TEMPLATE: {template}
ORIGINAL MESSAGE: {context.original_message}
SENDER NAME: {context.sender_name}
PLATFORM: {context.platform}

Make it:
- More personal and specific to the message
- Natural and conversational
- Keep the same intent as the template
- Under {self.PLATFORM_LIMITS.get(context.platform, 500)} characters

Return ONLY the personalized reply text."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media expert personalizing reply templates.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    async def batch_suggestions(
        self,
        messages: List[Dict[str, Any]],
        default_tone: ReplyTone = ReplyTone.FRIENDLY,
    ) -> List[Dict[str, Any]]:
        """
        Generate suggestions for multiple messages in batch.

        Efficient for processing inbox items.
        """
        results = []

        for msg in messages:
            context = ReplyContext(
                original_message=msg.get("content", ""),
                sender_name=msg.get("sender_name", "User"),
                sender_id=msg.get("sender_id", "unknown"),
                platform=msg.get("platform", "instagram"),
                message_type=msg.get("type", "comment"),
                sentiment=msg.get("sentiment"),
                intent=msg.get("intent"),
            )

            suggestions = await self.get_suggestions(
                context=context,
                num_suggestions=2,
                preferred_tones=[default_tone, ReplyTone.PROFESSIONAL],
            )

            results.append({
                "message_id": msg.get("id"),
                "suggestions": [
                    {
                        "text": s.text,
                        "tone": s.tone.value,
                        "confidence": s.confidence,
                    }
                    for s in suggestions
                ],
            })

        return results

    async def _suggest_tones(self, context: ReplyContext) -> List[ReplyTone]:
        """Auto-suggest appropriate tones based on context."""
        tones = []

        # Based on sentiment
        if context.sentiment == "positive":
            tones.extend([ReplyTone.ENTHUSIASTIC, ReplyTone.GRATEFUL])
        elif context.sentiment == "negative":
            tones.extend([ReplyTone.EMPATHETIC, ReplyTone.PROFESSIONAL])
        else:
            tones.append(ReplyTone.FRIENDLY)

        # Based on intent
        if context.intent == "question":
            tones.append(ReplyTone.INFORMATIVE)
        elif context.intent == "praise":
            tones.append(ReplyTone.GRATEFUL)
        elif context.intent == "complaint":
            tones.append(ReplyTone.EMPATHETIC)
        elif context.intent == "collaboration":
            tones.append(ReplyTone.PROFESSIONAL)

        # Based on platform
        if context.platform in ["linkedin"]:
            tones.append(ReplyTone.PROFESSIONAL)
        elif context.platform in ["tiktok", "instagram"]:
            tones.append(ReplyTone.CASUAL)

        # Remove duplicates and limit
        seen = set()
        unique_tones = []
        for tone in tones:
            if tone not in seen:
                seen.add(tone)
                unique_tones.append(tone)

        return unique_tones[:4] or [ReplyTone.FRIENDLY, ReplyTone.PROFESSIONAL]

    def _get_system_prompt(self, context: ReplyContext) -> str:
        """Build system prompt based on context."""
        base = """You are an expert social media community manager who crafts
perfect reply suggestions. Your replies are:
- Authentic and not robotic
- Appropriate for the platform
- Engaging and conversation-continuing
- Respectful of the original message's tone"""

        if context.brand_voice:
            base += f"""

Brand Voice Guidelines:
- Tone: {context.brand_voice.get('tone', 'friendly')}
- Style: {context.brand_voice.get('style', 'conversational')}
- Avoid: {', '.join(context.brand_voice.get('avoid', []))}"""

        return base

    def _build_suggestion_prompt(
        self,
        context: ReplyContext,
        tones: List[ReplyTone],
        char_limit: int,
        include_question: bool,
        include_cta: bool,
    ) -> str:
        """Build the suggestion generation prompt."""
        prompt = f"""Generate {len(tones)} reply suggestions for this message:

ORIGINAL MESSAGE: {context.original_message}
SENDER: {context.sender_name}
PLATFORM: {context.platform}
MESSAGE TYPE: {context.message_type}"""

        if context.sentiment:
            prompt += f"\nSENTIMENT: {context.sentiment}"

        if context.intent:
            prompt += f"\nINTENT: {context.intent}"

        if context.post_content:
            prompt += f"\nPOST BEING COMMENTED ON: {context.post_content[:200]}..."

        if context.thread:
            prompt += f"\nCONVERSATION TOPIC: {context.thread.topic or 'General'}"

        prompt += f"""

REQUIREMENTS:
- Maximum {char_limit} characters per reply
- Generate exactly {len(tones)} replies with these tones: {', '.join([t.value for t in tones])}"""

        if include_question:
            prompt += "\n- Include a follow-up question to continue engagement"

        if include_cta:
            prompt += "\n- Include a soft call-to-action (follow, check out, etc.)"

        prompt += """

FORMAT each reply as:
[TONE_NAME]
Reply text here
---REASONING---
Brief explanation of why this reply works
---END---

Generate replies now:"""

        return prompt

    def _parse_suggestions(
        self,
        response_text: str,
        tones: List[ReplyTone],
        char_limit: int,
    ) -> List[ReplySuggestion]:
        """Parse LLM response into ReplySuggestion objects."""
        suggestions = []

        # Split by ---END---
        parts = response_text.split("---END---")

        for i, part in enumerate(parts):
            if not part.strip():
                continue

            # Find tone
            tone = tones[i] if i < len(tones) else ReplyTone.FRIENDLY
            for t in ReplyTone:
                if f"[{t.value.upper()}]" in part.upper():
                    tone = t
                    break

            # Extract reply text
            lines = part.strip().split("\n")
            reply_lines = []
            reasoning = ""
            in_reasoning = False

            for line in lines:
                if "---REASONING---" in line:
                    in_reasoning = True
                    continue
                if in_reasoning:
                    reasoning += line + " "
                elif not line.startswith("[") and line.strip():
                    reply_lines.append(line)

            reply_text = "\n".join(reply_lines).strip()

            if reply_text:
                suggestions.append(ReplySuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    text=reply_text[:char_limit],
                    tone=tone,
                    confidence=0.85 - (i * 0.1),  # First suggestion highest confidence
                    reasoning=reasoning.strip(),
                    character_count=len(reply_text),
                    estimated_engagement=0.7 - (i * 0.05),
                    includes_question="?" in reply_text,
                    includes_cta=any(cta in reply_text.lower() for cta in [
                        "check out", "follow", "subscribe", "link in bio",
                        "dm me", "let me know", "drop a"
                    ]),
                    tags=[tone.value],
                ))

        # Fallback if parsing failed
        if not suggestions:
            suggestions.append(ReplySuggestion(
                suggestion_id=str(uuid.uuid4()),
                text="Thanks for your message! 🙏",
                tone=ReplyTone.FRIENDLY,
                confidence=0.5,
                reasoning="Fallback generic reply",
                character_count=26,
                estimated_engagement=0.5,
                includes_question=False,
                includes_cta=False,
            ))

        return suggestions

    async def get_emoji_suggestions(
        self,
        message: str,
        count: int = 5,
    ) -> List[str]:
        """Suggest relevant emojis for a reply."""
        client = await self._get_llm_client()

        prompt = f"""Suggest {count} relevant emojis for replying to this message:
"{message}"

Return ONLY the emojis separated by spaces, nothing else."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.5,
        )

        emojis = response.choices[0].message.content.strip().split()
        return emojis[:count]

    async def translate_reply(
        self,
        reply: str,
        target_language: str,
    ) -> str:
        """Translate a reply to another language while maintaining tone."""
        client = await self._get_llm_client()

        prompt = f"""Translate this social media reply to {target_language}.
Maintain the same tone, emoji usage, and casual style.

Reply: {reply}

Return ONLY the translated text."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()
