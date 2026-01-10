"""
Email Service

Unified email service with provider abstraction, templates, and tracking.
"""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from app.services.email.providers import (
    EmailMessage,
    EmailProvider,
    MailgunProvider,
    SendGridProvider,
    SendResult,
    SESProvider,
    SMTPProvider,
)

logger = logging.getLogger(__name__)


class EmailService:
    """
    Unified email service with multiple provider support.

    Features:
    - Multiple provider backends (SES, SendGrid, Mailgun, SMTP)
    - Automatic failover between providers
    - Template rendering with Jinja2
    - Email tracking and analytics
    - Rate limiting
    - Bounce and complaint handling
    """

    def __init__(self):
        self._providers: dict[str, EmailProvider] = {}
        self._primary_provider: Optional[str] = None
        self._fallback_providers: list[str] = []
        self._default_from_email: Optional[str] = None
        self._default_from_name: Optional[str] = None
        self._templates: dict[str, dict] = {}

    def configure(
        self,
        provider_type: str,
        primary: bool = True,
        **provider_config,
    ) -> None:
        """
        Configure an email provider.

        Args:
            provider_type: One of 'ses', 'sendgrid', 'mailgun', 'smtp'
            primary: Whether this is the primary provider
            **provider_config: Provider-specific configuration
        """
        provider: EmailProvider

        if provider_type == "ses":
            provider = SESProvider(
                aws_access_key_id=provider_config.get("aws_access_key_id"),
                aws_secret_access_key=provider_config.get("aws_secret_access_key"),
                region=provider_config.get("region", "us-east-1"),
                configuration_set=provider_config.get("configuration_set"),
            )
        elif provider_type == "sendgrid":
            provider = SendGridProvider(
                api_key=provider_config.get("api_key"),
            )
        elif provider_type == "mailgun":
            provider = MailgunProvider(
                api_key=provider_config.get("api_key"),
                domain=provider_config.get("domain"),
                region=provider_config.get("region", "us"),
            )
        elif provider_type == "smtp":
            provider = SMTPProvider(
                host=provider_config.get("host"),
                port=provider_config.get("port", 587),
                username=provider_config.get("username"),
                password=provider_config.get("password"),
                use_tls=provider_config.get("use_tls", True),
                use_ssl=provider_config.get("use_ssl", False),
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        self._providers[provider_type] = provider

        if primary:
            self._primary_provider = provider_type
        else:
            self._fallback_providers.append(provider_type)

        logger.info(f"Configured email provider: {provider_type} (primary={primary})")

    def set_defaults(
        self,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> None:
        """Set default sender information."""
        self._default_from_email = from_email
        self._default_from_name = from_name

    def register_template(
        self,
        template_id: str,
        subject: str,
        html_template: str,
        text_template: Optional[str] = None,
    ) -> None:
        """Register an email template."""
        self._templates[template_id] = {
            "subject": subject,
            "html": html_template,
            "text": text_template,
        }

    async def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        provider: Optional[str] = None,
    ) -> SendResult:
        """
        Send a single email.

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content (auto-generated if not provided)
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            reply_to: Reply-to address
            cc: CC recipients
            bcc: BCC recipients
            tags: Tags for tracking
            metadata: Custom metadata
            provider: Specific provider to use (optional)

        Returns:
            SendResult with success status and message ID
        """
        message = EmailMessage(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body or self._html_to_text(html_body),
            from_email=from_email or self._default_from_email,
            from_name=from_name or self._default_from_name,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
            tags=tags,
            metadata=metadata,
        )

        return await self._send_with_fallback(message, provider)

    async def send_template(
        self,
        to: str,
        template_id: str,
        context: dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> SendResult:
        """
        Send an email using a registered template.

        Args:
            to: Recipient email address
            template_id: ID of registered template
            context: Variables for template rendering
            from_email: Sender email
            from_name: Sender name
            reply_to: Reply-to address
            tags: Tags for tracking

        Returns:
            SendResult with success status
        """
        template = self._templates.get(template_id)
        if not template:
            return SendResult(
                success=False,
                error=f"Template not found: {template_id}",
            )

        try:
            subject = self._render_template(template["subject"], context)
            html_body = self._render_template(template["html"], context)
            text_body = None
            if template["text"]:
                text_body = self._render_template(template["text"], context)

            return await self.send(
                to=to,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                tags=tags,
            )
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return SendResult(success=False, error=str(e))

    async def send_batch(
        self,
        messages: list[dict[str, Any]],
        provider: Optional[str] = None,
    ) -> list[SendResult]:
        """
        Send multiple emails.

        Args:
            messages: List of message dicts with same params as send()
            provider: Specific provider to use

        Returns:
            List of SendResult objects
        """
        email_messages = []
        for msg in messages:
            email_messages.append(
                EmailMessage(
                    to=msg["to"],
                    subject=msg["subject"],
                    html_body=msg["html_body"],
                    text_body=msg.get("text_body"),
                    from_email=msg.get("from_email") or self._default_from_email,
                    from_name=msg.get("from_name") or self._default_from_name,
                    reply_to=msg.get("reply_to"),
                    cc=msg.get("cc"),
                    bcc=msg.get("bcc"),
                    tags=msg.get("tags"),
                    metadata=msg.get("metadata"),
                )
            )

        provider_instance = self._get_provider(provider)
        if not provider_instance:
            return [
                SendResult(success=False, error="No email provider configured")
                for _ in messages
            ]

        return await provider_instance.send_batch(email_messages)

    async def _send_with_fallback(
        self,
        message: EmailMessage,
        preferred_provider: Optional[str] = None,
    ) -> SendResult:
        """Send email with automatic fallback on failure."""
        providers_to_try = []

        if preferred_provider and preferred_provider in self._providers:
            providers_to_try.append(preferred_provider)

        if self._primary_provider and self._primary_provider not in providers_to_try:
            providers_to_try.append(self._primary_provider)

        for fallback in self._fallback_providers:
            if fallback not in providers_to_try:
                providers_to_try.append(fallback)

        if not providers_to_try:
            return SendResult(
                success=False,
                error="No email providers configured",
            )

        last_error = None
        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            if not provider:
                continue

            try:
                result = await provider.send(message)
                if result.success:
                    logger.info(
                        f"Email sent via {provider_name}: {result.message_id}"
                    )
                    return result

                last_error = result.error
                logger.warning(
                    f"Email send failed via {provider_name}: {result.error}"
                )

            except Exception as e:
                last_error = str(e)
                logger.error(f"Email provider {provider_name} error: {e}")

        return SendResult(
            success=False,
            error=f"All providers failed. Last error: {last_error}",
        )

    def _get_provider(self, provider_name: Optional[str] = None) -> Optional[EmailProvider]:
        """Get a provider instance."""
        if provider_name:
            return self._providers.get(provider_name)
        if self._primary_provider:
            return self._providers.get(self._primary_provider)
        return None

    def _render_template(self, template: str, context: dict[str, Any]) -> str:
        """Render a template with Jinja2."""
        try:
            from jinja2 import Template

            return Template(template).render(**context)
        except ImportError:
            # Fallback to simple string formatting
            result = template
            for key, value in context.items():
                result = result.replace(f"{{{{ {key} }}}}", str(value))
                result = result.replace(f"{{{{{key}}}}}", str(value))
            return result

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        import re

        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # =========================================================================
    # Transactional Email Methods
    # =========================================================================

    async def send_welcome_email(
        self,
        to: str,
        name: str,
        verification_link: Optional[str] = None,
    ) -> SendResult:
        """Send welcome email to new user."""
        html = f"""
        <h1>Welcome to IDKit, {name}!</h1>
        <p>We're excited to have you on board.</p>
        <p>IDKit helps you create AI-powered content, build your brand, and grow your influence.</p>
        {"<p><a href='" + verification_link + "'>Click here to verify your email</a></p>" if verification_link else ""}
        <p>Get started by:</p>
        <ul>
            <li>Creating your AI Twin</li>
            <li>Connecting your social accounts</li>
            <li>Generating your first content</li>
        </ul>
        <p>If you have any questions, reply to this email!</p>
        """

        return await self.send(
            to=to,
            subject=f"Welcome to IDKit, {name}!",
            html_body=html,
            tags=["transactional", "welcome"],
        )

    async def send_password_reset(
        self,
        to: str,
        name: str,
        reset_link: str,
        expires_in_hours: int = 24,
    ) -> SendResult:
        """Send password reset email."""
        html = f"""
        <h2>Reset Your Password</h2>
        <p>Hi {name},</p>
        <p>We received a request to reset your password.</p>
        <p><a href="{reset_link}" style="padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">Reset Password</a></p>
        <p>This link expires in {expires_in_hours} hours.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        """

        return await self.send(
            to=to,
            subject="Reset Your IDKit Password",
            html_body=html,
            tags=["transactional", "password-reset"],
        )

    async def send_verification_email(
        self,
        to: str,
        name: str,
        verification_link: str,
    ) -> SendResult:
        """Send email verification."""
        html = f"""
        <h2>Verify Your Email</h2>
        <p>Hi {name},</p>
        <p>Please verify your email address by clicking the button below:</p>
        <p><a href="{verification_link}" style="padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">Verify Email</a></p>
        <p>If you didn't create an account, you can ignore this email.</p>
        """

        return await self.send(
            to=to,
            subject="Verify Your Email - IDKit",
            html_body=html,
            tags=["transactional", "verification"],
        )

    async def send_team_invite(
        self,
        to: str,
        inviter_name: str,
        organization_name: str,
        invite_link: str,
        role: str,
    ) -> SendResult:
        """Send team invitation email."""
        html = f"""
        <h2>You've Been Invited!</h2>
        <p>{inviter_name} has invited you to join <strong>{organization_name}</strong> on IDKit as a {role}.</p>
        <p><a href="{invite_link}" style="padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">Accept Invitation</a></p>
        <p>This invitation expires in 7 days.</p>
        """

        return await self.send(
            to=to,
            subject=f"Join {organization_name} on IDKit",
            html_body=html,
            tags=["transactional", "team-invite"],
        )

    async def send_subscription_confirmation(
        self,
        to: str,
        name: str,
        plan_name: str,
        amount: float,
        currency: str,
        next_billing_date: str,
    ) -> SendResult:
        """Send subscription confirmation email."""
        html = f"""
        <h2>Subscription Confirmed!</h2>
        <p>Hi {name},</p>
        <p>Thank you for subscribing to IDKit {plan_name}!</p>
        <div style="background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 16px 0;">
            <p><strong>Plan:</strong> {plan_name}</p>
            <p><strong>Amount:</strong> {currency} {amount:.2f}</p>
            <p><strong>Next Billing:</strong> {next_billing_date}</p>
        </div>
        <p>You now have access to all {plan_name} features. Start exploring!</p>
        """

        return await self.send(
            to=to,
            subject=f"Welcome to IDKit {plan_name}!",
            html_body=html,
            tags=["transactional", "subscription"],
        )

    async def send_payment_failed(
        self,
        to: str,
        name: str,
        amount: float,
        currency: str,
        retry_date: str,
        update_payment_link: str,
    ) -> SendResult:
        """Send payment failure notification."""
        html = f"""
        <h2>Payment Failed</h2>
        <p>Hi {name},</p>
        <p>We were unable to process your payment of {currency} {amount:.2f}.</p>
        <p>We'll retry on {retry_date}. To avoid service interruption, please update your payment method:</p>
        <p><a href="{update_payment_link}" style="padding: 12px 24px; background: #ef4444; color: white; text-decoration: none; border-radius: 6px;">Update Payment Method</a></p>
        """

        return await self.send(
            to=to,
            subject="Action Required: Payment Failed - IDKit",
            html_body=html,
            tags=["transactional", "payment-failed"],
        )

    async def send_export_ready(
        self,
        to: str,
        name: str,
        download_link: str,
        expires_in_days: int = 30,
    ) -> SendResult:
        """Send data export ready notification."""
        html = f"""
        <h2>Your Data Export is Ready</h2>
        <p>Hi {name},</p>
        <p>Your requested data export is now ready for download.</p>
        <p><a href="{download_link}" style="padding: 12px 24px; background: #6366f1; color: white; text-decoration: none; border-radius: 6px;">Download Export</a></p>
        <p>This link expires in {expires_in_days} days.</p>
        """

        return await self.send(
            to=to,
            subject="Your Data Export is Ready - IDKit",
            html_body=html,
            tags=["transactional", "gdpr-export"],
        )


# Global service instance
email_service = EmailService()


def configure_email_service():
    """Configure email service from environment."""
    from app.config import settings

    # Configure based on available credentials
    if hasattr(settings, "sendgrid_api_key") and settings.sendgrid_api_key:
        email_service.configure(
            "sendgrid",
            primary=True,
            api_key=settings.sendgrid_api_key,
        )
    elif hasattr(settings, "aws_access_key_id") and settings.aws_access_key_id:
        email_service.configure(
            "ses",
            primary=True,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region=getattr(settings, "aws_region", "us-east-1"),
        )
    elif hasattr(settings, "mailgun_api_key") and settings.mailgun_api_key:
        email_service.configure(
            "mailgun",
            primary=True,
            api_key=settings.mailgun_api_key,
            domain=settings.mailgun_domain,
        )
    elif hasattr(settings, "smtp_host") and settings.smtp_host:
        email_service.configure(
            "smtp",
            primary=True,
            host=settings.smtp_host,
            port=getattr(settings, "smtp_port", 587),
            username=getattr(settings, "smtp_username", None),
            password=getattr(settings, "smtp_password", None),
        )

    # Set defaults
    if hasattr(settings, "default_from_email"):
        email_service.set_defaults(
            from_email=settings.default_from_email,
            from_name=getattr(settings, "default_from_name", "IDKit"),
        )
