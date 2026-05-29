"""
Push Notification API Endpoints

REST API for push notification device management and sending.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class DeviceTokenRequest(BaseModel):
    """Register device token."""
    token: str
    platform: str  # 'ios', 'android', 'web'
    device_id: Optional[str] = None
    device_name: Optional[str] = None


class DeviceTokenResponse(BaseModel):
    """Device token response."""
    token_id: str
    user_id: str
    platform: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class SendNotificationRequest(BaseModel):
    """Send notification request."""
    title: str
    body: str
    channel: str = "general"
    priority: str = "normal"
    data: dict = Field(default_factory=dict)
    image_url: Optional[str] = None
    action_url: Optional[str] = None


class BulkNotificationRequest(BaseModel):
    """Send bulk notification."""
    user_ids: list[str]
    title: str
    body: str
    channel: str = "general"
    priority: str = "normal"
    data: dict = Field(default_factory=dict)


class TopicNotificationRequest(BaseModel):
    """Send notification to topic subscribers."""
    topic: str
    title: str
    body: str
    data: dict = Field(default_factory=dict)


class ChannelResponse(BaseModel):
    """Notification channel info."""
    id: str
    name: str
    description: str


# --------------------------------------------------------------------------
# Device Management Endpoints
# --------------------------------------------------------------------------

@router.post("/devices", response_model=DeviceTokenResponse)
async def register_device(
    request: DeviceTokenRequest,
):
    """
    Register device for push notifications.

    Call this when the app starts or token refreshes.
    """
    from app.services.notifications import PushNotificationService, DeviceToken

    service = PushNotificationService()

    token = DeviceToken(
        token=request.token,
        platform=request.platform,
        user_id="current_user",
        device_id=request.device_id,
        device_name=request.device_name,
    )

    result = await service.register_device(token)

    return DeviceTokenResponse(
        token_id=result.token_id,
        user_id=result.user_id,
        platform=result.platform,
        device_id=result.device_id,
        device_name=result.device_name,
        is_active=result.is_active,
        created_at=result.created_at,
    )


@router.get("/devices", response_model=list[DeviceTokenResponse])
async def list_devices():
    """List user's registered devices."""
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()
    devices = await service.get_user_devices("current_user")

    return [
        DeviceTokenResponse(
            token_id=d.token_id,
            user_id=d.user_id,
            platform=d.platform,
            device_id=d.device_id,
            device_name=d.device_name,
            is_active=d.is_active,
            created_at=d.created_at,
        )
        for d in devices
    ]


@router.delete("/devices/{device_id}")
async def unregister_device(
    device_id: str,
):
    """Unregister a device from push notifications."""
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()
    await service.unregister_device("current_user", device_id)

    return {"success": True, "device_id": device_id}


# --------------------------------------------------------------------------
# Send Notification Endpoints
# --------------------------------------------------------------------------

@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    user_id: str = Query(..., description="Target user ID"),
):
    """
    Send push notification to a user.

    Requires admin permissions in production.
    """
    from app.services.notifications import (
        PushNotificationService,
        PushNotification,
        NotificationChannel,
        NotificationPriority,
    )

    service = PushNotificationService()

    try:
        channel = NotificationChannel(request.channel)
    except ValueError:
        channel = NotificationChannel.GENERAL

    try:
        priority = NotificationPriority(request.priority)
    except ValueError:
        priority = NotificationPriority.DEFAULT

    notification = PushNotification(
        user_id=user_id,
        title=request.title,
        body=request.body,
        channel=channel,
        priority=priority,
        data=request.data,
        image_url=request.image_url,
        action_url=request.action_url,
    )

    result = await service.send(notification)

    return {
        "success": result.get("success", False),
        "notification_id": notification.notification_id,
        "delivered_to": result.get("delivered_to", 0),
    }


@router.post("/send/bulk")
async def send_bulk_notification(
    request: BulkNotificationRequest,
):
    """
    Send notification to multiple users.

    Requires admin permissions in production.
    """
    from app.services.notifications import (
        PushNotificationService,
        PushNotification,
        NotificationChannel,
        NotificationPriority,
    )

    service = PushNotificationService()

    try:
        channel = NotificationChannel(request.channel)
    except ValueError:
        channel = NotificationChannel.GENERAL

    try:
        priority = NotificationPriority(request.priority)
    except ValueError:
        priority = NotificationPriority.DEFAULT

    notifications = [
        PushNotification(
            user_id=user_id,
            title=request.title,
            body=request.body,
            channel=channel,
            priority=priority,
            data=request.data,
        )
        for user_id in request.user_ids
    ]

    result = await service.send_bulk(notifications)

    return {
        "success": True,
        "total_users": len(request.user_ids),
        "delivered": result.get("delivered", 0),
        "failed": result.get("failed", 0),
    }


@router.post("/send/topic")
async def send_topic_notification(
    request: TopicNotificationRequest,
):
    """
    Send notification to all subscribers of a topic.

    Requires admin permissions in production.
    """
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()

    result = await service.send_to_topic(
        topic=request.topic,
        title=request.title,
        body=request.body,
        data=request.data,
    )

    return {
        "success": True,
        "topic": request.topic,
        "message_id": result.get("message_id"),
    }


# --------------------------------------------------------------------------
# Topic Management Endpoints
# --------------------------------------------------------------------------

@router.post("/topics/{topic}/subscribe")
async def subscribe_to_topic(
    topic: str,
):
    """Subscribe to a notification topic."""
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()
    await service.subscribe_to_topic("current_user", topic)

    return {"success": True, "topic": topic, "action": "subscribed"}


@router.delete("/topics/{topic}/subscribe")
async def unsubscribe_from_topic(
    topic: str,
):
    """Unsubscribe from a notification topic."""
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()
    await service.unsubscribe_from_topic("current_user", topic)

    return {"success": True, "topic": topic, "action": "unsubscribed"}


@router.get("/topics")
async def list_subscribed_topics():
    """List topics user is subscribed to."""
    from app.services.notifications import PushNotificationService

    service = PushNotificationService()
    topics = await service.get_subscribed_topics("current_user")

    return {"topics": topics}


# --------------------------------------------------------------------------
# Channel Info Endpoints
# --------------------------------------------------------------------------

@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels():
    """Get list of available notification channels."""
    from app.services.notifications import NotificationChannel

    return [
        ChannelResponse(
            id=c.value,
            name=c.value.replace("_", " ").title(),
            description=_get_channel_description(c),
        )
        for c in NotificationChannel
    ]


def _get_channel_description(channel) -> str:
    """Get description for notification channel."""
    from app.services.notifications import NotificationChannel

    descriptions = {
        NotificationChannel.ENGAGEMENT: "Likes, comments, and shares",
        NotificationChannel.CONTENT: "Content generation and publishing",
        NotificationChannel.SOCIAL: "DMs and mentions",
        NotificationChannel.MARKETING: "Brand deals and opportunities",
        NotificationChannel.ANALYTICS: "Analytics insights and reports",
        NotificationChannel.SYSTEM: "System updates and alerts",
    }
    return descriptions.get(channel, "")


@router.get("/test")
async def send_test_notification():
    """
    Send a test notification to current user.

    Useful for testing push notification setup.
    """
    from app.services.notifications import (
        PushNotificationService,
        PushNotification,
        NotificationChannel,
        NotificationPriority,
    )

    service = PushNotificationService()

    notification = PushNotification(
        user_id="current_user",
        title="Test Notification",
        body="This is a test notification from IDKit!",
        channel=NotificationChannel.SYSTEM,
        priority=NotificationPriority.DEFAULT,
        action_data={"test": True},
    )

    result = await service.send(notification)

    return {
        "success": result.status == "sent",
        "status": result.status,
        "message": "Test notification sent",
        "notification_id": notification.notification_id,
    }
