"""
Inbox API Endpoints

Unified inbox for comments and DMs across all social platforms.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.inbox import (
    UnifiedInboxService,
    MessageType,
    MessageStatus,
    MessageSentiment,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class InboxMessageResponse(BaseModel):
    """Unified inbox message."""
    id: str
    type: str
    platform: str
    account_id: str
    account_name: str

    # Sender info
    sender_id: str
    sender_name: str
    sender_username: Optional[str]
    sender_avatar_url: Optional[str]
    sender_follower_count: Optional[int]

    # Content
    content: str
    media_urls: List[str] = []

    # Context
    post_id: Optional[str]
    post_preview: Optional[str]
    conversation_id: Optional[str]
    parent_message_id: Optional[str]

    # Status
    status: str
    sentiment: Optional[str]
    intent: Optional[str]
    priority: int

    # Timestamps
    created_at: datetime
    read_at: Optional[datetime]
    replied_at: Optional[datetime]

    # AI
    suggested_replies: List[str] = []


class ConversationResponse(BaseModel):
    """DM conversation."""
    id: str
    platform: str
    account_id: str
    participant_id: str
    participant_name: str
    participant_username: Optional[str]
    participant_avatar_url: Optional[str]
    message_count: int
    unread_count: int
    last_message: Optional[InboxMessageResponse]
    last_activity: datetime
    is_muted: bool


class InboxStatsResponse(BaseModel):
    """Inbox statistics."""
    total_messages: int
    unread_count: int
    comments_count: int
    dms_count: int
    mentions_count: int
    sentiment_breakdown: dict
    platform_breakdown: dict
    response_rate: float
    avg_response_time_minutes: Optional[float]


class MarkReadRequest(BaseModel):
    """Request to mark messages as read."""
    message_ids: List[str]
    message_type: str = "comment"


class ReplyCommentRequest(BaseModel):
    """Request to reply to a comment."""
    reply_text: str = Field(..., min_length=1, max_length=2000)


class SendDmRequest(BaseModel):
    """Request to send a DM."""
    message_text: str = Field(..., min_length=1, max_length=10000)
    media_urls: Optional[List[str]] = None


class MarkSpamRequest(BaseModel):
    """Request to mark messages as spam."""
    message_ids: List[str]


class AnalyzeSentimentResponse(BaseModel):
    """Sentiment analysis result."""
    sentiment: str
    intent: str
    priority: int
    is_spam: bool


class SuggestRepliesResponse(BaseModel):
    """Reply suggestions."""
    suggestions: List[str]


class SyncResultResponse(BaseModel):
    """Result of inbox sync."""
    synced_platforms: List[str]
    new_comments: int
    new_dms: int
    errors: List[dict]


class BulkAnalyzeResponse(BaseModel):
    """Result of bulk sentiment analysis."""
    analyzed: int


class ActionResultResponse(BaseModel):
    """Generic action result."""
    success: bool
    count: Optional[int] = None
    message_id: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/messages", response_model=List[InboxMessageResponse])
async def get_inbox_messages(
    message_type: Optional[str] = Query(None, description="Filter by type: comment, dm, mention, reply"),
    status: Optional[str] = Query(None, description="Filter by status: unread, read, replied, archived, spam"),
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: positive, neutral, negative, question, urgent"),
    search: Optional[str] = Query(None, description="Search in message content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort by: created_at, priority, sentiment"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get unified inbox messages with filtering and pagination.

    Returns comments, DMs, and mentions from all connected platforms.
    """
    # Parse enums
    msg_type = None
    if message_type:
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid message_type. Valid: {[t.value for t in MessageType]}"
            )

    msg_status = None
    if status:
        try:
            msg_status = MessageStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid: {[s.value for s in MessageStatus]}"
            )

    msg_sentiment = None
    if sentiment:
        try:
            msg_sentiment = MessageSentiment(sentiment)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sentiment. Valid: {[s.value for s in MessageSentiment]}"
            )

    service = UnifiedInboxService(db)

    messages = await service.get_inbox(
        user_id=current_user.id,
        message_type=msg_type,
        status=msg_status,
        platforms=platforms,
        sentiment=msg_sentiment,
        search_query=search,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )

    return [
        InboxMessageResponse(
            id=str(m.id),
            type=m.type.value,
            platform=m.platform,
            account_id=str(m.account_id),
            account_name=m.account_name,
            sender_id=m.sender_id,
            sender_name=m.sender_name,
            sender_username=m.sender_username,
            sender_avatar_url=m.sender_avatar_url,
            sender_follower_count=m.sender_follower_count,
            content=m.content,
            media_urls=m.media_urls,
            post_id=m.post_id,
            post_preview=m.post_preview,
            conversation_id=m.conversation_id,
            parent_message_id=m.parent_message_id,
            status=m.status.value,
            sentiment=m.sentiment.value if m.sentiment else None,
            intent=m.intent.value if m.intent else None,
            priority=m.priority,
            created_at=m.created_at,
            read_at=m.read_at,
            replied_at=m.replied_at,
            suggested_replies=m.suggested_replies,
        )
        for m in messages
    ]


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    unread_only: bool = Query(False, description="Show only unread conversations"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get DM conversations grouped by participant.
    """
    service = UnifiedInboxService(db)

    conversations = await service.get_conversations(
        user_id=current_user.id,
        platforms=platforms,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )

    def format_last_message(msg):
        if not msg:
            return None
        return InboxMessageResponse(
            id=str(msg.id),
            type=msg.type.value,
            platform=msg.platform,
            account_id=str(msg.account_id),
            account_name=msg.account_name,
            sender_id=msg.sender_id,
            sender_name=msg.sender_name,
            sender_username=msg.sender_username,
            sender_avatar_url=msg.sender_avatar_url,
            sender_follower_count=msg.sender_follower_count,
            content=msg.content,
            media_urls=msg.media_urls,
            post_id=msg.post_id,
            post_preview=msg.post_preview,
            conversation_id=msg.conversation_id,
            parent_message_id=msg.parent_message_id,
            status=msg.status.value,
            sentiment=msg.sentiment.value if msg.sentiment else None,
            intent=msg.intent.value if msg.intent else None,
            priority=msg.priority,
            created_at=msg.created_at,
            read_at=msg.read_at,
            replied_at=msg.replied_at,
            suggested_replies=msg.suggested_replies,
        )

    return [
        ConversationResponse(
            id=c.id,
            platform=c.platform,
            account_id=str(c.account_id),
            participant_id=c.participant_id,
            participant_name=c.participant_name,
            participant_username=c.participant_username,
            participant_avatar_url=c.participant_avatar_url,
            message_count=c.message_count,
            unread_count=c.unread_count,
            last_message=format_last_message(c.last_message),
            last_activity=c.last_activity,
            is_muted=c.is_muted,
        )
        for c in conversations
    ]


@router.get("/stats", response_model=InboxStatsResponse)
async def get_inbox_stats(
    platforms: Optional[List[str]] = Query(None, description="Filter by platforms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get inbox statistics and counts.
    """
    service = UnifiedInboxService(db)

    stats = await service.get_inbox_stats(
        user_id=current_user.id,
        platforms=platforms,
    )

    return InboxStatsResponse(
        total_messages=stats.total_messages,
        unread_count=stats.unread_count,
        comments_count=stats.comments_count,
        dms_count=stats.dms_count,
        mentions_count=stats.mentions_count,
        sentiment_breakdown=stats.sentiment_breakdown,
        platform_breakdown=stats.platform_breakdown,
        response_rate=stats.response_rate,
        avg_response_time_minutes=stats.avg_response_time_minutes,
    )


@router.post("/messages/mark-read", response_model=ActionResultResponse)
async def mark_messages_as_read(
    request: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark messages as read.
    """
    try:
        msg_type = MessageType(request.message_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid message_type. Valid: {[t.value for t in MessageType]}"
        )

    service = UnifiedInboxService(db)

    try:
        message_uuids = [uuid.UUID(mid) for mid in request.message_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    count = await service.mark_as_read(
        user_id=current_user.id,
        message_ids=message_uuids,
        message_type=msg_type,
    )

    return ActionResultResponse(success=True, count=count)


@router.post("/comments/{comment_id}/reply", response_model=ActionResultResponse)
async def reply_to_comment(
    comment_id: str,
    request: ReplyCommentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reply to a comment on the platform.
    """
    try:
        comment_uuid = uuid.UUID(comment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")

    service = UnifiedInboxService(db)

    result = await service.reply_to_comment(
        user_id=current_user.id,
        comment_id=comment_uuid,
        reply_text=request.reply_text,
    )

    return ActionResultResponse(
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/conversations/{conversation_id}/send", response_model=ActionResultResponse)
async def send_dm(
    conversation_id: str,
    request: SendDmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a direct message in a conversation.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    service = UnifiedInboxService(db)

    result = await service.send_dm(
        user_id=current_user.id,
        conversation_id=conv_uuid,
        message_text=request.message_text,
        media_urls=request.media_urls,
    )

    return ActionResultResponse(
        success=result.get("success", False),
        message_id=result.get("message_id"),
        error=result.get("error"),
    )


@router.post("/messages/mark-spam", response_model=ActionResultResponse)
async def mark_as_spam(
    request: MarkSpamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark messages as spam.
    """
    try:
        message_uuids = [uuid.UUID(mid) for mid in request.message_ids]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    service = UnifiedInboxService(db)

    count = await service.mark_as_spam(
        user_id=current_user.id,
        message_ids=message_uuids,
    )

    return ActionResultResponse(success=True, count=count)


@router.post("/messages/{message_id}/analyze", response_model=AnalyzeSentimentResponse)
async def analyze_message_sentiment(
    message_id: str,
    message_type: str = Query("comment", description="Message type: comment or dm"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze sentiment and intent of a message using AI.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    try:
        msg_type = MessageType(message_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid message_type. Valid: {[t.value for t in MessageType]}"
        )

    service = UnifiedInboxService(db)

    result = await service.analyze_sentiment(
        message_id=msg_uuid,
        message_type=msg_type,
    )

    return AnalyzeSentimentResponse(
        sentiment=result.get("sentiment", "neutral"),
        intent=result.get("intent", "general"),
        priority=result.get("priority", 0),
        is_spam=result.get("is_spam", False),
    )


@router.get("/messages/{message_id}/suggestions", response_model=SuggestRepliesResponse)
async def get_reply_suggestions(
    message_id: str,
    message_type: str = Query("comment", description="Message type: comment or dm"),
    count: int = Query(3, ge=1, le=5, description="Number of suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-powered reply suggestions for a message.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    try:
        msg_type = MessageType(message_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid message_type. Valid: {[t.value for t in MessageType]}"
        )

    service = UnifiedInboxService(db)

    suggestions = await service.suggest_replies(
        message_id=msg_uuid,
        message_type=msg_type,
        count=count,
    )

    return SuggestRepliesResponse(suggestions=suggestions)


@router.post("/analyze-bulk", response_model=BulkAnalyzeResponse)
async def bulk_analyze_messages(
    limit: int = Query(100, ge=1, le=500, description="Max messages to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze sentiment for unanalyzed messages in bulk.
    """
    service = UnifiedInboxService(db)

    result = await service.bulk_analyze(
        user_id=current_user.id,
        limit=limit,
    )

    return BulkAnalyzeResponse(analyzed=result["analyzed"])


@router.post("/sync", response_model=SyncResultResponse)
async def sync_inbox(
    platform: Optional[str] = Query(None, description="Specific platform to sync"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sync comments and DMs from connected platforms.
    """
    service = UnifiedInboxService(db)

    result = await service.sync_inbox(
        user_id=current_user.id,
        platform=platform,
    )

    return SyncResultResponse(
        synced_platforms=result["synced_platforms"],
        new_comments=result["new_comments"],
        new_dms=result["new_dms"],
        errors=result["errors"],
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Quick endpoint to get total unread count for badge display.
    """
    service = UnifiedInboxService(db)

    stats = await service.get_inbox_stats(
        user_id=current_user.id,
    )

    return {"unread_count": stats.unread_count}
