"""
TASK 5.2.1: Backend Scheduling Engine

Content scheduling with timezone support and conflict detection
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, DateTime, Enum as SAEnum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ScheduleStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledPost(Base):
    """SQLAlchemy model for scheduled posts"""
    __tablename__ = "scheduled_posts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content_id = Column(PGUUID(as_uuid=True), ForeignKey("content_items.id"), nullable=True)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    
    # Platform
    platform = Column(String(32), nullable=False)  # instagram, tiktok, youtube, twitter, linkedin
    platform_account_id = Column(String(128))
    
    # Status
    status = Column(SAEnum(ScheduleStatus), nullable=False, default=ScheduleStatus.PENDING)
    error_message = Column(String(512))
    retry_count = Column(String(1), default="0")  # Max 3 retries
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    published_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="scheduled_posts")


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ScheduleCreate(BaseModel):
    """Request to create a scheduled post"""
    content_id: UUID
    scheduled_at: datetime = Field(..., description="When to publish (user's local time)")
    timezone: str = Field(default="UTC", description="User's timezone (e.g., America/New_York)")
    platform: str = Field(..., description="Target platform")
    platform_account_id: Optional[str] = None

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v: datetime) -> datetime:
        # Must be at least 5 minutes in the future
        if v < datetime.now(v.tzinfo) + timedelta(minutes=5):
            raise ValueError("Scheduled time must be at least 5 minutes in the future")
        return v

    @validator("platform")
    def validate_platform(cls, v: str) -> str:
        valid_platforms = ["instagram", "tiktok", "youtube", "twitter", "linkedin", "facebook"]
        if v.lower() not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v.lower()


class ScheduleUpdate(BaseModel):
    """Request to update a scheduled post"""
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    status: Optional[ScheduleStatus] = None

    @validator("scheduled_at")
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.now(v.tzinfo) + timedelta(minutes=5):
            raise ValueError("Scheduled time must be at least 5 minutes in the future")
        return v


class ScheduleResponse(BaseModel):
    """Scheduled post response"""
    id: UUID
    content_id: UUID
    scheduled_at: datetime
    timezone: str
    platform: str
    platform_account_id: Optional[str]
    status: ScheduleStatus
    error_message: Optional[str]
    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConflictWarning(BaseModel):
    """Warning about scheduling conflicts"""
    message: str
    conflicting_posts: List[UUID]
    severity: str  # "warning" or "error"


class ScheduleCreateResponse(BaseModel):
    """Response after creating a scheduled post"""
    schedule: ScheduleResponse
    conflicts: Optional[List[ConflictWarning]] = None


class CalendarEvent(BaseModel):
    """Calendar event for frontend display"""
    id: UUID
    title: str
    start: datetime
    end: datetime
    platform: str
    status: ScheduleStatus
    color: str
    
    @classmethod
    def from_scheduled_post(cls, post: ScheduledPost, content_title: str) -> "CalendarEvent":
        # Platform colors
        colors = {
            "instagram": "#E1306C",
            "tiktok": "#000000",
            "youtube": "#FF0000",
            "twitter": "#1DA1F2",
            "linkedin": "#0A66C2",
            "facebook": "#1877F2",
        }
        
        return cls(
            id=post.id,
            title=content_title,
            start=post.scheduled_at,
            end=post.scheduled_at + timedelta(minutes=30),  # Placeholder end time
            platform=post.platform,
            status=post.status,
            color=colors.get(post.platform, "#8B5CF6"),
        )


# ============================================================================
# Conflict Detection Service
# ============================================================================

class SchedulingConflictChecker:
    """Service for detecting scheduling conflicts"""
    
    MAX_POSTS_PER_HOUR = 10
    MAX_POSTS_PER_PLATFORM_PER_HOUR = 3
    
    @staticmethod
    async def check_conflicts(
        user_id: UUID,
        scheduled_at: datetime,
        platform: str,
        db_session,
        exclude_id: Optional[UUID] = None,
    ) -> List[ConflictWarning]:
        """
        Check for scheduling conflicts:
        1. Max 10 posts per hour across all platforms
        2. Max 3 posts per platform per hour
        3. No duplicate times on same platform
        """
        from sqlalchemy import select, and_, func
        
        warnings = []
        
        # Time window: 30 minutes before and after
        window_start = scheduled_at - timedelta(minutes=30)
        window_end = scheduled_at + timedelta(minutes=30)
        
        # Query existing scheduled posts in the window
        query = select(ScheduledPost).where(
            and_(
                ScheduledPost.user_id == user_id,
                ScheduledPost.scheduled_at >= window_start,
                ScheduledPost.scheduled_at <= window_end,
                ScheduledPost.status == ScheduleStatus.PENDING,
            )
        )
        
        if exclude_id:
            query = query.where(ScheduledPost.id != exclude_id)
        
        result = await db_session.execute(query)
        existing = result.scalars().all()
        
        # Check total posts per hour
        if len(existing) >= SchedulingConflictChecker.MAX_POSTS_PER_HOUR:
            warnings.append(ConflictWarning(
                message=f"You have {len(existing)} posts scheduled within this hour. Consider spreading them out.",
                conflicting_posts=[p.id for p in existing],
                severity="warning",
            ))
        
        # Check platform-specific conflicts
        platform_posts = [p for p in existing if p.platform == platform]
        if len(platform_posts) >= SchedulingConflictChecker.MAX_POSTS_PER_PLATFORM_PER_HOUR:
            warnings.append(ConflictWarning(
                message=f"You have {len(platform_posts)} posts scheduled for {platform} within this hour.",
                conflicting_posts=[p.id for p in platform_posts],
                severity="warning",
            ))
        
        # Check for exact time conflicts
        exact_conflicts = [p for p in existing if p.scheduled_at == scheduled_at and p.platform == platform]
        if exact_conflicts:
            warnings.append(ConflictWarning(
                message=f"Another post is already scheduled for {platform} at this exact time.",
                conflicting_posts=[p.id for p in exact_conflicts],
                severity="error",
            ))
        
        return warnings
