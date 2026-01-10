"""
A/B Testing Framework

Test different content variants to optimize engagement and performance.
"""

import uuid
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


class TestStatus(str, Enum):
    """Status of an A/B test."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestType(str, Enum):
    """Type of A/B test."""
    CONTENT = "content"  # Different post content
    CAPTION = "caption"  # Different captions
    HASHTAGS = "hashtags"  # Different hashtag sets
    POSTING_TIME = "posting_time"  # Different posting times
    THUMBNAIL = "thumbnail"  # Different thumbnails
    CTA = "cta"  # Different calls to action
    FORMAT = "format"  # Different content formats


class WinnerCriteria(str, Enum):
    """Metric to determine winner."""
    ENGAGEMENT_RATE = "engagement_rate"
    TOTAL_ENGAGEMENT = "total_engagement"
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    COMMENTS = "comments"
    SHARES = "shares"


@dataclass
class TestVariant:
    """A variant in an A/B test."""
    id: str
    name: str
    content: Dict[str, Any]  # Platform-specific content
    weight: float = 50.0  # Distribution weight (percentage)

    # Metrics
    impressions: int = 0
    engagement: int = 0
    clicks: int = 0
    conversions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0

    # Calculated
    engagement_rate: float = 0.0
    click_rate: float = 0.0
    conversion_rate: float = 0.0

    # Tracking
    post_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ABTest:
    """A/B test configuration and results."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]

    # Configuration
    test_type: TestType
    variants: List[TestVariant]
    winner_criteria: WinnerCriteria
    platforms: List[str]

    # Scheduling
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    min_sample_size: int = 100  # Minimum impressions per variant
    confidence_level: float = 0.95  # Statistical confidence required

    # Status
    status: TestStatus = TestStatus.DRAFT
    winner_variant_id: Optional[str] = None
    statistical_significance: Optional[float] = None

    # Tracking
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


@dataclass
class TestResult:
    """Result of an A/B test analysis."""
    test_id: uuid.UUID
    is_conclusive: bool
    winner_variant_id: Optional[str]
    winner_variant_name: Optional[str]
    confidence: float
    improvement_percent: float
    variants_summary: List[Dict[str, Any]]
    recommendation: str


class ABTestingService:
    """
    A/B Testing service for content optimization.

    Features:
    - Multi-variant testing
    - Statistical significance calculation
    - Auto-winner detection
    - Platform-specific testing
    - Time-based testing
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._tests_cache: Dict[uuid.UUID, List[ABTest]] = {}

    # =========================================================================
    # TEST MANAGEMENT
    # =========================================================================

    async def create_test(
        self,
        user_id: uuid.UUID,
        name: str,
        test_type: TestType,
        variants: List[Dict[str, Any]],
        winner_criteria: WinnerCriteria = WinnerCriteria.ENGAGEMENT_RATE,
        platforms: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_sample_size: int = 100,
        confidence_level: float = 0.95,
        description: Optional[str] = None,
    ) -> ABTest:
        """
        Create a new A/B test.

        Args:
            user_id: User creating the test
            name: Test name
            test_type: Type of test
            variants: List of variant configs with 'name' and 'content'
            winner_criteria: Metric to determine winner
            platforms: Platforms to run test on
            start_date: When to start (None = immediately)
            end_date: When to end (None = when conclusive)
            min_sample_size: Minimum impressions per variant
            confidence_level: Required statistical confidence

        Returns:
            Created ABTest
        """
        if len(variants) < 2:
            raise ValueError("A/B test requires at least 2 variants")

        if len(variants) > 5:
            raise ValueError("Maximum 5 variants allowed")

        # Create variant objects with equal weights
        weight_per_variant = 100.0 / len(variants)
        test_variants = []

        for i, v in enumerate(variants):
            test_variants.append(TestVariant(
                id=f"variant_{chr(65 + i)}",  # A, B, C, D, E
                name=v.get("name", f"Variant {chr(65 + i)}"),
                content=v.get("content", {}),
                weight=v.get("weight", weight_per_variant),
            ))

        test = ABTest(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            description=description,
            test_type=test_type,
            variants=test_variants,
            winner_criteria=winner_criteria,
            platforms=platforms or ["instagram", "tiktok", "twitter"],
            start_date=start_date or datetime.now(timezone.utc),
            end_date=end_date,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
            status=TestStatus.DRAFT,
        )

        # Cache the test
        if user_id not in self._tests_cache:
            self._tests_cache[user_id] = []
        self._tests_cache[user_id].append(test)

        return test

    async def get_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> Optional[ABTest]:
        """Get a specific test."""
        tests = self._tests_cache.get(user_id, [])
        for test in tests:
            if test.id == test_id:
                return test
        return None

    async def get_tests(
        self,
        user_id: uuid.UUID,
        status: Optional[TestStatus] = None,
    ) -> List[ABTest]:
        """Get all tests for a user."""
        tests = self._tests_cache.get(user_id, [])
        if status:
            tests = [t for t in tests if t.status == status]
        return tests

    async def start_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> Optional[ABTest]:
        """Start a test."""
        test = await self.get_test(user_id, test_id)
        if test and test.status == TestStatus.DRAFT:
            test.status = TestStatus.RUNNING
            test.start_date = datetime.now(timezone.utc)
            test.updated_at = datetime.now(timezone.utc)
            return test
        return None

    async def pause_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> Optional[ABTest]:
        """Pause a running test."""
        test = await self.get_test(user_id, test_id)
        if test and test.status == TestStatus.RUNNING:
            test.status = TestStatus.PAUSED
            test.updated_at = datetime.now(timezone.utc)
            return test
        return None

    async def resume_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> Optional[ABTest]:
        """Resume a paused test."""
        test = await self.get_test(user_id, test_id)
        if test and test.status == TestStatus.PAUSED:
            test.status = TestStatus.RUNNING
            test.updated_at = datetime.now(timezone.utc)
            return test
        return None

    async def complete_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
        winner_variant_id: Optional[str] = None,
    ) -> Optional[ABTest]:
        """Complete a test and declare winner."""
        test = await self.get_test(user_id, test_id)
        if test and test.status in [TestStatus.RUNNING, TestStatus.PAUSED]:
            test.status = TestStatus.COMPLETED
            test.completed_at = datetime.now(timezone.utc)
            test.updated_at = datetime.now(timezone.utc)

            if winner_variant_id:
                test.winner_variant_id = winner_variant_id
            else:
                # Auto-determine winner
                result = await self.analyze_test(user_id, test_id)
                if result.is_conclusive:
                    test.winner_variant_id = result.winner_variant_id
                    test.statistical_significance = result.confidence

            return test
        return None

    async def cancel_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> Optional[ABTest]:
        """Cancel a test."""
        test = await self.get_test(user_id, test_id)
        if test and test.status in [TestStatus.DRAFT, TestStatus.RUNNING, TestStatus.PAUSED]:
            test.status = TestStatus.CANCELLED
            test.updated_at = datetime.now(timezone.utc)
            return test
        return None

    async def delete_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> bool:
        """Delete a test."""
        if user_id in self._tests_cache:
            original_len = len(self._tests_cache[user_id])
            self._tests_cache[user_id] = [
                t for t in self._tests_cache[user_id] if t.id != test_id
            ]
            return len(self._tests_cache[user_id]) < original_len
        return False

    # =========================================================================
    # VARIANT SELECTION
    # =========================================================================

    async def get_variant_for_user(
        self,
        test_id: uuid.UUID,
        user_identifier: str,
    ) -> Optional[TestVariant]:
        """
        Get consistent variant for a user (deterministic assignment).

        Uses hash-based assignment for consistency.
        """
        # Find the test
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id and test.status == TestStatus.RUNNING:
                    return self._assign_variant(test, user_identifier)
        return None

    def _assign_variant(
        self,
        test: ABTest,
        user_identifier: str,
    ) -> TestVariant:
        """Deterministically assign a variant based on user identifier."""
        # Create hash from test ID and user identifier
        hash_input = f"{test.id}:{user_identifier}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Normalize to 0-100
        bucket = hash_value % 100

        # Assign based on weights
        cumulative = 0.0
        for variant in test.variants:
            cumulative += variant.weight
            if bucket < cumulative:
                return variant

        # Fallback to last variant
        return test.variants[-1]

    async def get_random_variant(
        self,
        test_id: uuid.UUID,
    ) -> Optional[TestVariant]:
        """Get a random variant based on weights."""
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id and test.status == TestStatus.RUNNING:
                    return self._weighted_random_variant(test)
        return None

    def _weighted_random_variant(self, test: ABTest) -> TestVariant:
        """Select variant based on weights."""
        total_weight = sum(v.weight for v in test.variants)
        r = random.uniform(0, total_weight)

        cumulative = 0.0
        for variant in test.variants:
            cumulative += variant.weight
            if r <= cumulative:
                return variant

        return test.variants[-1]

    # =========================================================================
    # METRICS TRACKING
    # =========================================================================

    async def record_impression(
        self,
        test_id: uuid.UUID,
        variant_id: str,
        count: int = 1,
    ):
        """Record impressions for a variant."""
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id:
                    for variant in test.variants:
                        if variant.id == variant_id:
                            variant.impressions += count
                            return

    async def record_engagement(
        self,
        test_id: uuid.UUID,
        variant_id: str,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        saves: int = 0,
        clicks: int = 0,
    ):
        """Record engagement metrics for a variant."""
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id:
                    for variant in test.variants:
                        if variant.id == variant_id:
                            variant.likes += likes
                            variant.comments += comments
                            variant.shares += shares
                            variant.saves += saves
                            variant.clicks += clicks
                            variant.engagement = (
                                variant.likes +
                                variant.comments * 3 +
                                variant.shares * 5 +
                                variant.saves * 4
                            )
                            if variant.impressions > 0:
                                variant.engagement_rate = (variant.engagement / variant.impressions) * 100
                                variant.click_rate = (variant.clicks / variant.impressions) * 100
                            return

    async def record_conversion(
        self,
        test_id: uuid.UUID,
        variant_id: str,
        count: int = 1,
    ):
        """Record conversions for a variant."""
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id:
                    for variant in test.variants:
                        if variant.id == variant_id:
                            variant.conversions += count
                            if variant.impressions > 0:
                                variant.conversion_rate = (variant.conversions / variant.impressions) * 100
                            return

    async def link_post_to_variant(
        self,
        test_id: uuid.UUID,
        variant_id: str,
        post_id: str,
    ):
        """Link a published post to a variant for tracking."""
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id:
                    for variant in test.variants:
                        if variant.id == variant_id:
                            if post_id not in variant.post_ids:
                                variant.post_ids.append(post_id)
                            return

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    async def analyze_test(
        self,
        user_id: uuid.UUID,
        test_id: uuid.UUID,
    ) -> TestResult:
        """
        Analyze test results and determine winner.

        Uses statistical significance testing.
        """
        test = await self.get_test(user_id, test_id)
        if not test:
            raise ValueError("Test not found")

        variants = test.variants

        # Check minimum sample size
        min_impressions = min(v.impressions for v in variants)
        has_sufficient_data = min_impressions >= test.min_sample_size

        # Get the metric value based on winner criteria
        def get_metric_value(v: TestVariant) -> float:
            if test.winner_criteria == WinnerCriteria.ENGAGEMENT_RATE:
                return v.engagement_rate
            elif test.winner_criteria == WinnerCriteria.TOTAL_ENGAGEMENT:
                return float(v.engagement)
            elif test.winner_criteria == WinnerCriteria.IMPRESSIONS:
                return float(v.impressions)
            elif test.winner_criteria == WinnerCriteria.CLICKS:
                return float(v.clicks)
            elif test.winner_criteria == WinnerCriteria.CONVERSIONS:
                return float(v.conversions)
            elif test.winner_criteria == WinnerCriteria.COMMENTS:
                return float(v.comments)
            elif test.winner_criteria == WinnerCriteria.SHARES:
                return float(v.shares)
            return v.engagement_rate

        # Sort variants by metric
        sorted_variants = sorted(variants, key=get_metric_value, reverse=True)
        best_variant = sorted_variants[0]
        second_best = sorted_variants[1] if len(sorted_variants) > 1 else None

        # Calculate statistical significance
        confidence = 0.0
        is_conclusive = False

        if has_sufficient_data and second_best:
            confidence = self._calculate_significance(
                best_variant,
                second_best,
                test.winner_criteria,
            )
            is_conclusive = confidence >= test.confidence_level

        # Calculate improvement
        improvement = 0.0
        if second_best:
            best_value = get_metric_value(best_variant)
            second_value = get_metric_value(second_best)
            if second_value > 0:
                improvement = ((best_value - second_value) / second_value) * 100

        # Build variants summary
        variants_summary = []
        for v in variants:
            variants_summary.append({
                "id": v.id,
                "name": v.name,
                "impressions": v.impressions,
                "engagement": v.engagement,
                "engagement_rate": round(v.engagement_rate, 2),
                "likes": v.likes,
                "comments": v.comments,
                "shares": v.shares,
                "saves": v.saves,
                "clicks": v.clicks,
                "click_rate": round(v.click_rate, 2),
                "conversions": v.conversions,
                "conversion_rate": round(v.conversion_rate, 2),
                "metric_value": round(get_metric_value(v), 2),
                "is_winner": v.id == best_variant.id and is_conclusive,
            })

        # Generate recommendation
        if is_conclusive:
            recommendation = (
                f"Variant '{best_variant.name}' is the clear winner with {round(improvement, 1)}% "
                f"improvement in {test.winner_criteria.value}. Consider using this variant for future content."
            )
        elif not has_sufficient_data:
            recommendation = (
                f"Need more data. Current minimum is {min_impressions} impressions, "
                f"target is {test.min_sample_size}. Continue running the test."
            )
        else:
            recommendation = (
                f"Results are not statistically significant yet (confidence: {round(confidence * 100, 1)}%). "
                f"Continue running the test or consider if the difference is meaningful for your goals."
            )

        return TestResult(
            test_id=test_id,
            is_conclusive=is_conclusive,
            winner_variant_id=best_variant.id if is_conclusive else None,
            winner_variant_name=best_variant.name if is_conclusive else None,
            confidence=confidence,
            improvement_percent=round(improvement, 2),
            variants_summary=variants_summary,
            recommendation=recommendation,
        )

    def _calculate_significance(
        self,
        variant_a: TestVariant,
        variant_b: TestVariant,
        criteria: WinnerCriteria,
    ) -> float:
        """
        Calculate statistical significance using a simplified approach.

        Returns confidence level (0-1).
        """
        # Get rates based on criteria
        if criteria in [WinnerCriteria.ENGAGEMENT_RATE, WinnerCriteria.TOTAL_ENGAGEMENT]:
            rate_a = variant_a.engagement / variant_a.impressions if variant_a.impressions > 0 else 0
            rate_b = variant_b.engagement / variant_b.impressions if variant_b.impressions > 0 else 0
            n_a = variant_a.impressions
            n_b = variant_b.impressions
        elif criteria == WinnerCriteria.CLICKS:
            rate_a = variant_a.clicks / variant_a.impressions if variant_a.impressions > 0 else 0
            rate_b = variant_b.clicks / variant_b.impressions if variant_b.impressions > 0 else 0
            n_a = variant_a.impressions
            n_b = variant_b.impressions
        else:
            rate_a = variant_a.engagement_rate / 100
            rate_b = variant_b.engagement_rate / 100
            n_a = variant_a.impressions
            n_b = variant_b.impressions

        if n_a == 0 or n_b == 0:
            return 0.0

        # Pooled proportion
        p_pool = (rate_a * n_a + rate_b * n_b) / (n_a + n_b)

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))

        if se == 0:
            return 0.0

        # Z-score
        z = abs(rate_a - rate_b) / se

        # Convert to confidence (simplified approximation)
        # Using cumulative distribution approximation
        confidence = min(0.999, 1 - 2 * (1 - self._norm_cdf(z)))

        return confidence

    def _norm_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    # =========================================================================
    # AUTO-COMPLETION
    # =========================================================================

    async def check_and_complete_tests(
        self,
        user_id: uuid.UUID,
    ) -> List[ABTest]:
        """
        Check running tests and auto-complete if conclusive.

        Returns list of completed tests.
        """
        tests = await self.get_tests(user_id, status=TestStatus.RUNNING)
        completed = []

        for test in tests:
            # Check if end date reached
            if test.end_date and datetime.now(timezone.utc) >= test.end_date:
                await self.complete_test(user_id, test.id)
                completed.append(test)
                continue

            # Check if statistically significant
            result = await self.analyze_test(user_id, test.id)
            if result.is_conclusive:
                await self.complete_test(user_id, test.id, result.winner_variant_id)
                completed.append(test)

        return completed

    # =========================================================================
    # CONTENT GENERATION HELPERS
    # =========================================================================

    async def get_variant_content(
        self,
        test_id: uuid.UUID,
        variant_id: str,
        platform: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get platform-specific content for a variant.
        """
        for user_tests in self._tests_cache.values():
            for test in user_tests:
                if test.id == test_id:
                    for variant in test.variants:
                        if variant.id == variant_id:
                            content = variant.content
                            # Return platform-specific content if available
                            if platform in content:
                                return content[platform]
                            # Return generic content
                            return content
        return None

    async def create_caption_test(
        self,
        user_id: uuid.UUID,
        name: str,
        captions: List[str],
        platforms: Optional[List[str]] = None,
    ) -> ABTest:
        """
        Quick helper to create a caption A/B test.
        """
        variants = [
            {"name": f"Caption {chr(65 + i)}", "content": {"caption": caption}}
            for i, caption in enumerate(captions)
        ]

        return await self.create_test(
            user_id=user_id,
            name=name,
            test_type=TestType.CAPTION,
            variants=variants,
            winner_criteria=WinnerCriteria.ENGAGEMENT_RATE,
            platforms=platforms,
        )

    async def create_hashtag_test(
        self,
        user_id: uuid.UUID,
        name: str,
        hashtag_sets: List[List[str]],
        platforms: Optional[List[str]] = None,
    ) -> ABTest:
        """
        Quick helper to create a hashtag A/B test.
        """
        variants = [
            {
                "name": f"Hashtag Set {chr(65 + i)}",
                "content": {"hashtags": hashtags}
            }
            for i, hashtags in enumerate(hashtag_sets)
        ]

        return await self.create_test(
            user_id=user_id,
            name=name,
            test_type=TestType.HASHTAGS,
            variants=variants,
            winner_criteria=WinnerCriteria.IMPRESSIONS,
            platforms=platforms,
        )

    async def create_posting_time_test(
        self,
        user_id: uuid.UUID,
        name: str,
        times: List[Dict[str, Any]],  # [{"day": "monday", "hour": 9}, ...]
        platforms: Optional[List[str]] = None,
    ) -> ABTest:
        """
        Quick helper to create a posting time A/B test.
        """
        variants = [
            {
                "name": f"{t.get('day', 'day').title()} {t.get('hour', 12)}:00",
                "content": {"posting_time": t}
            }
            for t in times
        ]

        return await self.create_test(
            user_id=user_id,
            name=name,
            test_type=TestType.POSTING_TIME,
            variants=variants,
            winner_criteria=WinnerCriteria.ENGAGEMENT_RATE,
            platforms=platforms,
        )
