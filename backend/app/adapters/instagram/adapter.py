"""
Instagram Platform Adapter

Integration with Instagram Graph API for content publishing and analytics.
https://developers.facebook.com/docs/instagram-api
"""

import httpx
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from app.config import settings
from app.adapters.interfaces.base import (
    BasePlatformAdapter,
    ContentType,
    OAuthTokens,
    AccountInfo,
    PublishContent,
    PublishResult,
    AnalyticsData,
    PostMetrics,
    Comment,
    DirectMessage,
)


class InstagramAdapter(BasePlatformAdapter):
    """
    Instagram platform adapter.

    Uses Instagram Graph API (requires Facebook Business account).

    Supports:
    - Feed posts (images, carousels)
    - Reels
    - Stories (limited API support)
    - Analytics/Insights
    - Comment management
    - Direct messages (with approval)
    """

    OAUTH_BASE_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    API_BASE_URL = "https://graph.facebook.com/v18.0"

    DEFAULT_SCOPES = [
        "instagram_basic",
        "instagram_content_publish",
        "instagram_manage_comments",
        "instagram_manage_insights",
        "instagram_manage_messages",
        "pages_show_list",
        "pages_read_engagement",
        "business_management",
    ]

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        self.app_id = app_id or settings.instagram_app_id
        self.app_secret = app_secret or settings.instagram_app_secret
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def platform_name(self) -> str:
        return "instagram"

    @property
    def supported_content_types(self) -> list[ContentType]:
        return [ContentType.POST, ContentType.REEL, ContentType.STORY, ContentType.CAROUSEL]

    @property
    def supports_scheduling(self) -> bool:
        return True  # Via Facebook Creator Studio

    @property
    def supports_analytics(self) -> bool:
        return True

    @property
    def supports_comments(self) -> bool:
        return True

    @property
    def supports_dms(self) -> bool:
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    # ==================== OAuth ====================

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """Get Facebook OAuth authorization URL for Instagram."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(scopes or self.DEFAULT_SCOPES),
            "response_type": "code",
        }
        return f"{self.OAUTH_BASE_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """Exchange authorization code for access token."""
        client = await self._get_client()

        # Get short-lived token
        response = await client.get(
            f"{self.API_BASE_URL}/oauth/access_token",
            params={
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")

        data = response.json()
        short_lived_token = data["access_token"]

        # Exchange for long-lived token
        long_response = await client.get(
            f"{self.API_BASE_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short_lived_token,
            },
        )

        if long_response.status_code != 200:
            raise Exception(f"Long-lived token exchange failed: {long_response.text}")

        long_data = long_response.json()

        expires_at = None
        if "expires_in" in long_data:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(seconds=long_data["expires_in"])

        return OAuthTokens(
            access_token=long_data["access_token"],
            refresh_token=None,  # Facebook uses long-lived tokens
            expires_at=expires_at,
            token_type=long_data.get("token_type", "Bearer"),
            raw_response=long_data,
        )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """
        Refresh long-lived token.

        Facebook tokens can be refreshed if they haven't expired yet.
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": refresh_token,  # Use current token as exchange token
            },
        )

        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.text}")

        data = response.json()

        expires_at = None
        if "expires_in" in data:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])

        return OAuthTokens(
            access_token=data["access_token"],
            expires_at=expires_at,
            token_type=data.get("token_type", "Bearer"),
            raw_response=data,
        )

    # ==================== Account ====================

    async def get_account_info(
        self,
        access_token: str,
    ) -> AccountInfo:
        """Get Instagram business account information."""
        client = await self._get_client()

        # First get Facebook Pages
        pages_response = await client.get(
            f"{self.API_BASE_URL}/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,instagram_business_account",
            },
        )

        if pages_response.status_code != 200:
            raise Exception(f"Failed to get pages: {pages_response.text}")

        pages_data = pages_response.json()

        # Find page with Instagram account
        ig_account_id = None
        for page in pages_data.get("data", []):
            if page.get("instagram_business_account"):
                ig_account_id = page["instagram_business_account"]["id"]
                break

        if not ig_account_id:
            raise Exception("No Instagram Business account found")

        # Get Instagram account details
        ig_response = await client.get(
            f"{self.API_BASE_URL}/{ig_account_id}",
            params={
                "access_token": access_token,
                "fields": "id,username,name,profile_picture_url,followers_count,follows_count,media_count,biography,website",
            },
        )

        if ig_response.status_code != 200:
            raise Exception(f"Failed to get Instagram account: {ig_response.text}")

        ig_data = ig_response.json()

        return AccountInfo(
            platform_user_id=ig_data["id"],
            username=ig_data.get("username"),
            display_name=ig_data.get("name"),
            profile_url=f"https://www.instagram.com/{ig_data.get('username', '')}",
            profile_image_url=ig_data.get("profile_picture_url"),
            account_type="business",
            follower_count=ig_data.get("followers_count", 0),
            following_count=ig_data.get("follows_count", 0),
            capabilities={
                "can_post_feed": True,
                "can_post_reels": True,
                "can_post_stories": True,
                "can_access_insights": True,
            },
            raw_response=ig_data,
        )

    async def _get_ig_account_id(self, access_token: str) -> str:
        """Get Instagram Business Account ID from token."""
        account_info = await self.get_account_info(access_token)
        return account_info.platform_user_id

    # ==================== Publishing ====================

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish content to Instagram.

        Instagram API requires a two-step process:
        1. Create media container
        2. Publish the container
        """
        ig_account_id = await self._get_ig_account_id(access_token)

        if content.content_type == ContentType.REEL:
            return await self._publish_reel(access_token, ig_account_id, content)
        elif content.content_type == ContentType.CAROUSEL:
            return await self._publish_carousel(access_token, ig_account_id, content)
        elif content.content_type == ContentType.STORY:
            return await self._publish_story(access_token, ig_account_id, content)
        else:
            return await self._publish_feed_post(access_token, ig_account_id, content)

    async def _publish_feed_post(
        self,
        access_token: str,
        ig_account_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a single image/video feed post."""
        client = await self._get_client()

        if not content.media_urls:
            return PublishResult(
                success=False,
                error_message="Media URL is required",
            )

        media_url = content.media_urls[0]
        is_video = any(ext in media_url.lower() for ext in [".mp4", ".mov", ".avi"])

        caption = content.text or ""
        if content.hashtags:
            caption += "\n\n" + " ".join(f"#{tag}" for tag in content.hashtags)

        # Step 1: Create media container
        container_params = {
            "access_token": access_token,
            "caption": caption[:2200],  # Instagram caption limit
        }

        if is_video:
            container_params["media_type"] = "VIDEO"
            container_params["video_url"] = media_url
        else:
            container_params["image_url"] = media_url

        container_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media",
            data=container_params,
        )

        if container_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to create container: {container_response.text}",
            )

        container_id = container_response.json().get("id")

        # For video, wait for processing
        if is_video:
            await self._wait_for_container(access_token, container_id)

        # Step 2: Publish container
        publish_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media_publish",
            data={
                "access_token": access_token,
                "creation_id": container_id,
            },
        )

        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to publish: {publish_response.text}",
            )

        media_id = publish_response.json().get("id")

        # Get permalink
        permalink_response = await client.get(
            f"{self.API_BASE_URL}/{media_id}",
            params={
                "access_token": access_token,
                "fields": "permalink",
            },
        )

        permalink = None
        if permalink_response.status_code == 200:
            permalink = permalink_response.json().get("permalink")

        return PublishResult(
            success=True,
            platform_post_id=media_id,
            platform_post_url=permalink,
            metadata={"container_id": container_id},
        )

    async def _publish_reel(
        self,
        access_token: str,
        ig_account_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a Reel."""
        client = await self._get_client()

        if not content.media_urls:
            return PublishResult(
                success=False,
                error_message="Video URL is required for Reels",
            )

        caption = content.text or ""
        if content.hashtags:
            caption += "\n\n" + " ".join(f"#{tag}" for tag in content.hashtags)

        # Create Reel container
        container_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media",
            data={
                "access_token": access_token,
                "media_type": "REELS",
                "video_url": content.media_urls[0],
                "caption": caption[:2200],
                "share_to_feed": content.extras.get("share_to_feed", True),
            },
        )

        if container_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to create Reel container: {container_response.text}",
            )

        container_id = container_response.json().get("id")

        # Wait for video processing
        await self._wait_for_container(access_token, container_id)

        # Publish
        publish_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media_publish",
            data={
                "access_token": access_token,
                "creation_id": container_id,
            },
        )

        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to publish Reel: {publish_response.text}",
            )

        media_id = publish_response.json().get("id")

        return PublishResult(
            success=True,
            platform_post_id=media_id,
            platform_post_url=f"https://www.instagram.com/reel/{media_id}/",
        )

    async def _publish_carousel(
        self,
        access_token: str,
        ig_account_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a carousel post with multiple images/videos."""
        client = await self._get_client()

        if len(content.media_urls) < 2:
            return PublishResult(
                success=False,
                error_message="Carousel requires at least 2 media items",
            )

        # Create individual media containers
        children_ids = []
        for media_url in content.media_urls[:10]:  # Max 10 items
            is_video = any(ext in media_url.lower() for ext in [".mp4", ".mov"])

            child_params = {
                "access_token": access_token,
                "is_carousel_item": True,
            }

            if is_video:
                child_params["media_type"] = "VIDEO"
                child_params["video_url"] = media_url
            else:
                child_params["image_url"] = media_url

            child_response = await client.post(
                f"{self.API_BASE_URL}/{ig_account_id}/media",
                data=child_params,
            )

            if child_response.status_code != 200:
                continue

            child_id = child_response.json().get("id")

            if is_video:
                await self._wait_for_container(access_token, child_id)

            children_ids.append(child_id)

        if len(children_ids) < 2:
            return PublishResult(
                success=False,
                error_message="Failed to create enough media items for carousel",
            )

        caption = content.text or ""
        if content.hashtags:
            caption += "\n\n" + " ".join(f"#{tag}" for tag in content.hashtags)

        # Create carousel container
        carousel_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media",
            data={
                "access_token": access_token,
                "media_type": "CAROUSEL",
                "caption": caption[:2200],
                "children": ",".join(children_ids),
            },
        )

        if carousel_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to create carousel: {carousel_response.text}",
            )

        container_id = carousel_response.json().get("id")

        # Publish
        publish_response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/media_publish",
            data={
                "access_token": access_token,
                "creation_id": container_id,
            },
        )

        if publish_response.status_code != 200:
            return PublishResult(
                success=False,
                error_message=f"Failed to publish carousel: {publish_response.text}",
            )

        media_id = publish_response.json().get("id")

        return PublishResult(
            success=True,
            platform_post_id=media_id,
        )

    async def _publish_story(
        self,
        access_token: str,
        ig_account_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a Story."""
        # Stories API is limited for third-party apps
        return PublishResult(
            success=False,
            error_message="Story publishing via API is currently limited",
        )

    async def _wait_for_container(
        self,
        access_token: str,
        container_id: str,
        max_attempts: int = 30,
    ):
        """Wait for video container to finish processing."""
        import asyncio

        client = await self._get_client()

        for _ in range(max_attempts):
            status_response = await client.get(
                f"{self.API_BASE_URL}/{container_id}",
                params={
                    "access_token": access_token,
                    "fields": "status_code",
                },
            )

            if status_response.status_code == 200:
                status = status_response.json().get("status_code")
                if status == "FINISHED":
                    return
                elif status == "ERROR":
                    raise Exception("Container processing failed")

            await asyncio.sleep(2)

        raise Exception("Container processing timeout")

    # ==================== Analytics ====================

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[AnalyticsData]:
        """Get Instagram Insights."""
        client = await self._get_client()
        ig_account_id = await self._get_ig_account_id(access_token)

        # Get account insights
        response = await client.get(
            f"{self.API_BASE_URL}/{ig_account_id}/insights",
            params={
                "access_token": access_token,
                "metric": "impressions,reach,follower_count,profile_views,website_clicks",
                "period": "day",
                "since": int(start_date.timestamp()),
                "until": int(end_date.timestamp()),
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get insights: {response.text}")

        data = response.json()

        # Process insights data
        results = []
        metrics_by_date = {}

        for metric in data.get("data", []):
            metric_name = metric["name"]
            for value in metric.get("values", []):
                date_str = value["end_time"][:10]
                if date_str not in metrics_by_date:
                    metrics_by_date[date_str] = {}
                metrics_by_date[date_str][metric_name] = value["value"]

        for date_str, metrics in metrics_by_date.items():
            results.append(
                AnalyticsData(
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    total_impressions=metrics.get("impressions", 0),
                    total_reach=metrics.get("reach", 0),
                    follower_count=metrics.get("follower_count", 0),
                    profile_visits=metrics.get("profile_views", 0),
                    website_clicks=metrics.get("website_clicks", 0),
                    raw_response=metrics,
                )
            )

        return results

    async def get_post_metrics(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> PostMetrics:
        """Get metrics for a specific post."""
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/{platform_post_id}/insights",
            params={
                "access_token": access_token,
                "metric": "impressions,reach,likes,comments,shares,saved",
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get post insights: {response.text}")

        data = response.json()

        metrics = {}
        for item in data.get("data", []):
            metrics[item["name"]] = item["values"][0]["value"] if item.get("values") else 0

        return PostMetrics(
            platform_post_id=platform_post_id,
            impressions=metrics.get("impressions", 0),
            reach=metrics.get("reach", 0),
            like_count=metrics.get("likes", 0),
            comment_count=metrics.get("comments", 0),
            share_count=metrics.get("shares", 0),
            save_count=metrics.get("saved", 0),
            raw_response=metrics,
        )

    # ==================== Comments ====================

    async def get_comments(
        self,
        access_token: str,
        platform_post_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[Comment], Optional[str]]:
        """Get comments on a post."""
        client = await self._get_client()

        params = {
            "access_token": access_token,
            "fields": "id,text,timestamp,username,like_count,replies{id,text,timestamp,username}",
            "limit": limit,
        }

        if cursor:
            params["after"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/{platform_post_id}/comments",
            params=params,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get comments: {response.text}")

        data = response.json()
        comments = []

        for item in data.get("data", []):
            comments.append(
                Comment(
                    platform_comment_id=item["id"],
                    author_id=item.get("username", ""),
                    author_username=item.get("username"),
                    content=item.get("text", ""),
                    like_count=item.get("like_count", 0),
                    reply_count=len(item.get("replies", {}).get("data", [])),
                    posted_at=datetime.fromisoformat(
                        item.get("timestamp", "").replace("Z", "+00:00")
                    ) if item.get("timestamp") else None,
                    raw_response=item,
                )
            )

        next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
        return comments, next_cursor

    async def reply_to_comment(
        self,
        access_token: str,
        platform_comment_id: str,
        text: str,
    ) -> Comment:
        """Reply to a comment."""
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/{platform_comment_id}/replies",
            data={
                "access_token": access_token,
                "message": text,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to reply: {response.text}")

        reply_id = response.json().get("id")

        return Comment(
            platform_comment_id=reply_id,
            author_id="",
            content=text,
            parent_comment_id=platform_comment_id,
            posted_at=datetime.utcnow(),
        )

    # ==================== Direct Messages ====================

    async def get_conversations(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> tuple[list[dict], Optional[str]]:
        """Get DM conversations."""
        client = await self._get_client()
        ig_account_id = await self._get_ig_account_id(access_token)

        params = {
            "access_token": access_token,
            "fields": "participants,updated_time,messages{message,created_time,from}",
            "limit": limit,
        }

        if cursor:
            params["after"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/{ig_account_id}/conversations",
            params=params,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get conversations: {response.text}")

        data = response.json()
        conversations = data.get("data", [])
        next_cursor = data.get("paging", {}).get("cursors", {}).get("after")

        return conversations, next_cursor

    async def send_message(
        self,
        access_token: str,
        recipient_id: str,
        text: Optional[str] = None,
        media_url: Optional[str] = None,
    ) -> DirectMessage:
        """Send a direct message."""
        client = await self._get_client()
        ig_account_id = await self._get_ig_account_id(access_token)

        message_data = {
            "access_token": access_token,
            "recipient": {"id": recipient_id},
        }

        if text:
            message_data["message"] = {"text": text}
        elif media_url:
            message_data["message"] = {
                "attachment": {
                    "type": "image",
                    "payload": {"url": media_url},
                }
            }

        response = await client.post(
            f"{self.API_BASE_URL}/{ig_account_id}/messages",
            json=message_data,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.text}")

        data = response.json()

        return DirectMessage(
            platform_message_id=data.get("message_id", ""),
            conversation_id="",
            sender_id=ig_account_id,
            content=text,
            is_outgoing=True,
            sent_at=datetime.utcnow(),
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
