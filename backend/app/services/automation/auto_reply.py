"""
Auto-Reply Automation Service

Intelligent auto-reply system for comments and DMs with
rule-based triggers and AI-powered responses.
"""

import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.social import SocialAccount, Comment, DmMessage, DmConversation


class TriggerType(str, Enum):
    """Types of auto-reply triggers."""
    KEYWORD = "keyword"
    SENTIMENT = "sentiment"
    INTENT = "intent"
    MENTION = "mention"
    QUESTION = "question"
    NEW_FOLLOWER = "new_follower"
    FIRST_MESSAGE = "first_message"
    TIME_BASED = "time_based"
    ALL = "all"


class ReplyMode(str, Enum):
    """How replies are generated."""
    TEMPLATE = "template"
    AI_GENERATED = "ai_generated"
    AI_ENHANCED = "ai_enhanced"


@dataclass
class AutoReplyRule:
    """Auto-reply rule configuration."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool

    # Trigger configuration
    trigger_type: TriggerType
    trigger_value: Optional[str]  # keyword, sentiment value, etc.
    trigger_regex: Optional[str]  # Regex pattern for advanced matching

    # Reply configuration
    reply_mode: ReplyMode
    reply_template: str
    ai_context: Optional[str]  # Additional context for AI generation

    # Targeting
    platforms: List[str]
    message_types: List[str]  # "comment", "dm", "mention"

    # Rate limiting
    delay_seconds: int = 0
    max_replies_per_hour: int = 60
    max_replies_per_day: int = 500
    cooldown_per_user_minutes: int = 60

    # Exclusions
    exclude_keywords: List[str] = field(default_factory=list)
    exclude_users: List[str] = field(default_factory=list)

    # Tracking
    replies_count: int = 0
    last_reply_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReplyResult:
    """Result of an auto-reply attempt."""
    success: bool
    rule_id: uuid.UUID
    message_id: uuid.UUID
    reply_text: Optional[str]
    platform: str
    error: Optional[str] = None
    was_delayed: bool = False
    scheduled_for: Optional[datetime] = None


@dataclass
class RuleMatch:
    """Result of rule matching against a message."""
    rule: AutoReplyRule
    confidence: float
    matched_trigger: str
    suggested_reply: str


class AutoReplyService:
    """
    Intelligent auto-reply service.

    Features:
    - Rule-based triggers (keywords, sentiment, intent)
    - Template and AI-generated replies
    - Rate limiting and cooldowns
    - Platform-specific handling
    - Reply scheduling
    """

    # Default reply templates by intent
    DEFAULT_TEMPLATES = {
        "question": "Thanks for your question! We'll get back to you soon. 🙏",
        "praise": "Thank you so much for the kind words! It means a lot. ❤️",
        "complaint": "We're sorry to hear that. Please DM us so we can help resolve this.",
        "collaboration": "Thanks for reaching out! We'll review your proposal and get back to you.",
        "general": "Thanks for your comment! We appreciate you engaging with our content. 🙌",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None
        self._adapters = {}
        self._rules_cache: Dict[uuid.UUID, List[AutoReplyRule]] = {}
        self._user_cooldowns: Dict[str, datetime] = {}
        self._hourly_counts: Dict[uuid.UUID, int] = {}
        self._daily_counts: Dict[uuid.UUID, int] = {}

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    async def _get_adapter(self, platform: str):
        """Get platform adapter lazily."""
        if platform not in self._adapters:
            if platform == "youtube":
                from app.adapters.youtube.adapter import YouTubeAdapter
                self._adapters[platform] = YouTubeAdapter()
            elif platform == "instagram":
                from app.adapters.instagram.adapter import InstagramAdapter
                self._adapters[platform] = InstagramAdapter()
            elif platform == "tiktok":
                from app.adapters.tiktok.adapter import TikTokAdapter
                self._adapters[platform] = TikTokAdapter()
            elif platform == "twitter":
                from app.adapters.twitter.adapter import TwitterAdapter
                self._adapters[platform] = TwitterAdapter()
            elif platform == "facebook":
                from app.adapters.facebook.adapter import FacebookAdapter
                self._adapters[platform] = FacebookAdapter()
            elif platform == "linkedin":
                from app.adapters.linkedin.adapter import LinkedInAdapter
                self._adapters[platform] = LinkedInAdapter()
        return self._adapters.get(platform)

    # =========================================================================
    # RULE MANAGEMENT
    # =========================================================================

    async def create_rule(
        self,
        user_id: uuid.UUID,
        name: str,
        trigger_type: TriggerType,
        reply_template: str,
        trigger_value: Optional[str] = None,
        trigger_regex: Optional[str] = None,
        reply_mode: ReplyMode = ReplyMode.TEMPLATE,
        ai_context: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        message_types: Optional[List[str]] = None,
        delay_seconds: int = 0,
        max_replies_per_hour: int = 60,
        max_replies_per_day: int = 500,
        cooldown_per_user_minutes: int = 60,
        exclude_keywords: Optional[List[str]] = None,
        exclude_users: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> AutoReplyRule:
        """
        Create a new auto-reply rule.
        """
        rule = AutoReplyRule(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            is_active=True,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            trigger_regex=trigger_regex,
            reply_mode=reply_mode,
            reply_template=reply_template,
            ai_context=ai_context,
            platforms=platforms or ["instagram", "tiktok", "youtube", "twitter", "facebook"],
            message_types=message_types or ["comment", "mention"],
            delay_seconds=delay_seconds,
            max_replies_per_hour=max_replies_per_hour,
            max_replies_per_day=max_replies_per_day,
            cooldown_per_user_minutes=cooldown_per_user_minutes,
            exclude_keywords=exclude_keywords or [],
            exclude_users=exclude_users or [],
        )

        # Store in database (would need AutoReplyRule model)
        # For now, cache in memory
        if user_id not in self._rules_cache:
            self._rules_cache[user_id] = []
        self._rules_cache[user_id].append(rule)

        return rule

    async def get_rules(
        self,
        user_id: uuid.UUID,
        active_only: bool = True,
    ) -> List[AutoReplyRule]:
        """Get all rules for a user."""
        rules = self._rules_cache.get(user_id, [])
        if active_only:
            rules = [r for r in rules if r.is_active]
        return rules

    async def update_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
        **updates,
    ) -> Optional[AutoReplyRule]:
        """Update an existing rule."""
        rules = self._rules_cache.get(user_id, [])
        for rule in rules:
            if rule.id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                rule.updated_at = datetime.now(timezone.utc)
                return rule
        return None

    async def delete_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
    ) -> bool:
        """Delete a rule."""
        if user_id in self._rules_cache:
            original_len = len(self._rules_cache[user_id])
            self._rules_cache[user_id] = [
                r for r in self._rules_cache[user_id] if r.id != rule_id
            ]
            return len(self._rules_cache[user_id]) < original_len
        return False

    async def toggle_rule(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID,
        is_active: bool,
    ) -> Optional[AutoReplyRule]:
        """Enable or disable a rule."""
        return await self.update_rule(user_id, rule_id, is_active=is_active)

    # =========================================================================
    # MESSAGE PROCESSING
    # =========================================================================

    async def process_message(
        self,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
        message_content: str,
        message_type: str,
        platform: str,
        sender_id: str,
        sender_name: Optional[str] = None,
        sentiment: Optional[str] = None,
        intent: Optional[str] = None,
        account_id: Optional[uuid.UUID] = None,
    ) -> Optional[ReplyResult]:
        """
        Process a message and auto-reply if rules match.

        Returns ReplyResult if a reply was sent, None otherwise.
        """
        # Get active rules for user
        rules = await self.get_rules(user_id, active_only=True)
        if not rules:
            return None

        # Find matching rules
        matches = await self._find_matching_rules(
            rules=rules,
            message_content=message_content,
            message_type=message_type,
            platform=platform,
            sender_id=sender_id,
            sentiment=sentiment,
            intent=intent,
        )

        if not matches:
            return None

        # Use the highest confidence match
        best_match = max(matches, key=lambda m: m.confidence)
        rule = best_match.rule

        # Check rate limits
        if not await self._check_rate_limits(rule, sender_id):
            return ReplyResult(
                success=False,
                rule_id=rule.id,
                message_id=message_id,
                reply_text=None,
                platform=platform,
                error="Rate limit exceeded",
            )

        # Generate reply
        reply_text = await self._generate_reply(
            rule=rule,
            message_content=message_content,
            sender_name=sender_name,
            match=best_match,
        )

        # Check for delay
        if rule.delay_seconds > 0:
            scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=rule.delay_seconds)
            # In production, queue for later sending
            return ReplyResult(
                success=True,
                rule_id=rule.id,
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
                was_delayed=True,
                scheduled_for=scheduled_for,
            )

        # Send reply immediately
        result = await self._send_reply(
            account_id=account_id,
            message_id=message_id,
            message_type=message_type,
            platform=platform,
            reply_text=reply_text,
            user_id=user_id,
        )

        # Update tracking
        if result.success:
            await self._update_tracking(rule, sender_id)

        return result

    async def _find_matching_rules(
        self,
        rules: List[AutoReplyRule],
        message_content: str,
        message_type: str,
        platform: str,
        sender_id: str,
        sentiment: Optional[str],
        intent: Optional[str],
    ) -> List[RuleMatch]:
        """Find rules that match the message."""
        matches = []
        message_lower = message_content.lower()

        for rule in rules:
            # Check platform
            if platform not in rule.platforms:
                continue

            # Check message type
            if message_type not in rule.message_types:
                continue

            # Check exclusions
            if sender_id in rule.exclude_users:
                continue

            if any(kw.lower() in message_lower for kw in rule.exclude_keywords):
                continue

            # Check trigger
            confidence = 0.0
            matched_trigger = ""

            if rule.trigger_type == TriggerType.ALL:
                confidence = 1.0
                matched_trigger = "all"

            elif rule.trigger_type == TriggerType.KEYWORD:
                if rule.trigger_value and rule.trigger_value.lower() in message_lower:
                    confidence = 0.9
                    matched_trigger = f"keyword:{rule.trigger_value}"

            elif rule.trigger_type == TriggerType.SENTIMENT:
                if sentiment and rule.trigger_value == sentiment:
                    confidence = 0.85
                    matched_trigger = f"sentiment:{sentiment}"

            elif rule.trigger_type == TriggerType.INTENT:
                if intent and rule.trigger_value == intent:
                    confidence = 0.85
                    matched_trigger = f"intent:{intent}"

            elif rule.trigger_type == TriggerType.QUESTION:
                if "?" in message_content or self._looks_like_question(message_content):
                    confidence = 0.8
                    matched_trigger = "question"

            elif rule.trigger_type == TriggerType.MENTION:
                if message_type == "mention":
                    confidence = 0.9
                    matched_trigger = "mention"

            # Check regex pattern
            if rule.trigger_regex and confidence == 0:
                try:
                    if re.search(rule.trigger_regex, message_content, re.IGNORECASE):
                        confidence = 0.9
                        matched_trigger = f"regex:{rule.trigger_regex}"
                except re.error:
                    pass

            if confidence > 0:
                matches.append(RuleMatch(
                    rule=rule,
                    confidence=confidence,
                    matched_trigger=matched_trigger,
                    suggested_reply=rule.reply_template,
                ))

        return matches

    def _looks_like_question(self, text: str) -> bool:
        """Check if text appears to be a question."""
        question_starters = [
            "how", "what", "when", "where", "why", "who", "which",
            "can", "could", "would", "should", "is", "are", "do", "does",
            "will", "have", "has", "am", "was", "were",
        ]
        first_word = text.split()[0].lower() if text.split() else ""
        return first_word in question_starters

    async def _check_rate_limits(
        self,
        rule: AutoReplyRule,
        sender_id: str,
    ) -> bool:
        """Check if rate limits allow sending a reply."""
        now = datetime.now(timezone.utc)

        # Check user cooldown
        cooldown_key = f"{rule.id}:{sender_id}"
        if cooldown_key in self._user_cooldowns:
            last_reply = self._user_cooldowns[cooldown_key]
            if now - last_reply < timedelta(minutes=rule.cooldown_per_user_minutes):
                return False

        # Check hourly limit
        hourly_count = self._hourly_counts.get(rule.id, 0)
        if hourly_count >= rule.max_replies_per_hour:
            return False

        # Check daily limit
        daily_count = self._daily_counts.get(rule.id, 0)
        if daily_count >= rule.max_replies_per_day:
            return False

        return True

    async def _update_tracking(
        self,
        rule: AutoReplyRule,
        sender_id: str,
    ):
        """Update tracking after successful reply."""
        now = datetime.now(timezone.utc)

        # Update cooldown
        cooldown_key = f"{rule.id}:{sender_id}"
        self._user_cooldowns[cooldown_key] = now

        # Update counts
        self._hourly_counts[rule.id] = self._hourly_counts.get(rule.id, 0) + 1
        self._daily_counts[rule.id] = self._daily_counts.get(rule.id, 0) + 1

        # Update rule
        rule.replies_count += 1
        rule.last_reply_at = now

    async def _generate_reply(
        self,
        rule: AutoReplyRule,
        message_content: str,
        sender_name: Optional[str],
        match: RuleMatch,
    ) -> str:
        """Generate reply text based on rule mode."""
        if rule.reply_mode == ReplyMode.TEMPLATE:
            # Simple template substitution
            reply = rule.reply_template
            if sender_name:
                reply = reply.replace("{name}", sender_name)
                reply = reply.replace("{sender}", sender_name)
            return reply

        elif rule.reply_mode == ReplyMode.AI_GENERATED:
            # Full AI generation
            return await self._generate_ai_reply(
                message=message_content,
                sender_name=sender_name,
                context=rule.ai_context,
                base_template=None,
            )

        elif rule.reply_mode == ReplyMode.AI_ENHANCED:
            # AI-enhanced template
            return await self._generate_ai_reply(
                message=message_content,
                sender_name=sender_name,
                context=rule.ai_context,
                base_template=rule.reply_template,
            )

        return rule.reply_template

    async def _generate_ai_reply(
        self,
        message: str,
        sender_name: Optional[str],
        context: Optional[str],
        base_template: Optional[str],
    ) -> str:
        """Generate AI-powered reply."""
        client = await self._get_llm_client()

        if base_template:
            prompt = f"""Enhance this reply template to be more personalized and engaging.

ORIGINAL MESSAGE: {message[:500]}
SENDER NAME: {sender_name or "User"}
TEMPLATE: {base_template}
{f"CONTEXT: {context}" if context else ""}

Requirements:
- Keep the same tone and intent as the template
- Make it feel more personal and less generic
- Keep it concise (under 200 characters)
- Sound natural and friendly

Return ONLY the enhanced reply text, nothing else."""
        else:
            prompt = f"""Generate a friendly, engaging reply to this social media message.

MESSAGE: {message[:500]}
SENDER NAME: {sender_name or "User"}
{f"CONTEXT: {context}" if context else ""}

Requirements:
- Be friendly and authentic
- Keep it concise (under 200 characters)
- Match the tone of the original message
- Include a relevant response or acknowledgment

Return ONLY the reply text, nothing else."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly social media manager crafting personalized replies.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()

    async def _send_reply(
        self,
        account_id: Optional[uuid.UUID],
        message_id: uuid.UUID,
        message_type: str,
        platform: str,
        reply_text: str,
        user_id: uuid.UUID,
    ) -> ReplyResult:
        """Send the reply via platform adapter."""
        if not account_id:
            return ReplyResult(
                success=False,
                rule_id=uuid.uuid4(),
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
                error="No account ID provided",
            )

        # Get account
        result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.id == account_id,
                SocialAccount.user_id == user_id,
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return ReplyResult(
                success=False,
                rule_id=uuid.uuid4(),
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
                error="Account not found",
            )

        # Get adapter
        adapter = await self._get_adapter(platform)
        if not adapter:
            return ReplyResult(
                success=False,
                rule_id=uuid.uuid4(),
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
                error=f"Platform {platform} not supported",
            )

        try:
            if message_type == "comment":
                # Get comment
                comment_result = await self.db.execute(
                    select(Comment).where(Comment.id == message_id)
                )
                comment = comment_result.scalar_one_or_none()

                if comment:
                    await adapter.reply_comment(
                        access_token=account.access_token,
                        comment_id=comment.platform_comment_id,
                        text=reply_text,
                    )

                    # Mark as replied
                    comment.is_replied = True
                    comment.replied_at = datetime.now(timezone.utc)
                    await self.db.commit()

            elif message_type == "dm":
                # Get conversation
                dm_result = await self.db.execute(
                    select(DmMessage).where(DmMessage.id == message_id)
                )
                dm = dm_result.scalar_one_or_none()

                if dm:
                    conv_result = await self.db.execute(
                        select(DmConversation).where(DmConversation.id == dm.conversation_id)
                    )
                    conv = conv_result.scalar_one_or_none()

                    if conv:
                        await adapter.send_message(
                            access_token=account.access_token,
                            user_id=conv.participant_id,
                            text=reply_text,
                        )

            return ReplyResult(
                success=True,
                rule_id=uuid.uuid4(),
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
            )

        except Exception as e:
            return ReplyResult(
                success=False,
                rule_id=uuid.uuid4(),
                message_id=message_id,
                reply_text=reply_text,
                platform=platform,
                error=str(e),
            )

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    async def process_pending_messages(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> List[ReplyResult]:
        """Process pending unread messages for auto-reply."""
        # Get user's accounts
        accounts_result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.is_active == True,
            )
        )
        accounts = accounts_result.scalars().all()
        account_ids = [a.id for a in accounts]
        account_lookup = {a.id: a for a in accounts}

        if not account_ids:
            return []

        # Get unprocessed comments
        comments_query = (
            select(Comment)
            .where(
                Comment.account_id.in_(account_ids),
                Comment.is_read == False,
                Comment.is_replied == False,
                Comment.is_spam == False,
            )
            .limit(limit)
        )
        comments_result = await self.db.execute(comments_query)
        comments = comments_result.scalars().all()

        results = []

        for comment in comments:
            account = account_lookup.get(comment.account_id)
            if not account:
                continue

            result = await self.process_message(
                user_id=user_id,
                message_id=comment.id,
                message_content=comment.content,
                message_type="mention" if comment.is_mention else "comment",
                platform=account.platform,
                sender_id=comment.author_id,
                sender_name=comment.author_name,
                sentiment=comment.sentiment,
                intent=comment.intent,
                account_id=account.id,
            )

            if result:
                results.append(result)

            # Mark as read regardless
            comment.is_read = True
            comment.read_at = datetime.now(timezone.utc)

        await self.db.commit()

        return results

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_rule_stats(
        self,
        user_id: uuid.UUID,
        rule_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Get statistics for auto-reply rules."""
        rules = await self.get_rules(user_id, active_only=False)

        if rule_id:
            rules = [r for r in rules if r.id == rule_id]

        total_replies = sum(r.replies_count for r in rules)
        active_rules = sum(1 for r in rules if r.is_active)

        rule_stats = []
        for rule in rules:
            rule_stats.append({
                "id": str(rule.id),
                "name": rule.name,
                "is_active": rule.is_active,
                "trigger_type": rule.trigger_type.value,
                "replies_count": rule.replies_count,
                "last_reply_at": rule.last_reply_at.isoformat() if rule.last_reply_at else None,
                "created_at": rule.created_at.isoformat(),
            })

        return {
            "total_rules": len(rules),
            "active_rules": active_rules,
            "total_replies": total_replies,
            "rules": rule_stats,
        }

    async def reset_daily_counts(self):
        """Reset daily reply counts (call daily via cron)."""
        self._daily_counts.clear()

    async def reset_hourly_counts(self):
        """Reset hourly reply counts (call hourly via cron)."""
        self._hourly_counts.clear()
