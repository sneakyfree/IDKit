"""
Social Listening Models

Database models for social listening queries and mentions.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ListeningQuery(Base, UUIDMixin, TimestampMixin):
    """
    Social listening query / monitor.

    Tracks keywords across platforms for brand mentions and sentiment.
    """

    __tablename__ = "listening_queries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    keywords: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )  # ["keyword1", "keyword2"]

    platforms: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )  # ["twitter", "instagram", "youtube"]

    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True,
    )  # active, paused, archived

    mentions_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )

    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="listening_queries")
    mentions: Mapped[List["ListeningMention"]] = relationship(
        "ListeningMention", back_populates="query",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ListeningQuery {self.name} - {self.mentions_count} mentions>"


class ListeningMention(Base, UUIDMixin, TimestampMixin):
    """
    Individual social mention captured by listening.
    """

    __tablename__ = "listening_mentions"

    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listening_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    author_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    author_avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text, nullable=False,
    )

    url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    sentiment: Mapped[str] = mapped_column(
        String(20), default="neutral", nullable=False,
    )  # positive, neutral, negative

    sentiment_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False,
    )  # -1.0 to 1.0

    engagement: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )  # Total interactions (likes + comments + shares)

    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    # Relationships
    query: Mapped["ListeningQuery"] = relationship(
        "ListeningQuery", back_populates="mentions",
    )

    def __repr__(self) -> str:
        return f"<ListeningMention {self.platform} - {self.sentiment}>"
