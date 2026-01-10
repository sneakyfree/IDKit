"""
Facebook Platform Adapter

Implements Facebook Graph API for posting to Pages, Groups,
Stories, analytics, and engagement management.

Facebook API Documentation:
- Graph API: https://developers.facebook.com/docs/graph-api
- Marketing API: https://developers.facebook.com/docs/marketing-api
"""

from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.adapters.interfaces.base import (
    AnalyticsData,
    BasePlatformAdapter,
    Comment,
    Message,
    OAuthTokens,
    PublishContent,
    PublishResult,
    UserProfile,
)


class FacebookAdapter(BasePlatformAdapter):
    """
    Facebook platform adapter for Pages and Groups.

    Uses Facebook Graph API with OAuth 2.0.
    """

    AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    API_BASE_URL = "https://graph.facebook.com/v18.0"

    # Available permissions
    PERMISSIONS = {
        "public_profile": "Read basic profile info",
        "email": "Read email address",
        "pages_show_list": "List user's Pages",
        "pages_read_engagement": "Read Page engagement data",
        "pages_manage_posts": "Create and manage Page posts",
        "pages_manage_engagement": "Manage Page comments and reactions",
        "pages_read_user_content": "Read user-generated content on Pages",
        "pages_messaging": "Manage Page conversations",
        "publish_video": "Upload videos to Pages",
        "groups_access_member_info": "Access group member info",
        "publish_to_groups": "Post to groups",
        "business_management": "Manage business assets",
    }

    def __init__(self, app_id: str, app_secret: str):
        """
        Initialize Facebook adapter.

        Args:
            app_id: Facebook app ID
            app_secret: Facebook app secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """
        Generate Facebook OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF protection state parameter
            scopes: List of permission scopes

        Returns:
            Authorization URL for user consent
        """
        if scopes is None:
            scopes = [
                "public_profile",
                "email",
                "pages_show_list",
                "pages_read_engagement",
                "pages_manage_posts",
                "pages_manage_engagement",
            ]

        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code",
        }

        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthTokens:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code from callback
            redirect_uri: OAuth callback URL

        Returns:
            OAuth tokens
        """
        client = await self._get_client()

        # Get short-lived token
        response = await client.get(
            self.TOKEN_URL,
            params={
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        result = response.json()

        # Exchange for long-lived token
        long_lived_response = await client.get(
            self.TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": result["access_token"],
            },
        )
        long_lived_response.raise_for_status()
        long_lived_result = long_lived_response.json()

        return OAuthTokens(
            access_token=long_lived_result["access_token"],
            refresh_token=None,  # Facebook doesn't use refresh tokens
            expires_in=long_lived_result.get("expires_in"),
            token_type="Bearer",
            scope=None,
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh an access token.

        Note: Facebook long-lived tokens can be refreshed by exchanging
        them again before expiration.

        Args:
            refresh_token: Current access token (Facebook uses access token)

        Returns:
            New OAuth tokens
        """
        client = await self._get_client()

        response = await client.get(
            self.TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": refresh_token,
            },
        )
        response.raise_for_status()
        result = response.json()

        return OAuthTokens(
            access_token=result["access_token"],
            refresh_token=None,
            expires_in=result.get("expires_in"),
            token_type="Bearer",
            scope=None,
        )

    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token.

        Args:
            access_token: Token to revoke

        Returns:
            True if revocation successful
        """
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/me/permissions",
            params={"access_token": access_token},
        )

        return response.status_code == 200

    async def get_user_profile(self, access_token: str) -> UserProfile:
        """
        Get authenticated user's profile.

        Args:
            access_token: Valid access token

        Returns:
            User profile information
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/me",
            params={
                "access_token": access_token,
                "fields": "id,name,email,picture.type(large),link",
            },
        )
        response.raise_for_status()
        user = response.json()

        return UserProfile(
            id=user.get("id"),
            username=None,  # Facebook doesn't have usernames
            display_name=user.get("name"),
            avatar_url=user.get("picture", {}).get("data", {}).get("url"),
            bio=None,
            email=user.get("email"),
            profile_url=user.get("link"),
            raw_data=user,
        )

    async def get_pages(self, access_token: str) -> list[dict]:
        """
        Get Pages managed by the user.

        Args:
            access_token: Valid access token with pages_show_list permission

        Returns:
            List of Page data with access tokens
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/me/accounts",
            params={
                "access_token": access_token,
                "fields": "id,name,access_token,category,picture.type(large),fan_count,followers_count,link",
            },
        )
        response.raise_for_status()

        return response.json().get("data", [])

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish content to Facebook (Page or User timeline).

        Args:
            access_token: Valid access token (use Page token for Page posts)
            content: Content to publish

        Returns:
            Publish result with post ID
        """
        client = await self._get_client()

        # Determine target (page_id from metadata or 'me')
        target_id = content.metadata.get("page_id", "me") if content.metadata else "me"

        # Build post data
        post_data = {
            "access_token": access_token,
        }

        if content.text:
            post_data["message"] = content.text

        # Handle different content types
        if content.video_url:
            # Video upload
            return await self._publish_video(access_token, target_id, content)
        elif content.image_urls:
            # Photo(s) upload
            if len(content.image_urls) == 1:
                return await self._publish_photo(access_token, target_id, content)
            else:
                return await self._publish_photos(access_token, target_id, content)
        else:
            # Text-only post
            response = await client.post(
                f"{self.API_BASE_URL}/{target_id}/feed",
                data=post_data,
            )
            response.raise_for_status()
            result = response.json()

            post_id = result.get("id")
            return PublishResult(
                success=True,
                platform_post_id=post_id,
                url=f"https://facebook.com/{post_id}" if post_id else None,
                raw_response=result,
            )

    async def _publish_photo(
        self,
        access_token: str,
        target_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a single photo."""
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/{target_id}/photos",
            data={
                "access_token": access_token,
                "url": content.image_urls[0],
                "caption": content.text or "",
            },
        )
        response.raise_for_status()
        result = response.json()

        photo_id = result.get("id")
        post_id = result.get("post_id")

        return PublishResult(
            success=True,
            platform_post_id=post_id or photo_id,
            url=f"https://facebook.com/{post_id}" if post_id else None,
            raw_response=result,
        )

    async def _publish_photos(
        self,
        access_token: str,
        target_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish multiple photos as a carousel."""
        client = await self._get_client()

        # Upload photos without publishing
        photo_ids = []
        for image_url in content.image_urls[:10]:  # Max 10 photos
            response = await client.post(
                f"{self.API_BASE_URL}/{target_id}/photos",
                data={
                    "access_token": access_token,
                    "url": image_url,
                    "published": "false",
                },
            )
            response.raise_for_status()
            photo_ids.append(response.json().get("id"))

        # Create multi-photo post
        attached_media = [{"media_fbid": pid} for pid in photo_ids]

        response = await client.post(
            f"{self.API_BASE_URL}/{target_id}/feed",
            data={
                "access_token": access_token,
                "message": content.text or "",
            },
            json={"attached_media": attached_media},
        )
        response.raise_for_status()
        result = response.json()

        post_id = result.get("id")
        return PublishResult(
            success=True,
            platform_post_id=post_id,
            url=f"https://facebook.com/{post_id}" if post_id else None,
            raw_response=result,
        )

    async def _publish_video(
        self,
        access_token: str,
        target_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """Publish a video."""
        client = await self._get_client()

        # Facebook supports URL-based video upload
        response = await client.post(
            f"{self.API_BASE_URL}/{target_id}/videos",
            data={
                "access_token": access_token,
                "file_url": content.video_url,
                "description": content.text or "",
                "title": content.metadata.get("title", "") if content.metadata else "",
            },
        )
        response.raise_for_status()
        result = response.json()

        video_id = result.get("id")
        return PublishResult(
            success=True,
            platform_post_id=video_id,
            url=f"https://facebook.com/{video_id}" if video_id else None,
            raw_response=result,
        )

    async def publish_to_story(
        self,
        access_token: str,
        page_id: str,
        media_url: str,
        media_type: str = "photo",
    ) -> PublishResult:
        """
        Publish to Page Story.

        Args:
            access_token: Page access token
            page_id: Page ID
            media_url: URL of media to share
            media_type: 'photo' or 'video'

        Returns:
            Publish result
        """
        client = await self._get_client()

        if media_type == "video":
            endpoint = f"{self.API_BASE_URL}/{page_id}/video_stories"
            data = {"video_url": media_url}
        else:
            endpoint = f"{self.API_BASE_URL}/{page_id}/photo_stories"
            data = {"photo_url": media_url}

        data["access_token"] = access_token

        response = await client.post(endpoint, data=data)
        response.raise_for_status()
        result = response.json()

        return PublishResult(
            success=True,
            platform_post_id=result.get("id"),
            raw_response=result,
        )

    async def delete_post(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> bool:
        """
        Delete a post.

        Args:
            access_token: Valid access token
            platform_post_id: Post ID to delete

        Returns:
            True if deletion successful
        """
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/{platform_post_id}",
            params={"access_token": access_token},
        )

        return response.status_code == 200

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        platform_post_id: Optional[str] = None,
    ) -> list[AnalyticsData]:
        """
        Get Page/Post analytics.

        Args:
            access_token: Page access token
            start_date: Analytics start date
            end_date: Analytics end date
            platform_post_id: Optional specific post ID

        Returns:
            List of analytics data
        """
        client = await self._get_client()

        if platform_post_id:
            # Get specific post insights
            response = await client.get(
                f"{self.API_BASE_URL}/{platform_post_id}/insights",
                params={
                    "access_token": access_token,
                    "metric": "post_impressions,post_impressions_unique,post_engaged_users,post_reactions_by_type_total",
                },
            )
            response.raise_for_status()
            result = response.json()

            metrics = {item["name"]: item["values"][0]["value"] for item in result.get("data", [])}

            reactions = metrics.get("post_reactions_by_type_total", {})
            total_reactions = sum(reactions.values()) if isinstance(reactions, dict) else 0

            return [AnalyticsData(
                date=datetime.utcnow(),
                impressions=metrics.get("post_impressions", 0),
                reach=metrics.get("post_impressions_unique", 0),
                engagement=metrics.get("post_engaged_users", 0),
                likes=total_reactions,
                raw_data=result,
            )]

        # Get Page insights
        # First get the page ID from posts or use 'me'
        response = await client.get(
            f"{self.API_BASE_URL}/me/insights",
            params={
                "access_token": access_token,
                "metric": "page_impressions,page_impressions_unique,page_engaged_users,page_post_engagements,page_fans",
                "period": "day",
                "since": int(start_date.timestamp()),
                "until": int(end_date.timestamp()),
            },
        )
        response.raise_for_status()
        result = response.json()

        # Process page insights
        analytics = []
        metrics_by_date = {}

        for metric_data in result.get("data", []):
            metric_name = metric_data["name"]
            for value_data in metric_data.get("values", []):
                date_str = value_data.get("end_time", "")[:10]
                if date_str not in metrics_by_date:
                    metrics_by_date[date_str] = {}
                metrics_by_date[date_str][metric_name] = value_data.get("value", 0)

        for date_str, metrics in metrics_by_date.items():
            analytics.append(AnalyticsData(
                date=datetime.fromisoformat(date_str),
                impressions=metrics.get("page_impressions", 0),
                reach=metrics.get("page_impressions_unique", 0),
                engagement=metrics.get("page_engaged_users", 0),
                followers=metrics.get("page_fans", 0),
                raw_data=metrics,
            ))

        return analytics

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
            platform_post_id: Post ID
            cursor: Pagination cursor
            limit: Maximum comments to return

        Returns:
            Tuple of (comments list, next cursor)
        """
        client = await self._get_client()

        params = {
            "access_token": access_token,
            "fields": "id,message,created_time,from{id,name,picture},like_count,comment_count,parent{id}",
            "limit": min(limit, 100),
        }

        if cursor:
            params["after"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/{platform_post_id}/comments",
            params=params,
        )
        response.raise_for_status()
        result = response.json()

        comments = []
        for item in result.get("data", []):
            author = item.get("from", {})
            comments.append(Comment(
                id=item.get("id"),
                post_id=platform_post_id,
                text=item.get("message"),
                author_id=author.get("id"),
                author_name=author.get("name"),
                author_avatar=author.get("picture", {}).get("data", {}).get("url"),
                created_at=datetime.fromisoformat(item.get("created_time", "").replace("+0000", "+00:00")),
                like_count=item.get("like_count", 0),
                reply_count=item.get("comment_count", 0),
                parent_id=item.get("parent", {}).get("id"),
                raw_data=item,
            ))

        paging = result.get("paging", {})
        next_cursor = paging.get("cursors", {}).get("after") if paging.get("next") else None

        return comments, next_cursor

    async def reply_to_comment(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> Optional[Comment]:
        """
        Reply to a comment.

        Args:
            access_token: Valid access token
            comment_id: Comment ID to reply to
            text: Reply text

        Returns:
            Created reply comment
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/{comment_id}/comments",
            data={
                "access_token": access_token,
                "message": text,
            },
        )
        response.raise_for_status()
        result = response.json()

        return Comment(
            id=result.get("id"),
            post_id=comment_id,
            text=text,
            created_at=datetime.utcnow(),
            parent_id=comment_id,
            raw_data=result,
        )

    async def get_messages(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[Message], Optional[str]]:
        """
        Get Page conversations.

        Requires pages_messaging permission.

        Args:
            access_token: Page access token
            cursor: Pagination cursor
            limit: Maximum conversations to return

        Returns:
            Tuple of (messages list, next cursor)
        """
        client = await self._get_client()

        params = {
            "access_token": access_token,
            "fields": "id,participants,messages{id,message,from,created_time}",
            "limit": min(limit, 100),
        }

        if cursor:
            params["after"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/me/conversations",
            params=params,
        )
        response.raise_for_status()
        result = response.json()

        messages = []
        for conversation in result.get("data", []):
            conv_id = conversation.get("id")
            for msg in conversation.get("messages", {}).get("data", []):
                sender = msg.get("from", {})
                messages.append(Message(
                    id=msg.get("id"),
                    conversation_id=conv_id,
                    text=msg.get("message"),
                    sender_id=sender.get("id"),
                    sender_name=sender.get("name"),
                    created_at=datetime.fromisoformat(msg.get("created_time", "").replace("+0000", "+00:00")),
                    raw_data=msg,
                ))

        paging = result.get("paging", {})
        next_cursor = paging.get("cursors", {}).get("after") if paging.get("next") else None

        return messages, next_cursor

    async def send_message(
        self,
        access_token: str,
        user_id: str,
        text: str,
    ) -> Optional[Message]:
        """
        Send a message to a user.

        Uses Facebook Messenger Platform API.

        Args:
            access_token: Page access token
            user_id: Recipient user ID (PSID)
            text: Message text

        Returns:
            Created message
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/me/messages",
            params={"access_token": access_token},
            json={
                "recipient": {"id": user_id},
                "message": {"text": text},
            },
        )
        response.raise_for_status()
        result = response.json()

        return Message(
            id=result.get("message_id"),
            text=text,
            created_at=datetime.utcnow(),
            raw_data=result,
        )

    async def get_groups(self, access_token: str) -> list[dict]:
        """
        Get groups the user is admin of.

        Args:
            access_token: Valid access token

        Returns:
            List of group data
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/me/groups",
            params={
                "access_token": access_token,
                "fields": "id,name,description,member_count,privacy,picture.type(large)",
                "admin_only": "true",
            },
        )
        response.raise_for_status()

        return response.json().get("data", [])

    async def publish_to_group(
        self,
        access_token: str,
        group_id: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish to a Facebook Group.

        Requires publish_to_groups permission.

        Args:
            access_token: Valid access token
            group_id: Group ID
            content: Content to publish

        Returns:
            Publish result
        """
        client = await self._get_client()

        post_data = {
            "access_token": access_token,
            "message": content.text or "",
        }

        if content.link:
            post_data["link"] = content.link

        response = await client.post(
            f"{self.API_BASE_URL}/{group_id}/feed",
            data=post_data,
        )
        response.raise_for_status()
        result = response.json()

        post_id = result.get("id")
        return PublishResult(
            success=True,
            platform_post_id=post_id,
            url=f"https://facebook.com/{post_id}" if post_id else None,
            raw_response=result,
        )
