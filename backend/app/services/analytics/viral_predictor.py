"""
Viral Score Predictor Service

Predicts the viral potential of content before publishing.
Uses ML-based scoring and historical performance data.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ViralPotential(str, Enum):
    """Viral potential categories."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VIRAL = "viral"


class ContentType(str, Enum):
    """Content type for analysis."""
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    TEXT = "text"
    STORY = "story"
    REEL = "reel"
    SHORT = "short"


@dataclass
class ViralFactor:
    """A factor contributing to viral potential."""
    name: str
    score: float  # 0-1
    weight: float  # Factor importance
    description: str
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ViralPrediction:
    """Complete viral prediction for content."""
    content_id: Optional[str] = None
    platform: str = ""

    # Overall scores
    viral_score: float = 0.0  # 0-100
    viral_potential: ViralPotential = ViralPotential.LOW
    confidence: float = 0.0  # 0-1

    # Predicted metrics
    predicted_views: tuple[int, int] = (0, 0)  # (min, max)
    predicted_likes: tuple[int, int] = (0, 0)
    predicted_comments: tuple[int, int] = (0, 0)
    predicted_shares: tuple[int, int] = (0, 0)

    # Factor breakdown
    factors: list[ViralFactor] = field(default_factory=list)

    # Improvements
    improvement_suggestions: list[str] = field(default_factory=list)
    potential_score_increase: float = 0.0

    # Timing
    best_posting_times: list[str] = field(default_factory=list)
    worst_posting_times: list[str] = field(default_factory=list)

    # Comparison
    similar_content_avg_score: float = 0.0
    percentile_rank: float = 0.0  # How this content compares to others

    # Analysis timestamp
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContentAnalysis:
    """Analysis of content for viral prediction."""
    # Text analysis
    hook_strength: float = 0.0
    emotional_appeal: float = 0.0
    curiosity_factor: float = 0.0
    call_to_action_strength: float = 0.0
    readability_score: float = 0.0

    # Visual analysis (if applicable)
    visual_quality: float = 0.0
    thumbnail_appeal: float = 0.0
    color_vibrancy: float = 0.0

    # Structural analysis
    optimal_length: bool = False
    has_hashtags: bool = False
    hashtag_quality: float = 0.0
    has_mentions: bool = False
    has_cta: bool = False

    # Trend alignment
    trend_alignment: float = 0.0
    trending_topics_used: list[str] = field(default_factory=list)
    trending_sounds_used: list[str] = field(default_factory=list)


class ViralScorePredictor:
    """
    Predicts viral potential of content before publishing.

    Features:
    - Multi-factor viral scoring
    - Platform-specific optimization
    - Historical performance correlation
    - Improvement suggestions
    - Optimal timing recommendations
    """

    # Platform-specific optimal content lengths
    OPTIMAL_LENGTHS = {
        "tiktok": {"video": (15, 60), "text": (50, 150)},
        "instagram": {"video": (30, 90), "text": (100, 200), "carousel": (5, 10)},
        "youtube": {"video": (480, 900), "text": (200, 400)},  # 8-15 min for YouTube
        "twitter": {"text": (100, 280)},
        "linkedin": {"text": (150, 300)},
    }

    # Platform-specific weights
    PLATFORM_WEIGHTS = {
        "tiktok": {
            "hook_strength": 0.25,
            "trend_alignment": 0.20,
            "visual_quality": 0.15,
            "emotional_appeal": 0.15,
            "hashtag_quality": 0.10,
            "posting_time": 0.10,
            "content_length": 0.05,
        },
        "instagram": {
            "visual_quality": 0.25,
            "hook_strength": 0.20,
            "hashtag_quality": 0.15,
            "emotional_appeal": 0.15,
            "trend_alignment": 0.10,
            "posting_time": 0.10,
            "content_length": 0.05,
        },
        "youtube": {
            "hook_strength": 0.20,
            "thumbnail_appeal": 0.20,
            "content_quality": 0.20,
            "seo_optimization": 0.15,
            "emotional_appeal": 0.10,
            "posting_time": 0.10,
            "content_length": 0.05,
        },
        "twitter": {
            "hook_strength": 0.25,
            "trend_alignment": 0.25,
            "emotional_appeal": 0.20,
            "curiosity_factor": 0.15,
            "posting_time": 0.10,
            "content_length": 0.05,
        },
        "linkedin": {
            "value_proposition": 0.25,
            "hook_strength": 0.20,
            "professional_relevance": 0.20,
            "emotional_appeal": 0.15,
            "posting_time": 0.15,
            "content_length": 0.05,
        },
    }

    # Viral trigger words by category
    VIRAL_TRIGGERS = {
        "curiosity": [
            "secret", "revealed", "you won't believe", "discover", "hidden",
            "truth about", "what nobody tells you", "insider", "exposed",
        ],
        "urgency": [
            "now", "today", "immediately", "don't miss", "limited", "last chance",
            "before it's too late", "urgent", "breaking",
        ],
        "value": [
            "free", "save", "easy", "quick", "simple", "step-by-step",
            "how to", "tips", "guide", "tutorial", "learn",
        ],
        "emotion": [
            "amazing", "incredible", "unbelievable", "shocking", "inspiring",
            "heartwarming", "hilarious", "terrifying", "beautiful", "powerful",
        ],
        "social_proof": [
            "everyone", "millions", "viral", "trending", "popular",
            "famous", "celebrity", "expert", "proven", "tested",
        ],
    }

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        historical_data: Optional[dict] = None,
    ):
        """
        Initialize viral predictor.

        Args:
            llm_client: LLM for advanced text analysis
            historical_data: Historical performance data for calibration
        """
        self.llm_client = llm_client
        self.historical_data = historical_data or {}

    async def predict(
        self,
        content: dict,
        platform: str,
        creator_stats: Optional[dict] = None,
        posting_time: Optional[datetime] = None,
    ) -> ViralPrediction:
        """
        Predict viral potential of content.

        Args:
            content: Content to analyze (text, media_urls, hashtags, etc.)
            platform: Target platform
            creator_stats: Creator's historical performance
            posting_time: Intended posting time

        Returns:
            Viral prediction with scores and suggestions
        """
        # Analyze content
        analysis = await self._analyze_content(content, platform)

        # Get platform weights
        weights = self.PLATFORM_WEIGHTS.get(
            platform,
            self.PLATFORM_WEIGHTS["instagram"]
        )

        # Calculate factor scores
        factors = []

        # Hook strength
        hook_score = analysis.hook_strength
        factors.append(ViralFactor(
            name="Hook Strength",
            score=hook_score,
            weight=weights.get("hook_strength", 0.2),
            description=self._describe_hook_score(hook_score),
            suggestions=self._get_hook_suggestions(hook_score, content),
        ))

        # Emotional appeal
        emotion_score = analysis.emotional_appeal
        factors.append(ViralFactor(
            name="Emotional Appeal",
            score=emotion_score,
            weight=weights.get("emotional_appeal", 0.15),
            description=self._describe_emotion_score(emotion_score),
            suggestions=self._get_emotion_suggestions(emotion_score),
        ))

        # Trend alignment
        trend_score = analysis.trend_alignment
        factors.append(ViralFactor(
            name="Trend Alignment",
            score=trend_score,
            weight=weights.get("trend_alignment", 0.15),
            description=self._describe_trend_score(trend_score),
            suggestions=self._get_trend_suggestions(trend_score, platform),
        ))

        # Visual quality (if applicable)
        if content.get("media_urls") or content.get("thumbnail_url"):
            visual_score = analysis.visual_quality
            factors.append(ViralFactor(
                name="Visual Quality",
                score=visual_score,
                weight=weights.get("visual_quality", 0.15),
                description=self._describe_visual_score(visual_score),
                suggestions=self._get_visual_suggestions(visual_score),
            ))

        # Hashtag quality
        hashtag_score = analysis.hashtag_quality
        factors.append(ViralFactor(
            name="Hashtag Strategy",
            score=hashtag_score,
            weight=weights.get("hashtag_quality", 0.1),
            description=self._describe_hashtag_score(hashtag_score),
            suggestions=self._get_hashtag_suggestions(hashtag_score, content),
        ))

        # Content length optimization
        length_score = 1.0 if analysis.optimal_length else 0.5
        factors.append(ViralFactor(
            name="Content Length",
            score=length_score,
            weight=weights.get("content_length", 0.05),
            description="Optimal" if analysis.optimal_length else "Could be improved",
            suggestions=self._get_length_suggestions(content, platform),
        ))

        # Posting time
        time_score = self._calculate_time_score(posting_time, platform)
        factors.append(ViralFactor(
            name="Posting Time",
            score=time_score,
            weight=weights.get("posting_time", 0.1),
            description=self._describe_time_score(time_score),
            suggestions=self._get_time_suggestions(platform),
        ))

        # Calculate weighted viral score
        total_weight = sum(f.weight for f in factors)
        viral_score = sum(f.score * f.weight for f in factors) / total_weight * 100

        # Determine viral potential category
        if viral_score >= 80:
            potential = ViralPotential.VIRAL
        elif viral_score >= 60:
            potential = ViralPotential.HIGH
        elif viral_score >= 40:
            potential = ViralPotential.MODERATE
        else:
            potential = ViralPotential.LOW

        # Calculate predicted metrics
        predicted_views = self._predict_views(viral_score, creator_stats, platform)
        predicted_likes = self._predict_likes(viral_score, predicted_views)
        predicted_comments = self._predict_comments(viral_score, predicted_views)
        predicted_shares = self._predict_shares(viral_score, predicted_views)

        # Aggregate improvement suggestions
        all_suggestions = []
        for factor in factors:
            if factor.score < 0.7:
                all_suggestions.extend(factor.suggestions[:2])

        # Calculate potential improvement
        low_factors = [f for f in factors if f.score < 0.7]
        potential_increase = sum(
            (0.7 - f.score) * f.weight * 100
            for f in low_factors
        ) / total_weight

        # Best posting times
        best_times = self._get_best_posting_times(platform)
        worst_times = self._get_worst_posting_times(platform)

        return ViralPrediction(
            platform=platform,
            viral_score=round(viral_score, 1),
            viral_potential=potential,
            confidence=self._calculate_confidence(factors),
            predicted_views=predicted_views,
            predicted_likes=predicted_likes,
            predicted_comments=predicted_comments,
            predicted_shares=predicted_shares,
            factors=factors,
            improvement_suggestions=all_suggestions[:5],
            potential_score_increase=round(potential_increase, 1),
            best_posting_times=best_times,
            worst_posting_times=worst_times,
            percentile_rank=viral_score,  # Simplified
        )

    async def _analyze_content(
        self,
        content: dict,
        platform: str,
    ) -> ContentAnalysis:
        """Analyze content for viral factors."""
        analysis = ContentAnalysis()

        text = content.get("text", "") or content.get("caption", "")
        hashtags = content.get("hashtags", [])

        # Analyze hook (first line/sentence)
        analysis.hook_strength = self._analyze_hook(text)

        # Analyze emotional appeal
        analysis.emotional_appeal = self._analyze_emotion(text)

        # Analyze curiosity factor
        analysis.curiosity_factor = self._analyze_curiosity(text)

        # Analyze CTA
        analysis.call_to_action_strength = self._analyze_cta(text)
        analysis.has_cta = analysis.call_to_action_strength > 0.5

        # Analyze readability
        analysis.readability_score = self._analyze_readability(text)

        # Analyze hashtags
        analysis.has_hashtags = len(hashtags) > 0
        analysis.hashtag_quality = self._analyze_hashtags(hashtags, platform)

        # Analyze length
        analysis.optimal_length = self._check_optimal_length(content, platform)

        # Analyze trend alignment (simplified without external data)
        analysis.trend_alignment = self._analyze_trend_alignment(
            text, hashtags, platform
        )

        # Visual analysis (placeholder - would use vision model)
        if content.get("media_urls") or content.get("thumbnail_url"):
            analysis.visual_quality = 0.7  # Default for now
            analysis.thumbnail_appeal = 0.7

        return analysis

    def _analyze_hook(self, text: str) -> float:
        """Analyze hook strength of opening text."""
        if not text:
            return 0.0

        # Get first sentence/line
        lines = text.split('\n')
        first_line = lines[0] if lines else ""

        score = 0.5  # Base score

        # Check for viral triggers in opening
        for category, triggers in self.VIRAL_TRIGGERS.items():
            for trigger in triggers:
                if trigger.lower() in first_line.lower():
                    score += 0.1
                    break

        # Check for question
        if '?' in first_line:
            score += 0.1

        # Check for numbers/lists
        if re.search(r'\d+', first_line):
            score += 0.1

        # Check for capitalization (attention grabbing but not excessive)
        caps_ratio = sum(1 for c in first_line if c.isupper()) / max(len(first_line), 1)
        if 0.1 < caps_ratio < 0.5:
            score += 0.05

        # Check length (not too short, not too long)
        if 20 <= len(first_line) <= 100:
            score += 0.1

        return min(score, 1.0)

    def _analyze_emotion(self, text: str) -> float:
        """Analyze emotional appeal of content."""
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.4  # Base score

        # Check for emotion triggers
        emotion_triggers = self.VIRAL_TRIGGERS["emotion"]
        emotion_count = sum(1 for t in emotion_triggers if t in text_lower)
        score += min(emotion_count * 0.1, 0.3)

        # Check for exclamation marks (excitement)
        exclamations = text.count('!')
        if 1 <= exclamations <= 3:
            score += 0.1
        elif exclamations > 3:
            score -= 0.1  # Too many is spammy

        # Check for emojis (simplified)
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F650]', text))
        if 1 <= emoji_count <= 5:
            score += 0.1

        return min(max(score, 0.0), 1.0)

    def _analyze_curiosity(self, text: str) -> float:
        """Analyze curiosity-inducing elements."""
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.3

        # Check for curiosity triggers
        curiosity_triggers = self.VIRAL_TRIGGERS["curiosity"]
        for trigger in curiosity_triggers:
            if trigger in text_lower:
                score += 0.15

        # Check for open loops/incomplete information
        incomplete_phrases = ["but", "however", "wait", "here's the thing"]
        for phrase in incomplete_phrases:
            if phrase in text_lower:
                score += 0.1

        # Questions create curiosity
        score += min(text.count('?') * 0.1, 0.2)

        return min(score, 1.0)

    def _analyze_cta(self, text: str) -> float:
        """Analyze call-to-action strength."""
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.0

        cta_phrases = [
            "follow", "like", "comment", "share", "subscribe", "click",
            "tap", "link in bio", "check out", "dm me", "save this",
            "tag", "let me know", "drop a", "tell me", "what do you think",
        ]

        for phrase in cta_phrases:
            if phrase in text_lower:
                score += 0.2

        return min(score, 1.0)

    def _analyze_readability(self, text: str) -> float:
        """Analyze text readability."""
        if not text:
            return 0.5

        words = text.split()
        sentences = text.split('.')

        if not words:
            return 0.5

        # Average word length
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Penalize very long words
        if avg_word_length > 7:
            return 0.4
        elif avg_word_length > 5:
            return 0.7
        else:
            return 0.9

    def _analyze_hashtags(self, hashtags: list[str], platform: str) -> float:
        """Analyze hashtag strategy."""
        if not hashtags:
            return 0.3  # Missing hashtags penalty

        count = len(hashtags)

        # Platform-specific optimal counts
        optimal_counts = {
            "instagram": (5, 15),
            "tiktok": (3, 5),
            "twitter": (1, 3),
            "linkedin": (3, 5),
            "youtube": (5, 15),
        }

        min_opt, max_opt = optimal_counts.get(platform, (3, 10))

        if min_opt <= count <= max_opt:
            score = 0.8
        elif count < min_opt:
            score = 0.5
        else:
            score = 0.6  # Too many hashtags

        # Check for variety (not all broad/niche)
        broad_tags = ["fyp", "viral", "trending", "explore"]
        broad_count = sum(1 for h in hashtags if h.lower() in broad_tags)
        niche_count = count - broad_count

        if 0 < broad_count < count and niche_count > 0:
            score += 0.1  # Good mix

        return min(score, 1.0)

    def _check_optimal_length(self, content: dict, platform: str) -> bool:
        """Check if content length is optimal for platform."""
        text = content.get("text", "") or content.get("caption", "")
        duration = content.get("duration_seconds", 0)

        optimal = self.OPTIMAL_LENGTHS.get(platform, {})

        # Check video duration
        if duration and "video" in optimal:
            min_d, max_d = optimal["video"]
            if min_d <= duration <= max_d:
                return True

        # Check text length
        if text and "text" in optimal:
            min_t, max_t = optimal["text"]
            if min_t <= len(text) <= max_t:
                return True

        return False

    def _analyze_trend_alignment(
        self,
        text: str,
        hashtags: list[str],
        platform: str,
    ) -> float:
        """Analyze alignment with current trends."""
        # In production, this would check against real trend data
        # For now, check for common trending patterns

        score = 0.4  # Base score

        trend_indicators = ["trend", "viral", "fyp", "foryou", "explore"]
        text_lower = text.lower() if text else ""

        for indicator in trend_indicators:
            if indicator in text_lower or any(indicator in h.lower() for h in hashtags):
                score += 0.1

        return min(score, 1.0)

    def _calculate_time_score(
        self,
        posting_time: Optional[datetime],
        platform: str,
    ) -> float:
        """Calculate posting time optimization score."""
        if not posting_time:
            return 0.5  # Neutral if no time specified

        hour = posting_time.hour
        day = posting_time.weekday()  # 0=Monday

        # General peak hours (9-11 AM, 7-9 PM)
        peak_hours = [9, 10, 11, 19, 20, 21]
        if hour in peak_hours:
            return 0.9

        # Good hours
        good_hours = [12, 13, 14, 17, 18]
        if hour in good_hours:
            return 0.7

        # Off-peak
        if hour < 6 or hour > 22:
            return 0.3

        return 0.5

    def _predict_views(
        self,
        viral_score: float,
        creator_stats: Optional[dict],
        platform: str,
    ) -> tuple[int, int]:
        """Predict view range based on viral score."""
        base_followers = creator_stats.get("follower_count", 10000) if creator_stats else 10000

        # Viral score affects reach multiplier
        if viral_score >= 80:
            multiplier = (3.0, 10.0)
        elif viral_score >= 60:
            multiplier = (1.5, 3.0)
        elif viral_score >= 40:
            multiplier = (0.5, 1.5)
        else:
            multiplier = (0.1, 0.5)

        min_views = int(base_followers * multiplier[0])
        max_views = int(base_followers * multiplier[1])

        return (min_views, max_views)

    def _predict_likes(
        self,
        viral_score: float,
        views: tuple[int, int],
    ) -> tuple[int, int]:
        """Predict like range."""
        # Average like rate varies by viral potential
        if viral_score >= 80:
            rate = (0.08, 0.15)
        elif viral_score >= 60:
            rate = (0.05, 0.08)
        else:
            rate = (0.02, 0.05)

        return (int(views[0] * rate[0]), int(views[1] * rate[1]))

    def _predict_comments(
        self,
        viral_score: float,
        views: tuple[int, int],
    ) -> tuple[int, int]:
        """Predict comment range."""
        if viral_score >= 80:
            rate = (0.02, 0.05)
        elif viral_score >= 60:
            rate = (0.01, 0.02)
        else:
            rate = (0.005, 0.01)

        return (int(views[0] * rate[0]), int(views[1] * rate[1]))

    def _predict_shares(
        self,
        viral_score: float,
        views: tuple[int, int],
    ) -> tuple[int, int]:
        """Predict share range."""
        if viral_score >= 80:
            rate = (0.01, 0.03)
        elif viral_score >= 60:
            rate = (0.005, 0.01)
        else:
            rate = (0.001, 0.005)

        return (int(views[0] * rate[0]), int(views[1] * rate[1]))

    def _calculate_confidence(self, factors: list[ViralFactor]) -> float:
        """Calculate prediction confidence."""
        # More factors analyzed = higher confidence
        factor_count = len(factors)
        base_confidence = min(factor_count * 0.1, 0.6)

        # Consistency of scores increases confidence
        scores = [f.score for f in factors]
        if scores:
            variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
            consistency_bonus = max(0, 0.3 - variance)
        else:
            consistency_bonus = 0

        return min(base_confidence + consistency_bonus, 0.95)

    def _describe_hook_score(self, score: float) -> str:
        """Generate description for hook score."""
        if score >= 0.8:
            return "Strong hook that grabs attention immediately"
        elif score >= 0.6:
            return "Good hook with room for improvement"
        elif score >= 0.4:
            return "Moderate hook - consider making it more compelling"
        else:
            return "Weak hook - first impression needs work"

    def _describe_emotion_score(self, score: float) -> str:
        """Generate description for emotion score."""
        if score >= 0.8:
            return "Highly emotional content that resonates strongly"
        elif score >= 0.6:
            return "Good emotional appeal"
        else:
            return "Could use more emotional elements"

    def _describe_trend_score(self, score: float) -> str:
        """Generate description for trend alignment."""
        if score >= 0.8:
            return "Well-aligned with current trends"
        elif score >= 0.6:
            return "Some trend alignment"
        else:
            return "Consider incorporating trending elements"

    def _describe_visual_score(self, score: float) -> str:
        """Generate description for visual quality."""
        if score >= 0.8:
            return "High-quality visuals"
        elif score >= 0.6:
            return "Good visual quality"
        else:
            return "Visual quality could be improved"

    def _describe_hashtag_score(self, score: float) -> str:
        """Generate description for hashtag strategy."""
        if score >= 0.8:
            return "Excellent hashtag strategy"
        elif score >= 0.6:
            return "Good hashtag usage"
        else:
            return "Hashtag strategy needs improvement"

    def _describe_time_score(self, score: float) -> str:
        """Generate description for posting time."""
        if score >= 0.8:
            return "Optimal posting time"
        elif score >= 0.6:
            return "Good posting time"
        else:
            return "Consider posting at peak hours"

    def _get_hook_suggestions(self, score: float, content: dict) -> list[str]:
        """Get suggestions for improving hook."""
        suggestions = []

        if score < 0.7:
            suggestions.append("Start with a question to create curiosity")
            suggestions.append("Use power words like 'secret', 'revealed', or 'discover'")
            suggestions.append("Include a number or statistic in your opening")

        return suggestions

    def _get_emotion_suggestions(self, score: float) -> list[str]:
        """Get suggestions for improving emotional appeal."""
        suggestions = []

        if score < 0.7:
            suggestions.append("Share a personal story or experience")
            suggestions.append("Use vivid, descriptive language")
            suggestions.append("Include emotional trigger words")

        return suggestions

    def _get_trend_suggestions(self, score: float, platform: str) -> list[str]:
        """Get suggestions for trend alignment."""
        suggestions = []

        if score < 0.7:
            suggestions.append(f"Check {platform}'s explore page for trending topics")
            suggestions.append("Use trending sounds or audio")
            suggestions.append("Reference current events or cultural moments")

        return suggestions

    def _get_visual_suggestions(self, score: float) -> list[str]:
        """Get suggestions for visual improvement."""
        suggestions = []

        if score < 0.7:
            suggestions.append("Use high-contrast colors for better visibility")
            suggestions.append("Ensure good lighting in videos")
            suggestions.append("Create an eye-catching thumbnail")

        return suggestions

    def _get_hashtag_suggestions(self, score: float, content: dict) -> list[str]:
        """Get suggestions for hashtag strategy."""
        suggestions = []

        hashtags = content.get("hashtags", [])

        if not hashtags:
            suggestions.append("Add relevant hashtags for discoverability")
        elif len(hashtags) < 3:
            suggestions.append("Add more specific niche hashtags")
        elif len(hashtags) > 15:
            suggestions.append("Reduce hashtags to the most relevant ones")

        if score < 0.7:
            suggestions.append("Mix broad and niche hashtags")
            suggestions.append("Research hashtags your audience follows")

        return suggestions

    def _get_length_suggestions(self, content: dict, platform: str) -> list[str]:
        """Get suggestions for content length."""
        optimal = self.OPTIMAL_LENGTHS.get(platform, {})
        suggestions = []

        text = content.get("text", "") or content.get("caption", "")
        if text and "text" in optimal:
            min_t, max_t = optimal["text"]
            if len(text) < min_t:
                suggestions.append(f"Consider adding more detail ({min_t}-{max_t} characters recommended)")
            elif len(text) > max_t:
                suggestions.append(f"Consider shortening your text ({min_t}-{max_t} characters recommended)")

        return suggestions

    def _get_time_suggestions(self, platform: str) -> list[str]:
        """Get suggestions for posting time."""
        return [
            "Post during peak hours (9-11 AM or 7-9 PM)",
            "Test different times and track performance",
            "Consider your audience's timezone",
        ]

    def _get_best_posting_times(self, platform: str) -> list[str]:
        """Get best posting times for platform."""
        # Generalized best times
        return ["9:00 AM", "11:00 AM", "7:00 PM", "9:00 PM"]

    def _get_worst_posting_times(self, platform: str) -> list[str]:
        """Get worst posting times for platform."""
        return ["2:00 AM", "4:00 AM", "5:00 AM"]
