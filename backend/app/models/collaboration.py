"""
Collaboration Models

Database models for content co-creation and real-time collaboration.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class CollaborationProject(Base, UUIDMixin, TimestampMixin):
    """
    Content co-creation project between multiple creators.
    """

    __tablename__ = "collaboration_projects"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False, index=True,
    )  # active, completed, archived

    project_type: Mapped[str] = mapped_column(
        String(50), default="content", nullable=False,
    )  # content, campaign, podcast

    settings: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", backref="owned_collaborations")
    members: Mapped[List["CollaborationMember"]] = relationship(
        "CollaborationMember", back_populates="project",
        cascade="all, delete-orphan",
    )
    messages: Mapped[List["CollaborationMessage"]] = relationship(
        "CollaborationMessage", back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CollaborationProject {self.name} - {self.status}>"


class CollaborationMember(Base, UUIDMixin, TimestampMixin):
    """
    Member of a collaboration project.
    """

    __tablename__ = "collaboration_members"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collaboration_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50), default="member", nullable=False,
    )  # owner, editor, viewer

    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False,
    )  # pending, accepted, declined

    # Relationships
    project: Mapped["CollaborationProject"] = relationship(
        "CollaborationProject", back_populates="members",
    )
    user: Mapped["User"] = relationship("User", backref="collaboration_memberships")

    def __repr__(self) -> str:
        return f"<CollaborationMember {self.user_id} - {self.role}>"


class CollaborationMessage(Base, UUIDMixin, TimestampMixin):
    """
    Message in a collaboration thread.
    """

    __tablename__ = "collaboration_messages"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collaboration_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text, nullable=False,
    )

    message_type: Mapped[str] = mapped_column(
        String(50), default="text", nullable=False,
    )  # text, file, system

    attachments: Mapped[dict] = mapped_column(
        JSONB, default=list, nullable=False,
    )

    # Relationships
    project: Mapped["CollaborationProject"] = relationship(
        "CollaborationProject", back_populates="messages",
    )
    sender: Mapped["User"] = relationship("User", backref="collaboration_messages")

    def __repr__(self) -> str:
        return f"<CollaborationMessage {self.sender_id}>"
