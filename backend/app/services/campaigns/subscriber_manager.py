"""
Subscriber Management Service

Manage subscriber lists, segments, and subscription status
for email and SMS marketing campaigns.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class SubscriberStatus(str, Enum):
    """Status of a subscriber."""
    ACTIVE = "active"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"
    PENDING = "pending"  # Double opt-in pending


class SubscriptionSource(str, Enum):
    """Source of subscription."""
    WEBSITE_FORM = "website_form"
    LANDING_PAGE = "landing_page"
    API = "api"
    IMPORT = "import"
    MANUAL = "manual"
    CHECKOUT = "checkout"
    SOCIAL_MEDIA = "social_media"
    GIVEAWAY = "giveaway"


class ChannelType(str, Enum):
    """Communication channel types."""
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


@dataclass
class Subscriber:
    """A subscriber in the system."""
    subscriber_id: str
    user_id: str  # Owner of the subscriber
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    status: SubscriberStatus = SubscriberStatus.ACTIVE
    source: SubscriptionSource = SubscriptionSource.WEBSITE_FORM
    channels: List[ChannelType] = field(default_factory=lambda: [ChannelType.EMAIL])

    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    list_ids: List[str] = field(default_factory=list)

    # Engagement tracking
    email_opens: int = 0
    email_clicks: int = 0
    sms_clicks: int = 0
    last_engaged_at: Optional[datetime] = None
    engagement_score: float = 0.0

    # Subscription management
    subscribed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    unsubscribed_at: Optional[datetime] = None
    unsubscribe_reason: Optional[str] = None
    double_opt_in_confirmed: bool = False
    confirmation_token: Optional[str] = None

    # Location/preferences
    timezone: Optional[str] = None
    language: str = "en"
    country: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SubscriberList:
    """A list of subscribers."""
    list_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_public: bool = False
    double_opt_in: bool = True
    welcome_email_enabled: bool = True
    welcome_email_template_id: Optional[str] = None

    # Stats
    subscriber_count: int = 0
    active_count: int = 0
    unsubscribed_count: int = 0

    # Settings
    default_tags: List[str] = field(default_factory=list)
    allowed_channels: List[ChannelType] = field(default_factory=lambda: [ChannelType.EMAIL])

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Segment:
    """A dynamic segment of subscribers."""
    segment_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    condition_match: str = "all"  # 'all' or 'any'
    subscriber_count: int = 0
    is_dynamic: bool = True  # Auto-updates based on conditions
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriberManager:
    """
    Subscriber list and management service.

    Features:
    - Subscriber CRUD operations
    - List management
    - Dynamic segmentation
    - Double opt-in handling
    - Engagement scoring
    - Import/export
    - Tag management
    """

    def __init__(self):
        self._subscribers: Dict[str, Subscriber] = {}
        self._lists: Dict[str, SubscriberList] = {}
        self._segments: Dict[str, Segment] = {}

    # =========================================================================
    # SUBSCRIBER OPERATIONS
    # =========================================================================

    async def add_subscriber(
        self,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        source: SubscriptionSource = SubscriptionSource.WEBSITE_FORM,
        list_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        channels: Optional[List[ChannelType]] = None,
        require_double_opt_in: bool = True,
    ) -> Subscriber:
        """
        Add a new subscriber.
        """
        if not email and not phone:
            raise ValueError("Either email or phone is required")

        # Check for existing subscriber
        existing = await self.find_subscriber(
            user_id=user_id,
            email=email,
            phone=phone,
        )

        if existing:
            # Update existing subscriber
            return await self.update_subscriber(
                user_id=user_id,
                subscriber_id=existing.subscriber_id,
                list_ids=list(set(existing.list_ids + (list_ids or []))),
                tags=list(set(existing.tags + (tags or []))),
            )

        # Determine initial status
        status = SubscriberStatus.PENDING if require_double_opt_in else SubscriberStatus.ACTIVE

        subscriber = Subscriber(
            subscriber_id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name or ''} {last_name or ''}".strip() or None,
            status=status,
            source=source,
            channels=channels or [ChannelType.EMAIL] if email else [ChannelType.SMS],
            list_ids=list_ids or [],
            tags=tags or [],
            custom_fields=custom_fields or {},
            double_opt_in_confirmed=not require_double_opt_in,
            confirmation_token=str(uuid.uuid4()) if require_double_opt_in else None,
        )

        self._subscribers[subscriber.subscriber_id] = subscriber

        # Update list counts
        for list_id in subscriber.list_ids:
            if list_id in self._lists:
                self._lists[list_id].subscriber_count += 1
                if subscriber.status == SubscriberStatus.ACTIVE:
                    self._lists[list_id].active_count += 1

        return subscriber

    async def get_subscriber(
        self,
        subscriber_id: str,
    ) -> Optional[Subscriber]:
        """Get a subscriber by ID."""
        return self._subscribers.get(subscriber_id)

    async def find_subscriber(
        self,
        user_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Optional[Subscriber]:
        """Find a subscriber by email or phone."""
        for sub in self._subscribers.values():
            if sub.user_id != user_id:
                continue
            if email and sub.email == email:
                return sub
            if phone and sub.phone == phone:
                return sub
        return None

    async def get_subscribers(
        self,
        user_id: str,
        list_id: Optional[str] = None,
        status: Optional[SubscriberStatus] = None,
        tags: Optional[List[str]] = None,
        channel: Optional[ChannelType] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Subscriber]:
        """Get subscribers with filtering."""
        subscribers = [
            s for s in self._subscribers.values()
            if s.user_id == user_id
        ]

        if list_id:
            subscribers = [s for s in subscribers if list_id in s.list_ids]

        if status:
            subscribers = [s for s in subscribers if s.status == status]

        if tags:
            subscribers = [s for s in subscribers if any(t in s.tags for t in tags)]

        if channel:
            subscribers = [s for s in subscribers if channel in s.channels]

        if search:
            search_lower = search.lower()
            subscribers = [
                s for s in subscribers
                if (s.email and search_lower in s.email.lower()) or
                   (s.full_name and search_lower in s.full_name.lower()) or
                   (s.phone and search_lower in s.phone)
            ]

        subscribers.sort(key=lambda s: s.created_at, reverse=True)
        return subscribers[offset:offset + limit]

    async def update_subscriber(
        self,
        user_id: str,
        subscriber_id: str,
        **updates,
    ) -> Optional[Subscriber]:
        """Update a subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber or subscriber.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(subscriber, key):
                setattr(subscriber, key, value)

        # Update full name if first/last changed
        if "first_name" in updates or "last_name" in updates:
            subscriber.full_name = f"{subscriber.first_name or ''} {subscriber.last_name or ''}".strip() or None

        subscriber.updated_at = datetime.now(timezone.utc)
        return subscriber

    async def delete_subscriber(
        self,
        user_id: str,
        subscriber_id: str,
    ) -> bool:
        """Permanently delete a subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber or subscriber.user_id != user_id:
            return False

        # Update list counts
        for list_id in subscriber.list_ids:
            if list_id in self._lists:
                self._lists[list_id].subscriber_count -= 1
                if subscriber.status == SubscriberStatus.ACTIVE:
                    self._lists[list_id].active_count -= 1

        del self._subscribers[subscriber_id]
        return True

    async def unsubscribe(
        self,
        subscriber_id: str,
        reason: Optional[str] = None,
        channel: Optional[ChannelType] = None,
    ) -> Optional[Subscriber]:
        """Unsubscribe a subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber:
            return None

        if channel:
            # Unsubscribe from specific channel
            if channel in subscriber.channels:
                subscriber.channels.remove(channel)
            if not subscriber.channels:
                subscriber.status = SubscriberStatus.UNSUBSCRIBED
        else:
            # Unsubscribe from all
            subscriber.status = SubscriberStatus.UNSUBSCRIBED

        subscriber.unsubscribed_at = datetime.now(timezone.utc)
        subscriber.unsubscribe_reason = reason
        subscriber.updated_at = datetime.now(timezone.utc)

        # Update list counts
        for list_id in subscriber.list_ids:
            if list_id in self._lists:
                self._lists[list_id].active_count -= 1
                self._lists[list_id].unsubscribed_count += 1

        return subscriber

    async def resubscribe(
        self,
        subscriber_id: str,
        channels: Optional[List[ChannelType]] = None,
    ) -> Optional[Subscriber]:
        """Resubscribe a previously unsubscribed subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber:
            return None

        subscriber.status = SubscriberStatus.ACTIVE
        subscriber.channels = channels or [ChannelType.EMAIL]
        subscriber.unsubscribed_at = None
        subscriber.unsubscribe_reason = None
        subscriber.updated_at = datetime.now(timezone.utc)

        # Update list counts
        for list_id in subscriber.list_ids:
            if list_id in self._lists:
                self._lists[list_id].active_count += 1
                self._lists[list_id].unsubscribed_count -= 1

        return subscriber

    async def confirm_double_opt_in(
        self,
        confirmation_token: str,
    ) -> Optional[Subscriber]:
        """Confirm double opt-in subscription."""
        for subscriber in self._subscribers.values():
            if subscriber.confirmation_token == confirmation_token:
                subscriber.status = SubscriberStatus.ACTIVE
                subscriber.double_opt_in_confirmed = True
                subscriber.confirmation_token = None
                subscriber.updated_at = datetime.now(timezone.utc)
                return subscriber
        return None

    # =========================================================================
    # LIST MANAGEMENT
    # =========================================================================

    async def create_list(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        double_opt_in: bool = True,
        welcome_email_enabled: bool = True,
        default_tags: Optional[List[str]] = None,
        allowed_channels: Optional[List[ChannelType]] = None,
    ) -> SubscriberList:
        """Create a new subscriber list."""
        sub_list = SubscriberList(
            list_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            double_opt_in=double_opt_in,
            welcome_email_enabled=welcome_email_enabled,
            default_tags=default_tags or [],
            allowed_channels=allowed_channels or [ChannelType.EMAIL],
        )

        self._lists[sub_list.list_id] = sub_list
        return sub_list

    async def get_lists(
        self,
        user_id: str,
    ) -> List[SubscriberList]:
        """Get all lists for a user."""
        return [
            l for l in self._lists.values()
            if l.user_id == user_id
        ]

    async def get_list(
        self,
        list_id: str,
    ) -> Optional[SubscriberList]:
        """Get a specific list."""
        return self._lists.get(list_id)

    async def update_list(
        self,
        user_id: str,
        list_id: str,
        **updates,
    ) -> Optional[SubscriberList]:
        """Update a list."""
        sub_list = self._lists.get(list_id)
        if not sub_list or sub_list.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(sub_list, key):
                setattr(sub_list, key, value)

        sub_list.updated_at = datetime.now(timezone.utc)
        return sub_list

    async def delete_list(
        self,
        user_id: str,
        list_id: str,
        delete_subscribers: bool = False,
    ) -> bool:
        """Delete a list."""
        sub_list = self._lists.get(list_id)
        if not sub_list or sub_list.user_id != user_id:
            return False

        # Handle subscribers
        for subscriber in self._subscribers.values():
            if list_id in subscriber.list_ids:
                if delete_subscribers and len(subscriber.list_ids) == 1:
                    # Delete subscriber if only in this list
                    del self._subscribers[subscriber.subscriber_id]
                else:
                    # Just remove from list
                    subscriber.list_ids.remove(list_id)

        del self._lists[list_id]
        return True

    async def add_to_list(
        self,
        subscriber_id: str,
        list_id: str,
    ) -> Optional[Subscriber]:
        """Add subscriber to a list."""
        subscriber = self._subscribers.get(subscriber_id)
        sub_list = self._lists.get(list_id)

        if not subscriber or not sub_list:
            return None

        if list_id not in subscriber.list_ids:
            subscriber.list_ids.append(list_id)
            sub_list.subscriber_count += 1
            if subscriber.status == SubscriberStatus.ACTIVE:
                sub_list.active_count += 1

        return subscriber

    async def remove_from_list(
        self,
        subscriber_id: str,
        list_id: str,
    ) -> Optional[Subscriber]:
        """Remove subscriber from a list."""
        subscriber = self._subscribers.get(subscriber_id)
        sub_list = self._lists.get(list_id)

        if not subscriber or not sub_list:
            return None

        if list_id in subscriber.list_ids:
            subscriber.list_ids.remove(list_id)
            sub_list.subscriber_count -= 1
            if subscriber.status == SubscriberStatus.ACTIVE:
                sub_list.active_count -= 1

        return subscriber

    # =========================================================================
    # SEGMENTATION
    # =========================================================================

    async def create_segment(
        self,
        user_id: str,
        name: str,
        conditions: List[Dict[str, Any]],
        description: Optional[str] = None,
        condition_match: str = "all",
    ) -> Segment:
        """
        Create a dynamic segment.

        Conditions format:
        [
            {"field": "status", "operator": "equals", "value": "active"},
            {"field": "engagement_score", "operator": "greater_than", "value": 50},
            {"field": "tags", "operator": "contains", "value": "vip"},
        ]
        """
        segment = Segment(
            segment_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            conditions=conditions,
            condition_match=condition_match,
        )

        # Calculate initial count
        segment.subscriber_count = len(await self.get_segment_subscribers(
            user_id, segment.segment_id
        ))

        self._segments[segment.segment_id] = segment
        return segment

    async def get_segments(
        self,
        user_id: str,
    ) -> List[Segment]:
        """Get all segments for a user."""
        return [
            s for s in self._segments.values()
            if s.user_id == user_id
        ]

    async def get_segment_subscribers(
        self,
        user_id: str,
        segment_id: str,
    ) -> List[Subscriber]:
        """Get subscribers matching a segment."""
        segment = self._segments.get(segment_id)
        if not segment or segment.user_id != user_id:
            return []

        subscribers = [
            s for s in self._subscribers.values()
            if s.user_id == user_id
        ]

        return [
            s for s in subscribers
            if self._matches_segment(s, segment)
        ]

    def _matches_segment(
        self,
        subscriber: Subscriber,
        segment: Segment,
    ) -> bool:
        """Check if subscriber matches segment conditions."""
        results = []

        for condition in segment.conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            if not field or not operator:
                continue

            # Get field value from subscriber
            if field in ["email", "phone", "first_name", "last_name", "status", "source"]:
                field_value = getattr(subscriber, field, None)
            elif field == "engagement_score":
                field_value = subscriber.engagement_score
            elif field == "tags":
                field_value = subscriber.tags
            elif field == "list_ids":
                field_value = subscriber.list_ids
            elif field in subscriber.custom_fields:
                field_value = subscriber.custom_fields[field]
            else:
                field_value = None

            # Evaluate condition
            match = False
            if operator == "equals":
                match = field_value == value
            elif operator == "not_equals":
                match = field_value != value
            elif operator == "contains":
                if isinstance(field_value, list):
                    match = value in field_value
                elif isinstance(field_value, str):
                    match = value in field_value
            elif operator == "not_contains":
                if isinstance(field_value, list):
                    match = value not in field_value
                elif isinstance(field_value, str):
                    match = value not in field_value
            elif operator == "greater_than":
                match = field_value is not None and field_value > value
            elif operator == "less_than":
                match = field_value is not None and field_value < value
            elif operator == "is_empty":
                match = not field_value
            elif operator == "is_not_empty":
                match = bool(field_value)

            results.append(match)

        if not results:
            return False

        if segment.condition_match == "all":
            return all(results)
        else:  # "any"
            return any(results)

    async def update_segment(
        self,
        user_id: str,
        segment_id: str,
        **updates,
    ) -> Optional[Segment]:
        """Update a segment."""
        segment = self._segments.get(segment_id)
        if not segment or segment.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(segment, key):
                setattr(segment, key, value)

        # Recalculate count
        segment.subscriber_count = len(await self.get_segment_subscribers(
            user_id, segment_id
        ))

        segment.updated_at = datetime.now(timezone.utc)
        return segment

    async def delete_segment(
        self,
        user_id: str,
        segment_id: str,
    ) -> bool:
        """Delete a segment."""
        segment = self._segments.get(segment_id)
        if not segment or segment.user_id != user_id:
            return False

        del self._segments[segment_id]
        return True

    # =========================================================================
    # TAG MANAGEMENT
    # =========================================================================

    async def add_tags(
        self,
        user_id: str,
        subscriber_id: str,
        tags: List[str],
    ) -> Optional[Subscriber]:
        """Add tags to a subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber or subscriber.user_id != user_id:
            return None

        subscriber.tags = list(set(subscriber.tags + tags))
        subscriber.updated_at = datetime.now(timezone.utc)
        return subscriber

    async def remove_tags(
        self,
        user_id: str,
        subscriber_id: str,
        tags: List[str],
    ) -> Optional[Subscriber]:
        """Remove tags from a subscriber."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber or subscriber.user_id != user_id:
            return None

        subscriber.tags = [t for t in subscriber.tags if t not in tags]
        subscriber.updated_at = datetime.now(timezone.utc)
        return subscriber

    async def get_all_tags(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all tags used by a user with counts."""
        tag_counts: Dict[str, int] = {}

        for subscriber in self._subscribers.values():
            if subscriber.user_id != user_id:
                continue
            for tag in subscriber.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return [
            {"tag": tag, "count": count}
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        ]

    async def bulk_tag(
        self,
        user_id: str,
        subscriber_ids: List[str],
        tags: List[str],
        action: str = "add",  # 'add' or 'remove'
    ) -> int:
        """Add or remove tags from multiple subscribers."""
        count = 0
        for subscriber_id in subscriber_ids:
            if action == "add":
                result = await self.add_tags(user_id, subscriber_id, tags)
            else:
                result = await self.remove_tags(user_id, subscriber_id, tags)
            if result:
                count += 1
        return count

    # =========================================================================
    # ENGAGEMENT TRACKING
    # =========================================================================

    async def track_engagement(
        self,
        subscriber_id: str,
        engagement_type: str,  # 'email_open', 'email_click', 'sms_click'
    ) -> Optional[Subscriber]:
        """Track subscriber engagement."""
        subscriber = self._subscribers.get(subscriber_id)
        if not subscriber:
            return None

        if engagement_type == "email_open":
            subscriber.email_opens += 1
        elif engagement_type == "email_click":
            subscriber.email_clicks += 1
        elif engagement_type == "sms_click":
            subscriber.sms_clicks += 1

        subscriber.last_engaged_at = datetime.now(timezone.utc)
        subscriber.engagement_score = self._calculate_engagement_score(subscriber)
        subscriber.updated_at = datetime.now(timezone.utc)

        return subscriber

    def _calculate_engagement_score(self, subscriber: Subscriber) -> float:
        """Calculate engagement score (0-100)."""
        score = 0.0

        # Open rate contribution (max 30)
        score += min(subscriber.email_opens * 3, 30)

        # Click rate contribution (max 40)
        score += min((subscriber.email_clicks + subscriber.sms_clicks) * 5, 40)

        # Recency contribution (max 30)
        if subscriber.last_engaged_at:
            days_since = (datetime.now(timezone.utc) - subscriber.last_engaged_at).days
            if days_since < 7:
                score += 30
            elif days_since < 30:
                score += 20
            elif days_since < 90:
                score += 10

        return min(score, 100)

    # =========================================================================
    # IMPORT/EXPORT
    # =========================================================================

    async def import_subscribers(
        self,
        user_id: str,
        subscribers_data: List[Dict[str, Any]],
        list_id: Optional[str] = None,
        default_tags: Optional[List[str]] = None,
        update_existing: bool = True,
    ) -> Dict[str, Any]:
        """Import subscribers from data."""
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for i, data in enumerate(subscribers_data):
            try:
                email = data.get("email")
                phone = data.get("phone")

                if not email and not phone:
                    skipped += 1
                    continue

                existing = await self.find_subscriber(user_id, email, phone)

                if existing and not update_existing:
                    skipped += 1
                    continue

                if existing:
                    await self.update_subscriber(
                        user_id=user_id,
                        subscriber_id=existing.subscriber_id,
                        first_name=data.get("first_name", existing.first_name),
                        last_name=data.get("last_name", existing.last_name),
                        custom_fields={**existing.custom_fields, **data.get("custom_fields", {})},
                    )
                    updated += 1
                else:
                    await self.add_subscriber(
                        user_id=user_id,
                        email=email,
                        phone=phone,
                        first_name=data.get("first_name"),
                        last_name=data.get("last_name"),
                        source=SubscriptionSource.IMPORT,
                        list_ids=[list_id] if list_id else [],
                        tags=default_tags or [],
                        custom_fields=data.get("custom_fields", {}),
                        require_double_opt_in=False,
                    )
                    created += 1

            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": errors,
            "total_processed": len(subscribers_data),
        }

    async def export_subscribers(
        self,
        user_id: str,
        list_id: Optional[str] = None,
        status: Optional[SubscriberStatus] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Export subscribers to data."""
        subscribers = await self.get_subscribers(
            user_id=user_id,
            list_id=list_id,
            status=status,
            limit=10000,
        )

        default_fields = ["email", "phone", "first_name", "last_name", "status", "tags", "subscribed_at"]
        export_fields = fields or default_fields

        return [
            {
                field: getattr(subscriber, field, subscriber.custom_fields.get(field))
                for field in export_fields
            }
            for subscriber in subscribers
        ]

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get subscriber statistics."""
        subscribers = [s for s in self._subscribers.values() if s.user_id == user_id]

        status_counts = {status.value: 0 for status in SubscriberStatus}
        source_counts = {source.value: 0 for source in SubscriptionSource}
        channel_counts = {channel.value: 0 for channel in ChannelType}

        total_engagement = 0.0

        for sub in subscribers:
            status_counts[sub.status.value] += 1
            source_counts[sub.source.value] += 1
            for channel in sub.channels:
                channel_counts[channel.value] += 1
            total_engagement += sub.engagement_score

        return {
            "total_subscribers": len(subscribers),
            "active_subscribers": status_counts.get("active", 0),
            "unsubscribed": status_counts.get("unsubscribed", 0),
            "pending_confirmation": status_counts.get("pending", 0),
            "by_status": status_counts,
            "by_source": source_counts,
            "by_channel": channel_counts,
            "avg_engagement_score": round(total_engagement / len(subscribers), 2) if subscribers else 0,
            "total_lists": len([l for l in self._lists.values() if l.user_id == user_id]),
            "total_segments": len([s for s in self._segments.values() if s.user_id == user_id]),
        }

    async def get_growth_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get subscriber growth statistics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        subscribers = [s for s in self._subscribers.values() if s.user_id == user_id]

        new_subscribers = [s for s in subscribers if s.subscribed_at >= cutoff]
        unsubscribed = [s for s in subscribers if s.unsubscribed_at and s.unsubscribed_at >= cutoff]

        # Group by day
        daily_new: Dict[str, int] = {}
        for sub in new_subscribers:
            day = sub.subscribed_at.strftime("%Y-%m-%d")
            daily_new[day] = daily_new.get(day, 0) + 1

        return {
            "period_days": days,
            "new_subscribers": len(new_subscribers),
            "unsubscribed": len(unsubscribed),
            "net_growth": len(new_subscribers) - len(unsubscribed),
            "daily_signups": daily_new,
            "avg_daily_signups": round(len(new_subscribers) / days, 2),
        }
