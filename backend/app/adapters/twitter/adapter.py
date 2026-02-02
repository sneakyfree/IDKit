"""
Twitter/X Platform Adapter

Implements Twitter API v2 for tweeting, media upload, analytics,
and engagement management.

Twitter API Documentation:
- API v2: https://developer.twitter.com/en/docs/twitter-api
- OAuth 2.0: https://developer.twitter.com/en/docs/authentication/oauth-2-0
"""

import base64
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


class TwitterAdapter(BasePlatformAdapter):
    """
    Twitter/X platform adapter for tweets and engagement.

    Uses Twitter API v2 with OAuth 2.0 PKCE flow.
    """

    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    API_BASE_URL = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1"

    # Available scopes
    SCOPES = {
        "tweet.read": "Read tweets",
        "tweet.write": "Create and delete tweets",
        "tweet.moderate.write": "Hide/unhide replies",
        "users.read": "Read user profile",
        "follows.read": "Read follows",
        "follows.write": "Follow/unfollow",
        "offline.access": "Refresh tokens",
        "space.read": "Read Spaces",
        "mute.read": "Read mutes",
        "mute.write": "Mute/unmute",
        "like.read": "Read likes",
        "like.write": "Like/unlike",
        "list.read": "Read lists",
        "list.write": "Create/manage lists",
        "block.read": "Read blocks",
        "block.write": "Block/unblock",
        "bookmark.read": "Read bookmarks",
        "bookmark.write": "Create/delete bookmarks",
        "dm.read": "Read direct messages",
        "dm.write": "Send direct messages",
    }

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Twitter adapter.

        Args:
            client_id: Twitter app client ID
            client_secret: Twitter app client secret
        """
        self.client_id = client_id
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

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier."""
        return secrets.token_urlsafe(32)

    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier."""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """
        Generate Twitter OAuth 2.0 authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF protection state parameter
            scopes: List of permission scopes

        Returns:
            Authorization URL for user consent
        """
        if scopes is None:
            scopes = [
                "tweet.read",
                "tweet.write",
                "users.read",
                "offline.access",
                "like.read",
                "like.write",
            ]

        # Generate PKCE values
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
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
            redirect_uri: OAuth callback URL
            code_verifier: PKCE code verifier

        Returns:
            OAuth tokens
        """
        client = await self._get_client()

        # Prepare Basic auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        response = await client.post(
            self.TOKEN_URL,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}",
            },
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

        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        response = await client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}",
            },
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

        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        response = await client.post(
            f"{self.TOKEN_URL.replace('/token', '/revoke')}",
            data={
                "token": access_token,
                "token_type_hint": "access_token",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_header}",
            },
        )

        return response.status_code == 200

    async def get_user_profile(self, access_token: str) -> AccountInfo:
        """
        Get authenticated user's profile.

        Args:
            access_token: Valid access token

        Returns:
            User profile information
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "user.fields": "id,name,username,description,profile_image_url,public_metrics,verified,created_at,url"
            },
        )
        response.raise_for_status()
        result = response.json()

        user = result.get("data", {})
        metrics = user.get("public_metrics", {})

        return AccountInfo(
            id=user.get("id"),
            username=user.get("username"),
            display_name=user.get("name"),
            avatar_url=user.get("profile_image_url"),
            bio=user.get("description"),
            followers_count=metrics.get("followers_count"),
            following_count=metrics.get("following_count"),
            posts_count=metrics.get("tweet_count"),
            is_verified=user.get("verified", False),
            profile_url=f"https://twitter.com/{user.get('username')}",
            raw_data=user,
        )

    async def _upload_media(
        self,
        access_token: str,
        media_url: str,
        media_type: str = "image",
    ) -> Optional[str]:
        """
        Upload media to Twitter.

        Uses the v1.1 media upload endpoint (chunked upload for large files).

        Args:
            access_token: Valid access token
            media_url: URL of media to upload
            media_type: Type of media ('image' or 'video')

        Returns:
            Media ID string or None
        """
        client = await self._get_client()

        # Download media
        media_response = await client.get(media_url)
        media_data = media_response.content
        media_size = len(media_data)

        # Determine media category
        if media_type == "video":
            media_category = "tweet_video"
        elif media_type == "gif":
            media_category = "tweet_gif"
        else:
            media_category = "tweet_image"

        # For small images, use simple upload
        if media_type == "image" and media_size < 5 * 1024 * 1024:  # 5MB
            response = await client.post(
                f"{self.UPLOAD_URL}/media/upload.json",
                headers={"Authorization": f"Bearer {access_token}"},
                data={
                    "media_data": base64.b64encode(media_data).decode(),
                },
            )
            response.raise_for_status()
            return response.json().get("media_id_string")

        # For larger files, use chunked upload
        # Step 1: INIT
        init_response = await client.post(
            f"{self.UPLOAD_URL}/media/upload.json",
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "command": "INIT",
                "total_bytes": media_size,
                "media_type": "video/mp4" if media_type == "video" else "image/jpeg",
                "media_category": media_category,
            },
        )
        init_response.raise_for_status()
        media_id = init_response.json().get("media_id_string")

        # Step 2: APPEND (chunked)
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        segment_index = 0

        for i in range(0, media_size, chunk_size):
            chunk = media_data[i:i + chunk_size]

            await client.post(
                f"{self.UPLOAD_URL}/media/upload.json",
                headers={"Authorization": f"Bearer {access_token}"},
                data={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index,
                },
                files={"media": chunk},
            )
            segment_index += 1

        # Step 3: FINALIZE
        finalize_response = await client.post(
            f"{self.UPLOAD_URL}/media/upload.json",
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "command": "FINALIZE",
                "media_id": media_id,
            },
        )
        finalize_response.raise_for_status()
        result = finalize_response.json()

        # Check if processing is needed
        processing_info = result.get("processing_info")
        if processing_info:
            # Wait for processing to complete
            while processing_info.get("state") in ("pending", "in_progress"):
                wait_time = processing_info.get("check_after_secs", 5)
                import asyncio
                await asyncio.sleep(wait_time)

                status_response = await client.get(
                    f"{self.UPLOAD_URL}/media/upload.json",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={
                        "command": "STATUS",
                        "media_id": media_id,
                    },
                )
                status_response.raise_for_status()
                processing_info = status_response.json().get("processing_info", {})

            if processing_info.get("state") == "failed":
                return None

        return media_id

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish a tweet.

        Args:
            access_token: Valid access token with tweet.write scope
            content: Content to publish

        Returns:
            Publish result with tweet ID
        """
        client = await self._get_client()

        tweet_data = {}

        # Add text
        if content.text:
            tweet_data["text"] = content.text[:280]  # Twitter character limit

        # Upload and attach media
        media_ids = []

        if content.video_url:
            media_id = await self._upload_media(access_token, content.video_url, "video")
            if media_id:
                media_ids.append(media_id)

        if content.image_urls:
            for image_url in content.image_urls[:4]:  # Max 4 images
                media_id = await self._upload_media(access_token, image_url, "image")
                if media_id:
                    media_ids.append(media_id)

        if media_ids:
            tweet_data["media"] = {"media_ids": media_ids}

        # Add reply settings if specified
        if content.metadata and content.metadata.get("reply_settings"):
            tweet_data["reply_settings"] = content.metadata["reply_settings"]

        # Add quote tweet if specified
        if content.metadata and content.metadata.get("quote_tweet_id"):
            tweet_data["quote_tweet_id"] = content.metadata["quote_tweet_id"]

        # Create tweet
        response = await client.post(
            f"{self.API_BASE_URL}/tweets",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=tweet_data,
        )
        response.raise_for_status()
        result = response.json()

        tweet_id = result.get("data", {}).get("id")

        return PublishResult(
            success=True,
            platform_post_id=tweet_id,
            url=f"https://twitter.com/i/status/{tweet_id}" if tweet_id else None,
            raw_response=result,
        )

    async def delete_post(
        self,
        access_token: str,
        platform_post_id: str,
    ) -> bool:
        """
        Delete a tweet.

        Args:
            access_token: Valid access token with tweet.write scope
            platform_post_id: Tweet ID to delete

        Returns:
            True if deletion successful
        """
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/tweets/{platform_post_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        return response.status_code == 200

    async def create_thread(
        self,
        access_token: str,
        tweets: list[PublishContent],
    ) -> list[PublishResult]:
        """
        Create a Twitter thread.

        Args:
            access_token: Valid access token
            tweets: List of tweet contents

        Returns:
            List of publish results for each tweet
        """
        results = []
        reply_to_id = None

        for tweet in tweets:
            # Add reply reference if this is part of thread
            if reply_to_id:
                if tweet.metadata is None:
                    tweet.metadata = {}
                tweet.metadata["reply_to_id"] = reply_to_id

            result = await self.publish(access_token, tweet)
            results.append(result)

            if result.success and result.platform_post_id:
                reply_to_id = result.platform_post_id
            else:
                break  # Stop thread on failure

        return results

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        platform_post_id: Optional[str] = None,
    ) -> list[AnalyticsData]:
        """
        Get tweet analytics.

        Note: Detailed analytics require Twitter Premium API access.
        Basic metrics are available through public_metrics.

        Args:
            access_token: Valid access token
            start_date: Analytics start date
            end_date: Analytics end date
            platform_post_id: Optional specific tweet ID

        Returns:
            List of analytics data
        """
        client = await self._get_client()

        if platform_post_id:
            # Get specific tweet metrics
            response = await client.get(
                f"{self.API_BASE_URL}/tweets/{platform_post_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "tweet.fields": "public_metrics,created_at,organic_metrics,non_public_metrics",
                },
            )
            response.raise_for_status()
            result = response.json()

            tweet = result.get("data", {})
            metrics = tweet.get("public_metrics", {})

            return [AnalyticsData(
                date=datetime.fromisoformat(tweet.get("created_at", "").replace("Z", "+00:00")),
                impressions=metrics.get("impression_count", 0),
                reach=0,  # Not available in basic API
                engagement=metrics.get("like_count", 0) + metrics.get("retweet_count", 0) + metrics.get("reply_count", 0),
                likes=metrics.get("like_count", 0),
                comments=metrics.get("reply_count", 0),
                shares=metrics.get("retweet_count", 0),
                raw_data=tweet,
            )]

        # Get user's recent tweets
        user_profile = await self.get_user_profile(access_token)

        response = await client.get(
            f"{self.API_BASE_URL}/users/{user_profile.id}/tweets",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "tweet.fields": "public_metrics,created_at",
                "max_results": 100,
                "start_time": start_date.isoformat() + "Z",
                "end_time": end_date.isoformat() + "Z",
            },
        )
        response.raise_for_status()
        result = response.json()

        analytics = []
        for tweet in result.get("data", []):
            metrics = tweet.get("public_metrics", {})
            analytics.append(AnalyticsData(
                date=datetime.fromisoformat(tweet.get("created_at", "").replace("Z", "+00:00")),
                impressions=metrics.get("impression_count", 0),
                reach=0,
                engagement=metrics.get("like_count", 0) + metrics.get("retweet_count", 0) + metrics.get("reply_count", 0),
                likes=metrics.get("like_count", 0),
                comments=metrics.get("reply_count", 0),
                shares=metrics.get("retweet_count", 0),
                raw_data=tweet,
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
        Get replies to a tweet.

        Args:
            access_token: Valid access token
            platform_post_id: Tweet ID
            cursor: Pagination token
            limit: Maximum replies to return

        Returns:
            Tuple of (comments list, next cursor)
        """
        client = await self._get_client()

        # Search for replies to this tweet
        params = {
            "query": f"conversation_id:{platform_post_id}",
            "tweet.fields": "author_id,created_at,public_metrics,in_reply_to_user_id",
            "expansions": "author_id",
            "user.fields": "name,username,profile_image_url",
            "max_results": min(limit, 100),
        }

        if cursor:
            params["next_token"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/tweets/search/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        result = response.json()

        # Build user lookup
        users = {}
        for user in result.get("includes", {}).get("users", []):
            users[user["id"]] = user

        comments = []
        for tweet in result.get("data", []):
            if tweet.get("id") == platform_post_id:
                continue  # Skip the original tweet

            author = users.get(tweet.get("author_id"), {})
            metrics = tweet.get("public_metrics", {})

            comments.append(Comment(
                id=tweet.get("id"),
                post_id=platform_post_id,
                text=tweet.get("text"),
                author_id=tweet.get("author_id"),
                author_name=author.get("name"),
                author_username=author.get("username"),
                author_avatar=author.get("profile_image_url"),
                created_at=datetime.fromisoformat(tweet.get("created_at", "").replace("Z", "+00:00")),
                like_count=metrics.get("like_count", 0),
                reply_count=metrics.get("reply_count", 0),
                raw_data=tweet,
            ))

        next_token = result.get("meta", {}).get("next_token")

        return comments, next_token

    async def reply_to_comment(
        self,
        access_token: str,
        comment_id: str,
        text: str,
    ) -> Optional[Comment]:
        """
        Reply to a tweet (comment).

        Args:
            access_token: Valid access token
            comment_id: Tweet ID to reply to
            text: Reply text

        Returns:
            Created reply as Comment
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/tweets",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "text": text[:280],
                "reply": {"in_reply_to_tweet_id": comment_id},
            },
        )
        response.raise_for_status()
        result = response.json()

        tweet = result.get("data", {})

        return Comment(
            id=tweet.get("id"),
            post_id=comment_id,
            text=tweet.get("text"),
            created_at=datetime.utcnow(),
            raw_data=tweet,
        )

    async def get_messages(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> tuple[list[DirectMessage], Optional[str]]:
        """
        Get direct messages.

        Requires dm.read scope.

        Args:
            access_token: Valid access token
            cursor: Pagination cursor
            limit: Maximum messages to return

        Returns:
            Tuple of (messages list, next cursor)
        """
        client = await self._get_client()

        params = {
            "dm_event.fields": "id,text,created_at,sender_id,dm_conversation_id,attachments",
            "expansions": "sender_id,attachments.media_keys",
            "max_results": min(limit, 100),
        }

        if cursor:
            params["pagination_token"] = cursor

        response = await client.get(
            f"{self.API_BASE_URL}/dm_events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        result = response.json()

        # Build user lookup
        users = {}
        for user in result.get("includes", {}).get("users", []):
            users[user["id"]] = user

        messages = []
        for event in result.get("data", []):
            sender = users.get(event.get("sender_id"), {})

            messages.append(DirectMessage(
                id=event.get("id"),
                conversation_id=event.get("dm_conversation_id"),
                text=event.get("text"),
                sender_id=event.get("sender_id"),
                sender_name=sender.get("name"),
                sender_username=sender.get("username"),
                created_at=datetime.fromisoformat(event.get("created_at", "").replace("Z", "+00:00")),
                raw_data=event,
            ))

        next_token = result.get("meta", {}).get("next_token")

        return messages, next_token

    async def send_message(
        self,
        access_token: str,
        user_id: str,
        text: str,
    ) -> Optional[DirectMessage]:
        """
        Send a direct message.

        Requires dm.write scope.

        Args:
            access_token: Valid access token
            user_id: Recipient user ID
            text: Message text

        Returns:
            Created message
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/dm_conversations/with/{user_id}/messages",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"text": text},
        )
        response.raise_for_status()
        result = response.json()

        event = result.get("data", {})

        return DirectMessage(
            id=event.get("dm_event_id"),
            conversation_id=event.get("dm_conversation_id"),
            text=text,
            created_at=datetime.utcnow(),
            raw_data=event,
        )

    async def like_tweet(
        self,
        access_token: str,
        tweet_id: str,
    ) -> bool:
        """
        Like a tweet.

        Args:
            access_token: Valid access token
            tweet_id: Tweet ID to like

        Returns:
            True if successful
        """
        client = await self._get_client()

        # Get user ID
        user_profile = await self.get_user_profile(access_token)

        response = await client.post(
            f"{self.API_BASE_URL}/users/{user_profile.id}/likes",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"tweet_id": tweet_id},
        )

        return response.status_code == 200

    async def unlike_tweet(
        self,
        access_token: str,
        tweet_id: str,
    ) -> bool:
        """
        Unlike a tweet.

        Args:
            access_token: Valid access token
            tweet_id: Tweet ID to unlike

        Returns:
            True if successful
        """
        client = await self._get_client()

        # Get user ID
        user_profile = await self.get_user_profile(access_token)

        response = await client.delete(
            f"{self.API_BASE_URL}/users/{user_profile.id}/likes/{tweet_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        return response.status_code == 200

    async def retweet(
        self,
        access_token: str,
        tweet_id: str,
    ) -> bool:
        """
        Retweet a tweet.

        Args:
            access_token: Valid access token
            tweet_id: Tweet ID to retweet

        Returns:
            True if successful
        """
        client = await self._get_client()

        user_profile = await self.get_user_profile(access_token)

        response = await client.post(
            f"{self.API_BASE_URL}/users/{user_profile.id}/retweets",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"tweet_id": tweet_id},
        )

        return response.status_code == 200

    async def search_tweets(
        self,
        access_token: str,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Search for tweets.

        Args:
            access_token: Valid access token
            query: Search query
            max_results: Maximum tweets to return

        Returns:
            List of tweet data
        """
        client = await self._get_client()

        response = await client.get(
            f"{self.API_BASE_URL}/tweets/search/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "query": query,
                "tweet.fields": "author_id,created_at,public_metrics",
                "max_results": min(max_results, 100),
            },
        )
        response.raise_for_status()

        return response.json().get("data", [])
