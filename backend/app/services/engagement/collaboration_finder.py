"""
Collaboration Finder Service

AI-powered influencer matching for collaborations, partnerships,
and cross-promotions based on niche, audience, and compatibility.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CollaborationType(str, Enum):
    """Types of collaborations."""
    COLLAB_POST = "collab_post"  # Joint content creation
    CROSS_PROMO = "cross_promo"  # Mutual promotion
    TAKEOVER = "takeover"  # Account takeover
    GIVEAWAY = "giveaway"  # Joint giveaway
    CHALLENGE = "challenge"  # Joint challenge/trend
    PODCAST_GUEST = "podcast_guest"  # Podcast appearance
    LIVE_STREAM = "live_stream"  # Joint live stream
    SERIES = "series"  # Content series together
    BRAND_CAMPAIGN = "brand_campaign"  # Joint brand deal


class CollaborationStatus(str, Enum):
    """Status of collaboration requests."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class InfluencerProfile:
    """Profile for collaboration matching."""
    user_id: str
    username: str
    display_name: str
    platforms: List[str]
    niches: List[str]
    total_followers: int
    engagement_rate: float
    avg_views: int = 0
    content_style: List[str] = field(default_factory=list)
    collaboration_types: List[CollaborationType] = field(default_factory=list)
    location: Optional[str] = None
    language: str = "en"
    verified: bool = False
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    past_collaborations: int = 0
    response_rate: float = 0.0  # % of messages responded to
    avg_response_time_hours: float = 24.0


@dataclass
class CollaborationMatch:
    """A matched influencer for potential collaboration."""
    match_id: str
    influencer: InfluencerProfile
    overall_score: float  # 0-100
    niche_score: float
    audience_score: float
    engagement_score: float
    compatibility_score: float
    matching_niches: List[str]
    matching_platforms: List[str]
    recommended_collab_types: List[CollaborationType]
    estimated_reach: int
    strengths: List[str]
    considerations: List[str]
    suggested_approach: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CollaborationRequest:
    """A collaboration request between influencers."""
    request_id: str
    sender_id: str
    recipient_id: str
    collab_type: CollaborationType
    title: str
    description: str
    proposed_date: Optional[datetime] = None
    platforms: List[str] = field(default_factory=list)
    status: CollaborationStatus = CollaborationStatus.PENDING
    message: Optional[str] = None
    response_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None


class CollaborationFinder:
    """
    AI-powered collaboration and partnership finder.

    Features:
    - Influencer discovery and matching
    - Niche and audience compatibility scoring
    - Collaboration type recommendations
    - Outreach message generation
    - Request management
    """

    # Scoring weights
    WEIGHTS = {
        "niche": 0.30,
        "audience": 0.25,
        "engagement": 0.25,
        "compatibility": 0.20,
    }

    # Ideal follower ratios for collaborations (partner/self)
    IDEAL_FOLLOWER_RATIO = {
        "min": 0.3,  # Partner should have at least 30% of your followers
        "max": 3.0,  # Partner should have at most 3x your followers
        "optimal_min": 0.5,
        "optimal_max": 2.0,
    }

    def __init__(self):
        self._llm_client = None
        self._influencer_cache: Dict[str, InfluencerProfile] = {}
        self._request_cache: Dict[str, CollaborationRequest] = {}

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            from app.config import settings
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    async def find_collaborators(
        self,
        user_profile: InfluencerProfile,
        target_niches: Optional[List[str]] = None,
        target_platforms: Optional[List[str]] = None,
        collab_types: Optional[List[CollaborationType]] = None,
        min_followers: int = 1000,
        max_followers: Optional[int] = None,
        min_engagement_rate: float = 1.0,
        location: Optional[str] = None,
        limit: int = 20,
    ) -> List[CollaborationMatch]:
        """
        Find potential collaborators matching criteria.

        Args:
            user_profile: The user's profile for matching
            target_niches: Specific niches to target
            target_platforms: Platforms for collaboration
            collab_types: Types of collaborations interested in
            min_followers: Minimum follower count
            max_followers: Maximum follower count
            min_engagement_rate: Minimum engagement rate
            location: Geographic preference
            limit: Maximum results to return

        Returns:
            List of collaboration matches sorted by score
        """
        # Use target criteria or defaults from user profile
        niches = target_niches or user_profile.niches
        platforms = target_platforms or user_profile.platforms

        # Get candidate influencers (in production, from database)
        candidates = await self._get_candidates(
            niches=niches,
            platforms=platforms,
            min_followers=min_followers,
            max_followers=max_followers or user_profile.total_followers * 5,
            min_engagement_rate=min_engagement_rate,
            location=location,
            exclude_user_id=user_profile.user_id,
        )

        # Score each candidate
        matches = []
        for candidate in candidates:
            match = await self._score_match(
                user_profile=user_profile,
                candidate=candidate,
                target_niches=niches,
                target_platforms=platforms,
                preferred_collab_types=collab_types,
            )
            matches.append(match)

        # Sort by overall score
        matches.sort(key=lambda m: m.overall_score, reverse=True)

        return matches[:limit]

    async def discover_by_content(
        self,
        user_profile: InfluencerProfile,
        content_keywords: List[str],
        limit: int = 10,
    ) -> List[CollaborationMatch]:
        """
        Discover collaborators based on content similarity.

        Finds influencers creating similar content for potential synergy.
        """
        # In production, use content analysis to find similar creators
        candidates = await self._search_by_content(
            keywords=content_keywords,
            platforms=user_profile.platforms,
            exclude_user_id=user_profile.user_id,
        )

        matches = []
        for candidate in candidates:
            match = await self._score_match(
                user_profile=user_profile,
                candidate=candidate,
                target_niches=user_profile.niches,
                target_platforms=user_profile.platforms,
            )
            matches.append(match)

        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return matches[:limit]

    async def get_recommended_partners(
        self,
        user_profile: InfluencerProfile,
        limit: int = 10,
    ) -> List[CollaborationMatch]:
        """
        Get AI-recommended collaboration partners.

        Uses multiple signals to find ideal partners.
        """
        # Multi-factor recommendation
        matches = await self.find_collaborators(
            user_profile=user_profile,
            min_followers=int(user_profile.total_followers * 0.3),
            max_followers=int(user_profile.total_followers * 3),
            min_engagement_rate=user_profile.engagement_rate * 0.5,
            limit=limit * 2,
        )

        # Re-rank with AI insights
        for match in matches:
            ai_boost = await self._get_ai_compatibility_boost(
                user_profile, match.influencer
            )
            match.overall_score = min(100, match.overall_score + ai_boost)

        matches.sort(key=lambda m: m.overall_score, reverse=True)
        return matches[:limit]

    async def create_collaboration_request(
        self,
        sender_id: str,
        recipient_id: str,
        collab_type: CollaborationType,
        title: str,
        description: str,
        proposed_date: Optional[datetime] = None,
        platforms: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> CollaborationRequest:
        """
        Create a collaboration request.
        """
        request = CollaborationRequest(
            request_id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            collab_type=collab_type,
            title=title,
            description=description,
            proposed_date=proposed_date,
            platforms=platforms or [],
            message=message,
        )

        # Store request
        self._request_cache[request.request_id] = request

        return request

    async def respond_to_request(
        self,
        request_id: str,
        user_id: str,
        accept: bool,
        response_message: Optional[str] = None,
    ) -> CollaborationRequest:
        """
        Respond to a collaboration request.
        """
        request = self._request_cache.get(request_id)
        if not request:
            raise ValueError("Request not found")

        if request.recipient_id != user_id:
            raise ValueError("Not authorized to respond to this request")

        request.status = CollaborationStatus.ACCEPTED if accept else CollaborationStatus.DECLINED
        request.response_message = response_message
        request.responded_at = datetime.now(timezone.utc)

        return request

    async def get_pending_requests(
        self,
        user_id: str,
        as_sender: bool = False,
    ) -> List[CollaborationRequest]:
        """
        Get pending collaboration requests.
        """
        requests = []
        for request in self._request_cache.values():
            if request.status != CollaborationStatus.PENDING:
                continue

            if as_sender:
                if request.sender_id == user_id:
                    requests.append(request)
            else:
                if request.recipient_id == user_id:
                    requests.append(request)

        return requests

    async def generate_outreach_message(
        self,
        sender_profile: InfluencerProfile,
        recipient_profile: InfluencerProfile,
        collab_type: CollaborationType,
        custom_notes: Optional[str] = None,
    ) -> str:
        """
        Generate a personalized outreach message for collaboration.
        """
        client = await self._get_llm_client()

        collab_descriptions = {
            CollaborationType.COLLAB_POST: "creating a collaborative post together",
            CollaborationType.CROSS_PROMO: "cross-promoting each other's content",
            CollaborationType.TAKEOVER: "doing an account takeover",
            CollaborationType.GIVEAWAY: "hosting a joint giveaway",
            CollaborationType.CHALLENGE: "starting a challenge together",
            CollaborationType.PODCAST_GUEST: "having you as a podcast guest",
            CollaborationType.LIVE_STREAM: "doing a joint live stream",
            CollaborationType.SERIES: "creating a content series together",
            CollaborationType.BRAND_CAMPAIGN: "partnering on brand campaigns",
        }

        prompt = f"""Write a personalized, friendly DM to propose a collaboration.

SENDER: {sender_profile.display_name} (@{sender_profile.username})
- Niches: {', '.join(sender_profile.niches)}
- Followers: {sender_profile.total_followers:,}
- Platforms: {', '.join(sender_profile.platforms)}

RECIPIENT: {recipient_profile.display_name} (@{recipient_profile.username})
- Niches: {', '.join(recipient_profile.niches)}
- Followers: {recipient_profile.total_followers:,}
- Bio: {recipient_profile.bio or 'N/A'}

COLLABORATION TYPE: {collab_descriptions.get(collab_type, collab_type.value)}

{f"ADDITIONAL NOTES: {custom_notes}" if custom_notes else ""}

Requirements:
- Be genuine and not too salesy
- Mention specific reasons why they'd be a good match
- Keep it concise (under 300 characters for DM)
- Include a clear ask/next step
- Sound personal, not like a template

Write the DM message only:"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You write authentic, effective collaboration outreach messages.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.8,
        )

        return response.choices[0].message.content.strip()

    async def suggest_collab_ideas(
        self,
        profile1: InfluencerProfile,
        profile2: InfluencerProfile,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate creative collaboration ideas for two influencers.
        """
        client = await self._get_llm_client()

        prompt = f"""Generate {count} creative collaboration ideas for these two influencers:

INFLUENCER 1: {profile1.display_name}
- Niches: {', '.join(profile1.niches)}
- Platforms: {', '.join(profile1.platforms)}
- Style: {', '.join(profile1.content_style) if profile1.content_style else 'N/A'}

INFLUENCER 2: {profile2.display_name}
- Niches: {', '.join(profile2.niches)}
- Platforms: {', '.join(profile2.platforms)}
- Style: {', '.join(profile2.content_style) if profile2.content_style else 'N/A'}

For each idea provide:
1. Title (catchy name)
2. Description (2-3 sentences)
3. Best platform
4. Collaboration type
5. Estimated effort (low/medium/high)

Format as JSON array."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative social media strategist. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.9,
        )

        try:
            import json
            ideas = json.loads(response.choices[0].message.content)
            return ideas if isinstance(ideas, list) else []
        except json.JSONDecodeError:
            return []

    async def _get_candidates(
        self,
        niches: List[str],
        platforms: List[str],
        min_followers: int,
        max_followers: int,
        min_engagement_rate: float,
        location: Optional[str],
        exclude_user_id: str,
    ) -> List[InfluencerProfile]:
        """Get candidate influencers from database."""
        # In production, query database
        # Return mock data for now
        return self._generate_mock_candidates(
            niches, platforms, min_followers, max_followers
        )

    async def _search_by_content(
        self,
        keywords: List[str],
        platforms: List[str],
        exclude_user_id: str,
    ) -> List[InfluencerProfile]:
        """Search influencers by content keywords."""
        # In production, use search/ML
        return []

    async def _score_match(
        self,
        user_profile: InfluencerProfile,
        candidate: InfluencerProfile,
        target_niches: List[str],
        target_platforms: List[str],
        preferred_collab_types: Optional[List[CollaborationType]] = None,
    ) -> CollaborationMatch:
        """Score a potential collaboration match."""
        # Calculate individual scores

        # Niche score
        matching_niches = list(set(user_profile.niches) & set(candidate.niches))
        niche_overlap = len(matching_niches) / max(len(user_profile.niches), 1)
        niche_score = min(100, niche_overlap * 100 + (20 if matching_niches else 0))

        # Audience/reach score
        follower_ratio = candidate.total_followers / max(user_profile.total_followers, 1)
        if self.IDEAL_FOLLOWER_RATIO["optimal_min"] <= follower_ratio <= self.IDEAL_FOLLOWER_RATIO["optimal_max"]:
            audience_score = 100
        elif self.IDEAL_FOLLOWER_RATIO["min"] <= follower_ratio <= self.IDEAL_FOLLOWER_RATIO["max"]:
            audience_score = 70
        else:
            audience_score = 40
        audience_score = min(100, audience_score)

        # Engagement score
        engagement_ratio = candidate.engagement_rate / max(user_profile.engagement_rate, 0.1)
        engagement_score = min(100, 50 + (engagement_ratio * 25))

        # Platform compatibility
        matching_platforms = list(set(user_profile.platforms) & set(candidate.platforms))
        platform_overlap = len(matching_platforms) / max(len(user_profile.platforms), 1)
        compatibility_score = min(100, platform_overlap * 80 + 20)

        # Overall score
        overall_score = (
            niche_score * self.WEIGHTS["niche"] +
            audience_score * self.WEIGHTS["audience"] +
            engagement_score * self.WEIGHTS["engagement"] +
            compatibility_score * self.WEIGHTS["compatibility"]
        )

        # Recommend collaboration types
        recommended_types = self._recommend_collab_types(
            user_profile, candidate, preferred_collab_types
        )

        # Generate insights
        strengths = []
        considerations = []

        if niche_score > 70:
            strengths.append(f"Strong niche alignment in {', '.join(matching_niches[:2])}")
        if engagement_ratio > 1.2:
            strengths.append("Higher than average engagement rate")
        if candidate.verified:
            strengths.append("Verified account adds credibility")
        if candidate.response_rate > 0.7:
            strengths.append("Highly responsive to messages")

        if follower_ratio > 2:
            considerations.append("Larger audience may have different expectations")
        if follower_ratio < 0.5:
            considerations.append("Smaller audience - consider value exchange")
        if not matching_platforms:
            considerations.append("Different primary platforms - cross-platform collab needed")

        # Suggested approach
        approach = await self._generate_approach(user_profile, candidate, recommended_types)

        return CollaborationMatch(
            match_id=str(uuid.uuid4()),
            influencer=candidate,
            overall_score=round(overall_score, 1),
            niche_score=round(niche_score, 1),
            audience_score=round(audience_score, 1),
            engagement_score=round(engagement_score, 1),
            compatibility_score=round(compatibility_score, 1),
            matching_niches=matching_niches,
            matching_platforms=matching_platforms,
            recommended_collab_types=recommended_types,
            estimated_reach=candidate.total_followers + user_profile.total_followers,
            strengths=strengths,
            considerations=considerations,
            suggested_approach=approach,
        )

    def _recommend_collab_types(
        self,
        user: InfluencerProfile,
        candidate: InfluencerProfile,
        preferred: Optional[List[CollaborationType]],
    ) -> List[CollaborationType]:
        """Recommend collaboration types based on profiles."""
        recommended = []

        # Common platforms suggest certain types
        common_platforms = set(user.platforms) & set(candidate.platforms)

        if "instagram" in common_platforms:
            recommended.extend([CollaborationType.COLLAB_POST, CollaborationType.LIVE_STREAM])
        if "youtube" in common_platforms:
            recommended.extend([CollaborationType.PODCAST_GUEST, CollaborationType.SERIES])
        if "tiktok" in common_platforms:
            recommended.extend([CollaborationType.CHALLENGE, CollaborationType.CROSS_PROMO])

        # Similar follower count suggests giveaways
        ratio = candidate.total_followers / max(user.total_followers, 1)
        if 0.5 <= ratio <= 2:
            recommended.append(CollaborationType.GIVEAWAY)

        # Cross promo always works
        recommended.append(CollaborationType.CROSS_PROMO)

        # Filter by preferred if specified
        if preferred:
            recommended = [r for r in recommended if r in preferred] or recommended

        # Remove duplicates, keep order
        seen = set()
        unique = []
        for r in recommended:
            if r not in seen:
                seen.add(r)
                unique.append(r)

        return unique[:4]

    async def _generate_approach(
        self,
        user: InfluencerProfile,
        candidate: InfluencerProfile,
        collab_types: List[CollaborationType],
    ) -> str:
        """Generate a suggested approach for the collaboration."""
        ratio = candidate.total_followers / max(user.total_followers, 1)

        if ratio > 2:
            return "Lead with value - explain what unique benefit you bring to their larger audience"
        elif ratio < 0.5:
            return "Offer mentorship angle - emphasize mutual growth and cross-exposure"
        else:
            return "Propose equal partnership - suggest a mutually beneficial content exchange"

    async def _get_ai_compatibility_boost(
        self,
        user: InfluencerProfile,
        candidate: InfluencerProfile,
    ) -> float:
        """Get AI-computed compatibility boost."""
        # In production, use ML model
        # Simple heuristic for now
        boost = 0

        # Same location boost
        if user.location and candidate.location and user.location == candidate.location:
            boost += 5

        # Same language boost
        if user.language == candidate.language:
            boost += 3

        # Content style overlap
        style_overlap = len(set(user.content_style) & set(candidate.content_style))
        boost += style_overlap * 2

        return min(boost, 15)

    def _generate_mock_candidates(
        self,
        niches: List[str],
        platforms: List[str],
        min_followers: int,
        max_followers: int,
    ) -> List[InfluencerProfile]:
        """Generate mock candidates for testing."""
        import random

        mock_data = [
            ("lifestyle_sarah", "Sarah Chen", ["lifestyle", "fashion", "travel"]),
            ("tech_mike", "Mike Johnson", ["tech", "gaming", "reviews"]),
            ("fitness_emma", "Emma Wilson", ["fitness", "health", "nutrition"]),
            ("food_alex", "Alex Rodriguez", ["food", "cooking", "recipes"]),
            ("beauty_zoe", "Zoe Thompson", ["beauty", "skincare", "makeup"]),
            ("travel_jake", "Jake Miller", ["travel", "adventure", "photography"]),
            ("music_luna", "Luna Park", ["music", "entertainment", "lifestyle"]),
            ("art_oliver", "Oliver Brown", ["art", "design", "creativity"]),
        ]

        candidates = []
        for username, name, candidate_niches in mock_data:
            if not any(n in candidate_niches for n in niches):
                continue

            followers = random.randint(min_followers, max_followers)

            candidates.append(InfluencerProfile(
                user_id=str(uuid.uuid4()),
                username=username,
                display_name=name,
                platforms=random.sample(platforms, min(2, len(platforms))),
                niches=candidate_niches,
                total_followers=followers,
                engagement_rate=random.uniform(2.0, 8.0),
                avg_views=int(followers * random.uniform(0.1, 0.3)),
                content_style=["educational", "entertaining"],
                location="United States",
                verified=random.choice([True, False]),
                bio=f"{name} | Content Creator | {candidate_niches[0].title()} enthusiast",
                past_collaborations=random.randint(0, 50),
                response_rate=random.uniform(0.5, 0.95),
            ))

        return candidates

    async def get_collaboration_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get collaboration statistics for a user."""
        requests = [r for r in self._request_cache.values()
                   if r.sender_id == user_id or r.recipient_id == user_id]

        sent = [r for r in requests if r.sender_id == user_id]
        received = [r for r in requests if r.recipient_id == user_id]

        return {
            "total_requests_sent": len(sent),
            "total_requests_received": len(received),
            "accepted_rate": sum(1 for r in sent if r.status == CollaborationStatus.ACCEPTED) / max(len(sent), 1),
            "pending_incoming": sum(1 for r in received if r.status == CollaborationStatus.PENDING),
            "pending_outgoing": sum(1 for r in sent if r.status == CollaborationStatus.PENDING),
            "completed_collaborations": sum(1 for r in requests if r.status == CollaborationStatus.COMPLETED),
            "by_type": {
                ct.value: sum(1 for r in requests if r.collab_type == ct)
                for ct in CollaborationType
            },
        }
