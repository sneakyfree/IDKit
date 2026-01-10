"""
YouTube Platform Adapter

Integration with YouTube Data API v3 for video publishing and analytics.
https://developers.google.com/youtube/v3
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
)


class YouTubeAdapter(BasePlatformAdapter):
    """
    YouTube platform adapter.

    Supports:
    - Video uploads (regular and Shorts)
    - Community posts
    - Analytics
    - Comment management
    """

    OAUTH_BASE_URL = "https://accounts.google.com/o/oauth2"
    API_BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

    DEFAULT_SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.client_id = client_id or settings.youtube_client_id
        self.client_secret = client_secret or settings.youtube_client_secret
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def platform_name(self) -> str:
        return "youtube"

    @property
    def supported_content_types(self) -> list[ContentType]:
        return [ContentType.VIDEO, ContentType.SHORT, ContentType.POST]

    @property
    def supports_scheduling(self) -> bool:
        return True

    @property
    def supports_analytics(self) -> bool:
        return True

    @property
    def supports_comments(self) -> bool:
        return True

    @property
    def supports_dms(self) -> bool:
        return False

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
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes or self.DEFAULT_SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.OAUTH_BASE_URL}/auth?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
    ) -> OAuthTokens:
        """Exchange authorization code for tokens."""
        client = await self._get_client()

        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")

        data = response.json()

        expires_at = None
        if "expires_in" in data:
            expires_at = datetime.utcnow().replace(
                second=datetime.utcnow().second + data["expires_in"]
            )

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            scope=data.get("scope"),
            token_type=data.get("token_type", "Bearer"),
            raw_response=data,
        )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> OAuthTokens:
        """Refresh an expired access token."""
        client = await self._get_client()

        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
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
            refresh_token=refresh_token,  # Keep original refresh token
            expires_at=expires_at,
            scope=data.get("scope"),
            token_type=data.get("token_type", "Bearer"),
            raw_response=data,
        )

    # ==================== Account ====================

    async def get_account_info(
        self,
        access_token: str,
    ) -> AccountInfo:
        """Get YouTube channel information."""
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/channels",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "part": "snippet,statistics,contentDetails",
                "mine": "true",
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get channel info: {response.text}")

        data = response.json()

        if not data.get("items"):
            raise Exception("No YouTube channel found for this account")

        channel = data["items"][0]
        snippet = channel.get("snippet", {})
        stats = channel.get("statistics", {})

        return AccountInfo(
            platform_user_id=channel["id"],
            username=snippet.get("customUrl", "").lstrip("@"),
            display_name=snippet.get("title"),
            profile_url=f"https://www.youtube.com/channel/{channel['id']}",
            profile_image_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
            account_type="creator",
            follower_count=int(stats.get("subscriberCount", 0)),
            following_count=0,
            capabilities={
                "can_upload": True,
                "can_livestream": True,
                "can_post_community": stats.get("hiddenSubscriberCount", False) is False,
            },
            raw_response=channel,
        )

    # ==================== Publishing ====================

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish a video to YouTube.

        For Shorts, the video should be vertical (9:16) and under 60 seconds.
        """
        if content.content_type == ContentType.POST:
            return await self._publish_community_post(access_token, content)

        if not content.media_urls and not content.media_files:
            return PublishResult(
                success=False,
                error_message="Video file or URL is required",
            )

        client = await self._get_client()

        # Prepare video metadata
        is_short = content.content_type == ContentType.SHORT
        title = content.title or "Untitled Video"

        # Add #Shorts hashtag for Shorts
        if is_short and "#Shorts" not in title:
            title = f"{title} #Shorts"

        description = content.text or ""
        if content.hashtags:
            description += "\n\n" + " ".join(f"#{tag}" for tag in content.hashtags)

        video_metadata = {
            "snippet": {
                "title": title[:100],  # YouTube title limit
                "description": description[:5000],  # YouTube description limit
                "tags": content.hashtags[:500] if content.hashtags else [],
                "categoryId": content.extras.get("category_id", "22"),  # 22 = People & Blogs
            },
            "status": {
                "privacyStatus": content.extras.get("privacy", "public"),
                "selfDeclaredMadeForKids": content.extras.get("made_for_kids", False),
            },
        }

        # Handle scheduled publishing
        if content.scheduled_at:
            video_metadata["status"]["privacyStatus"] = "private"
            video_metadata["status"]["publishAt"] = content.scheduled_at.isoformat() + "Z"

        try:
            # For URL-based media, we need to download and re-upload
            # YouTube doesn't support uploading from URL directly
            if content.media_urls:
                # Download the video
                video_response = await client.get(content.media_urls[0])
                if video_response.status_code != 200:
                    return PublishResult(
                        success=False,
                        error_message="Failed to download video from URL",
                    )
                video_data = video_response.content
            else:
                video_data = content.media_files[0]

            # Upload video using resumable upload
            # Step 1: Initialize upload
            init_response = await client.post(
                f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*",
                    "X-Upload-Content-Length": str(len(video_data)),
                },
                json=video_metadata,
            )

            if init_response.status_code not in (200, 201):
                return PublishResult(
                    success=False,
                    error_message=f"Failed to initialize upload: {init_response.text}",
                )

            upload_url = init_response.headers.get("Location")
            if not upload_url:
                return PublishResult(
                    success=False,
                    error_message="No upload URL received",
                )

            # Step 2: Upload video content
            upload_response = await client.put(
                upload_url,
                headers={
                    "Content-Type": "video/*",
                    "Content-Length": str(len(video_data)),
                },
                content=video_data,
            )

            if upload_response.status_code not in (200, 201):
                return PublishResult(
                    success=False,
                    error_message=f"Failed to upload video: {upload_response.text}",
                )

            video_data_response = upload_response.json()

            return PublishResult(
                success=True,
                platform_post_id=video_data_response["id"],
                platform_post_url=f"https://www.youtube.com/watch?v={video_data_response['id']}",
                metadata=video_data_response,
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    async def _publish_community_post(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish a community post.

        Note: Community posts API is limited. This is a placeholder.
        """
        # YouTube Community Posts API is not publicly available
        # Would need to use YouTube Studio automation or wait for API
        return PublishResult(
            success=False,
            error_message="Community posts are not yet supported via API",
        )

    async def delete_post(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> bool:
        """Delete a video."""
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/videos",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"id": platform_post_id},
        )

        return response.status_code == 204

    # ==================== Analytics ====================

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[AnalyticsData]:
        """Get channel analytics."""
        client = await self._get_client()

        # Get channel ID first
        account_info = await self.get_account_info(access_token)
        channel_id = account_info.platform_user_id

        # YouTube Analytics API
        response = await client.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "ids": f"channel=={channel_id}",
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "metrics": "views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares,subscribersGained,subscribersLost",
                "dimensions": "day",
                "sort": "day",
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get analytics: {response.text}")

        data = response.json()
        results = []

        for row in data.get("rows", []):
            date_str = row[0]
            results.append(
                AnalyticsData(
                    date=datetime.strptime(date_str, "%Y-%m-%d"),
                    total_impressions=int(row[1]) if len(row) > 1 else 0,  # views
                    total_engagements=int(row[4]) + int(row[5]) + int(row[6]) if len(row) > 6 else 0,
                    likes_received=int(row[4]) if len(row) > 4 else 0,
                    comments_received=int(row[5]) if len(row) > 5 else 0,
                    shares_received=int(row[6]) if len(row) > 6 else 0,
                    follower_change=int(row[7]) - int(row[8]) if len(row) > 8 else 0,
                    raw_response={"row": row},
                )
            )

        return results

    async def get_post_metrics(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> PostMetrics:
        """Get metrics for a specific video."""
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/videos",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "part": "statistics",
                "id": platform_post_id,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get video stats: {response.text}")

        data = response.json()

        if not data.get("items"):
            raise Exception("Video not found")

        stats = data["items"][0].get("statistics", {})

        return PostMetrics(
            platform_post_id=platform_post_id,
            view_count=int(stats.get("viewCount", 0)),
            like_count=int(stats.get("likeCount", 0)),
            comment_count=int(stats.get("commentCount", 0)),
            raw_response=stats,
        )

    # ==================== Comments ====================

    async def get_comments(
        self,
        access_token: str,
        platform_post_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[Comment], Optional[str]]:
        """Get comments on a video."""
        client = await self._get_client()

        params = {
            "part": "snippet",
            "videoId": platform_post_id,
            "maxResults": min(limit, 100),
            "order": "time",
        }

        if cursor:
            params["pageToken"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/commentThreads",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get comments: {response.text}")

        data = response.json()
        comments = []

        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append(
                Comment(
                    platform_comment_id=item["id"],
                    author_id=snippet.get("authorChannelId", {}).get("value", ""),
                    author_username=snippet.get("authorDisplayName"),
                    author_display_name=snippet.get("authorDisplayName"),
                    author_avatar_url=snippet.get("authorProfileImageUrl"),
                    content=snippet.get("textDisplay", ""),
                    like_count=snippet.get("likeCount", 0),
                    reply_count=item["snippet"].get("totalReplyCount", 0),
                    posted_at=datetime.fromisoformat(
                        snippet.get("publishedAt", "").replace("Z", "+00:00")
                    ) if snippet.get("publishedAt") else None,
                    raw_response=item,
                )
            )

        next_cursor = data.get("nextPageToken")
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
            f"{self.API_BASE_URL}/comments",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            params={"part": "snippet"},
            json={
                "snippet": {
                    "parentId": platform_comment_id,
                    "textOriginal": text,
                },
            },
        )

        if response.status_code not in (200, 201):
            raise Exception(f"Failed to reply: {response.text}")

        data = response.json()
        snippet = data["snippet"]

        return Comment(
            platform_comment_id=data["id"],
            author_id=snippet.get("authorChannelId", {}).get("value", ""),
            author_username=snippet.get("authorDisplayName"),
            content=snippet.get("textDisplay", ""),
            posted_at=datetime.fromisoformat(
                snippet.get("publishedAt", "").replace("Z", "+00:00")
            ) if snippet.get("publishedAt") else None,
            parent_comment_id=platform_comment_id,
            raw_response=data,
        )

    async def delete_comment(
        self,
        access_token: str,
        platform_comment_id: str,
    ) -> bool:
        """Delete a comment."""
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/comments",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"id": platform_comment_id},
        )

        return response.status_code == 204

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
