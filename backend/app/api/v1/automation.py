"""
Automation API Endpoints

Auto-reply rules and engagement automation.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.automation import (
    AutoReplyService,
    TriggerType,
    ReplyMode,
)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class RuleTriggerConfig(BaseModel):
    """Configuration for rule triggers."""
    keywords: Optional[List[str]] = None
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    intent: Optional[str] = None  # "question", "complaint", "praise", etc.
    regex_pattern: Optional[str] = None


class CreateRuleRequest(BaseModel):
    """Request to create an auto-reply rule."""
    name: str = Field(..., min_length=1, max_length=100)
    trigger_type: str = Field(..., description="keyword, sentiment, intent, all, regex")
    trigger_config: RuleTriggerConfig
    reply_template: str = Field(..., min_length=1)
    reply_mode: str = Field(default="template", description="template, ai_enhanced, full_ai")
    platforms: Optional[List[str]] = None
    message_types: Optional[List[str]] = None  # "comment", "dm"
    is_active: bool = True
    priority: int = Field(default=0, ge=0, le=100)
    delay_seconds: int = Field(default=0, ge=0, le=3600)
    rate_limit_per_hour: int = Field(default=60, ge=1, le=1000)


class UpdateRuleRequest(BaseModel):
    """Request to update an auto-reply rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    trigger_type: Optional[str] = None
    trigger_config: Optional[RuleTriggerConfig] = None
    reply_template: Optional[str] = None
    reply_mode: Optional[str] = None
    platforms: Optional[List[str]] = None
    message_types: Optional[List[str]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    delay_seconds: Optional[int] = Field(None, ge=0, le=3600)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=1000)


class RuleResponse(BaseModel):
    """Response for an auto-reply rule."""
    id: str
    name: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    reply_template: str
    reply_mode: str
    platforms: List[str]
    message_types: List[str]
    is_active: bool
    priority: int
    delay_seconds: int
    rate_limit_per_hour: int
    created_at: datetime
    updated_at: datetime
    stats: Dict[str, Any]


class ReplyResultResponse(BaseModel):
    """Response for a processed reply."""
    message_id: str
    rule_id: str
    rule_name: str
    original_message: str
    reply_text: str
    reply_mode: str
    platform: str
    was_rate_limited: bool
    delay_applied: int


class ProcessMessageRequest(BaseModel):
    """Request to process a message for auto-reply."""
    message_id: str
    message_content: str
    message_type: str = "comment"  # "comment" or "dm"
    platform: str
    sender_id: str
    sender_name: Optional[str] = None
    post_context: Optional[str] = None


class AutomationStatsResponse(BaseModel):
    """Statistics for automation."""
    total_rules: int
    active_rules: int
    total_replies_sent: int
    replies_today: int
    replies_this_week: int
    top_rules: List[Dict[str, Any]]
    platform_breakdown: Dict[str, int]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/rules", response_model=RuleResponse)
async def create_rule(
    request: CreateRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new auto-reply rule.

    Rules define when and how to automatically respond to comments and DMs.
    """
    try:
        trigger_type = TriggerType(request.trigger_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_type. Valid options: {[t.value for t in TriggerType]}"
        )

    try:
        reply_mode = ReplyMode(request.reply_mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reply_mode. Valid options: {[m.value for m in ReplyMode]}"
        )

    service = AutoReplyService(db)

    # Build trigger config
    trigger_config = {}
    if request.trigger_config.keywords:
        trigger_config["keywords"] = request.trigger_config.keywords
    if request.trigger_config.sentiment:
        trigger_config["sentiment"] = request.trigger_config.sentiment
    if request.trigger_config.intent:
        trigger_config["intent"] = request.trigger_config.intent
    if request.trigger_config.regex_pattern:
        trigger_config["regex_pattern"] = request.trigger_config.regex_pattern

    rule = await service.create_rule(
        user_id=current_user.id,
        name=request.name,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        reply_template=request.reply_template,
        reply_mode=reply_mode,
        platforms=request.platforms,
        message_types=request.message_types,
        priority=request.priority,
        delay_seconds=request.delay_seconds,
        rate_limit_per_hour=request.rate_limit_per_hour,
    )

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        trigger_type=rule.trigger_type.value,
        trigger_config=rule.trigger_config,
        reply_template=rule.reply_template,
        reply_mode=rule.reply_mode.value,
        platforms=rule.platforms,
        message_types=rule.message_types,
        is_active=rule.is_active,
        priority=rule.priority,
        delay_seconds=rule.delay_seconds,
        rate_limit_per_hour=rule.rate_limit_per_hour,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        stats=rule.stats,
    )


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all auto-reply rules for the current user.
    """
    service = AutoReplyService(db)

    rules = await service.get_rules(
        user_id=current_user.id,
        is_active=is_active,
        platform=platform,
    )

    return [
        RuleResponse(
            id=rule.id,
            name=rule.name,
            trigger_type=rule.trigger_type.value,
            trigger_config=rule.trigger_config,
            reply_template=rule.reply_template,
            reply_mode=rule.reply_mode.value,
            platforms=rule.platforms,
            message_types=rule.message_types,
            is_active=rule.is_active,
            priority=rule.priority,
            delay_seconds=rule.delay_seconds,
            rate_limit_per_hour=rule.rate_limit_per_hour,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            stats=rule.stats,
        )
        for rule in rules
    ]


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific auto-reply rule.
    """
    service = AutoReplyService(db)

    rule = await service.get_rule(
        user_id=current_user.id,
        rule_id=rule_id,
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        trigger_type=rule.trigger_type.value,
        trigger_config=rule.trigger_config,
        reply_template=rule.reply_template,
        reply_mode=rule.reply_mode.value,
        platforms=rule.platforms,
        message_types=rule.message_types,
        is_active=rule.is_active,
        priority=rule.priority,
        delay_seconds=rule.delay_seconds,
        rate_limit_per_hour=rule.rate_limit_per_hour,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        stats=rule.stats,
    )


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    request: UpdateRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an auto-reply rule.
    """
    service = AutoReplyService(db)

    # Build update dict
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.trigger_type is not None:
        try:
            updates["trigger_type"] = TriggerType(request.trigger_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trigger_type")
    if request.trigger_config is not None:
        trigger_config = {}
        if request.trigger_config.keywords:
            trigger_config["keywords"] = request.trigger_config.keywords
        if request.trigger_config.sentiment:
            trigger_config["sentiment"] = request.trigger_config.sentiment
        if request.trigger_config.intent:
            trigger_config["intent"] = request.trigger_config.intent
        if request.trigger_config.regex_pattern:
            trigger_config["regex_pattern"] = request.trigger_config.regex_pattern
        updates["trigger_config"] = trigger_config
    if request.reply_template is not None:
        updates["reply_template"] = request.reply_template
    if request.reply_mode is not None:
        try:
            updates["reply_mode"] = ReplyMode(request.reply_mode)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid reply_mode")
    if request.platforms is not None:
        updates["platforms"] = request.platforms
    if request.message_types is not None:
        updates["message_types"] = request.message_types
    if request.is_active is not None:
        updates["is_active"] = request.is_active
    if request.priority is not None:
        updates["priority"] = request.priority
    if request.delay_seconds is not None:
        updates["delay_seconds"] = request.delay_seconds
    if request.rate_limit_per_hour is not None:
        updates["rate_limit_per_hour"] = request.rate_limit_per_hour

    rule = await service.update_rule(
        user_id=current_user.id,
        rule_id=rule_id,
        **updates,
    )

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        trigger_type=rule.trigger_type.value,
        trigger_config=rule.trigger_config,
        reply_template=rule.reply_template,
        reply_mode=rule.reply_mode.value,
        platforms=rule.platforms,
        message_types=rule.message_types,
        is_active=rule.is_active,
        priority=rule.priority,
        delay_seconds=rule.delay_seconds,
        rate_limit_per_hour=rule.rate_limit_per_hour,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        stats=rule.stats,
    )


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an auto-reply rule.
    """
    service = AutoReplyService(db)

    success = await service.delete_rule(
        user_id=current_user.id,
        rule_id=rule_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"message": "Rule deleted successfully"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle a rule's active status.
    """
    service = AutoReplyService(db)

    rule = await service.get_rule(user_id=current_user.id, rule_id=rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    updated_rule = await service.update_rule(
        user_id=current_user.id,
        rule_id=rule_id,
        is_active=not rule.is_active,
    )

    return {
        "id": updated_rule.id,
        "is_active": updated_rule.is_active,
        "message": f"Rule {'activated' if updated_rule.is_active else 'deactivated'}",
    }


@router.post("/process", response_model=Optional[ReplyResultResponse])
async def process_message(
    request: ProcessMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process a message through auto-reply rules.

    Returns a reply if any rule matches, or null if no rules apply.
    """
    service = AutoReplyService(db)

    result = await service.process_message(
        user_id=current_user.id,
        message_id=request.message_id,
        message_content=request.message_content,
        message_type=request.message_type,
        platform=request.platform,
        sender_id=request.sender_id,
        sender_name=request.sender_name,
        post_context=request.post_context,
    )

    if not result:
        return None

    return ReplyResultResponse(
        message_id=result.message_id,
        rule_id=result.rule_id,
        rule_name=result.rule_name,
        original_message=result.original_message,
        reply_text=result.reply_text,
        reply_mode=result.reply_mode.value,
        platform=result.platform,
        was_rate_limited=result.was_rate_limited,
        delay_applied=result.delay_applied,
    )


@router.get("/stats", response_model=AutomationStatsResponse)
async def get_automation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get automation statistics.
    """
    service = AutoReplyService(db)

    stats = await service.get_stats(user_id=current_user.id)

    return AutomationStatsResponse(**stats)


@router.get("/history")
async def get_reply_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    platform: Optional[str] = None,
    rule_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get history of auto-replies sent.
    """
    service = AutoReplyService(db)

    history = await service.get_reply_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        platform=platform,
        rule_id=rule_id,
    )

    return history
