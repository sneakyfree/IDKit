"""
Feed Ranking Algorithm

TikTok-inspired algorithm for ranking posts in the IDKit feed.
Prioritizes engagement signals + recency + personalization.
"""

import math
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.models.feed import FeedPost, Follow, FeedLike, FeedComment, FeedSave, UserProfile


class FeedAlgorithm:
    """
    TikTok-inspired feed ranking algorithm.

    Calculates scores based on:
    - Engagement rate (likes, comments, shares, saves)
    - Recency (newer posts score higher)
    - Creator quality (historical engagement)
    - Personalization (user preferences and interactions)
    """

    # Weight factors for scoring
    WEIGHTS = {
        "engagement_rate": 0.35,
        "recency": 0.25,
        "creator_quality": 0.15,
        "personalization": 0.15,
        "diversity": 0.10,
    }

    # Engagement multipliers
    ENGAGEMENT_MULTIPLIERS = {
        "like": 1.0,
        "comment": 2.0,
        "share": 3.0,
        "save": 2.5,
    }

    # Recency half-life in hours (posts lose half their recency score after this time)
    RECENCY_HALF_LIFE = 48

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_post_score(
        self,
        post: FeedPost,
        viewer_id: uuid.UUID | None = None,
    ) -> float:
        """
        Calculate ranking score for a single post.

        Args:
            post: The post to score
            viewer_id: Optional viewer ID for personalization

        Returns:
            Score between 0 and 1
        """
        engagement = self._engagement_score(post)
        recency = self._recency_score(post.created_at)
        creator = await self._creator_quality_score(post.user_id)

        personal = 0.0
        if viewer_id:
            personal = await self._personalization_score(post, viewer_id)

        score = (
            engagement * self.WEIGHTS["engagement_rate"]
            + recency * self.WEIGHTS["recency"]
            + creator * self.WEIGHTS["creator_quality"]
            + personal * self.WEIGHTS["personalization"]
        )

        return min(max(score, 0.0), 1.0)

    def _engagement_score(self, post: FeedPost) -> float:
        """
        Calculate engagement rate score.

        Higher engagement relative to views = higher score.
        New posts with no views get a neutral score.
        """
        if post.view_count == 0:
            return 0.5  # Neutral score for new posts

        weighted_engagement = (
            post.like_count * self.ENGAGEMENT_MULTIPLIERS["like"]
            + post.comment_count * self.ENGAGEMENT_MULTIPLIERS["comment"]
            + post.share_count * self.ENGAGEMENT_MULTIPLIERS["share"]
            + post.save_count * self.ENGAGEMENT_MULTIPLIERS["save"]
        )

        engagement_rate = weighted_engagement / post.view_count

        # Scale to 0-1 range (10% engagement = perfect score)
        return min(engagement_rate * 10, 1.0)

    def _recency_score(self, created_at: datetime) -> float:
        """
        Calculate recency decay score.

        Uses exponential decay with configurable half-life.
        """
        now = datetime.now(timezone.utc)

        # Handle timezone-naive datetime
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        hours_old = (now - created_at).total_seconds() / 3600
        return math.exp(-hours_old / self.RECENCY_HALF_LIFE * math.log(2))

    async def _creator_quality_score(self, user_id: uuid.UUID) -> float:
        """
        Calculate creator quality based on historical engagement.

        Looks at average engagement across recent posts.
        """
        # Get recent posts from this creator
        result = await self.db.execute(
            select(
                func.avg(FeedPost.engagement_score).label("avg_engagement"),
                func.count(FeedPost.id).label("post_count"),
            )
            .where(FeedPost.user_id == user_id)
            .where(
                FeedPost.created_at
                > func.now() - func.cast("30 days", func.literal_column("interval"))
            )
        )
        row = result.one_or_none()

        if row is None or row.post_count == 0:
            return 0.5  # Neutral for new creators

        # Return average engagement, capped at 1.0
        return min(row.avg_engagement or 0.5, 1.0)

    async def _personalization_score(
        self,
        post: FeedPost,
        viewer_id: uuid.UUID,
    ) -> float:
        """
        Calculate personalization score based on viewer's preferences.

        Factors:
        - Following the creator
        - Engagement with similar content
        - Hashtag affinity
        """
        score = 0.0

        # Boost if viewer follows the creator
        follow_result = await self.db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == viewer_id,
                    Follow.following_id == post.user_id,
                )
            )
        )
        if follow_result.scalar_one_or_none():
            score += 0.5

        # Check if viewer has liked creator's posts before
        like_result = await self.db.execute(
            select(func.count(FeedLike.id)).where(
                and_(
                    FeedLike.user_id == viewer_id,
                    FeedLike.post_id.in_(
                        select(FeedPost.id).where(FeedPost.user_id == post.user_id)
                    ),
                )
            )
        )
        like_count = like_result.scalar() or 0
        if like_count > 0:
            score += min(like_count * 0.1, 0.3)

        # Hashtag affinity scoring
        hashtag_score = await self._hashtag_affinity_score(post, viewer_id)
        score += hashtag_score

        return min(score, 1.0)

    async def _hashtag_affinity_score(
        self,
        post: FeedPost,
        viewer_id: uuid.UUID,
    ) -> float:
        """
        Calculate hashtag affinity score based on viewer's interaction history.

        Analyzes hashtags from posts the viewer has engaged with (liked, commented, saved)
        and computes overlap with the current post's hashtags.

        Returns:
            Score between 0 and 0.3 (max contribution to personalization)
        """
        post_hashtags = set(post.hashtags) if post.hashtags else set()
        if not post_hashtags:
            return 0.0

        # Get viewer's hashtag preferences from their profile niche_tags
        profile_result = await self.db.execute(
            select(UserProfile.niche_tags).where(UserProfile.user_id == viewer_id)
        )
        profile_row = profile_result.scalar_one_or_none()
        profile_tags = set(profile_row) if profile_row else set()

        # Get hashtags from posts the viewer has liked (recent 100)
        liked_hashtags_result = await self.db.execute(
            select(FeedPost.hashtags)
            .join(FeedLike, FeedLike.post_id == FeedPost.id)
            .where(FeedLike.user_id == viewer_id)
            .where(FeedPost.hashtags.isnot(None))
            .order_by(FeedLike.created_at.desc())
            .limit(100)
        )
        liked_posts_hashtags = liked_hashtags_result.scalars().all()

        # Get hashtags from posts the viewer has commented on (recent 50)
        commented_hashtags_result = await self.db.execute(
            select(FeedPost.hashtags)
            .join(FeedComment, FeedComment.post_id == FeedPost.id)
            .where(FeedComment.user_id == viewer_id)
            .where(FeedPost.hashtags.isnot(None))
            .order_by(FeedComment.created_at.desc())
            .limit(50)
        )
        commented_posts_hashtags = commented_hashtags_result.scalars().all()

        # Get hashtags from posts the viewer has saved (recent 50)
        saved_hashtags_result = await self.db.execute(
            select(FeedPost.hashtags)
            .join(FeedSave, FeedSave.post_id == FeedPost.id)
            .where(FeedSave.user_id == viewer_id)
            .where(FeedPost.hashtags.isnot(None))
            .order_by(FeedSave.created_at.desc())
            .limit(50)
        )
        saved_posts_hashtags = saved_hashtags_result.scalars().all()

        # Build weighted hashtag frequency map
        hashtag_weights: dict[str, float] = {}

        # Profile niche_tags get high weight (explicit preference)
        for tag in profile_tags:
            hashtag_weights[tag.lower()] = hashtag_weights.get(tag.lower(), 0) + 3.0

        # Liked posts contribute to affinity (weight: 1.0 per occurrence)
        for hashtags in liked_posts_hashtags:
            if hashtags:
                for tag in hashtags:
                    hashtag_weights[tag.lower()] = hashtag_weights.get(tag.lower(), 0) + 1.0

        # Comments show higher interest (weight: 1.5 per occurrence)
        for hashtags in commented_posts_hashtags:
            if hashtags:
                for tag in hashtags:
                    hashtag_weights[tag.lower()] = hashtag_weights.get(tag.lower(), 0) + 1.5

        # Saves indicate strong interest (weight: 2.0 per occurrence)
        for hashtags in saved_posts_hashtags:
            if hashtags:
                for tag in hashtags:
                    hashtag_weights[tag.lower()] = hashtag_weights.get(tag.lower(), 0) + 2.0

        if not hashtag_weights:
            return 0.0

        # Calculate affinity score based on overlap
        total_affinity = 0.0
        max_weight = max(hashtag_weights.values()) if hashtag_weights else 1.0

        for tag in post_hashtags:
            tag_lower = tag.lower()
            if tag_lower in hashtag_weights:
                # Normalize weight relative to max seen
                normalized_weight = hashtag_weights[tag_lower] / max_weight
                total_affinity += normalized_weight

        # Normalize by number of post hashtags and cap at 0.3
        if len(post_hashtags) > 0:
            affinity_score = total_affinity / len(post_hashtags)
        else:
            affinity_score = 0.0

        return min(affinity_score * 0.3, 0.3)

    async def get_personalized_feed(
        self,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
        feed_type: str = "for_you",
    ) -> List[FeedPost]:
        """
        Generate personalized feed for user.

        Args:
            user_id: User ID for personalization (None for anonymous)
            page: Page number (1-indexed)
            page_size: Number of posts per page
            feed_type: 'for_you', 'following', 'trending', 'discover'

        Returns:
            List of posts sorted by relevance
        """
        offset = (page - 1) * page_size

        if feed_type == "following" and user_id:
            # For "following" feed: show public posts + followers-only posts from followed users
            following_ids = select(Follow.following_id).where(
                Follow.follower_id == user_id
            )
            # Get posts that are either:
            # 1. Public posts from followed users, OR
            # 2. Followers-only posts from followed users (user follows them so they can see)
            query = select(FeedPost).where(
                and_(
                    FeedPost.user_id.in_(following_ids),
                    or_(
                        FeedPost.visibility == "public",
                        FeedPost.visibility == "followers",
                    ),
                )
            )
            # Order by recency for following feed
            query = query.order_by(FeedPost.created_at.desc())
        elif feed_type == "trending":
            # Base query for public posts only
            query = select(FeedPost).where(FeedPost.visibility == "public")
            # Sort by trending score
            query = query.order_by(FeedPost.trending_score.desc())
        else:  # for_you or discover
            # Base query for public posts only
            query = select(FeedPost).where(FeedPost.visibility == "public")
            # Mix of engagement and recency
            query = query.order_by(
                (FeedPost.engagement_score * 0.7 + FeedPost.viral_score * 0.3).desc(),
                FeedPost.created_at.desc(),
            )

        # Apply pagination
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        posts = list(result.scalars().all())

        # If personalized, re-rank with full algorithm
        if user_id and feed_type in ("for_you", "discover"):
            scored_posts = []
            for post in posts:
                score = await self.calculate_post_score(post, user_id)
                scored_posts.append((score, post))

            scored_posts.sort(key=lambda x: x[0], reverse=True)
            posts = [post for _, post in scored_posts]

        return posts


async def update_post_scores(db: AsyncSession, post_ids: List[uuid.UUID]) -> None:
    """
    Background task to update engagement scores for posts.

    Should be called periodically or after engagement events.
    """
    algorithm = FeedAlgorithm(db)

    for post_id in post_ids:
        result = await db.execute(select(FeedPost).where(FeedPost.id == post_id))
        post = result.scalar_one_or_none()

        if post:
            # Update engagement score
            post.engagement_score = algorithm._engagement_score(post)

            # Update trending score (engagement * recency)
            recency = algorithm._recency_score(post.created_at)
            post.trending_score = post.engagement_score * recency

    await db.commit()
