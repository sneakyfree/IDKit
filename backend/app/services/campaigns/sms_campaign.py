"""
SMS Campaign Builder Service

Create, manage, and send SMS marketing campaigns
with personalization, scheduling, and analytics.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class SMSCampaignStatus(str, Enum):
    """Status of an SMS campaign."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SMSType(str, Enum):
    """Types of SMS campaigns."""
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    ALERT = "alert"
    REMINDER = "reminder"
    OTP = "otp"


@dataclass
class SMSTemplate:
    """SMS template configuration."""
    template_id: str
    user_id: str
    name: str
    message: str
    sms_type: SMSType = SMSType.PROMOTIONAL
    variables: List[str] = field(default_factory=list)
    character_count: int = 0
    segment_count: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SMSRecipient:
    """An SMS recipient."""
    phone_number: str
    name: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class SMSSendResult:
    """Result of sending an SMS."""
    recipient_phone: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    cost: float = 0.0
    segments: int = 1


@dataclass
class SMSCampaign:
    """An SMS campaign."""
    campaign_id: str
    user_id: str
    name: str
    message: str
    sender_id: str = ""  # Sender name/number
    sms_type: SMSType = SMSType.PROMOTIONAL
    template_id: Optional[str] = None
    list_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: SMSCampaignStatus = SMSCampaignStatus.DRAFT
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    # Message info
    character_count: int = 0
    segment_count: int = 1

    # Stats
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    clicked_count: int = 0  # For links with tracking
    opted_out_count: int = 0
    total_cost: float = 0.0

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SMSCampaignBuilder:
    """
    SMS campaign creation and management service.

    Features:
    - Campaign creation with templates
    - Message personalization
    - Character/segment counting
    - Link shortening and tracking
    - Scheduling and automation
    - Delivery analytics
    - Compliance helpers (opt-out handling)
    """

    # SMS segment sizes
    GSM_SEGMENT_SIZE = 160  # Standard characters
    UNICODE_SEGMENT_SIZE = 70  # Unicode characters
    CONCAT_GSM_SIZE = 153  # Concatenated GSM
    CONCAT_UNICODE_SIZE = 67  # Concatenated Unicode

    # GSM-7 character set (basic)
    GSM_CHARS = set(
        "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ ÆæßÉ!\"#¤%&'()*+,-./0123456789:;<=>?"
        "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
    )

    def __init__(self):
        self._llm_client = None
        self._campaigns: Dict[str, SMSCampaign] = {}
        self._templates: Dict[str, SMSTemplate] = {}

    async def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from openai import AsyncOpenAI
            from app.config import settings
            self._llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._llm_client

    # =========================================================================
    # TEMPLATE MANAGEMENT
    # =========================================================================

    async def create_template(
        self,
        user_id: str,
        name: str,
        message: str,
        sms_type: SMSType = SMSType.PROMOTIONAL,
    ) -> SMSTemplate:
        """Create a new SMS template."""
        variables = self._extract_variables(message)
        char_count, segment_count = self._calculate_segments(message)

        template = SMSTemplate(
            template_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            message=message,
            sms_type=sms_type,
            variables=variables,
            character_count=char_count,
            segment_count=segment_count,
        )

        self._templates[template.template_id] = template
        return template

    async def get_templates(
        self,
        user_id: str,
        sms_type: Optional[SMSType] = None,
    ) -> List[SMSTemplate]:
        """Get user's SMS templates."""
        templates = [
            t for t in self._templates.values()
            if t.user_id == user_id
        ]

        if sms_type:
            templates = [t for t in templates if t.sms_type == sms_type]

        return templates

    async def update_template(
        self,
        user_id: str,
        template_id: str,
        **updates,
    ) -> Optional[SMSTemplate]:
        """Update a template."""
        template = self._templates.get(template_id)
        if not template or template.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        # Recalculate if message changed
        if "message" in updates:
            template.variables = self._extract_variables(template.message)
            template.character_count, template.segment_count = self._calculate_segments(template.message)

        template.updated_at = datetime.now(timezone.utc)
        return template

    async def delete_template(
        self,
        user_id: str,
        template_id: str,
    ) -> bool:
        """Delete a template."""
        template = self._templates.get(template_id)
        if not template or template.user_id != user_id:
            return False

        del self._templates[template_id]
        return True

    def _extract_variables(self, message: str) -> List[str]:
        """Extract merge tag variables from message."""
        import re
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, message)
        return list(set(matches))

    def _is_gsm(self, text: str) -> bool:
        """Check if text uses only GSM-7 characters."""
        return all(c in self.GSM_CHARS for c in text)

    def _calculate_segments(self, message: str) -> tuple:
        """Calculate character count and SMS segments needed."""
        char_count = len(message)

        if self._is_gsm(message):
            if char_count <= self.GSM_SEGMENT_SIZE:
                return char_count, 1
            else:
                segments = (char_count + self.CONCAT_GSM_SIZE - 1) // self.CONCAT_GSM_SIZE
                return char_count, segments
        else:
            if char_count <= self.UNICODE_SEGMENT_SIZE:
                return char_count, 1
            else:
                segments = (char_count + self.CONCAT_UNICODE_SIZE - 1) // self.CONCAT_UNICODE_SIZE
                return char_count, segments

    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================

    async def create_campaign(
        self,
        user_id: str,
        name: str,
        message: str,
        sender_id: str,
        sms_type: SMSType = SMSType.PROMOTIONAL,
        template_id: Optional[str] = None,
        list_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> SMSCampaign:
        """Create a new SMS campaign."""
        char_count, segment_count = self._calculate_segments(message)

        campaign = SMSCampaign(
            campaign_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            message=message,
            sender_id=sender_id,
            sms_type=sms_type,
            template_id=template_id,
            list_ids=list_ids or [],
            tags=tags or [],
            character_count=char_count,
            segment_count=segment_count,
        )

        self._campaigns[campaign.campaign_id] = campaign
        return campaign

    async def create_from_template(
        self,
        user_id: str,
        template_id: str,
        name: str,
        sender_id: str,
        list_ids: Optional[List[str]] = None,
        message_overrides: Optional[Dict[str, str]] = None,
    ) -> SMSCampaign:
        """Create a campaign from a template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError("Template not found")

        message = template.message
        if message_overrides:
            for key, value in message_overrides.items():
                message = message.replace(f"{{{{{key}}}}}", value)

        return await self.create_campaign(
            user_id=user_id,
            name=name,
            message=message,
            sender_id=sender_id,
            sms_type=template.sms_type,
            template_id=template_id,
            list_ids=list_ids,
        )

    async def get_campaigns(
        self,
        user_id: str,
        status: Optional[SMSCampaignStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SMSCampaign]:
        """Get user's SMS campaigns."""
        campaigns = [
            c for c in self._campaigns.values()
            if c.user_id == user_id
        ]

        if status:
            campaigns = [c for c in campaigns if c.status == status]

        campaigns.sort(key=lambda c: c.created_at, reverse=True)
        return campaigns[offset:offset + limit]

    async def get_campaign(
        self,
        campaign_id: str,
    ) -> Optional[SMSCampaign]:
        """Get a specific campaign."""
        return self._campaigns.get(campaign_id)

    async def update_campaign(
        self,
        user_id: str,
        campaign_id: str,
        **updates,
    ) -> Optional[SMSCampaign]:
        """Update a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status not in [SMSCampaignStatus.DRAFT, SMSCampaignStatus.SCHEDULED]:
            raise ValueError("Cannot update campaign that is sending or sent")

        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        # Recalculate segments if message changed
        if "message" in updates:
            campaign.character_count, campaign.segment_count = self._calculate_segments(campaign.message)

        campaign.updated_at = datetime.now(timezone.utc)
        return campaign

    async def delete_campaign(
        self,
        user_id: str,
        campaign_id: str,
    ) -> bool:
        """Delete a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return False

        if campaign.status == SMSCampaignStatus.SENDING:
            raise ValueError("Cannot delete campaign that is sending")

        del self._campaigns[campaign_id]
        return True

    # =========================================================================
    # SCHEDULING & SENDING
    # =========================================================================

    async def schedule_campaign(
        self,
        user_id: str,
        campaign_id: str,
        scheduled_at: datetime,
    ) -> Optional[SMSCampaign]:
        """Schedule a campaign for future sending."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status != SMSCampaignStatus.DRAFT:
            raise ValueError("Can only schedule draft campaigns")

        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Scheduled time must be in the future")

        campaign.status = SMSCampaignStatus.SCHEDULED
        campaign.scheduled_at = scheduled_at
        campaign.updated_at = datetime.now(timezone.utc)

        return campaign

    async def cancel_scheduled(
        self,
        user_id: str,
        campaign_id: str,
    ) -> Optional[SMSCampaign]:
        """Cancel a scheduled campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status != SMSCampaignStatus.SCHEDULED:
            raise ValueError("Campaign is not scheduled")

        campaign.status = SMSCampaignStatus.DRAFT
        campaign.scheduled_at = None
        campaign.updated_at = datetime.now(timezone.utc)

        return campaign

    async def send_campaign(
        self,
        user_id: str,
        campaign_id: str,
        recipients: List[SMSRecipient],
    ) -> Dict[str, Any]:
        """Send a campaign immediately."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise ValueError("Campaign not found")

        if campaign.status not in [SMSCampaignStatus.DRAFT, SMSCampaignStatus.SCHEDULED]:
            raise ValueError("Campaign cannot be sent")

        campaign.status = SMSCampaignStatus.SENDING
        campaign.total_recipients = len(recipients)

        results = []
        total_cost = 0.0

        for recipient in recipients:
            result = await self._send_single_sms(campaign, recipient)
            results.append(result)

            if result.success:
                campaign.sent_count += 1
                total_cost += result.cost
            else:
                campaign.failed_count += 1

        campaign.status = SMSCampaignStatus.SENT
        campaign.sent_at = datetime.now(timezone.utc)
        campaign.total_cost = total_cost

        return {
            "campaign_id": campaign_id,
            "total": len(recipients),
            "success": campaign.sent_count,
            "failed": campaign.failed_count,
            "total_cost": round(total_cost, 4),
            "total_segments": campaign.sent_count * campaign.segment_count,
        }

    async def _send_single_sms(
        self,
        campaign: SMSCampaign,
        recipient: SMSRecipient,
    ) -> SMSSendResult:
        """Send a single SMS."""
        # Personalize message
        message = self._personalize_message(campaign.message, recipient)

        # Add opt-out text for promotional messages
        if campaign.sms_type == SMSType.PROMOTIONAL:
            message = self._add_opt_out(message)

        # Calculate cost (mock pricing: $0.0075 per segment)
        _, segments = self._calculate_segments(message)
        cost = segments * 0.0075

        # In production, use SMS service (Twilio, Vonage, etc.)
        return SMSSendResult(
            recipient_phone=recipient.phone_number,
            success=True,
            message_id=str(uuid.uuid4()),
            sent_at=datetime.now(timezone.utc),
            cost=cost,
            segments=segments,
        )

    def _personalize_message(
        self,
        message: str,
        recipient: SMSRecipient,
    ) -> str:
        """Replace merge tags with recipient data."""
        result = message

        if recipient.name:
            name_parts = recipient.name.split()
            result = result.replace("{{first_name}}", name_parts[0] if name_parts else "")
            result = result.replace("{{name}}", recipient.name)

        result = result.replace("{{phone}}", recipient.phone_number)

        for key, value in recipient.variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result

    def _add_opt_out(self, message: str) -> str:
        """Add opt-out text to promotional messages."""
        opt_out = "\nReply STOP to opt out"
        if "STOP" not in message.upper():
            return message + opt_out
        return message

    async def send_test_sms(
        self,
        user_id: str,
        campaign_id: str,
        test_phone: str,
        test_name: Optional[str] = None,
    ) -> SMSSendResult:
        """Send a test SMS."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise ValueError("Campaign not found")

        recipient = SMSRecipient(
            phone_number=test_phone,
            name=test_name or "Test User",
        )

        return await self._send_single_sms(campaign, recipient)

    # =========================================================================
    # AI CONTENT GENERATION
    # =========================================================================

    async def generate_sms_content(
        self,
        topic: str,
        sms_type: SMSType,
        max_characters: int = 160,
        include_link: bool = False,
        tone: str = "friendly",
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered SMS content suggestions."""
        client = await self._get_llm_client()

        prompt = f"""Generate 3 SMS messages for:

TOPIC: {topic}
SMS TYPE: {sms_type.value}
MAX CHARACTERS: {max_characters}
INCLUDE LINK PLACEHOLDER: {include_link}
TONE: {tone}

Requirements:
- Keep under {max_characters} characters
- Be concise and clear
- Include a call to action
- {"Include {{link}} placeholder for URL" if include_link else ""}
- For promotional: will add opt-out text automatically

For each message provide:
1. The message text
2. Character count
3. Estimated engagement (low, medium, high)

Format as JSON array."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an SMS marketing expert. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
            temperature=0.8,
        )

        try:
            import json
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return []

    # =========================================================================
    # LINK TRACKING
    # =========================================================================

    async def shorten_link(
        self,
        url: str,
        campaign_id: Optional[str] = None,
    ) -> str:
        """Shorten and track a link for SMS."""
        import hashlib
        hash_val = hashlib.md5(f"{url}{campaign_id}".encode()).hexdigest()[:6]
        return f"https://idkit.io/s/{hash_val}"

    async def replace_links_with_tracking(
        self,
        message: str,
        campaign_id: str,
    ) -> str:
        """Replace links in message with tracking links."""
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)

        result = message
        for url in urls:
            short_url = await self.shorten_link(url, campaign_id)
            result = result.replace(url, short_url)

        return result

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_campaign_stats(
        self,
        user_id: str,
        campaign_id: str,
    ) -> Dict[str, Any]:
        """Get detailed statistics for a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return {}

        delivery_rate = (campaign.delivered_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        click_rate = (campaign.clicked_count / campaign.delivered_count * 100) if campaign.delivered_count > 0 else 0
        opt_out_rate = (campaign.opted_out_count / campaign.delivered_count * 100) if campaign.delivered_count > 0 else 0

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "total_recipients": campaign.total_recipients,
            "sent_count": campaign.sent_count,
            "delivered_count": campaign.delivered_count,
            "failed_count": campaign.failed_count,
            "clicked_count": campaign.clicked_count,
            "opted_out_count": campaign.opted_out_count,
            "delivery_rate": round(delivery_rate, 2),
            "click_rate": round(click_rate, 2),
            "opt_out_rate": round(opt_out_rate, 2),
            "total_segments": campaign.sent_count * campaign.segment_count,
            "total_cost": round(campaign.total_cost, 4),
            "cost_per_message": round(campaign.total_cost / max(campaign.sent_count, 1), 4),
        }

    async def get_dashboard_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get SMS marketing dashboard statistics."""
        campaigns = [c for c in self._campaigns.values() if c.user_id == user_id]

        total_sent = sum(c.sent_count for c in campaigns)
        total_delivered = sum(c.delivered_count for c in campaigns)
        total_cost = sum(c.total_cost for c in campaigns)

        return {
            "total_campaigns": len(campaigns),
            "draft_campaigns": sum(1 for c in campaigns if c.status == SMSCampaignStatus.DRAFT),
            "sent_campaigns": sum(1 for c in campaigns if c.status == SMSCampaignStatus.SENT),
            "total_messages_sent": total_sent,
            "total_delivered": total_delivered,
            "avg_delivery_rate": round((total_delivered / total_sent * 100) if total_sent > 0 else 0, 2),
            "total_spend": round(total_cost, 2),
        }

    # =========================================================================
    # COMPLIANCE
    # =========================================================================

    async def handle_opt_out(
        self,
        phone_number: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Handle opt-out request from a recipient."""
        # In production, update subscriber status
        return {
            "success": True,
            "phone_number": phone_number,
            "action": "opted_out",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_opt_out_status(
        self,
        phone_number: str,
        user_id: str,
    ) -> bool:
        """Check if a phone number has opted out."""
        # In production, check database
        return False

    def validate_phone_number(self, phone: str) -> Dict[str, Any]:
        """Validate a phone number format."""
        import re

        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)

        # Check E.164 format
        e164_pattern = r'^\+[1-9]\d{1,14}$'
        is_valid = bool(re.match(e164_pattern, cleaned))

        return {
            "original": phone,
            "cleaned": cleaned,
            "is_valid": is_valid,
            "format": "E.164" if is_valid else "invalid",
        }
