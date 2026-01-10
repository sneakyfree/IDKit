"""
LinkedIn Platform Adapter

Implements LinkedIn API for posting, sharing, analytics,
and engagement management for personal profiles and Company Pages.

LinkedIn API Documentation:
- API Overview: https://learn.microsoft.com/en-us/linkedin/
- Share API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares
- UGC Posts: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/ugc-post-api
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


class LinkedInAdapter(BasePlatformAdapter):
    """
    LinkedIn platform adapter for profiles and Company Pages.

    Uses LinkedIn Marketing API with OAuth 2.0.
    """

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_BASE_URL = "https://api.linkedin.com/v2"
    REST_API_URL = "https://api.linkedin.com/rest"

    # Available scopes
    SCOPES = {
        "openid": "OpenID Connect",
        "profile": "Read basic profile",
        "email": "Read email address",
        "w_member_social": "Post, comment, and react on behalf of user",
        "r_basicprofile": "Read basic profile (legacy)",
        "r_organization_social": "Read organization posts",
        "w_organization_social": "Post on behalf of organization",
        "rw_organization_admin": "Manage organization pages",
        "r_organization_admin": "Read organization admin data",
    }

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize LinkedIn adapter.

        Args:
            client_id: LinkedIn app client ID
            client_secret: LinkedIn app client secret
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

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        scopes: Optional[list[str]] = None,
    ) -> str:
        """
        Generate LinkedIn OAuth 2.0 authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF protection state parameter
            scopes: List of permission scopes

        Returns:
            Authorization URL for user consent
        """
        if scopes is None:
            scopes = [
                "openid",
                "profile",
                "email",
                "w_member_social",
            ]

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(scopes),
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

        response = await client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
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
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
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
            "https://www.linkedin.com/oauth/v2/revoke",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": access_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
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

        # Get basic profile with userinfo endpoint (OpenID Connect)
        response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        user = response.json()

        return UserProfile(
            id=user.get("sub"),
            username=None,  # LinkedIn doesn't expose public usernames via API
            display_name=user.get("name"),
            avatar_url=user.get("picture"),
            bio=None,  # Not available in userinfo
            email=user.get("email"),
            profile_url=None,  # Not available in userinfo
            raw_data=user,
        )

    async def get_member_urn(self, access_token: str) -> str:
        """
        Get the authenticated user's member URN.

        Args:
            access_token: Valid access token

        Returns:
            Member URN string (e.g., 'urn:li:person:ABC123')
        """
        profile = await self.get_user_profile(access_token)
        return f"urn:li:person:{profile.id}"

    async def get_organizations(self, access_token: str) -> list[dict]:
        """
        Get organizations (Company Pages) the user can manage.

        Requires rw_organization_admin scope.

        Args:
            access_token: Valid access token

        Returns:
            List of organization data
        """
        client = await self._get_client()

        # First get the user's member URN
        member_urn = await self.get_member_urn(access_token)

        # Get organization access control
        response = await client.get(
            f"{self.API_BASE_URL}/organizationAcls",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            params={
                "q": "roleAssignee",
                "role": "ADMINISTRATOR",
                "projection": "(elements*(organization~(localizedName,vanityName,logoV2)))",
            },
        )

        if response.status_code != 200:
            return []

        result = response.json()

        organizations = []
        for element in result.get("elements", []):
            org = element.get("organization~", {})
            organizations.append({
                "id": element.get("organization"),
                "name": org.get("localizedName"),
                "vanity_name": org.get("vanityName"),
                "logo_url": org.get("logoV2", {}).get("original~", {}).get("elements", [{}])[0].get("identifiers", [{}])[0].get("identifier"),
            })

        return organizations

    async def _register_image(
        self,
        access_token: str,
        owner_urn: str,
    ) -> tuple[str, str]:
        """
        Register an image for upload.

        Args:
            access_token: Valid access token
            owner_urn: Owner URN (person or organization)

        Returns:
            Tuple of (asset URN, upload URL)
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/assets?action=registerUpload",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": owner_urn,
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent",
                        }
                    ],
                }
            },
        )
        response.raise_for_status()
        result = response.json()

        value = result.get("value", {})
        asset = value.get("asset")
        upload_url = value.get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")

        return asset, upload_url

    async def _upload_image(
        self,
        access_token: str,
        upload_url: str,
        image_url: str,
    ) -> bool:
        """
        Upload image to LinkedIn.

        Args:
            access_token: Valid access token
            upload_url: Pre-signed upload URL
            image_url: Source image URL

        Returns:
            True if upload successful
        """
        client = await self._get_client()

        # Download image
        image_response = await client.get(image_url)
        image_data = image_response.content

        # Upload to LinkedIn
        response = await client.put(
            upload_url,
            content=image_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "image/jpeg",
            },
        )

        return response.status_code in (200, 201)

    async def _register_video(
        self,
        access_token: str,
        owner_urn: str,
        file_size: int,
    ) -> tuple[str, str]:
        """
        Register a video for upload.

        Args:
            access_token: Valid access token
            owner_urn: Owner URN
            file_size: Video file size in bytes

        Returns:
            Tuple of (asset URN, upload URL)
        """
        client = await self._get_client()

        response = await client.post(
            f"{self.API_BASE_URL}/assets?action=registerUpload",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "owner": owner_urn,
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent",
                        }
                    ],
                    "fileSize": file_size,
                }
            },
        )
        response.raise_for_status()
        result = response.json()

        value = result.get("value", {})
        asset = value.get("asset")
        upload_url = value.get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}).get("uploadUrl")

        return asset, upload_url

    async def publish(
        self,
        access_token: str,
        content: PublishContent,
    ) -> PublishResult:
        """
        Publish content to LinkedIn.

        Args:
            access_token: Valid access token with w_member_social scope
            content: Content to publish

        Returns:
            Publish result with post ID
        """
        client = await self._get_client()

        # Determine author (person or organization)
        if content.metadata and content.metadata.get("organization_urn"):
            author_urn = content.metadata["organization_urn"]
        else:
            author_urn = await self.get_member_urn(access_token)

        # Build UGC post
        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content.text or "",
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }

        share_content = post_data["specificContent"]["com.linkedin.ugc.ShareContent"]

        # Handle media
        if content.image_urls:
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = []

            for image_url in content.image_urls[:9]:  # Max 9 images
                # Register and upload image
                asset_urn, upload_url = await self._register_image(access_token, author_urn)
                await self._upload_image(access_token, upload_url, image_url)

                share_content["media"].append({
                    "status": "READY",
                    "media": asset_urn,
                })

        elif content.video_url:
            # Video upload is more complex, requires chunked upload
            # For now, share as article with video link
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{
                "status": "READY",
                "originalUrl": content.video_url,
            }]

        elif content.link:
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{
                "status": "READY",
                "originalUrl": content.link,
                "title": {"text": content.metadata.get("link_title", "")} if content.metadata else None,
                "description": {"text": content.metadata.get("link_description", "")} if content.metadata else None,
            }]

        # Create post
        response = await client.post(
            f"{self.API_BASE_URL}/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=post_data,
        )
        response.raise_for_status()
        result = response.json()

        post_id = result.get("id")
        # Extract share ID from URN
        share_id = post_id.split(":")[-1] if post_id else None

        return PublishResult(
            success=True,
            platform_post_id=post_id,
            url=f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None,
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
            platform_post_id: Post URN to delete

        Returns:
            True if deletion successful
        """
        client = await self._get_client()

        response = await client.delete(
            f"{self.API_BASE_URL}/ugcPosts/{platform_post_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

        return response.status_code in (200, 204)

    async def publish_article(
        self,
        access_token: str,
        title: str,
        body: str,
        thumbnail_url: Optional[str] = None,
        organization_urn: Optional[str] = None,
    ) -> PublishResult:
        """
        Publish a LinkedIn article.

        Args:
            access_token: Valid access token
            title: Article title
            body: Article body (HTML supported)
            thumbnail_url: Optional thumbnail image
            organization_urn: Optional organization to publish as

        Returns:
            Publish result
        """
        # LinkedIn Articles API is restricted
        # Using standard post with link for now
        content = PublishContent(
            text=f"{title}\n\n{body[:500]}...",
            metadata={"organization_urn": organization_urn} if organization_urn else None,
        )

        return await self.publish(access_token, content)

    async def get_analytics(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        platform_post_id: Optional[str] = None,
    ) -> list[AnalyticsData]:
        """
        Get post/page analytics.

        Note: Detailed analytics require Marketing Developer Platform access.

        Args:
            access_token: Valid access token
            start_date: Analytics start date
            end_date: Analytics end date
            platform_post_id: Optional specific post URN

        Returns:
            List of analytics data
        """
        client = await self._get_client()

        if platform_post_id:
            # Get specific post statistics
            response = await client.get(
                f"{self.API_BASE_URL}/socialActions/{platform_post_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            )

            if response.status_code != 200:
                return []

            result = response.json()

            return [AnalyticsData(
                date=datetime.utcnow(),
                likes=result.get("likesSummary", {}).get("totalLikes", 0),
                comments=result.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                shares=0,  # Not directly available
                raw_data=result,
            )]

        # Get user's recent posts with engagement
        member_urn = await self.get_member_urn(access_token)

        response = await client.get(
            f"{self.API_BASE_URL}/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            params={
                "q": "authors",
                "authors": f"List({member_urn})",
                "count": 50,
            },
        )

        if response.status_code != 200:
            return []

        result = response.json()
        analytics = []

        for post in result.get("elements", []):
            created = post.get("created", {}).get("time", 0)
            post_date = datetime.fromtimestamp(created / 1000) if created else datetime.utcnow()

            if not (start_date <= post_date <= end_date):
                continue

            analytics.append(AnalyticsData(
                date=post_date,
                impressions=0,  # Not available in basic API
                engagement=0,
                raw_data=post,
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
            platform_post_id: Post URN
            cursor: Pagination cursor (start index)
            limit: Maximum comments to return

        Returns:
            Tuple of (comments list, next cursor)
        """
        client = await self._get_client()

        start = int(cursor) if cursor else 0

        response = await client.get(
            f"{self.API_BASE_URL}/socialActions/{platform_post_id}/comments",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            params={
                "start": start,
                "count": min(limit, 100),
            },
        )
        response.raise_for_status()
        result = response.json()

        comments = []
        for item in result.get("elements", []):
            actor = item.get("actor")
            comments.append(Comment(
                id=item.get("$URN"),
                post_id=platform_post_id,
                text=item.get("message", {}).get("text"),
                author_id=actor,
                created_at=datetime.fromtimestamp(item.get("created", {}).get("time", 0) / 1000),
                like_count=item.get("likesSummary", {}).get("totalLikes", 0),
                raw_data=item,
            ))

        # Calculate next cursor
        paging = result.get("paging", {})
        total = paging.get("total", 0)
        next_start = start + len(comments)
        next_cursor = str(next_start) if next_start < total else None

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
            comment_id: Comment URN to reply to
            text: Reply text

        Returns:
            Created reply comment
        """
        client = await self._get_client()

        # Extract post URN from comment URN
        # Comment URN format: urn:li:comment:(urn:li:ugcPost:xxx,yyy)
        post_urn = comment_id.split("(")[1].split(",")[0] if "(" in comment_id else None

        if not post_urn:
            return None

        actor_urn = await self.get_member_urn(access_token)

        response = await client.post(
            f"{self.API_BASE_URL}/socialActions/{post_urn}/comments",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={
                "actor": actor_urn,
                "message": {"text": text},
                "parentComment": comment_id,
            },
        )
        response.raise_for_status()
        result = response.json()

        return Comment(
            id=result.get("$URN"),
            post_id=post_urn,
            text=text,
            author_id=actor_urn,
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
        Get direct messages.

        Note: LinkedIn Messaging API requires special partnership access.

        Args:
            access_token: Valid access token
            cursor: Pagination cursor
            limit: Maximum messages to return

        Returns:
            Empty list (not available for standard apps)
        """
        # LinkedIn Messaging API requires partnership agreement
        return [], None

    async def send_message(
        self,
        access_token: str,
        user_id: str,
        text: str,
    ) -> Optional[Message]:
        """
        Send a direct message.

        Note: LinkedIn Messaging API requires special partnership access.

        Args:
            access_token: Valid access token
            user_id: Recipient member URN
            text: Message text

        Returns:
            None (not available for standard apps)
        """
        # LinkedIn Messaging API requires partnership agreement
        return None

    async def like_post(
        self,
        access_token: str,
        post_urn: str,
    ) -> bool:
        """
        Like a post.

        Args:
            access_token: Valid access token
            post_urn: Post URN to like

        Returns:
            True if successful
        """
        client = await self._get_client()

        actor_urn = await self.get_member_urn(access_token)

        response = await client.post(
            f"{self.API_BASE_URL}/socialActions/{post_urn}/likes",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json={"actor": actor_urn},
        )

        return response.status_code in (200, 201)

    async def unlike_post(
        self,
        access_token: str,
        post_urn: str,
    ) -> bool:
        """
        Unlike a post.

        Args:
            access_token: Valid access token
            post_urn: Post URN to unlike

        Returns:
            True if successful
        """
        client = await self._get_client()

        actor_urn = await self.get_member_urn(access_token)

        response = await client.delete(
            f"{self.API_BASE_URL}/socialActions/{post_urn}/likes/{actor_urn}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

        return response.status_code in (200, 204)
