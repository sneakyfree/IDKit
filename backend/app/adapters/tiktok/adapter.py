"""
TikTok Platform Adapter

Implements TikTok Content Posting API and Login Kit for video publishing,
analytics, and comment management.

TikTok API Documentation:
- Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started
- Login Kit: https://developers.tiktok.com/doc/login-kit-web
"""

import asyncio
import hashlib
import secrets
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.adapters.interfaces.base import (
    AccountInfo,
    AnalyticsData,
    BasePlatformAdapter,
    Comment,
    ContentType,
    DirectMessage,
    OAuthTokens,
    PublishContent,
    PublishResult,
)


class TikTokAdapter(BasePlatformAdapter):
    """
    TikTok platform adapter for video publishing and engagement.

    Uses TikTok's Content Posting API for video uploads and
    Login Kit for OAuth authentication.
    """

    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    API_BASE_URL = "https://open.tiktokapis.com/v2"

    # Available scopes
    SCOPES = {
        "user.info.basic": "Read basic user info",
        "user.info.profile": "Read user profile",
        "user.info.stats": "Read user statistics",
        "video.list": "List user's videos",
        "video.publish": "Publish videos",
        "video.upload": "Upload videos",
    }

    def __init__(self, client_key: str, client_secret: str):
        """
        Initialize TikTok adapter.

        Args:
            client_key: TikTok app client key
            client_secret: TikTok app client secret
        """
        self.client_key = client_key
        self.client_secret = client_secret
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
        Generate TikTok OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF protection state parameter
            scopes: List of permission scopes

        Returns:
            Authorization URL for user consent
        """
        if scopes is None:
            scopes = [
                "user.info.basic",
                "video.list",
                "video.publish",
                "video.upload",
            ]

        # Generate code verifier for PKCE
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = hashlib.sha256(code_verifier.encode()).hexdigest()

        params = {
            "client_key": self.client_key,
            "response_type": "code",
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
            "state": f"{state}:{code_verifier}",  # Store verifier in state
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
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
            redirect_uri: OAuth callback URL (must match authorization)
            code_verifier: PKCE code verifier

        Returns:
            OAuth tokens
        """
        client = await self._get_client()

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        response = await client.post(
            self.TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        result = response.json()

        return OAuthTokens(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_in=result.get("expires_in"),
            token_type=result.get("token_type", "Bearer"),
            scope=result.get("scope"),
        )

    async def refresh_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh an expired access token.

        Args:
            refresh_token: Refresh token from previous authorization

        Returns:
            New OAuth tokens
        """
        client = await self._get_client()

        response = await client.post(
            self.TOKEN_URL,
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        result = response.json()

        return OAuthTokens(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_in=result.get("expires_in"),
            token_type=result.get("token_type", "Bearer"),
            scope=result.get("scope"),
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

        response = await client.post(
            f"{self.API_BASE_URL}/oauth/revoke/",
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "token": access_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        return response.status_code == 200

    async def get_user_profile(self, access_token: str) -> AccountInfo:
        """
        Get authenticated user's profile.

        Args:
            access_token: Valid access token

        Returns:
            Account information
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/user/info/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "fields": "open_id,union_id,avatar_url,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count"
            },
        )
        response.raise_for_status()
        result = response.json()

        user = result.get("data", {}).get("user", {})

        return AccountInfo(
            platform_user_id=user.get("open_id", ""),
            username=user.get("display_name"),
            display_name=user.get("display_name"),
            profile_url=user.get("profile_deep_link"),
            profile_image_url=user.get("avatar_url"),
            account_type="creator",
            follower_count=user.get("follower_count", 0),
            following_count=user.get("following_count", 0),
            capabilities={"video_count": user.get("video_count", 0), "is_verified": user.get("is_verified", False)},
            raw_response=user,
        )

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish video to TikTok.

        TikTok uses a two-step process:
        1. Initialize upload and get upload URL
        2. Upload video file
        3. Create/publish post

        Args:
            access_token: Valid access token with video.publish scope
            content: Content to publish (must include video)

        Returns:
            Publish result with video ID
        """
        if not content.video_url:
            raise ValueError("TikTok requires a video URL")

        client = await self._get_client()

        # Step 1: Initialize video upload
        # Get file size first
        video_response = await client.head(content.video_url)
        video_size = int(video_response.headers.get("content-length", 0))

        if video_size == 0:
            # Try downloading to get size
            video_response = await client.get(content.video_url)
            video_size = len(video_response.content)
            video_data = video_response.content
        else:
            video_data = None

        # Initialize upload
        init_response = await client.post(
            f"{self.API_BASE_URL}/post/publish/video/init/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "post_info": {
                    "title": content.text[:150] if content.text else "",
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": video_size,  # Single chunk upload
                    "total_chunk_count": 1,
                },
            },
        )
        init_response.raise_for_status()
        init_result = init_response.json()

        publish_id = init_result.get("data", {}).get("publish_id")
        upload_url = init_result.get("data", {}).get("upload_url")

        if not upload_url:
            return PublishResult(
                success=False,
                error="Failed to get upload URL from TikTok",
            )

        # Step 2: Upload video file
        if video_data is None:
            video_response = await client.get(content.video_url)
            video_data = video_response.content

        upload_response = await client.put(
            upload_url,
            content=video_data,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            },
        )
        upload_response.raise_for_status()

        # Step 3: Check publish status
        # TikTok processes videos asynchronously
        status_response = await client.post(
            f"{self.API_BASE_URL}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"publish_id": publish_id},
        )
        status_response.raise_for_status()
        status_result = status_response.json()

        status = status_result.get("data", {}).get("status")

        if status == "FAILED":
            return PublishResult(
                success=False,
                error=status_result.get("data", {}).get("fail_reason", "Unknown error"),
            )

        return PublishResult(
            success=True,
            platform_post_id=publish_id,
            url=None,  # TikTok doesn't return URL immediately
            raw_response=status_result,
        )

    async def delete_post(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> bool:
        """
        Delete a video from TikTok.

        Note: TikTok doesn't provide a delete API in Content Posting API.
        Users must delete videos through the TikTok app.

        Args:
            access_token: Valid access token
            platform_post_id: TikTok video ID

        Returns:
            False (not supported)
        """
        # TikTok doesn't support video deletion via API
        return False

    async def get_post_status(
        self,
        access_token: str,
        publish_id: str,
    ) -> dict:
        """
        Check the status of a video publish operation.

        Args:
            access_token: Valid access token
            publish_id: Publish ID from initial upload

        Returns:
            Status information
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"publish_id": publish_id},
        )
        response.raise_for_status()

        return response.json().get("data", {})

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        platform_post_id: Optional[str] = None,
    ) -> list[AnalyticsData]:
        """
        Get video analytics.

        Note: TikTok Research API is required for detailed analytics.
        Basic video info is available through video.list scope.

        Args:
            access_token: Valid access token
            start_date: Analytics start date
            end_date: Analytics end date
            platform_post_id: Optional specific video ID

        Returns:
            List of analytics data
        """
        client = await self._get_client()

        # Get user's videos with basic metrics
        response = await client.post(
            f"{self.API_BASE_URL}/video/list/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "max_count": 20,
                "fields": "id,create_time,cover_image_url,share_url,video_description,duration,title,like_count,comment_count,share_count,view_count",
            },
        )
        response.raise_for_status()
        result = response.json()

        analytics = []
        videos = result.get("data", {}).get("videos", [])

        for video in videos:
            create_time = video.get("create_time")
            if create_time:
                video_date = datetime.fromtimestamp(create_time)
                if not (start_date <= video_date <= end_date):
                    continue

            if platform_post_id and video.get("id") != platform_post_id:
                continue

            analytics.append(AnalyticsData(
                date=datetime.fromtimestamp(video.get("create_time", 0)),
                impressions=video.get("view_count", 0),
                reach=video.get("view_count", 0),  # TikTok doesn't separate these
                engagement=video.get("like_count", 0) + video.get("comment_count", 0) + video.get("share_count", 0),
                likes=video.get("like_count", 0),
                comments=video.get("comment_count", 0),
                shares=video.get("share_count", 0),
                video_views=video.get("view_count", 0),
                raw_data=video,
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
        Get comments on a video.

        Note: Comment reading requires additional API access from TikTok.

        Args:
            access_token: Valid access token
            platform_post_id: TikTok video ID
            cursor: Pagination cursor
            limit: Maximum comments to return

        Returns:
            Tuple of (comments list, next cursor)
        """
        client = await self._get_client()

        params = {
            "video_id": platform_post_id,
            "max_count": min(limit, 100),
            "fields": "id,video_id,text,create_time,like_count,reply_count,parent_comment_id",
        }
        if cursor:
            params["cursor"] = cursor

        response = await client.post(
            f"{self.API_BASE_URL}/comment/list/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=params,
        )

        # Check if API is available
        if response.status_code == 403:
            # Comment API not available for this app
            return [], None

        response.raise_for_status()
        result = response.json()

        comments = []
        for item in result.get("data", {}).get("comments", []):
            comments.append(Comment(
                id=item.get("id"),
                post_id=platform_post_id,
                text=item.get("text"),
                author_id=None,  # Not provided in basic API
                author_name=None,
                author_avatar=None,
                created_at=datetime.fromtimestamp(item.get("create_time", 0)),
                like_count=item.get("like_count", 0),
                reply_count=item.get("reply_count", 0),
                parent_id=item.get("parent_comment_id"),
                raw_data=item,
            ))

        next_cursor = result.get("data", {}).get("cursor")
        has_more = result.get("data", {}).get("has_more", False)

        return comments, next_cursor if has_more else None

    async def reply_to_comment(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> Optional[Comment]:
        """
        Reply to a comment.

        Note: Comment replying requires additional API access from TikTok.

        Args:
            access_token: Valid access token
            comment_id: ID of comment to reply to
            text: Reply text

        Returns:
            Created reply comment or None
        """
        # TikTok Comment Reply API requires additional permissions
        # and is not available to all developers
        return None

    async def get_messages(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[DirectMessage], Optional[str]]:
        """
        Get direct messages.

        Note: TikTok doesn't provide a DM API for third-party apps.

        Args:
            access_token: Valid access token
            cursor: Pagination cursor
            limit: Maximum messages to return

        Returns:
            Empty list (not supported)
        """
        # TikTok doesn't provide DM API access
        return [], None

    async def send_message(
        self,
        access_token: str,
        user_id: str,
        text: str,
    ) -> Optional[DirectMessage]:
        """
        Send a direct message.

        Note: TikTok doesn't provide a DM API for third-party apps.

        Args:
            access_token: Valid access token
            user_id: Recipient user ID
            text: Message text

        Returns:
            None (not supported)
        """
        # TikTok doesn't provide DM API access
        return None

    async def get_user_videos(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        max_count: int = 20,
    ) -> dict:
        """
        Get authenticated user's videos.

        Args:
            access_token: Valid access token
            cursor: Pagination cursor
            max_count: Maximum videos to return (max 20)

        Returns:
            Videos data with pagination info
        """
        client = await self._get_client()

        request_body = {
            "max_count": min(max_count, 20),
            "fields": "id,create_time,cover_image_url,share_url,video_description,duration,title,like_count,comment_count,share_count,view_count",
        }
        if cursor:
            request_body["cursor"] = cursor

        response = await client.post(
            f"{self.API_BASE_URL}/video/list/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=request_body,
        )
        response.raise_for_status()

        return response.json().get("data", {})

    async def query_videos(
        self,
        access_token: str,
        video_ids: list[str],
    ) -> list[dict]:
        """
        Query specific videos by ID.

        Args:
            access_token: Valid access token
            video_ids: List of video IDs to query

        Returns:
            List of video data
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/video/query/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "filters": {
                    "video_ids": video_ids[:20],  # Max 20 at a time
                },
                "fields": "id,create_time,cover_image_url,share_url,video_description,duration,title,like_count,comment_count,share_count,view_count",
            },
        )
        response.raise_for_status()

        return response.json().get("data", {}).get("videos", [])
