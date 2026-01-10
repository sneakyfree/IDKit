"""
Feed Service

Business logic for the IDKit social feed.
Handles posts, likes, comments, saves, and follows.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feed import (
    FeedPost,
    FeedLike,
    FeedComment,
    FeedSave,
    Follow,
    UserProfile,
    Hashtag,
)
from app.models.user import User
from app.services.feed.algorithm import FeedAlgorithm


class FeedService:
    """Service for feed operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.algorithm = FeedAlgorithm(db)

    # ==================== Feed ====================

    async def get_feed(
        self,
        user_id: uuid.UUID | None = None,
        feed_type: str = "for_you",
        page: int = 1,
        page_size: int = 20,
    ) -> List[FeedPost]:
        """Get personalized feed."""
        return await self.algorithm.get_personalized_feed(
            user_id=user_id,
            page=page,
            page_size=page_size,
            feed_type=feed_type,
        )

    # ==================== Posts ====================

    async def create_post(
        self,
        user_id: uuid.UUID,
        post_type: str,
        content_text: str | None = None,
        media_urls: List[str] | None = None,
        thumbnail_url: str | None = None,
        hashtags: List[str] | None = None,
        mentions: List[str] | None = None,
        visibility: str = "public",
        ai_generated: bool = False,
        source_content_id: uuid.UUID | None = None,
    ) -> FeedPost:
        """Create a new feed post."""
        post = FeedPost(
            user_id=user_id,
            post_type=post_type,
            content_text=content_text,
            media_urls=media_urls or [],
            thumbnail_url=thumbnail_url,
            hashtags=hashtags or [],
            mentions=mentions or [],
            visibility=visibility,
            ai_generated=ai_generated,
            source_content_id=source_content_id,
        )

        self.db.add(post)
        await self.db.flush()

        # Update hashtag counts
        if hashtags:
            await self._update_hashtag_counts(hashtags)

        # Increment user's post count
        await self._increment_post_count(user_id)

        await self.db.commit()
        await self.db.refresh(post)

        return post

    async def get_post(self, post_id: uuid.UUID) -> Optional[FeedPost]:
        """Get a single post by ID."""
        result = await self.db.execute(
            select(FeedPost).where(FeedPost.id == post_id)
        )
        return result.scalar_one_or_none()

    async def delete_post(self, post_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a post (only by owner)."""
        post = await self.get_post(post_id)
        if not post or post.user_id != user_id:
            return False

        await self.db.delete(post)
        await self._decrement_post_count(user_id)
        await self.db.commit()

        return True

    async def get_user_posts(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FeedPost]:
        """Get posts by a specific user."""
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(FeedPost)
            .where(FeedPost.user_id == user_id)
            .order_by(FeedPost.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        return list(result.scalars().all())

    # ==================== Likes ====================

    async def like_post(self, post_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Like a post. Returns True if newly liked, False if already liked."""
        # Check if already liked
        existing = await self.db.execute(
            select(FeedLike).where(
                and_(FeedLike.post_id == post_id, FeedLike.user_id == user_id)
            )
        )
        if existing.scalar_one_or_none():
            return False

        # Create like
        like = FeedLike(post_id=post_id, user_id=user_id)
        self.db.add(like)

        # Increment like count
        await self.db.execute(
            FeedPost.__table__.update()
            .where(FeedPost.id == post_id)
            .values(like_count=FeedPost.like_count + 1)
        )

        await self.db.commit()
        return True

    async def unlike_post(self, post_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Unlike a post. Returns True if unliked, False if wasn't liked."""
        result = await self.db.execute(
            delete(FeedLike)
            .where(and_(FeedLike.post_id == post_id, FeedLike.user_id == user_id))
            .returning(FeedLike.id)
        )

        if result.scalar_one_or_none():
            # Decrement like count
            await self.db.execute(
                FeedPost.__table__.update()
                .where(FeedPost.id == post_id)
                .values(like_count=FeedPost.like_count - 1)
            )
            await self.db.commit()
            return True

        return False

    async def is_post_liked(self, post_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if user has liked a post."""
        result = await self.db.execute(
            select(FeedLike.id).where(
                and_(FeedLike.post_id == post_id, FeedLike.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    # ==================== Comments ====================

    async def add_comment(
        self,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        parent_comment_id: uuid.UUID | None = None,
    ) -> FeedComment:
        """Add a comment to a post."""
        comment = FeedComment(
            post_id=post_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_comment_id,
        )

        self.db.add(comment)

        # Increment comment count
        await self.db.execute(
            FeedPost.__table__.update()
            .where(FeedPost.id == post_id)
            .values(comment_count=FeedPost.comment_count + 1)
        )

        await self.db.commit()
        await self.db.refresh(comment)

        return comment

    async def get_comments(
        self,
        post_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FeedComment]:
        """Get comments for a post."""
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(FeedComment)
            .where(
                and_(
                    FeedComment.post_id == post_id,
                    FeedComment.parent_comment_id.is_(None),  # Top-level only
                )
            )
            .order_by(FeedComment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        return list(result.scalars().all())

    # ==================== Saves ====================

    async def save_post(
        self,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
        collection_name: str = "Saved",
    ) -> bool:
        """Save a post to a collection."""
        # Check if already saved to this collection
        existing = await self.db.execute(
            select(FeedSave).where(
                and_(
                    FeedSave.post_id == post_id,
                    FeedSave.user_id == user_id,
                    FeedSave.collection_name == collection_name,
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        save = FeedSave(
            post_id=post_id,
            user_id=user_id,
            collection_name=collection_name,
        )
        self.db.add(save)

        # Increment save count
        await self.db.execute(
            FeedPost.__table__.update()
            .where(FeedPost.id == post_id)
            .values(save_count=FeedPost.save_count + 1)
        )

        await self.db.commit()
        return True

    async def unsave_post(
        self,
        post_id: uuid.UUID,
        user_id: uuid.UUID,
        collection_name: str = "Saved",
    ) -> bool:
        """Remove a post from saves."""
        result = await self.db.execute(
            delete(FeedSave)
            .where(
                and_(
                    FeedSave.post_id == post_id,
                    FeedSave.user_id == user_id,
                    FeedSave.collection_name == collection_name,
                )
            )
            .returning(FeedSave.id)
        )

        if result.scalar_one_or_none():
            await self.db.execute(
                FeedPost.__table__.update()
                .where(FeedPost.id == post_id)
                .values(save_count=FeedPost.save_count - 1)
            )
            await self.db.commit()
            return True

        return False

    # ==================== Follows ====================

    async def follow_user(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """Follow a user. Returns True if newly followed."""
        if follower_id == following_id:
            return False  # Can't follow yourself

        # Check if already following
        existing = await self.db.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.db.add(follow)

        # Update counts
        await self._increment_following_count(follower_id)
        await self._increment_follower_count(following_id)

        await self.db.commit()
        return True

    async def unfollow_user(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """Unfollow a user."""
        result = await self.db.execute(
            delete(Follow)
            .where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
            .returning(Follow.id)
        )

        if result.scalar_one_or_none():
            await self._decrement_following_count(follower_id)
            await self._decrement_follower_count(following_id)
            await self.db.commit()
            return True

        return False

    async def is_following(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """Check if user is following another user."""
        result = await self.db.execute(
            select(Follow.id).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_followers(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> List[UserProfile]:
        """Get followers of a user."""
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(UserProfile)
            .join(Follow, Follow.follower_id == UserProfile.user_id)
            .where(Follow.following_id == user_id)
            .offset(offset)
            .limit(page_size)
        )

        return list(result.scalars().all())

    async def get_following(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> List[UserProfile]:
        """Get users that a user is following."""
        offset = (page - 1) * page_size

        result = await self.db.execute(
            select(UserProfile)
            .join(Follow, Follow.following_id == UserProfile.user_id)
            .where(Follow.follower_id == user_id)
            .offset(offset)
            .limit(page_size)
        )

        return list(result.scalars().all())

    # ==================== Profiles ====================

    async def get_profile_by_username(
        self,
        username: str,
    ) -> Optional[UserProfile]:
        """Get profile by username."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.username == username)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Optional[UserProfile]:
        """Get profile by user ID."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # ==================== Hashtags ====================

    async def get_trending_hashtags(self, limit: int = 10) -> List[Hashtag]:
        """Get trending hashtags."""
        result = await self.db.execute(
            select(Hashtag)
            .order_by(Hashtag.trending_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_posts_by_hashtag(
        self,
        tag: str,
        page: int = 1,
        page_size: int = 20,
    ) -> List[FeedPost]:
        """Get posts with a specific hashtag."""
        offset = (page - 1) * page_size

        # PostgreSQL JSONB contains check
        result = await self.db.execute(
            select(FeedPost)
            .where(FeedPost.hashtags.contains([tag]))
            .order_by(FeedPost.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        return list(result.scalars().all())

    # ==================== Helper Methods ====================

    async def _update_hashtag_counts(self, hashtags: List[str]) -> None:
        """Update or create hashtags with counts."""
        for tag in hashtags:
            tag_lower = tag.lower().strip("#")

            result = await self.db.execute(
                select(Hashtag).where(Hashtag.tag == tag_lower)
            )
            hashtag = result.scalar_one_or_none()

            if hashtag:
                hashtag.post_count += 1
            else:
                hashtag = Hashtag(tag=tag_lower, post_count=1)
                self.db.add(hashtag)

    async def _increment_post_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(post_count=UserProfile.post_count + 1)
        )

    async def _decrement_post_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(post_count=UserProfile.post_count - 1)
        )

    async def _increment_follower_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(follower_count=UserProfile.follower_count + 1)
        )

    async def _decrement_follower_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(follower_count=UserProfile.follower_count - 1)
        )

    async def _increment_following_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(following_count=UserProfile.following_count + 1)
        )

    async def _decrement_following_count(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            UserProfile.__table__.update()
            .where(UserProfile.user_id == user_id)
            .values(following_count=UserProfile.following_count - 1)
        )
