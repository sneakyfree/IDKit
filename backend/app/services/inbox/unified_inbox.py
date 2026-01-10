"""
Unified Inbox Service

Aggregates comments and direct messages from all connected social platforms
into a single, manageable inbox with AI-powered response suggestions.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.social import SocialAccount, Comment, DmConversation, DmMessage


class MessageType(str, Enum):
    """Types of inbox messages."""
    COMMENT = "comment"
    DM = "dm"
    MENTION = "mention"
    REPLY = "reply"


class MessageStatus(str, Enum):
    """Status of inbox messages."""
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
    SPAM = "spam"


class MessageSentiment(str, Enum):
    """AI-detected sentiment of message."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    QUESTION = "question"
    URGENT = "urgent"


class MessageIntent(str, Enum):
    """AI-detected intent of message."""
    PRAISE = "praise"
    COMPLAINT = "complaint"
    QUESTION = "question"
    COLLABORATION = "collaboration"
    SPAM = "spam"
    SUPPORT = "support"
    GENERAL = "general"


@dataclass
class InboxMessage:
    """Unified inbox message from any platform."""
    id: uuid.UUID
    type: MessageType
    platform: str
    account_id: uuid.UUID
    account_name: str

    # Sender info
    sender_id: str
    sender_name: str
    sender_username: Optional[str]
    sender_avatar_url: Optional[str]
    sender_follower_count: Optional[int]

    # Message content
    content: str
    media_urls: List[str] = field(default_factory=list)

    # Context
    post_id: Optional[str] = None
    post_preview: Optional[str] = None
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None

    # Status and metadata
    status: MessageStatus = MessageStatus.UNREAD
    sentiment: Optional[MessageSentiment] = None
    intent: Optional[MessageIntent] = None
    priority: int = 0  # 0-10, higher = more important

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None

    # AI suggestions
    suggested_replies: List[str] = field(default_factory=list)
    auto_reply_sent: bool = False


@dataclass
class Conversation:
    """Grouped conversation (for DMs or comment threads)."""
    id: str
    platform: str
    account_id: uuid.UUID
    participant_id: str
    participant_name: str
    participant_username: Optional[str]
    participant_avatar_url: Optional[str]
    message_count: int
    unread_count: int
    last_message: Optional[InboxMessage]
    last_activity: datetime
    is_muted: bool = False


@dataclass
class InboxStats:
    """Statistics for the unified inbox."""
    total_messages: int
    unread_count: int
    comments_count: int
    dms_count: int
    mentions_count: int
    sentiment_breakdown: Dict[str, int]
    platform_breakdown: Dict[str, int]
    response_rate: float  # Percentage replied
    avg_response_time_minutes: Optional[float]


@dataclass
class AutoReplyRule:
    """Rule for automatic replies."""
    id: uuid.UUID
    name: str
    is_active: bool
    trigger_type: str  # "keyword", "sentiment", "intent", "all"
    trigger_value: Optional[str]  # e.g., keyword or sentiment value
    reply_template: str
    platforms: List[str]
    delay_minutes: int = 0
    max_replies_per_day: int = 100
    replies_today: int = 0


class UnifiedInboxService:
    """
    Unified inbox for managing comments and DMs across all platforms.

    Features:
    - Aggregated view of all messages
    - AI sentiment and intent analysis
    - Smart reply suggestions
    - Auto-reply rules
    - Priority scoring
    - Bulk actions
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_client = None
        self._adapters = {}

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
    # INBOX RETRIEVAL
    # =========================================================================

    async def get_inbox(
        self,
        user_id: uuid.UUID,
        message_type: Optional[MessageType] = None,
        status: Optional[MessageStatus] = None,
        platforms: Optional[List[str]] = None,
        sentiment: Optional[MessageSentiment] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",  # "created_at", "priority", "sentiment"
    ) -> List[InboxMessage]:
        """
        Get unified inbox messages with filtering and pagination.
        """
        # Get user's connected accounts
        accounts_query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            accounts_query = accounts_query.where(SocialAccount.platform.in_(platforms))

        accounts_result = await self.db.execute(accounts_query)
        accounts = accounts_result.scalars().all()
        account_ids = [a.id for a in accounts]
        account_lookup = {a.id: a for a in accounts}

        if not account_ids:
            return []

        messages = []

        # Get comments
        if message_type is None or message_type in [MessageType.COMMENT, MessageType.MENTION, MessageType.REPLY]:
            comments = await self._get_comments(
                account_ids=account_ids,
                status=status,
                sentiment=sentiment,
                search_query=search_query,
                account_lookup=account_lookup,
            )
            messages.extend(comments)

        # Get DMs
        if message_type is None or message_type == MessageType.DM:
            dms = await self._get_dms(
                account_ids=account_ids,
                status=status,
                sentiment=sentiment,
                search_query=search_query,
                account_lookup=account_lookup,
            )
            messages.extend(dms)

        # Sort
        if sort_by == "priority":
            messages.sort(key=lambda m: m.priority, reverse=True)
        elif sort_by == "sentiment":
            sentiment_order = {"urgent": 0, "negative": 1, "question": 2, "neutral": 3, "positive": 4}
            messages.sort(key=lambda m: sentiment_order.get(m.sentiment.value if m.sentiment else "neutral", 3))
        else:  # created_at
            messages.sort(key=lambda m: m.created_at, reverse=True)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size

        return messages[start:end]

    async def _get_comments(
        self,
        account_ids: List[uuid.UUID],
        status: Optional[MessageStatus],
        sentiment: Optional[MessageSentiment],
        search_query: Optional[str],
        account_lookup: Dict[uuid.UUID, SocialAccount],
    ) -> List[InboxMessage]:
        """Get comments from database."""
        query = select(Comment).where(Comment.account_id.in_(account_ids))

        if status:
            status_map = {
                MessageStatus.UNREAD: Comment.is_read == False,
                MessageStatus.READ: Comment.is_read == True,
                MessageStatus.REPLIED: Comment.is_replied == True,
                MessageStatus.SPAM: Comment.is_spam == True,
            }
            if status in status_map:
                query = query.where(status_map[status])

        if sentiment and hasattr(Comment, 'sentiment'):
            query = query.where(Comment.sentiment == sentiment.value)

        if search_query:
            query = query.where(Comment.content.ilike(f"%{search_query}%"))

        query = query.order_by(desc(Comment.created_at)).limit(500)

        result = await self.db.execute(query)
        comments = result.scalars().all()

        messages = []
        for comment in comments:
            account = account_lookup.get(comment.account_id)
            if not account:
                continue

            # Determine message type
            if comment.parent_comment_id:
                msg_type = MessageType.REPLY
            elif comment.is_mention:
                msg_type = MessageType.MENTION
            else:
                msg_type = MessageType.COMMENT

            # Determine status
            if comment.is_spam:
                msg_status = MessageStatus.SPAM
            elif comment.is_replied:
                msg_status = MessageStatus.REPLIED
            elif comment.is_read:
                msg_status = MessageStatus.READ
            else:
                msg_status = MessageStatus.UNREAD

            messages.append(InboxMessage(
                id=comment.id,
                type=msg_type,
                platform=account.platform,
                account_id=account.id,
                account_name=account.account_name or account.platform_user_id,
                sender_id=comment.author_id,
                sender_name=comment.author_name or "Unknown",
                sender_username=comment.author_username,
                sender_avatar_url=comment.author_avatar_url,
                sender_follower_count=None,
                content=comment.content,
                post_id=comment.post_id,
                parent_message_id=comment.parent_comment_id,
                status=msg_status,
                sentiment=MessageSentiment(comment.sentiment) if comment.sentiment else None,
                intent=MessageIntent(comment.intent) if comment.intent else None,
                priority=comment.priority or 0,
                created_at=comment.created_at,
                read_at=comment.read_at,
                replied_at=comment.replied_at,
            ))

        return messages

    async def _get_dms(
        self,
        account_ids: List[uuid.UUID],
        status: Optional[MessageStatus],
        sentiment: Optional[MessageSentiment],
        search_query: Optional[str],
        account_lookup: Dict[uuid.UUID, SocialAccount],
    ) -> List[InboxMessage]:
        """Get direct messages from database."""
        query = select(DmMessage).where(
            DmMessage.is_from_me == False,  # Only incoming messages
        )

        # Filter by conversations belonging to user's accounts
        conv_subquery = select(DmConversation.id).where(
            DmConversation.account_id.in_(account_ids)
        )
        query = query.where(DmMessage.conversation_id.in_(conv_subquery))

        if status:
            status_map = {
                MessageStatus.UNREAD: DmMessage.is_read == False,
                MessageStatus.READ: DmMessage.is_read == True,
            }
            if status in status_map:
                query = query.where(status_map[status])

        if search_query:
            query = query.where(DmMessage.content.ilike(f"%{search_query}%"))

        query = query.order_by(desc(DmMessage.created_at)).limit(500)

        result = await self.db.execute(query)
        dm_messages = result.scalars().all()

        # Get conversation data
        conv_ids = list(set(m.conversation_id for m in dm_messages))
        conv_query = select(DmConversation).where(DmConversation.id.in_(conv_ids))
        conv_result = await self.db.execute(conv_query)
        conversations = {c.id: c for c in conv_result.scalars().all()}

        messages = []
        for dm in dm_messages:
            conv = conversations.get(dm.conversation_id)
            if not conv:
                continue

            account = account_lookup.get(conv.account_id)
            if not account:
                continue

            msg_status = MessageStatus.READ if dm.is_read else MessageStatus.UNREAD

            messages.append(InboxMessage(
                id=dm.id,
                type=MessageType.DM,
                platform=account.platform,
                account_id=account.id,
                account_name=account.account_name or account.platform_user_id,
                sender_id=conv.participant_id,
                sender_name=conv.participant_name or "Unknown",
                sender_username=conv.participant_username,
                sender_avatar_url=conv.participant_avatar_url,
                sender_follower_count=None,
                content=dm.content,
                media_urls=dm.media_urls or [],
                conversation_id=str(conv.id),
                status=msg_status,
                sentiment=MessageSentiment(dm.sentiment) if dm.sentiment else None,
                priority=dm.priority or 0,
                created_at=dm.created_at,
                read_at=dm.read_at,
            ))

        return messages

    async def get_conversations(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> List[Conversation]:
        """
        Get DM conversations grouped by participant.
        """
        # Get user's accounts
        accounts_query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            accounts_query = accounts_query.where(SocialAccount.platform.in_(platforms))

        accounts_result = await self.db.execute(accounts_query)
        accounts = accounts_result.scalars().all()
        account_ids = [a.id for a in accounts]
        account_lookup = {a.id: a for a in accounts}

        if not account_ids:
            return []

        # Get conversations
        query = select(DmConversation).where(
            DmConversation.account_id.in_(account_ids)
        )

        if unread_only:
            query = query.where(DmConversation.unread_count > 0)

        query = query.order_by(desc(DmConversation.last_message_at)).limit(page_size).offset((page - 1) * page_size)

        result = await self.db.execute(query)
        db_conversations = result.scalars().all()

        conversations = []
        for conv in db_conversations:
            account = account_lookup.get(conv.account_id)
            if not account:
                continue

            # Get last message
            last_msg_query = (
                select(DmMessage)
                .where(DmMessage.conversation_id == conv.id)
                .order_by(desc(DmMessage.created_at))
                .limit(1)
            )
            last_msg_result = await self.db.execute(last_msg_query)
            last_msg = last_msg_result.scalar_one_or_none()

            last_message = None
            if last_msg:
                last_message = InboxMessage(
                    id=last_msg.id,
                    type=MessageType.DM,
                    platform=account.platform,
                    account_id=account.id,
                    account_name=account.account_name or "",
                    sender_id=conv.participant_id if not last_msg.is_from_me else "me",
                    sender_name=conv.participant_name or "Unknown",
                    sender_username=conv.participant_username,
                    sender_avatar_url=conv.participant_avatar_url,
                    content=last_msg.content,
                    created_at=last_msg.created_at,
                )

            conversations.append(Conversation(
                id=str(conv.id),
                platform=account.platform,
                account_id=account.id,
                participant_id=conv.participant_id,
                participant_name=conv.participant_name or "Unknown",
                participant_username=conv.participant_username,
                participant_avatar_url=conv.participant_avatar_url,
                message_count=conv.message_count or 0,
                unread_count=conv.unread_count or 0,
                last_message=last_message,
                last_activity=conv.last_message_at or conv.created_at,
                is_muted=conv.is_muted or False,
            ))

        return conversations

    async def get_inbox_stats(
        self,
        user_id: uuid.UUID,
        platforms: Optional[List[str]] = None,
    ) -> InboxStats:
        """
        Get statistics for the unified inbox.
        """
        # Get accounts
        accounts_query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platforms:
            accounts_query = accounts_query.where(SocialAccount.platform.in_(platforms))

        accounts_result = await self.db.execute(accounts_query)
        accounts = accounts_result.scalars().all()
        account_ids = [a.id for a in accounts]

        if not account_ids:
            return InboxStats(
                total_messages=0,
                unread_count=0,
                comments_count=0,
                dms_count=0,
                mentions_count=0,
                sentiment_breakdown={},
                platform_breakdown={},
                response_rate=0.0,
                avg_response_time_minutes=None,
            )

        # Count comments
        comments_total = await self.db.execute(
            select(func.count(Comment.id)).where(Comment.account_id.in_(account_ids))
        )
        comments_count = comments_total.scalar() or 0

        comments_unread = await self.db.execute(
            select(func.count(Comment.id)).where(
                Comment.account_id.in_(account_ids),
                Comment.is_read == False,
            )
        )
        comments_unread_count = comments_unread.scalar() or 0

        comments_replied = await self.db.execute(
            select(func.count(Comment.id)).where(
                Comment.account_id.in_(account_ids),
                Comment.is_replied == True,
            )
        )
        comments_replied_count = comments_replied.scalar() or 0

        mentions_result = await self.db.execute(
            select(func.count(Comment.id)).where(
                Comment.account_id.in_(account_ids),
                Comment.is_mention == True,
            )
        )
        mentions_count = mentions_result.scalar() or 0

        # Count DMs
        conv_subquery = select(DmConversation.id).where(
            DmConversation.account_id.in_(account_ids)
        )

        dms_total = await self.db.execute(
            select(func.count(DmMessage.id)).where(
                DmMessage.conversation_id.in_(conv_subquery),
                DmMessage.is_from_me == False,
            )
        )
        dms_count = dms_total.scalar() or 0

        dms_unread = await self.db.execute(
            select(func.count(DmMessage.id)).where(
                DmMessage.conversation_id.in_(conv_subquery),
                DmMessage.is_from_me == False,
                DmMessage.is_read == False,
            )
        )
        dms_unread_count = dms_unread.scalar() or 0

        # Platform breakdown
        platform_breakdown = {}
        for account in accounts:
            platform_comments = await self.db.execute(
                select(func.count(Comment.id)).where(Comment.account_id == account.id)
            )
            count = platform_comments.scalar() or 0
            platform_breakdown[account.platform] = platform_breakdown.get(account.platform, 0) + count

        # Sentiment breakdown (if available)
        sentiment_breakdown = {}
        for sentiment in MessageSentiment:
            sentiment_count = await self.db.execute(
                select(func.count(Comment.id)).where(
                    Comment.account_id.in_(account_ids),
                    Comment.sentiment == sentiment.value,
                )
            )
            count = sentiment_count.scalar() or 0
            if count > 0:
                sentiment_breakdown[sentiment.value] = count

        # Calculate response rate
        total_messages = comments_count + dms_count
        response_rate = (comments_replied_count / comments_count * 100) if comments_count > 0 else 0.0

        return InboxStats(
            total_messages=total_messages,
            unread_count=comments_unread_count + dms_unread_count,
            comments_count=comments_count,
            dms_count=dms_count,
            mentions_count=mentions_count,
            sentiment_breakdown=sentiment_breakdown,
            platform_breakdown=platform_breakdown,
            response_rate=round(response_rate, 1),
            avg_response_time_minutes=None,  # Would require response time tracking
        )

    # =========================================================================
    # MESSAGE ACTIONS
    # =========================================================================

    async def mark_as_read(
        self,
        user_id: uuid.UUID,
        message_ids: List[uuid.UUID],
        message_type: MessageType,
    ) -> int:
        """
        Mark messages as read.

        Returns count of messages updated.
        """
        if message_type == MessageType.DM:
            result = await self.db.execute(
                select(DmMessage).where(DmMessage.id.in_(message_ids))
            )
            messages = result.scalars().all()

            count = 0
            for msg in messages:
                if not msg.is_read:
                    msg.is_read = True
                    msg.read_at = datetime.now(timezone.utc)
                    count += 1

            await self.db.commit()
            return count
        else:
            result = await self.db.execute(
                select(Comment).where(Comment.id.in_(message_ids))
            )
            comments = result.scalars().all()

            count = 0
            for comment in comments:
                if not comment.is_read:
                    comment.is_read = True
                    comment.read_at = datetime.now(timezone.utc)
                    count += 1

            await self.db.commit()
            return count

    async def reply_to_comment(
        self,
        user_id: uuid.UUID,
        comment_id: uuid.UUID,
        reply_text: str,
    ) -> Dict[str, Any]:
        """
        Reply to a comment on the platform.
        """
        # Get comment
        result = await self.db.execute(
            select(Comment).where(Comment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            raise ValueError("Comment not found")

        # Get account
        account_result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.id == comment.account_id,
                SocialAccount.user_id == user_id,
            )
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found or access denied")

        # Get adapter and reply
        adapter = await self._get_adapter(account.platform)
        if not adapter:
            raise ValueError(f"Platform {account.platform} not supported")

        try:
            reply_result = await adapter.reply_comment(
                access_token=account.access_token,
                comment_id=comment.platform_comment_id,
                text=reply_text,
            )

            # Update comment status
            comment.is_replied = True
            comment.replied_at = datetime.now(timezone.utc)
            await self.db.commit()

            return {
                "success": True,
                "platform": account.platform,
                "reply_id": reply_result.get("id") if isinstance(reply_result, dict) else None,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def send_dm(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_text: str,
        media_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a direct message in an existing conversation.
        """
        # Get conversation
        result = await self.db.execute(
            select(DmConversation).where(DmConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")

        # Get account
        account_result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.id == conversation.account_id,
                SocialAccount.user_id == user_id,
            )
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found or access denied")

        # Get adapter and send
        adapter = await self._get_adapter(account.platform)
        if not adapter:
            raise ValueError(f"Platform {account.platform} not supported")

        try:
            send_result = await adapter.send_message(
                access_token=account.access_token,
                user_id=conversation.participant_id,
                text=message_text,
            )

            # Store sent message
            dm = DmMessage(
                conversation_id=conversation.id,
                platform_message_id=send_result.get("id") if isinstance(send_result, dict) else str(uuid.uuid4()),
                content=message_text,
                media_urls=media_urls,
                is_from_me=True,
                is_read=True,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(dm)

            # Update conversation
            conversation.last_message_at = datetime.now(timezone.utc)
            conversation.message_count = (conversation.message_count or 0) + 1

            await self.db.commit()

            return {
                "success": True,
                "message_id": str(dm.id),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def mark_as_spam(
        self,
        user_id: uuid.UUID,
        message_ids: List[uuid.UUID],
    ) -> int:
        """
        Mark comments as spam.
        """
        result = await self.db.execute(
            select(Comment).where(Comment.id.in_(message_ids))
        )
        comments = result.scalars().all()

        count = 0
        for comment in comments:
            comment.is_spam = True
            count += 1

        await self.db.commit()
        return count

    async def archive_messages(
        self,
        user_id: uuid.UUID,
        message_ids: List[uuid.UUID],
        message_type: MessageType,
    ) -> int:
        """
        Archive messages (mark as handled but keep for records).
        """
        # For now, just mark as read - could add archive flag later
        return await self.mark_as_read(user_id, message_ids, message_type)

    # =========================================================================
    # AI FEATURES
    # =========================================================================

    async def analyze_sentiment(
        self,
        message_id: uuid.UUID,
        message_type: MessageType,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment and intent of a message using AI.
        """
        # Get message content
        if message_type == MessageType.DM:
            result = await self.db.execute(
                select(DmMessage).where(DmMessage.id == message_id)
            )
            message = result.scalar_one_or_none()
            content = message.content if message else ""
        else:
            result = await self.db.execute(
                select(Comment).where(Comment.id == message_id)
            )
            message = result.scalar_one_or_none()
            content = message.content if message else ""

        if not content:
            return {"sentiment": "neutral", "intent": "general", "priority": 0}

        client = await self._get_llm_client()

        prompt = f"""Analyze this social media message:

MESSAGE: {content[:500]}

Provide:
1. Sentiment: positive, neutral, negative, question, or urgent
2. Intent: praise, complaint, question, collaboration, spam, support, or general
3. Priority: 0-10 (10 = needs immediate attention)
4. Is this spam? true/false

Return as JSON with keys: sentiment, intent, priority, is_spam"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media analyst who classifies messages accurately.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.3,
        )

        import json
        analysis = {}
        try:
            response_text = response.choices[0].message.content
            if "{" in response_text:
                json_start = response_text.index("{")
                json_end = response_text.rindex("}") + 1
                analysis = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            analysis = {
                "sentiment": "neutral",
                "intent": "general",
                "priority": 0,
                "is_spam": False,
            }

        # Update message in database
        if message:
            if message_type == MessageType.DM:
                message.sentiment = analysis.get("sentiment")
                message.priority = analysis.get("priority", 0)
            else:
                message.sentiment = analysis.get("sentiment")
                message.intent = analysis.get("intent")
                message.priority = analysis.get("priority", 0)
                message.is_spam = analysis.get("is_spam", False)

            await self.db.commit()

        return analysis

    async def suggest_replies(
        self,
        message_id: uuid.UUID,
        message_type: MessageType,
        count: int = 3,
    ) -> List[str]:
        """
        Generate AI-powered reply suggestions.
        """
        # Get message content
        if message_type == MessageType.DM:
            result = await self.db.execute(
                select(DmMessage).where(DmMessage.id == message_id)
            )
            message = result.scalar_one_or_none()
            content = message.content if message else ""
        else:
            result = await self.db.execute(
                select(Comment).where(Comment.id == message_id)
            )
            message = result.scalar_one_or_none()
            content = message.content if message else ""

        if not content:
            return []

        client = await self._get_llm_client()

        prompt = f"""Generate {count} reply suggestions for this social media message:

MESSAGE: {content[:500]}

Requirements:
- Be friendly and professional
- Keep replies concise (under 200 characters each)
- Vary the tone: casual, professional, enthusiastic
- If it's a question, answer helpfully
- If it's a complaint, be empathetic and solution-oriented
- If it's praise, express gratitude

Return as JSON array of strings."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media manager crafting engaging replies.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.8,
        )

        import json
        suggestions = []
        try:
            response_text = response.choices[0].message.content
            if "[" in response_text:
                json_start = response_text.index("[")
                json_end = response_text.rindex("]") + 1
                suggestions = json.loads(response_text[json_start:json_end])
        except (json.JSONDecodeError, ValueError):
            pass

        return suggestions[:count]

    async def bulk_analyze(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> Dict[str, int]:
        """
        Analyze sentiment for unanalyzed messages in bulk.
        """
        # Get accounts
        accounts_result = await self.db.execute(
            select(SocialAccount.id).where(
                SocialAccount.user_id == user_id,
                SocialAccount.is_active == True,
            )
        )
        account_ids = [r[0] for r in accounts_result.all()]

        if not account_ids:
            return {"analyzed": 0}

        # Get unanalyzed comments
        comments_query = (
            select(Comment)
            .where(
                Comment.account_id.in_(account_ids),
                Comment.sentiment.is_(None),
            )
            .limit(limit)
        )
        comments_result = await self.db.execute(comments_query)
        comments = comments_result.scalars().all()

        analyzed = 0
        for comment in comments:
            try:
                await self.analyze_sentiment(comment.id, MessageType.COMMENT)
                analyzed += 1
            except Exception:
                continue

        return {"analyzed": analyzed}

    # =========================================================================
    # SYNC FROM PLATFORMS
    # =========================================================================

    async def sync_inbox(
        self,
        user_id: uuid.UUID,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sync comments and DMs from connected platforms.
        """
        # Get accounts
        query = select(SocialAccount).where(
            SocialAccount.user_id == user_id,
            SocialAccount.is_active == True,
        )
        if platform:
            query = query.where(SocialAccount.platform == platform)

        accounts_result = await self.db.execute(query)
        accounts = accounts_result.scalars().all()

        results = {
            "synced_platforms": [],
            "new_comments": 0,
            "new_dms": 0,
            "errors": [],
        }

        for account in accounts:
            adapter = await self._get_adapter(account.platform)
            if not adapter:
                continue

            try:
                # Sync comments
                # Note: Would need to iterate through posts to get comments
                # This is a simplified version

                # Sync DMs
                messages = await adapter.get_messages(
                    access_token=account.access_token,
                )

                for msg in messages:
                    # Check if conversation exists
                    conv_result = await self.db.execute(
                        select(DmConversation).where(
                            DmConversation.account_id == account.id,
                            DmConversation.platform_conversation_id == msg.get("conversation_id", msg.get("sender_id")),
                        )
                    )
                    conversation = conv_result.scalar_one_or_none()

                    if not conversation:
                        conversation = DmConversation(
                            account_id=account.id,
                            platform_conversation_id=msg.get("conversation_id", msg.get("sender_id")),
                            participant_id=msg.get("sender_id"),
                            participant_name=msg.get("sender_name"),
                            participant_username=msg.get("sender_username"),
                            message_count=0,
                            unread_count=0,
                        )
                        self.db.add(conversation)
                        await self.db.flush()

                    # Check if message exists
                    msg_result = await self.db.execute(
                        select(DmMessage).where(
                            DmMessage.platform_message_id == msg.get("id"),
                        )
                    )
                    existing = msg_result.scalar_one_or_none()

                    if not existing:
                        dm = DmMessage(
                            conversation_id=conversation.id,
                            platform_message_id=msg.get("id"),
                            content=msg.get("text", ""),
                            media_urls=msg.get("media_urls", []),
                            is_from_me=msg.get("is_from_me", False),
                            is_read=False,
                            created_at=msg.get("created_at", datetime.now(timezone.utc)),
                        )
                        self.db.add(dm)

                        conversation.message_count = (conversation.message_count or 0) + 1
                        if not dm.is_from_me:
                            conversation.unread_count = (conversation.unread_count or 0) + 1
                        conversation.last_message_at = dm.created_at

                        results["new_dms"] += 1

                await self.db.commit()
                results["synced_platforms"].append(account.platform)

            except Exception as e:
                results["errors"].append({
                    "platform": account.platform,
                    "error": str(e),
                })

        return results
