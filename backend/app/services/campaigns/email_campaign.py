"""
Email Campaign Builder Service

Create, manage, and send email marketing campaigns
with templates, personalization, and analytics.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class CampaignStatus(str, Enum):
    """Status of an email campaign."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class EmailType(str, Enum):
    """Types of email campaigns."""
    NEWSLETTER = "newsletter"
    ANNOUNCEMENT = "announcement"
    PROMOTION = "promotion"
    WELCOME = "welcome"
    FOLLOW_UP = "follow_up"
    RE_ENGAGEMENT = "re_engagement"
    TRANSACTIONAL = "transactional"


@dataclass
class EmailTemplate:
    """Email template configuration."""
    template_id: str
    user_id: str
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    preview_text: Optional[str] = None
    email_type: EmailType = EmailType.NEWSLETTER
    variables: List[str] = field(default_factory=list)
    thumbnail_url: Optional[str] = None
    is_default: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EmailRecipient:
    """An email recipient."""
    email: str
    name: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class SendResult:
    """Result of sending an email."""
    recipient_email: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[datetime] = None


@dataclass
class EmailCampaign:
    """An email campaign."""
    campaign_id: str
    user_id: str
    name: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    preview_text: Optional[str] = None
    from_name: str = ""
    from_email: str = ""
    reply_to: Optional[str] = None
    email_type: EmailType = EmailType.NEWSLETTER
    template_id: Optional[str] = None
    list_ids: List[str] = field(default_factory=list)
    segment_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    status: CampaignStatus = CampaignStatus.DRAFT
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    # Stats
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    bounced_count: int = 0
    unsubscribed_count: int = 0
    complained_count: int = 0

    # A/B Testing
    is_ab_test: bool = False
    ab_variants: List[Dict[str, Any]] = field(default_factory=list)
    winning_variant: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EmailCampaignBuilder:
    """
    Email campaign creation and management service.

    Features:
    - Campaign creation with templates
    - AI-powered subject line and content generation
    - Personalization with merge tags
    - A/B testing support
    - Scheduling and automation
    - Delivery and engagement analytics
    """

    # Default merge tags
    MERGE_TAGS = {
        "{{first_name}}": "Subscriber's first name",
        "{{last_name}}": "Subscriber's last name",
        "{{email}}": "Subscriber's email",
        "{{unsubscribe_link}}": "Unsubscribe link",
        "{{view_in_browser}}": "View in browser link",
        "{{current_year}}": "Current year",
    }

    def __init__(self):
        self._llm_client = None
        self._email_client = None
        self._campaigns: Dict[str, EmailCampaign] = {}
        self._templates: Dict[str, EmailTemplate] = {}

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
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        preview_text: Optional[str] = None,
        email_type: EmailType = EmailType.NEWSLETTER,
    ) -> EmailTemplate:
        """Create a new email template."""
        # Extract variables from content
        variables = self._extract_variables(html_content)

        template = EmailTemplate(
            template_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content or self._html_to_text(html_content),
            preview_text=preview_text,
            email_type=email_type,
            variables=variables,
        )

        self._templates[template.template_id] = template
        return template

    async def get_templates(
        self,
        user_id: str,
        email_type: Optional[EmailType] = None,
    ) -> List[EmailTemplate]:
        """Get user's email templates."""
        templates = [
            t for t in self._templates.values()
            if t.user_id == user_id
        ]

        if email_type:
            templates = [t for t in templates if t.email_type == email_type]

        return templates

    async def get_template(
        self,
        template_id: str,
    ) -> Optional[EmailTemplate]:
        """Get a specific template."""
        return self._templates.get(template_id)

    async def update_template(
        self,
        user_id: str,
        template_id: str,
        **updates,
    ) -> Optional[EmailTemplate]:
        """Update a template."""
        template = self._templates.get(template_id)
        if not template or template.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.now(timezone.utc)

        # Re-extract variables if content changed
        if "html_content" in updates:
            template.variables = self._extract_variables(template.html_content)

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

    def _extract_variables(self, content: str) -> List[str]:
        """Extract merge tag variables from content."""
        import re
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================

    async def create_campaign(
        self,
        user_id: str,
        name: str,
        subject: str,
        html_content: str,
        from_name: str,
        from_email: str,
        text_content: Optional[str] = None,
        preview_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        email_type: EmailType = EmailType.NEWSLETTER,
        template_id: Optional[str] = None,
        list_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> EmailCampaign:
        """Create a new email campaign."""
        campaign = EmailCampaign(
            campaign_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content or self._html_to_text(html_content),
            preview_text=preview_text,
            from_name=from_name,
            from_email=from_email,
            reply_to=reply_to or from_email,
            email_type=email_type,
            template_id=template_id,
            list_ids=list_ids or [],
            tags=tags or [],
        )

        self._campaigns[campaign.campaign_id] = campaign
        return campaign

    async def create_from_template(
        self,
        user_id: str,
        template_id: str,
        name: str,
        from_name: str,
        from_email: str,
        list_ids: Optional[List[str]] = None,
        subject_override: Optional[str] = None,
        content_overrides: Optional[Dict[str, str]] = None,
    ) -> EmailCampaign:
        """Create a campaign from a template."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError("Template not found")

        html_content = template.html_content
        if content_overrides:
            for key, value in content_overrides.items():
                html_content = html_content.replace(f"{{{{{key}}}}}", value)

        return await self.create_campaign(
            user_id=user_id,
            name=name,
            subject=subject_override or template.subject,
            html_content=html_content,
            text_content=template.text_content,
            preview_text=template.preview_text,
            from_name=from_name,
            from_email=from_email,
            email_type=template.email_type,
            template_id=template_id,
            list_ids=list_ids,
        )

    async def get_campaigns(
        self,
        user_id: str,
        status: Optional[CampaignStatus] = None,
        email_type: Optional[EmailType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmailCampaign]:
        """Get user's campaigns."""
        campaigns = [
            c for c in self._campaigns.values()
            if c.user_id == user_id
        ]

        if status:
            campaigns = [c for c in campaigns if c.status == status]

        if email_type:
            campaigns = [c for c in campaigns if c.email_type == email_type]

        campaigns.sort(key=lambda c: c.created_at, reverse=True)
        return campaigns[offset:offset + limit]

    async def get_campaign(
        self,
        campaign_id: str,
    ) -> Optional[EmailCampaign]:
        """Get a specific campaign."""
        return self._campaigns.get(campaign_id)

    async def update_campaign(
        self,
        user_id: str,
        campaign_id: str,
        **updates,
    ) -> Optional[EmailCampaign]:
        """Update a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValueError("Cannot update campaign that is sending or sent")

        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

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

        if campaign.status == CampaignStatus.SENDING:
            raise ValueError("Cannot delete campaign that is sending")

        del self._campaigns[campaign_id]
        return True

    async def duplicate_campaign(
        self,
        user_id: str,
        campaign_id: str,
        new_name: Optional[str] = None,
    ) -> Optional[EmailCampaign]:
        """Duplicate an existing campaign."""
        original = self._campaigns.get(campaign_id)
        if not original or original.user_id != user_id:
            return None

        return await self.create_campaign(
            user_id=user_id,
            name=new_name or f"{original.name} (Copy)",
            subject=original.subject,
            html_content=original.html_content,
            text_content=original.text_content,
            preview_text=original.preview_text,
            from_name=original.from_name,
            from_email=original.from_email,
            reply_to=original.reply_to,
            email_type=original.email_type,
            template_id=original.template_id,
            list_ids=original.list_ids.copy(),
            tags=original.tags.copy(),
        )

    # =========================================================================
    # SCHEDULING & SENDING
    # =========================================================================

    async def schedule_campaign(
        self,
        user_id: str,
        campaign_id: str,
        scheduled_at: datetime,
    ) -> Optional[EmailCampaign]:
        """Schedule a campaign for future sending."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError("Can only schedule draft campaigns")

        if scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Scheduled time must be in the future")

        campaign.status = CampaignStatus.SCHEDULED
        campaign.scheduled_at = scheduled_at
        campaign.updated_at = datetime.now(timezone.utc)

        return campaign

    async def cancel_scheduled(
        self,
        user_id: str,
        campaign_id: str,
    ) -> Optional[EmailCampaign]:
        """Cancel a scheduled campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            return None

        if campaign.status != CampaignStatus.SCHEDULED:
            raise ValueError("Campaign is not scheduled")

        campaign.status = CampaignStatus.DRAFT
        campaign.scheduled_at = None
        campaign.updated_at = datetime.now(timezone.utc)

        return campaign

    async def send_campaign(
        self,
        user_id: str,
        campaign_id: str,
        recipients: List[EmailRecipient],
    ) -> Dict[str, Any]:
        """Send a campaign immediately."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise ValueError("Campaign not found")

        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValueError("Campaign cannot be sent")

        campaign.status = CampaignStatus.SENDING
        campaign.total_recipients = len(recipients)

        results = []
        for recipient in recipients:
            result = await self._send_single_email(campaign, recipient)
            results.append(result)

            if result.success:
                campaign.sent_count += 1

        campaign.status = CampaignStatus.SENT
        campaign.sent_at = datetime.now(timezone.utc)

        success_count = sum(1 for r in results if r.success)

        return {
            "campaign_id": campaign_id,
            "total": len(recipients),
            "success": success_count,
            "failed": len(recipients) - success_count,
            "results": [
                {
                    "email": r.recipient_email,
                    "success": r.success,
                    "error": r.error,
                }
                for r in results
            ],
        }

    async def _send_single_email(
        self,
        campaign: EmailCampaign,
        recipient: EmailRecipient,
    ) -> SendResult:
        """Send a single email."""
        # Personalize content
        html_content = self._personalize_content(
            campaign.html_content,
            recipient,
        )
        text_content = self._personalize_content(
            campaign.text_content or "",
            recipient,
        )
        subject = self._personalize_content(
            campaign.subject,
            recipient,
        )

        # In production, use email service (SendGrid, SES, etc.)
        # Mock success for now
        return SendResult(
            recipient_email=recipient.email,
            success=True,
            message_id=str(uuid.uuid4()),
            sent_at=datetime.now(timezone.utc),
        )

    def _personalize_content(
        self,
        content: str,
        recipient: EmailRecipient,
    ) -> str:
        """Replace merge tags with recipient data."""
        result = content

        # Standard tags
        if recipient.name:
            name_parts = recipient.name.split()
            result = result.replace("{{first_name}}", name_parts[0] if name_parts else "")
            result = result.replace("{{last_name}}", name_parts[-1] if len(name_parts) > 1 else "")

        result = result.replace("{{email}}", recipient.email)
        result = result.replace("{{current_year}}", str(datetime.now().year))

        # Custom variables
        for key, value in recipient.variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result

    async def send_test_email(
        self,
        user_id: str,
        campaign_id: str,
        test_email: str,
        test_name: Optional[str] = None,
    ) -> SendResult:
        """Send a test email."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise ValueError("Campaign not found")

        recipient = EmailRecipient(
            email=test_email,
            name=test_name or "Test User",
        )

        return await self._send_single_email(campaign, recipient)

    # =========================================================================
    # AI CONTENT GENERATION
    # =========================================================================

    async def generate_subject_lines(
        self,
        content_summary: str,
        email_type: EmailType,
        brand_voice: Optional[str] = None,
        count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered subject line suggestions."""
        client = await self._get_llm_client()

        prompt = f"""Generate {count} email subject lines for this content:

CONTENT SUMMARY: {content_summary}
EMAIL TYPE: {email_type.value}
{f"BRAND VOICE: {brand_voice}" if brand_voice else ""}

Requirements:
- Be compelling and click-worthy
- Keep under 60 characters
- Match the email type's tone
- Avoid spam trigger words
- Include a mix of styles (curiosity, urgency, benefit, personal)

For each subject line provide:
1. The subject line
2. Style used (curiosity, urgency, benefit, personal, question)
3. Estimated open rate improvement (low, medium, high)

Format as JSON array."""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an email marketing expert. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.8,
        )

        try:
            import json
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return []

    async def generate_email_content(
        self,
        topic: str,
        email_type: EmailType,
        key_points: List[str],
        tone: str = "friendly",
        include_cta: bool = True,
        cta_text: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate AI-powered email content."""
        client = await self._get_llm_client()

        prompt = f"""Write an email for the following:

TOPIC: {topic}
EMAIL TYPE: {email_type.value}
KEY POINTS TO COVER:
{chr(10).join(f'- {point}' for point in key_points)}
TONE: {tone}
INCLUDE CTA: {include_cta}
{f"CTA TEXT: {cta_text}" if cta_text else ""}

Generate:
1. Subject line
2. Preview text (under 100 chars)
3. Email body HTML (use basic HTML: h1, h2, p, ul, li, a, strong)

Format as JSON with keys: subject, preview_text, html_content"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert email copywriter. Return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        try:
            import json
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "subject": topic,
                "preview_text": "",
                "html_content": f"<p>{topic}</p>",
            }

    # =========================================================================
    # A/B TESTING
    # =========================================================================

    async def create_ab_test(
        self,
        user_id: str,
        campaign_id: str,
        variants: List[Dict[str, Any]],
        test_percentage: int = 20,
        winning_criteria: str = "open_rate",
    ) -> EmailCampaign:
        """Set up A/B testing for a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign or campaign.user_id != user_id:
            raise ValueError("Campaign not found")

        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError("Can only set up A/B test on draft campaigns")

        campaign.is_ab_test = True
        campaign.ab_variants = [
            {
                "variant_id": str(uuid.uuid4()),
                "name": v.get("name", f"Variant {i+1}"),
                "subject": v.get("subject", campaign.subject),
                "preview_text": v.get("preview_text", campaign.preview_text),
                "test_percentage": test_percentage // len(variants),
                "sent_count": 0,
                "opened_count": 0,
                "clicked_count": 0,
            }
            for i, v in enumerate(variants)
        ]

        return campaign

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

        open_rate = (campaign.opened_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        click_rate = (campaign.clicked_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        bounce_rate = (campaign.bounced_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0
        unsubscribe_rate = (campaign.unsubscribed_count / campaign.sent_count * 100) if campaign.sent_count > 0 else 0

        return {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "sent_at": campaign.sent_at.isoformat() if campaign.sent_at else None,
            "total_recipients": campaign.total_recipients,
            "sent_count": campaign.sent_count,
            "delivered_count": campaign.delivered_count,
            "opened_count": campaign.opened_count,
            "clicked_count": campaign.clicked_count,
            "bounced_count": campaign.bounced_count,
            "unsubscribed_count": campaign.unsubscribed_count,
            "complained_count": campaign.complained_count,
            "open_rate": round(open_rate, 2),
            "click_rate": round(click_rate, 2),
            "bounce_rate": round(bounce_rate, 2),
            "unsubscribe_rate": round(unsubscribe_rate, 2),
            "is_ab_test": campaign.is_ab_test,
            "ab_variants": campaign.ab_variants if campaign.is_ab_test else None,
        }

    async def get_dashboard_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get email marketing dashboard statistics."""
        campaigns = [c for c in self._campaigns.values() if c.user_id == user_id]

        total_sent = sum(c.sent_count for c in campaigns)
        total_opened = sum(c.opened_count for c in campaigns)
        total_clicked = sum(c.clicked_count for c in campaigns)

        return {
            "total_campaigns": len(campaigns),
            "draft_campaigns": sum(1 for c in campaigns if c.status == CampaignStatus.DRAFT),
            "sent_campaigns": sum(1 for c in campaigns if c.status == CampaignStatus.SENT),
            "scheduled_campaigns": sum(1 for c in campaigns if c.status == CampaignStatus.SCHEDULED),
            "total_emails_sent": total_sent,
            "total_opens": total_opened,
            "total_clicks": total_clicked,
            "avg_open_rate": round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
            "avg_click_rate": round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2),
        }
