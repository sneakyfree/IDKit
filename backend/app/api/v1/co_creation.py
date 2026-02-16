"""
Content Co-Creation API

Real endpoints replacing stubs for FEAT-075.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.services.collaboration import CollaborationService

router = APIRouter(prefix="/co-creation", tags=["Co-Creation"])


# ---- Schemas ----

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    project_type: str = "content"


class InviteMember(BaseModel):
    user_id: uuid.UUID
    role: str = "member"


class SendMessage(BaseModel):
    content: str = Field(min_length=1)
    message_type: str = "text"
    attachments: Optional[list] = None


# ---- Routes ----

@router.get("/projects")
async def list_projects(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List collaboration projects for current user."""
    service = CollaborationService(db)
    projects = await service.list_projects(current_user.id, status=status_filter)
    return {"projects": [p.to_dict() for p in projects], "total": len(projects)}


@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new collaboration project."""
    service = CollaborationService(db)
    project = await service.create(owner_id=current_user.id, **data.model_dump())
    return project.to_dict()


@router.get("/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details."""
    service = CollaborationService(db)
    project = await service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.post("/projects/{project_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    project_id: uuid.UUID,
    data: InviteMember,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invite a member to a project."""
    service = CollaborationService(db)
    member = await service.invite_member(
        project_id=project_id, user_id=data.user_id, role=data.role
    )
    return member.to_dict()


@router.post("/projects/{project_id}/accept")
async def accept_invite(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept a project invitation."""
    service = CollaborationService(db)
    member = await service.accept_invite(project_id, current_user.id)
    if not member:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return member.to_dict()


@router.post("/projects/{project_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    project_id: uuid.UUID,
    data: SendMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a collaboration thread."""
    service = CollaborationService(db)
    message = await service.send_message(
        project_id=project_id,
        sender_id=current_user.id,
        **data.model_dump(),
    )
    return message.to_dict()


@router.get("/projects/{project_id}/messages")
async def get_messages(
    project_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages for a project."""
    service = CollaborationService(db)
    messages = await service.get_messages(project_id, limit=limit, offset=offset)
    return {"messages": [m.to_dict() for m in messages], "total": len(messages)}


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a collaboration project."""
    service = CollaborationService(db)
    if not await service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
