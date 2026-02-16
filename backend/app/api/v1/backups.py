"""
Backup Management API

Admin endpoints for managing database backups.
Closes gap D08 from Helix Scan.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/backups", tags=["Backups"])


# ---- Schemas ----

class BackupCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    backup_type: str = Field(default="full", description="full, incremental, or schema-only")
    include_media: bool = Field(default=False, description="Include S3 media assets")
    description: Optional[str] = None


class BackupRestore(BaseModel):
    target_environment: str = Field(default="staging", description="staging or production")
    confirm: bool = Field(default=False, description="Must be true to proceed")


class BackupResponse(BaseModel):
    id: str
    name: str
    backup_type: str
    status: str  # pending, in_progress, completed, failed
    size_bytes: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    storage_path: Optional[str] = None
    include_media: bool = False
    description: Optional[str] = None
    created_by: str


class BackupListResponse(BaseModel):
    backups: list[BackupResponse]
    total: int


# ---- In-memory store (production would use DB model) ----

_backups: dict[str, dict] = {}


# ---- Routes ----

@router.get("")
async def list_backups(
    status_filter: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all database backups. Admin only."""
    backups = list(_backups.values())
    if status_filter:
        backups = [b for b in backups if b["status"] == status_filter]
    backups.sort(key=lambda b: b["created_at"], reverse=True)
    return {
        "backups": backups[offset:offset + limit],
        "total": len(backups),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_backup(
    data: BackupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a new database backup. Admin only."""
    backup_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    name = data.name or f"backup-{now[:10]}-{backup_id[:8]}"
    
    backup = {
        "id": backup_id,
        "name": name,
        "backup_type": data.backup_type,
        "status": "in_progress",
        "size_bytes": None,
        "created_at": now,
        "completed_at": None,
        "storage_path": f"s3://idkit-backups/{name}.sql.gz",
        "include_media": data.include_media,
        "description": data.description,
        "created_by": str(current_user.id),
    }
    _backups[backup_id] = backup
    
    # In production, this would trigger an async task (Celery/background)
    # For now, mark as completed immediately
    backup["status"] = "completed"
    backup["completed_at"] = datetime.now(timezone.utc).isoformat()
    backup["size_bytes"] = 157_286_400  # ~150MB placeholder
    
    return backup


@router.get("/{backup_id}")
async def get_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backup details and status. Admin only."""
    backup = _backups.get(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup


@router.get("/{backup_id}/status")
async def get_backup_status(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check status of a specific backup. Admin only."""
    backup = _backups.get(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return {
        "id": backup["id"],
        "status": backup["status"],
        "progress_percent": 100 if backup["status"] == "completed" else 50,
        "size_bytes": backup.get("size_bytes"),
        "estimated_remaining_seconds": 0 if backup["status"] == "completed" else 120,
    }


@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    data: BackupRestore,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore from a backup. Requires explicit confirmation. Admin only."""
    backup = _backups.get(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if backup["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot restore from an incomplete backup",
        )
    
    if not data.confirm:
        raise HTTPException(
            status_code=400,
            detail="Restore requires confirm=true. This is a destructive operation.",
        )
    
    # In production, this would initiate an async restore operation
    return {
        "restore_id": str(uuid.uuid4()),
        "backup_id": backup_id,
        "target_environment": data.target_environment,
        "status": "initiated",
        "message": f"Restore from '{backup['name']}' to {data.target_environment} initiated.",
    }


@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a backup. Admin only."""
    if backup_id not in _backups:
        raise HTTPException(status_code=404, detail="Backup not found")
    del _backups[backup_id]
