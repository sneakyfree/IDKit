"""
Content Moderation Service

AI-powered content moderation for the IDKit platform.
Uses OpenAI Moderation API and custom rules.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.moderation.models import (
    ModerationResult,
    ModerationCategory,
    ModerationAction,
    ModerationSeverity,
    ModerationConfig,
    ContentType,
    CategoryScore,
    ModerationReport,
    ModerationLog,
)

logger = logging.getLogger(__name__)


class ModerationService:
    """
    Service for moderating user-generated content.

    Uses multiple layers:
    1. Keyword blocklist (fast, deterministic)
    2. OpenAI Moderation API (comprehensive)
    3. Custom ML models (platform-specific) - future
    4. Human review queue (edge cases)
    """

    def __init__(self, config: Optional[ModerationConfig] = None):
        self.config = config or ModerationConfig()
        self._http_client: Optional[httpx.AsyncClient] = None

        # Compiled regex patterns for blocklist
        self._blocklist_patterns: list[re.Pattern] = []
        self._username_blocklist: list[re.Pattern] = []
        self._init_blocklists()

    def _init_blocklists(self):
        """Initialize blocklist patterns."""
        # Severe terms that should always be blocked
        severe_terms = [
            r"\b(kill|murder|death\s*to)\s+(yourself|urself|u)\b",
            r"\bkys\b",
            r"\b(cp|csam|pedo)\b",
            r"\b(isis|taliban|al[-\s]?qaeda)\b",
        ]

        self._blocklist_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in severe_terms
        ]

        # Username blocklist (impersonation, offensive)
        username_blocked = [
            r"^admin$",
            r"^moderator$",
            r"^idkit$",
            r"^support$",
            r"^official",
            r"verified$",
        ]

        self._username_blocklist = [
            re.compile(pattern, re.IGNORECASE) for pattern in username_blocked
        ]

    @property
    async def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # =========================================================================
    # Main Moderation Methods
    # =========================================================================

    async def moderate_text(
        self,
        text: str,
        content_type: ContentType = ContentType.TEXT,
        content_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> ModerationResult:
        """
        Moderate text content.

        Args:
            text: Text content to moderate
            content_type: Type of text content
            content_id: Optional content ID for logging
            user_id: Optional user ID for rate limiting

        Returns:
            ModerationResult with action and details
        """
        if not text or not text.strip():
            return ModerationResult(
                content_id=content_id,
                content_type=content_type,
                is_flagged=False,
                action=ModerationAction.APPROVE,
                severity=ModerationSeverity.NONE,
                confidence=1.0,
            )

        # Layer 1: Blocklist check (fast)
        blocklist_result = self._check_blocklist(text, content_type)
        if blocklist_result.is_flagged and blocklist_result.severity == ModerationSeverity.CRITICAL:
            return blocklist_result

        # Layer 2: OpenAI Moderation API
        api_result = await self._moderate_with_openai(text, content_id, content_type)

        # Combine results
        combined = self._combine_results(blocklist_result, api_result)

        # Determine action
        combined.action = self._determine_action(combined, user_id)

        return combined

    async def moderate_image(
        self,
        image_url: str,
        content_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> ModerationResult:
        """
        Moderate image content.

        Uses OpenAI Vision API for image analysis.

        Args:
            image_url: URL of the image to moderate
            content_id: Optional content ID
            user_id: Optional user ID

        Returns:
            ModerationResult
        """
        # Use GPT-4 Vision for image moderation
        result = await self._moderate_image_with_vision(image_url, content_id)
        result.action = self._determine_action(result, user_id)
        return result

    async def moderate_username(
        self,
        username: str,
        user_id: Optional[UUID] = None,
    ) -> ModerationResult:
        """
        Moderate a username for policy compliance.

        Args:
            username: Username to check
            user_id: Optional user ID

        Returns:
            ModerationResult
        """
        # Check blocklist
        for pattern in self._username_blocklist:
            if pattern.search(username):
                return ModerationResult(
                    content_id=None,
                    content_type=ContentType.USERNAME,
                    is_flagged=True,
                    action=ModerationAction.AUTO_REMOVE,
                    severity=ModerationSeverity.HIGH,
                    primary_category=ModerationCategory.SPAM,
                    confidence=1.0,
                    details=f"Username matches blocked pattern: {pattern.pattern}",
                )

        # Check for profanity/hate speech in username
        return await self.moderate_text(
            text=username,
            content_type=ContentType.USERNAME,
            user_id=user_id,
        )

    async def moderate_profile(
        self,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        username: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> dict[str, ModerationResult]:
        """
        Moderate a complete user profile.

        Args:
            bio: Profile bio text
            avatar_url: Avatar image URL
            username: Username
            user_id: User ID

        Returns:
            Dict of moderation results by field
        """
        results = {}

        if username:
            results["username"] = await self.moderate_username(username, user_id)

        if bio:
            results["bio"] = await self.moderate_text(
                text=bio,
                content_type=ContentType.PROFILE_BIO,
                user_id=user_id,
            )

        if avatar_url:
            results["avatar"] = await self.moderate_image(
                image_url=avatar_url,
                user_id=user_id,
            )

        return results

    async def moderate_post(
        self,
        text: Optional[str] = None,
        media_urls: Optional[list[str]] = None,
        content_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
    ) -> ModerationResult:
        """
        Moderate a complete feed post.

        Args:
            text: Post text content
            media_urls: List of media URLs
            content_id: Post ID
            user_id: User ID

        Returns:
            Combined moderation result
        """
        results: list[ModerationResult] = []

        # Moderate text
        if text:
            text_result = await self.moderate_text(
                text=text,
                content_id=content_id,
                user_id=user_id,
            )
            results.append(text_result)

        # Moderate each media item
        if media_urls:
            for url in media_urls[:5]:  # Limit to 5 media items
                if self._is_image_url(url):
                    image_result = await self.moderate_image(
                        image_url=url,
                        content_id=content_id,
                        user_id=user_id,
                    )
                    results.append(image_result)

        # Combine all results
        if not results:
            return ModerationResult(
                content_id=content_id,
                content_type=ContentType.TEXT,
                is_flagged=False,
                action=ModerationAction.APPROVE,
                severity=ModerationSeverity.NONE,
                confidence=1.0,
            )

        return self._combine_multiple_results(results)

    # =========================================================================
    # Blocklist Checking
    # =========================================================================

    def _check_blocklist(
        self,
        text: str,
        content_type: ContentType,
    ) -> ModerationResult:
        """Check text against blocklist patterns."""
        for pattern in self._blocklist_patterns:
            match = pattern.search(text)
            if match:
                return ModerationResult(
                    content_id=None,
                    content_type=content_type,
                    is_flagged=True,
                    action=ModerationAction.AUTO_REMOVE,
                    severity=ModerationSeverity.CRITICAL,
                    primary_category=ModerationCategory.HATE_THREATENING,
                    confidence=1.0,
                    details=f"Matched blocklist pattern",
                    categories=[
                        CategoryScore(
                            category=ModerationCategory.HATE_THREATENING,
                            score=1.0,
                            flagged=True,
                        )
                    ],
                )

        return ModerationResult(
            content_id=None,
            content_type=content_type,
            is_flagged=False,
            action=ModerationAction.APPROVE,
            severity=ModerationSeverity.NONE,
            confidence=1.0,
        )

    # =========================================================================
    # OpenAI Moderation API
    # =========================================================================

    async def _moderate_with_openai(
        self,
        text: str,
        content_id: Optional[UUID],
        content_type: ContentType,
    ) -> ModerationResult:
        """Use OpenAI Moderation API."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured, skipping API moderation")
            return ModerationResult(
                content_id=content_id,
                content_type=content_type,
                is_flagged=False,
                action=ModerationAction.APPROVE,
                severity=ModerationSeverity.NONE,
                confidence=0.5,
                details="API moderation skipped - no API key",
            )

        try:
            client = await self.http_client
            response = await client.post(
                "https://api.openai.com/v1/moderations",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": text},
            )

            if response.status_code != 200:
                logger.error(f"OpenAI Moderation API error: {response.status_code}")
                return self._fallback_result(content_id, content_type)

            data = response.json()
            return self._parse_openai_response(data, content_id, content_type)

        except Exception as e:
            logger.error(f"OpenAI Moderation API exception: {e}")
            return self._fallback_result(content_id, content_type)

    def _parse_openai_response(
        self,
        data: dict,
        content_id: Optional[UUID],
        content_type: ContentType,
    ) -> ModerationResult:
        """Parse OpenAI Moderation API response."""
        if not data.get("results"):
            return self._fallback_result(content_id, content_type)

        result = data["results"][0]
        categories = result.get("categories", {})
        scores = result.get("category_scores", {})
        flagged = result.get("flagged", False)

        # Map OpenAI categories to our categories
        category_mapping = {
            "hate": ModerationCategory.HATE,
            "hate/threatening": ModerationCategory.HATE_THREATENING,
            "harassment": ModerationCategory.HARASSMENT,
            "harassment/threatening": ModerationCategory.HARASSMENT_THREATENING,
            "self-harm": ModerationCategory.SELF_HARM,
            "self-harm/intent": ModerationCategory.SELF_HARM,
            "self-harm/instructions": ModerationCategory.SELF_HARM,
            "sexual": ModerationCategory.SEXUAL,
            "sexual/minors": ModerationCategory.SEXUAL_MINORS,
            "violence": ModerationCategory.VIOLENCE,
            "violence/graphic": ModerationCategory.VIOLENCE_GRAPHIC,
        }

        category_scores = []
        primary_category = None
        highest_score = 0.0

        for openai_cat, our_cat in category_mapping.items():
            score = scores.get(openai_cat, 0.0)
            is_flagged = categories.get(openai_cat, False)

            category_scores.append(
                CategoryScore(
                    category=our_cat,
                    score=score,
                    flagged=is_flagged,
                )
            )

            if score > highest_score:
                highest_score = score
                primary_category = our_cat

        # Determine severity
        severity = ModerationSeverity.NONE
        if highest_score >= 0.9:
            severity = ModerationSeverity.CRITICAL
        elif highest_score >= 0.7:
            severity = ModerationSeverity.HIGH
        elif highest_score >= 0.5:
            severity = ModerationSeverity.MEDIUM
        elif highest_score >= 0.3:
            severity = ModerationSeverity.LOW

        return ModerationResult(
            content_id=content_id,
            content_type=content_type,
            is_flagged=flagged,
            action=ModerationAction.APPROVE,  # Action determined later
            severity=severity,
            categories=category_scores,
            primary_category=primary_category if flagged else None,
            confidence=highest_score,
            model_version="openai-moderation-latest",
        )

    # =========================================================================
    # Image Moderation
    # =========================================================================

    async def _moderate_image_with_vision(
        self,
        image_url: str,
        content_id: Optional[UUID],
    ) -> ModerationResult:
        """Use GPT-4 Vision for image moderation."""
        if not settings.openai_api_key:
            return ModerationResult(
                content_id=content_id,
                content_type=ContentType.IMAGE,
                is_flagged=False,
                action=ModerationAction.APPROVE,
                severity=ModerationSeverity.NONE,
                confidence=0.5,
                details="Image moderation skipped - no API key",
            )

        try:
            client = await self.http_client
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a content moderation system. Analyze the image and respond with a JSON object containing:
{
    "flagged": boolean,
    "categories": {
        "violence": float (0-1),
        "sexual": float (0-1),
        "hate": float (0-1),
        "dangerous": float (0-1),
        "nudity": float (0-1)
    },
    "primary_issue": string or null,
    "severity": "none" | "low" | "medium" | "high" | "critical"
}
Only respond with the JSON object, no other text.""",
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url},
                                }
                            ],
                        },
                    ],
                    "max_tokens": 300,
                },
                timeout=60.0,
            )

            if response.status_code != 200:
                logger.error(f"Vision API error: {response.status_code}")
                return self._fallback_result(content_id, ContentType.IMAGE)

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            import json
            analysis = json.loads(content)

            categories = []
            category_mapping = {
                "violence": ModerationCategory.VIOLENCE,
                "sexual": ModerationCategory.SEXUAL,
                "hate": ModerationCategory.HATE,
                "dangerous": ModerationCategory.DANGEROUS,
                "nudity": ModerationCategory.NUDITY,
            }

            for key, cat in category_mapping.items():
                score = analysis.get("categories", {}).get(key, 0.0)
                categories.append(
                    CategoryScore(
                        category=cat,
                        score=score,
                        flagged=score > 0.5,
                    )
                )

            severity_mapping = {
                "none": ModerationSeverity.NONE,
                "low": ModerationSeverity.LOW,
                "medium": ModerationSeverity.MEDIUM,
                "high": ModerationSeverity.HIGH,
                "critical": ModerationSeverity.CRITICAL,
            }

            return ModerationResult(
                content_id=content_id,
                content_type=ContentType.IMAGE,
                is_flagged=analysis.get("flagged", False),
                action=ModerationAction.APPROVE,
                severity=severity_mapping.get(
                    analysis.get("severity", "none"),
                    ModerationSeverity.NONE,
                ),
                categories=categories,
                primary_category=self._get_primary_category(
                    analysis.get("primary_issue")
                ),
                confidence=max(c.score for c in categories) if categories else 0.0,
                model_version="gpt-4-vision",
            )

        except Exception as e:
            logger.error(f"Vision moderation exception: {e}")
            return self._fallback_result(content_id, ContentType.IMAGE)

    # =========================================================================
    # Action Determination
    # =========================================================================

    def _determine_action(
        self,
        result: ModerationResult,
        user_id: Optional[UUID] = None,
    ) -> ModerationAction:
        """Determine action based on moderation result."""
        # Zero tolerance categories
        if result.primary_category in self.config.zero_tolerance_categories:
            return ModerationAction.AUTO_REMOVE

        # Based on severity
        if result.severity == ModerationSeverity.CRITICAL:
            return ModerationAction.AUTO_REMOVE
        elif result.severity == ModerationSeverity.HIGH:
            return ModerationAction.FLAG_FOR_REVIEW
        elif result.severity == ModerationSeverity.MEDIUM:
            return ModerationAction.FLAG_FOR_REVIEW
        elif result.severity == ModerationSeverity.LOW:
            return ModerationAction.APPROVE

        # Based on confidence
        if result.confidence >= self.config.auto_remove_threshold:
            return ModerationAction.AUTO_REMOVE
        elif result.confidence >= self.config.flag_for_review_threshold:
            return ModerationAction.FLAG_FOR_REVIEW

        return ModerationAction.APPROVE

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _combine_results(
        self,
        *results: ModerationResult,
    ) -> ModerationResult:
        """Combine multiple moderation results."""
        if not results:
            return self._fallback_result(None, ContentType.TEXT)

        # Take the most severe result
        most_severe = max(
            results,
            key=lambda r: (
                r.severity.value if r.severity else "",
                r.confidence,
            ),
        )

        # Combine all categories
        all_categories = []
        for r in results:
            all_categories.extend(r.categories)

        # Deduplicate categories, keeping highest scores
        category_map: dict[ModerationCategory, CategoryScore] = {}
        for cat in all_categories:
            if cat.category not in category_map or cat.score > category_map[cat.category].score:
                category_map[cat.category] = cat

        return ModerationResult(
            content_id=most_severe.content_id,
            content_type=most_severe.content_type,
            is_flagged=any(r.is_flagged for r in results),
            action=most_severe.action,
            severity=most_severe.severity,
            categories=list(category_map.values()),
            primary_category=most_severe.primary_category,
            confidence=max(r.confidence for r in results),
        )

    def _combine_multiple_results(
        self,
        results: list[ModerationResult],
    ) -> ModerationResult:
        """Combine multiple moderation results into one."""
        return self._combine_results(*results)

    def _fallback_result(
        self,
        content_id: Optional[UUID],
        content_type: ContentType,
    ) -> ModerationResult:
        """Return fallback result when moderation fails."""
        return ModerationResult(
            content_id=content_id,
            content_type=content_type,
            is_flagged=False,
            action=ModerationAction.FLAG_FOR_REVIEW,
            severity=ModerationSeverity.NONE,
            confidence=0.0,
            details="Moderation service unavailable - flagged for manual review",
        )

    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image."""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
        url_lower = url.lower()
        return any(url_lower.endswith(ext) or ext + "?" in url_lower for ext in image_extensions)

    def _get_primary_category(
        self,
        issue: Optional[str],
    ) -> Optional[ModerationCategory]:
        """Map issue string to category."""
        if not issue:
            return None

        issue_lower = issue.lower()
        mapping = {
            "violence": ModerationCategory.VIOLENCE,
            "sexual": ModerationCategory.SEXUAL,
            "hate": ModerationCategory.HATE,
            "harassment": ModerationCategory.HARASSMENT,
            "nudity": ModerationCategory.NUDITY,
            "dangerous": ModerationCategory.DANGEROUS,
        }

        for key, cat in mapping.items():
            if key in issue_lower:
                return cat

        return None

    # =========================================================================
    # Database Operations (for logging and reports)
    # =========================================================================

    async def log_moderation_action(
        self,
        db: AsyncSession,
        result: ModerationResult,
        user_id: UUID,
        reviewer_id: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> ModerationLog:
        """Log a moderation action to the database."""
        from sqlalchemy import text

        log_id = uuid4()

        await db.execute(
            text("""
                INSERT INTO moderation_logs
                (id, content_id, content_type, user_id, action, reason,
                 automated, confidence, reviewer_id, notes, created_at)
                VALUES
                (:id, :content_id, :content_type, :user_id, :action, :reason,
                 :automated, :confidence, :reviewer_id, :notes, :created_at)
            """),
            {
                "id": log_id,
                "content_id": result.content_id,
                "content_type": result.content_type.value,
                "user_id": user_id,
                "action": result.action.value,
                "reason": result.primary_category.value if result.primary_category else None,
                "automated": reviewer_id is None,
                "confidence": result.confidence,
                "reviewer_id": reviewer_id,
                "notes": notes,
                "created_at": datetime.utcnow(),
            },
        )

        return ModerationLog(
            log_id=log_id,
            content_id=result.content_id,
            content_type=result.content_type,
            user_id=user_id,
            action=result.action,
            reason=result.primary_category,
            automated=reviewer_id is None,
            confidence=result.confidence,
            reviewer_id=reviewer_id,
            notes=notes,
        )

    async def create_report(
        self,
        db: AsyncSession,
        reporter_id: UUID,
        content_id: UUID,
        content_type: ContentType,
        reason: ModerationCategory,
        details: Optional[str] = None,
    ) -> ModerationReport:
        """Create a user report for content."""
        from sqlalchemy import text

        report_id = uuid4()

        await db.execute(
            text("""
                INSERT INTO moderation_reports
                (id, reporter_id, content_id, content_type, reason, details, status, created_at)
                VALUES
                (:id, :reporter_id, :content_id, :content_type, :reason, :details, 'pending', :created_at)
            """),
            {
                "id": report_id,
                "reporter_id": reporter_id,
                "content_id": content_id,
                "content_type": content_type.value,
                "reason": reason.value,
                "details": details,
                "created_at": datetime.utcnow(),
            },
        )

        return ModerationReport(
            report_id=report_id,
            reporter_id=reporter_id,
            content_id=content_id,
            content_type=content_type,
            reason=reason,
            details=details,
            status="pending",
        )

    async def get_user_flag_count(
        self,
        db: AsyncSession,
        user_id: UUID,
        hours: int = 24,
    ) -> int:
        """Get count of flags against a user in time window."""
        from sqlalchemy import text

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await db.execute(
            text("""
                SELECT COUNT(*) FROM moderation_logs
                WHERE user_id = :user_id
                AND action IN ('flag_for_review', 'auto_remove', 'warn_user')
                AND created_at > :cutoff
            """),
            {"user_id": user_id, "cutoff": cutoff},
        )

        return result.scalar() or 0


# Global service instance
moderation_service = ModerationService()
