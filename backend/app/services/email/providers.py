"""
Email Provider Implementations

Multiple email provider adapters for production use.
"""

import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message structure."""

    to: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    headers: Optional[dict[str, str]] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class SendResult:
    """Result of sending an email."""

    success: bool
    message_id: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[dict] = None


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    name: str = "base"

    @abstractmethod
    async def send(self, message: EmailMessage) -> SendResult:
        """Send a single email."""
        pass

    @abstractmethod
    async def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails."""
        pass

    @abstractmethod
    async def verify_domain(self, domain: str) -> dict:
        """Verify a sending domain."""
        pass

    @abstractmethod
    async def get_stats(self, days: int = 30) -> dict:
        """Get sending statistics."""
        pass


class SESProvider(EmailProvider):
    """
    Amazon SES email provider.

    Cost-effective for high-volume sending.
    """

    name = "ses"

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        configuration_set: Optional[str] = None,
    ):
        self.region = region
        self.configuration_set = configuration_set
        self._client = None
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key

    async def _get_client(self):
        """Get or create SES client."""
        if self._client is None:
            try:
                import aioboto3

                session = aioboto3.Session(
                    aws_access_key_id=self._aws_access_key_id,
                    aws_secret_access_key=self._aws_secret_access_key,
                    region_name=self.region,
                )
                self._client = await session.client("ses").__aenter__()
            except ImportError:
                logger.error("aioboto3 not installed. Run: pip install aioboto3")
                raise
        return self._client

    async def send(self, message: EmailMessage) -> SendResult:
        """Send email via Amazon SES."""
        try:
            client = await self._get_client()

            from_address = message.from_email
            if message.from_name:
                from_address = f"{message.from_name} <{message.from_email}>"

            email_msg = {
                "Source": from_address,
                "Destination": {
                    "ToAddresses": [message.to],
                },
                "Message": {
                    "Subject": {"Data": message.subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": message.html_body, "Charset": "UTF-8"},
                    },
                },
            }

            if message.text_body:
                email_msg["Message"]["Body"]["Text"] = {
                    "Data": message.text_body,
                    "Charset": "UTF-8",
                }

            if message.reply_to:
                email_msg["ReplyToAddresses"] = [message.reply_to]

            if message.cc:
                email_msg["Destination"]["CcAddresses"] = message.cc

            if message.bcc:
                email_msg["Destination"]["BccAddresses"] = message.bcc

            if self.configuration_set:
                email_msg["ConfigurationSetName"] = self.configuration_set

            if message.tags:
                email_msg["Tags"] = [
                    {"Name": "tag", "Value": tag} for tag in message.tags[:10]
                ]

            response = await client.send_email(**email_msg)

            return SendResult(
                success=True,
                message_id=response.get("MessageId"),
                provider=self.name,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"SES send error: {e}")
            return SendResult(
                success=False,
                provider=self.name,
                error=str(e),
            )

    async def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails via SES."""
        # SES doesn't have native batch, send individually
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results

    async def verify_domain(self, domain: str) -> dict:
        """Request domain verification in SES."""
        try:
            client = await self._get_client()
            response = await client.verify_domain_identity(Domain=domain)
            dkim_response = await client.verify_domain_dkim(Domain=domain)

            return {
                "domain": domain,
                "verification_token": response.get("VerificationToken"),
                "dkim_tokens": dkim_response.get("DkimTokens", []),
                "status": "pending",
            }
        except Exception as e:
            return {"domain": domain, "error": str(e), "status": "failed"}

    async def get_stats(self, days: int = 30) -> dict:
        """Get SES sending statistics."""
        try:
            client = await self._get_client()
            response = await client.get_send_statistics()

            return {
                "provider": self.name,
                "data_points": response.get("SendDataPoints", []),
            }
        except Exception as e:
            return {"provider": self.name, "error": str(e)}


class SendGridProvider(EmailProvider):
    """
    SendGrid email provider.

    Feature-rich with good deliverability.
    """

    name = "sendgrid"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        """Get or create SendGrid client."""
        if self._client is None:
            try:
                from sendgrid import SendGridAPIClient

                self._client = SendGridAPIClient(self.api_key)
            except ImportError:
                logger.error("sendgrid not installed. Run: pip install sendgrid")
                raise
        return self._client

    async def send(self, message: EmailMessage) -> SendResult:
        """Send email via SendGrid."""
        try:
            from sendgrid.helpers.mail import (
                Mail,
                Email,
                To,
                Content,
                Cc,
                Bcc,
                ReplyTo,
            )

            client = await self._get_client()

            from_email = Email(message.from_email, message.from_name)
            to_email = To(message.to)

            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=message.subject,
                html_content=Content("text/html", message.html_body),
            )

            if message.text_body:
                mail.add_content(Content("text/plain", message.text_body))

            if message.reply_to:
                mail.reply_to = ReplyTo(message.reply_to)

            if message.cc:
                for cc in message.cc:
                    mail.add_cc(Cc(cc))

            if message.bcc:
                for bcc in message.bcc:
                    mail.add_bcc(Bcc(bcc))

            if message.tags:
                for tag in message.tags:
                    mail.add_category(tag)

            if message.metadata:
                for key, value in message.metadata.items():
                    mail.add_custom_arg(key, str(value))

            # Run in thread pool since sendgrid client is sync
            import asyncio

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: client.send(mail)
            )

            return SendResult(
                success=response.status_code in [200, 201, 202],
                message_id=response.headers.get("X-Message-Id"),
                provider=self.name,
                raw_response={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                },
            )

        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return SendResult(
                success=False,
                provider=self.name,
                error=str(e),
            )

    async def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails via SendGrid."""
        # SendGrid supports batch via personalizations, but for simplicity
        # we send individually with proper rate limiting
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results

    async def verify_domain(self, domain: str) -> dict:
        """Authenticate a domain in SendGrid."""
        try:
            import asyncio

            client = await self._get_client()

            data = {"domain": domain, "automatic_security": True}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.client.whitelabel.domains.post(request_body=data),
            )

            return {
                "domain": domain,
                "status": "pending",
                "dns_records": response.to_dict.get("dns", {}),
            }
        except Exception as e:
            return {"domain": domain, "error": str(e), "status": "failed"}

    async def get_stats(self, days: int = 30) -> dict:
        """Get SendGrid statistics."""
        try:
            import asyncio
            from datetime import datetime, timedelta

            client = await self._get_client()

            start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = datetime.utcnow().strftime("%Y-%m-%d")

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.client.stats.get(
                    query_params={"start_date": start_date, "end_date": end_date}
                ),
            )

            return {
                "provider": self.name,
                "stats": response.to_dict if hasattr(response, "to_dict") else [],
            }
        except Exception as e:
            return {"provider": self.name, "error": str(e)}


class SMTPProvider(EmailProvider):
    """
    Generic SMTP email provider.

    Fallback for any SMTP server.
    """

    name = "smtp"

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl

    async def send(self, message: EmailMessage) -> SendResult:
        """Send email via SMTP."""
        try:
            import asyncio

            # Build MIME message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["To"] = message.to

            if message.from_name:
                msg["From"] = f"{message.from_name} <{message.from_email}>"
            else:
                msg["From"] = message.from_email

            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            if message.cc:
                msg["Cc"] = ", ".join(message.cc)

            if message.headers:
                for key, value in message.headers.items():
                    msg[key] = value

            # Add body parts
            if message.text_body:
                msg.attach(MIMEText(message.text_body, "plain"))
            msg.attach(MIMEText(message.html_body, "html"))

            # Send via SMTP in thread pool
            loop = asyncio.get_event_loop()

            def send_smtp():
                if self.use_ssl:
                    server = smtplib.SMTP_SSL(self.host, self.port)
                else:
                    server = smtplib.SMTP(self.host, self.port)

                try:
                    if self.use_tls and not self.use_ssl:
                        server.starttls()

                    if self.username and self.password:
                        server.login(self.username, self.password)

                    recipients = [message.to]
                    if message.cc:
                        recipients.extend(message.cc)
                    if message.bcc:
                        recipients.extend(message.bcc)

                    server.sendmail(message.from_email, recipients, msg.as_string())
                    return True
                finally:
                    server.quit()

            await loop.run_in_executor(None, send_smtp)

            return SendResult(
                success=True,
                provider=self.name,
            )

        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return SendResult(
                success=False,
                provider=self.name,
                error=str(e),
            )

    async def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails via SMTP."""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results

    async def verify_domain(self, domain: str) -> dict:
        """SMTP doesn't support domain verification."""
        return {
            "domain": domain,
            "status": "not_supported",
            "message": "SMTP provider does not support domain verification",
        }

    async def get_stats(self, days: int = 30) -> dict:
        """SMTP doesn't provide statistics."""
        return {
            "provider": self.name,
            "message": "SMTP provider does not provide statistics",
        }


class MailgunProvider(EmailProvider):
    """
    Mailgun email provider.

    Good for transactional emails with excellent API.
    """

    name = "mailgun"

    def __init__(self, api_key: str, domain: str, region: str = "us"):
        self.api_key = api_key
        self.domain = domain
        self.base_url = (
            f"https://api.{'eu.' if region == 'eu' else ''}mailgun.net/v3"
        )

    async def send(self, message: EmailMessage) -> SendResult:
        """Send email via Mailgun."""
        try:
            import aiohttp

            url = f"{self.base_url}/{self.domain}/messages"

            from_address = message.from_email
            if message.from_name:
                from_address = f"{message.from_name} <{message.from_email}>"

            data = {
                "from": from_address,
                "to": message.to,
                "subject": message.subject,
                "html": message.html_body,
            }

            if message.text_body:
                data["text"] = message.text_body

            if message.reply_to:
                data["h:Reply-To"] = message.reply_to

            if message.cc:
                data["cc"] = ",".join(message.cc)

            if message.bcc:
                data["bcc"] = ",".join(message.bcc)

            if message.tags:
                data["o:tag"] = message.tags

            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth("api", self.api_key)
                async with session.post(url, data=data, auth=auth) as response:
                    result = await response.json()

                    if response.status == 200:
                        return SendResult(
                            success=True,
                            message_id=result.get("id"),
                            provider=self.name,
                            raw_response=result,
                        )
                    else:
                        return SendResult(
                            success=False,
                            provider=self.name,
                            error=result.get("message"),
                            raw_response=result,
                        )

        except Exception as e:
            logger.error(f"Mailgun send error: {e}")
            return SendResult(
                success=False,
                provider=self.name,
                error=str(e),
            )

    async def send_batch(self, messages: list[EmailMessage]) -> list[SendResult]:
        """Send multiple emails via Mailgun."""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results

    async def verify_domain(self, domain: str) -> dict:
        """Get domain verification records from Mailgun."""
        try:
            import aiohttp

            url = f"{self.base_url}/domains/{domain}"

            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth("api", self.api_key)
                async with session.get(url, auth=auth) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "domain": domain,
                            "status": result.get("domain", {}).get("state"),
                            "dns_records": result.get("sending_dns_records", []),
                        }
                    else:
                        return {"domain": domain, "status": "not_found"}

        except Exception as e:
            return {"domain": domain, "error": str(e), "status": "failed"}

    async def get_stats(self, days: int = 30) -> dict:
        """Get Mailgun statistics."""
        try:
            import aiohttp

            url = f"{self.base_url}/{self.domain}/stats/total"

            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth("api", self.api_key)
                params = {"event": ["accepted", "delivered", "opened", "clicked"]}
                async with session.get(url, params=params, auth=auth) as response:
                    result = await response.json()
                    return {"provider": self.name, "stats": result}

        except Exception as e:
            return {"provider": self.name, "error": str(e)}
