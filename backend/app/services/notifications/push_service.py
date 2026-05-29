"""
Push Notification Service

Handles push notifications across iOS, Android, and web.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels."""
    ENGAGEMENT = "engagement"  # Likes, comments, follows
    CONTENT = "content"  # Content updates, publishing
    SOCIAL = "social"  # DMs, mentions
    MARKETING = "marketing"  # Brand deals, opportunities
    SYSTEM = "system"  # Account, security
    ANALYTICS = "analytics"  # Stats updates, milestones


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"
    URGENT = "urgent"


class DeviceType(str, Enum):
    """Device types for push."""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


@dataclass
class DeviceToken:
    """Device token for push notifications."""
    token_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    device_type: DeviceType = DeviceType.IOS
    token: str = ""
    device_name: Optional[str] = None
    app_version: Optional[str] = None
    os_version: Optional[str] = None

    # Preferences
    enabled: bool = True
    channels: list[NotificationChannel] = field(default_factory=lambda: list(NotificationChannel))

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    failed_count: int = 0


@dataclass
class PushNotification:
    """Push notification payload."""
    notification_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""

    # Content
    title: str = ""
    body: str = ""
    subtitle: Optional[str] = None
    image_url: Optional[str] = None

    # Targeting
    channel: NotificationChannel = NotificationChannel.SYSTEM
    priority: NotificationPriority = NotificationPriority.DEFAULT

    # Action
    action_type: Optional[str] = None  # 'open_post', 'open_profile', 'open_url'
    action_data: dict = field(default_factory=dict)
    deep_link: Optional[str] = None

    # Platform-specific
    ios_category: Optional[str] = None
    android_channel_id: Optional[str] = None
    badge_count: Optional[int] = None

    # Delivery
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Status
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, delivered, failed, expired

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class NotificationTemplate:
    """Template for generating notifications."""
    template_id: str
    channel: NotificationChannel
    title_template: str
    body_template: str
    action_type: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.DEFAULT


class PushNotificationService:
    """
    Manages push notifications across platforms.

    Features:
    - Multi-platform support (iOS, Android, Web)
    - Channel-based categorization
    - Template-based notifications
    - Scheduled delivery
    - Delivery tracking
    - User preferences
    """

    # Notification templates
    TEMPLATES = {
        "new_follower": NotificationTemplate(
            template_id="new_follower",
            channel=NotificationChannel.ENGAGEMENT,
            title_template="New Follower",
            body_template="{username} started following you",
            action_type="open_profile",
        ),
        "new_like": NotificationTemplate(
            template_id="new_like",
            channel=NotificationChannel.ENGAGEMENT,
            title_template="New Like",
            body_template="{username} liked your post",
            action_type="open_post",
        ),
        "new_comment": NotificationTemplate(
            template_id="new_comment",
            channel=NotificationChannel.ENGAGEMENT,
            title_template="New Comment",
            body_template='{username}: "{comment_preview}"',
            action_type="open_post",
            priority=NotificationPriority.HIGH,
        ),
        "new_message": NotificationTemplate(
            template_id="new_message",
            channel=NotificationChannel.SOCIAL,
            title_template="{username}",
            body_template="{message_preview}",
            action_type="open_chat",
            priority=NotificationPriority.HIGH,
        ),
        "content_published": NotificationTemplate(
            template_id="content_published",
            channel=NotificationChannel.CONTENT,
            title_template="Content Published",
            body_template='Your {content_type} "{title}" is now live on {platform}',
            action_type="open_post",
        ),
        "content_failed": NotificationTemplate(
            template_id="content_failed",
            channel=NotificationChannel.CONTENT,
            title_template="Publishing Failed",
            body_template='Failed to publish "{title}" to {platform}',
            action_type="open_content",
            priority=NotificationPriority.HIGH,
        ),
        "brand_opportunity": NotificationTemplate(
            template_id="brand_opportunity",
            channel=NotificationChannel.MARKETING,
            title_template="New Brand Opportunity",
            body_template="{brand_name} wants to work with you! ${amount}",
            action_type="open_opportunity",
            priority=NotificationPriority.HIGH,
        ),
        "milestone_reached": NotificationTemplate(
            template_id="milestone_reached",
            channel=NotificationChannel.ANALYTICS,
            title_template="🎉 Milestone Reached!",
            body_template="You've reached {milestone} {metric}!",
            action_type="open_analytics",
        ),
        "trending_content": NotificationTemplate(
            template_id="trending_content",
            channel=NotificationChannel.ANALYTICS,
            title_template="🔥 Your Content is Trending!",
            body_template='"{title}" is getting {views} views!',
            action_type="open_post",
            priority=NotificationPriority.HIGH,
        ),
        "security_alert": NotificationTemplate(
            template_id="security_alert",
            channel=NotificationChannel.SYSTEM,
            title_template="Security Alert",
            body_template="New login from {device} in {location}",
            action_type="open_security",
            priority=NotificationPriority.URGENT,
        ),
    }

    def __init__(
        self,
        fcm_credentials: Optional[dict] = None,
        apns_credentials: Optional[dict] = None,
        web_push_credentials: Optional[dict] = None,
    ):
        """
        Initialize push notification service.

        Args:
            fcm_credentials: Firebase Cloud Messaging credentials
            apns_credentials: Apple Push Notification service credentials
            web_push_credentials: Web Push credentials
        """
        self.fcm_credentials = fcm_credentials
        self.apns_credentials = apns_credentials
        self.web_push_credentials = web_push_credentials

        # In-memory storage for demo (use database in production)
        self._device_tokens: dict[str, list[DeviceToken]] = {}
        self._notifications: dict[str, PushNotification] = {}
        self._user_preferences: dict[str, dict] = {}

    async def register_device(
        self,
        user_id: str,
        device_type: DeviceType,
        token: str,
        device_name: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> DeviceToken:
        """
        Register a device for push notifications.

        Args:
            user_id: User ID
            device_type: Type of device
            token: Push token
            device_name: Optional device name
            app_version: Optional app version

        Returns:
            Registered device token
        """
        device = DeviceToken(
            user_id=user_id,
            device_type=device_type,
            token=token,
            device_name=device_name,
            app_version=app_version,
        )

        # Store device token
        if user_id not in self._device_tokens:
            self._device_tokens[user_id] = []

        # Check if token already exists
        existing = next(
            (d for d in self._device_tokens[user_id] if d.token == token),
            None
        )
        if existing:
            existing.last_used = datetime.utcnow()
            existing.device_name = device_name or existing.device_name
            existing.app_version = app_version or existing.app_version
            return existing

        self._device_tokens[user_id].append(device)
        logger.info(f"Registered device for user {user_id}: {device_type.value}")

        return device

    async def unregister_device(
        self,
        user_id: str,
        token: str,
    ) -> bool:
        """Unregister a device token."""
        if user_id not in self._device_tokens:
            return False

        original_count = len(self._device_tokens[user_id])
        self._device_tokens[user_id] = [
            d for d in self._device_tokens[user_id]
            if d.token != token
        ]

        return len(self._device_tokens[user_id]) < original_count

    async def send(
        self,
        notification: PushNotification,
    ) -> PushNotification:
        """
        Send a push notification.

        Args:
            notification: Notification to send

        Returns:
            Updated notification with send status
        """
        user_id = notification.user_id

        # Check user preferences
        if not await self._should_send(notification):
            notification.status = "blocked"
            return notification

        # Get user's device tokens
        devices = self._device_tokens.get(user_id, [])
        if not devices:
            notification.status = "no_devices"
            return notification

        # Filter enabled devices with matching channel
        eligible_devices = [
            d for d in devices
            if d.enabled and notification.channel in d.channels
        ]

        if not eligible_devices:
            notification.status = "channel_disabled"
            return notification

        # Send to each device
        success_count = 0
        for device in eligible_devices:
            try:
                if device.device_type == DeviceType.IOS:
                    await self._send_apns(device, notification)
                elif device.device_type == DeviceType.ANDROID:
                    await self._send_fcm(device, notification)
                elif device.device_type == DeviceType.WEB:
                    await self._send_web_push(device, notification)

                success_count += 1
                device.last_used = datetime.utcnow()
                device.failed_count = 0

            except Exception as e:
                logger.error(f"Failed to send to device {device.token_id}: {e}")
                device.failed_count += 1

                # Disable device after too many failures
                if device.failed_count >= 5:
                    device.enabled = False
                    logger.warning(f"Disabled device {device.token_id} due to repeated failures")

        notification.sent_at = datetime.utcnow()
        notification.status = "sent" if success_count > 0 else "failed"

        # Store notification
        self._notifications[notification.notification_id] = notification

        return notification

    async def send_from_template(
        self,
        user_id: str,
        template_id: str,
        variables: dict,
        action_data: Optional[dict] = None,
    ) -> PushNotification:
        """
        Send notification using a template.

        Args:
            user_id: Target user
            template_id: Template ID
            variables: Variables for template interpolation
            action_data: Optional action data

        Returns:
            Sent notification
        """
        template = self.TEMPLATES.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Interpolate variables
        title = template.title_template.format(**variables)
        body = template.body_template.format(**variables)

        notification = PushNotification(
            user_id=user_id,
            title=title,
            body=body,
            channel=template.channel,
            priority=template.priority,
            action_type=template.action_type,
            action_data=action_data or {},
        )

        return await self.send(notification)

    async def send_bulk(
        self,
        user_ids: list[str],
        notification: PushNotification,
    ) -> dict:
        """
        Send notification to multiple users.

        Args:
            user_ids: List of user IDs
            notification: Base notification

        Returns:
            Summary of send results
        """
        results = {
            "total": len(user_ids),
            "sent": 0,
            "failed": 0,
            "blocked": 0,
        }

        tasks = []
        for user_id in user_ids:
            notif_copy = PushNotification(
                user_id=user_id,
                title=notification.title,
                body=notification.body,
                subtitle=notification.subtitle,
                image_url=notification.image_url,
                channel=notification.channel,
                priority=notification.priority,
                action_type=notification.action_type,
                action_data=notification.action_data.copy(),
            )
            tasks.append(self.send(notif_copy))

        sent_notifications = await asyncio.gather(*tasks, return_exceptions=True)

        for result in sent_notifications:
            if isinstance(result, Exception):
                results["failed"] += 1
            elif result.status == "sent":
                results["sent"] += 1
            elif result.status in ["blocked", "channel_disabled"]:
                results["blocked"] += 1
            else:
                results["failed"] += 1

        return results

    async def schedule(
        self,
        notification: PushNotification,
        send_at: datetime,
    ) -> PushNotification:
        """
        Schedule a notification for future delivery.

        Args:
            notification: Notification to schedule
            send_at: When to send

        Returns:
            Scheduled notification
        """
        notification.scheduled_for = send_at
        notification.status = "scheduled"

        self._notifications[notification.notification_id] = notification

        logger.info(f"Scheduled notification {notification.notification_id} for {send_at}")

        return notification

    async def cancel_scheduled(
        self,
        notification_id: str,
    ) -> bool:
        """Cancel a scheduled notification."""
        notification = self._notifications.get(notification_id)
        if not notification:
            return False

        if notification.status != "scheduled":
            return False

        notification.status = "cancelled"
        return True

    async def update_preferences(
        self,
        user_id: str,
        preferences: dict,
    ) -> dict:
        """
        Update user notification preferences.

        Args:
            user_id: User ID
            preferences: Preference updates
                - enabled_channels: list of channels
                - quiet_hours: {"start": "22:00", "end": "08:00"}
                - muted_until: datetime

        Returns:
            Updated preferences
        """
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = {
                "enabled_channels": list(NotificationChannel),
                "quiet_hours": None,
                "muted_until": None,
            }

        current = self._user_preferences[user_id]

        if "enabled_channels" in preferences:
            current["enabled_channels"] = [
                NotificationChannel(c) for c in preferences["enabled_channels"]
            ]

        if "quiet_hours" in preferences:
            current["quiet_hours"] = preferences["quiet_hours"]

        if "muted_until" in preferences:
            current["muted_until"] = preferences["muted_until"]

        return current

    async def get_preferences(self, user_id: str) -> dict:
        """Get user notification preferences."""
        return self._user_preferences.get(user_id, {
            "enabled_channels": [c.value for c in NotificationChannel],
            "quiet_hours": None,
            "muted_until": None,
        })

    async def get_history(
        self,
        user_id: str,
        limit: int = 50,
        channel: Optional[NotificationChannel] = None,
    ) -> list[PushNotification]:
        """Get notification history for user."""
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id
        ]

        if channel:
            notifications = [n for n in notifications if n.channel == channel]

        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)

        return notifications[:limit]

    async def mark_read(
        self,
        notification_id: str,
    ) -> bool:
        """Mark a notification as read."""
        notification = self._notifications.get(notification_id)
        if not notification:
            return False

        notification.read_at = datetime.utcnow()
        return True

    async def get_unread_count(
        self,
        user_id: str,
        channel: Optional[NotificationChannel] = None,
    ) -> int:
        """Get count of unread notifications."""
        notifications = [
            n for n in self._notifications.values()
            if n.user_id == user_id and n.read_at is None
        ]

        if channel:
            notifications = [n for n in notifications if n.channel == channel]

        return len(notifications)


    async def get_user_devices(self, user_id: str) -> list:
        """List registered devices for a user. Returns [] for users with no devices."""
        # In production this hits a DB. Preview returns empty.
        return []

    async def get_subscribed_topics(self, user_id: str) -> list[str]:
        """List topic subscriptions for a user. Returns [] for users with none."""
        return []

    async def _should_send(self, notification: PushNotification) -> bool:
        """Check if notification should be sent based on preferences."""
        prefs = self._user_preferences.get(notification.user_id, {})

        # Check if channel is enabled
        enabled_channels = prefs.get("enabled_channels", list(NotificationChannel))
        if notification.channel not in enabled_channels:
            return False

        # Check if muted
        muted_until = prefs.get("muted_until")
        if muted_until and datetime.utcnow() < muted_until:
            return False

        # Check quiet hours
        quiet_hours = prefs.get("quiet_hours")
        if quiet_hours:
            now = datetime.utcnow()
            current_time = now.strftime("%H:%M")
            start = quiet_hours.get("start", "")
            end = quiet_hours.get("end", "")

            if start and end:
                if start <= current_time or current_time <= end:
                    # Allow urgent notifications through quiet hours
                    if notification.priority != NotificationPriority.URGENT:
                        return False

        return True

    async def _send_apns(
        self,
        device: DeviceToken,
        notification: PushNotification,
    ) -> None:
        """Send via Apple Push Notification service."""
        # In production, use apns2 or similar library
        logger.info(f"[APNS] Sending to device {device.token[:20]}...")

        payload = {
            "aps": {
                "alert": {
                    "title": notification.title,
                    "body": notification.body,
                    "subtitle": notification.subtitle,
                },
                "sound": "default",
                "badge": notification.badge_count,
                "category": notification.ios_category,
            },
            "action_type": notification.action_type,
            "action_data": notification.action_data,
        }

        # Simulate sending
        await asyncio.sleep(0.1)

    async def _send_fcm(
        self,
        device: DeviceToken,
        notification: PushNotification,
    ) -> None:
        """Send via Firebase Cloud Messaging."""
        # In production, use firebase-admin SDK
        logger.info(f"[FCM] Sending to device {device.token[:20]}...")

        payload = {
            "notification": {
                "title": notification.title,
                "body": notification.body,
                "image": notification.image_url,
            },
            "android": {
                "priority": notification.priority.value,
                "notification": {
                    "channel_id": notification.android_channel_id or notification.channel.value,
                },
            },
            "data": {
                "action_type": notification.action_type,
                "action_data": json.dumps(notification.action_data),
            },
        }

        # Simulate sending
        await asyncio.sleep(0.1)

    async def _send_web_push(
        self,
        device: DeviceToken,
        notification: PushNotification,
    ) -> None:
        """Send via Web Push."""
        # In production, use pywebpush
        logger.info(f"[Web Push] Sending to device {device.token[:20]}...")

        payload = {
            "title": notification.title,
            "body": notification.body,
            "icon": notification.image_url,
            "data": {
                "action_type": notification.action_type,
                "action_data": notification.action_data,
            },
        }

        # Simulate sending
        await asyncio.sleep(0.1)

    async def process_scheduled(self) -> int:
        """Process scheduled notifications. Call periodically."""
        now = datetime.utcnow()
        sent_count = 0

        for notification in list(self._notifications.values()):
            if notification.status == "scheduled" and notification.scheduled_for:
                if notification.scheduled_for <= now:
                    notification.status = "pending"
                    await self.send(notification)
                    sent_count += 1

        return sent_count
