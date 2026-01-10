"""
Base Platform Adapter Interface

Abstract interface for social media platform integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Optional
import uuid


class ContentType(str, Enum):
    """Types of content that can be published."""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    SHORT = "short"
    VIDEO = "video"
    TWEET = "tweet"
    THREAD = "thread"
    ARTICLE = "article"
    CAROUSEL = "carousel"


@dataclass
class OAuthTokens:
    """OAuth token data."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    token_type: str = "Bearer"
    raw_response: dict = field(default_factory=dict)


@dataclass
class AccountInfo:
    """Social account information."""
    platform_user_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    account_type: Optional[str] = None  # 'personal', 'business', 'creator'
    follower_count: int = 0
    following_count: int = 0
    capabilities: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


@dataclass
class PublishContent:
    """Content to publish to a platform."""
    content_type: ContentType
    text: Optional[str] = None
    media_urls: list[str] = field(default_factory=list)
    media_files: list[bytes] = field(default_factory=list)

    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)

    # Scheduling
    scheduled_at: Optional[datetime] = None

    # Platform-specific options
    extras: dict = field(default_factory=dict)


@dataclass
class PublishResult:
    """Result of publishing content."""
    success: bool
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry
    metadata: dict = field(default_factory=dict)


@dataclass
class Comment:
    """Social media comment."""
    platform_comment_id: str
    author_id: str
    author_username: Optional[str] = None
    author_display_name: Optional[str] = None
    author_avatar_url: Optional[str] = None
    content: str = ""
    like_count: int = 0
    reply_count: int = 0
    posted_at: Optional[datetime] = None
    parent_comment_id: Optional[str] = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class DirectMessage:
    """Direct message."""
    platform_message_id: str
    conversation_id: str
    sender_id: str
    sender_username: Optional[str] = None
    content: Optional[str] = None
    media_urls: list[str] = field(default_factory=list)
    sent_at: Optional[datetime] = None
    is_outgoing: bool = False
    raw_response: dict = field(default_factory=dict)


@dataclass
class AnalyticsData:
    """Analytics data for a time period."""
    date: datetime
    follower_count: int = 0
    follower_change: int = 0
    total_reach: int = 0
    total_impressions: int = 0
    total_engagements: int = 0
    engagement_rate: float = 0.0
    likes_received: int = 0
    comments_received: int = 0
    shares_received: int = 0
    saves_received: int = 0
    profile_visits: int = 0
    website_clicks: int = 0
    audience_demographics: dict = field(default_factory=dict)
    raw_response: dict = field(default_factory=dict)


@dataclass
class PostMetrics:
    """Metrics for a specific post."""
    platform_post_id: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    save_count: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    raw_response: dict = field(default_factory=dict)


class BasePlatformAdapter(ABC):
    """
    Abstract base class for social media platform adapters.

    Implement this interface to add support for new platforms
    (YouTube, Instagram, TikTok, X, Facebook, LinkedIn).
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Unique identifier for this platform."""
        pass

    @property
    @abstractmethod
    def supported_content_types(self) -> list[ContentType]:
        """Content types this platform supports."""
        pass

    @property
    def requires_oauth(self) -> bool:
        """Whether this platform requires OAuth authentication."""
        return True

    @property
    def supports_scheduling(self) -> bool:
        """Whether this platform supports scheduled posts."""
        return False

    @property
    def supports_analytics(self) -> bool:
        """Whether this platform provides analytics."""
        return True

    @property
    def supports_comments(self) -> bool:
        """Whether we can read/reply to comments."""
        return True

    @property
    def supports_dms(self) -> bool:
        """Whether we can read/send direct messages."""
        return False

    # ==================== OAuth ====================

    @abstractmethod
    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """
        Get OAuth authorization URL for user to grant access.

        Args:
            redirect_uri: Callback URL after authorization
            state: CSRF protection state token
            scopes: Requested permission scopes

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            OAuth tokens
        """
        pass

    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """
        Refresh an expired access token.

        Args:
            refresh_token: Refresh token from previous exchange

        Returns:
            New OAuth tokens
        """
        pass

    # ==================== Account ====================

    @abstractmethod
    async def get_account_info(
        self,
        access_token: str,
    ) -> AccountInfo:
        """
        Get information about the authenticated account.

        Args:
            access_token: Valid access token

        Returns:
            Account information
        """
        pass

    async def verify_token(
        self,
        access_token: str,
    ) -> bool:
        """
        Verify that an access token is still valid.

        Default implementation tries to get account info.
        """
        try:
            await self.get_account_info(access_token)
            return True
        except Exception:
            return False

    # ==================== Publishing ====================

    @abstractmethod
    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish content to the platform.

        Args:
            access_token: Valid access token
            content: Content to publish

        Returns:
            Publishing result
        """
        pass

    async def upload_media(
        self,
        access_token: str,
        media_data: bytes,
        media_type: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Upload media to the platform (for platforms requiring pre-upload).

        Args:
            access_token: Valid access token
            media_data: Media file bytes
            media_type: MIME type
            filename: Optional filename

        Returns:
            Platform media ID or URL
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support separate media upload"
        )

    async def delete_post(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> bool:
        """
        Delete a published post.

        Args:
            access_token: Valid access token
            platform_post_id: Platform's post ID

        Returns:
            True if successfully deleted
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support post deletion"
        )

    # ==================== Analytics ====================

    @abstractmethod
    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[AnalyticsData]:
        """
        Get account analytics for a date range.

        Args:
            access_token: Valid access token
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of daily analytics
        """
        pass

    async def get_post_metrics(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> PostMetrics:
        """
        Get metrics for a specific post.

        Args:
            access_token: Valid access token
            platform_post_id: Platform's post ID

        Returns:
            Post metrics
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support individual post metrics"
        )

    # ==================== Comments ====================

    async def get_comments(
        self,
        access_token: str,
        platform_post_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[Comment], Optional[str]]:
        """
        Get comments on a post.

        Args:
            access_token: Valid access token
            platform_post_id: Platform's post ID
            cursor: Pagination cursor
            limit: Maximum comments to return

        Returns:
            Tuple of (comments, next_cursor)
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support comment reading"
        )

    async def reply_to_comment(
        self,
        access_token: str,
        platform_comment_id: str,
        text: str,
    ) -> Comment:
        """
        Reply to a comment.

        Args:
            access_token: Valid access token
            platform_comment_id: Platform's comment ID
            text: Reply text

        Returns:
            Created reply comment
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support comment replies"
        )

    async def delete_comment(
        self,
        access_token: str,
        platform_comment_id: str,
    ) -> bool:
        """
        Delete a comment.

        Args:
            access_token: Valid access token
            platform_comment_id: Platform's comment ID

        Returns:
            True if successfully deleted
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support comment deletion"
        )

    # ==================== Direct Messages ====================

    async def get_conversations(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> tuple[list[dict], Optional[str]]:
        """
        Get DM conversations.

        Returns:
            Tuple of (conversations, next_cursor)
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support direct messages"
        )

    async def get_messages(
        self,
        access_token: str,
        conversation_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[DirectMessage], Optional[str]]:
        """
        Get messages in a conversation.

        Returns:
            Tuple of (messages, next_cursor)
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support direct messages"
        )

    async def send_message(
        self,
        access_token: str,
        recipient_id: str,
        text: Optional[str] = None,
        media_url: Optional[str] = None,
    ) -> DirectMessage:
        """
        Send a direct message.

        Returns:
            Sent message
        """
        raise NotImplementedError(
            f"{self.platform_name} does not support direct messages"
        )

    # ==================== Utilities ====================

    def validate_content(
        self,
        content: PublishContent,
    ) -> tuple[bool, list[str]]:
        """
        Validate content before publishing.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if content.content_type not in self.supported_content_types:
            issues.append(
                f"{content.content_type} is not supported on {self.platform_name}"
            )

        return len(issues) == 0, issues

    async def get_rate_limit_status(
        self,
        access_token: str,
    ) -> dict:
        """
        Get current rate limit status.

        Returns:
            Rate limit info (remaining, limit, reset_at)
        """
        return {
            "remaining": None,
            "limit": None,
            "reset_at": None,
        }
