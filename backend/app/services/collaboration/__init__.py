"""
Collaboration Service

Business logic for content co-creation projects.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collaboration import (
    CollaborationProject,
    CollaborationMember,
    CollaborationMessage,
)


class CollaborationService:
    """Service for collaboration project management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        project_type: str = "content",
    ) -> CollaborationProject:
        """Create a new collaboration project."""
        project = CollaborationProject(
            owner_id=owner_id,
            name=name,
            description=description,
            project_type=project_type,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # Add owner as first member
        member = CollaborationMember(
            project_id=project.id,
            user_id=owner_id,
            role="owner",
            invited_at=datetime.utcnow(),
            accepted_at=datetime.utcnow(),
            status="accepted",
        )
        self.db.add(member)
        await self.db.commit()
        return project

    async def list_projects(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[CollaborationProject]:
        """List projects where user is a member."""
        query = (
            select(CollaborationProject)
            .join(CollaborationMember)
            .where(CollaborationMember.user_id == user_id)
            .options(
                selectinload(CollaborationProject.members),
                selectinload(CollaborationProject.messages),
            )
            .order_by(CollaborationProject.created_at.desc())
        )
        if status:
            query = query.where(CollaborationProject.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get(self, project_id: uuid.UUID) -> Optional[CollaborationProject]:
        """Get a project by ID."""
        query = (
            select(CollaborationProject)
            .where(CollaborationProject.id == project_id)
            .options(
                selectinload(CollaborationProject.members),
                selectinload(CollaborationProject.messages),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def invite_member(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "member",
    ) -> CollaborationMember:
        """Invite a user to a project."""
        member = CollaborationMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            invited_at=datetime.utcnow(),
            status="pending",
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def accept_invite(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[CollaborationMember]:
        """Accept a project invitation."""
        query = (
            select(CollaborationMember)
            .where(
                CollaborationMember.project_id == project_id,
                CollaborationMember.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        if not member:
            return None
        member.status = "accepted"
        member.accepted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def send_message(
        self,
        project_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        message_type: str = "text",
        attachments: Optional[list] = None,
    ) -> CollaborationMessage:
        """Send a message in a collaboration thread."""
        message = CollaborationMessage(
            project_id=project_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            attachments=attachments or [],
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self,
        project_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CollaborationMessage]:
        """Get messages for a project."""
        query = (
            select(CollaborationMessage)
            .where(CollaborationMessage.project_id == project_id)
            .order_by(CollaborationMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        """Delete a collaboration project."""
        project = await self.get(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.commit()
        return True
