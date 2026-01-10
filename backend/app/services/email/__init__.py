"""
Email Service

Production-ready email sending with multiple provider support.
"""

from app.services.email.service import EmailService, email_service
from app.services.email.providers import (
    EmailProvider,
    SESProvider,
    SendGridProvider,
    SMTPProvider,
)

__all__ = [
    "EmailService",
    "email_service",
    "EmailProvider",
    "SESProvider",
    "SendGridProvider",
    "SMTPProvider",
]
