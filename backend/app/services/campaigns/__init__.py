"""
Campaign Services

Email campaigns, SMS campaigns, and subscriber management.
"""

from app.services.campaigns.email_campaign import (
    EmailCampaignBuilder,
    EmailCampaign,
    EmailTemplate,
    EmailRecipient,
    CampaignStatus,
    SendResult,
)
from app.services.campaigns.sms_campaign import (
    SMSCampaignBuilder,
    SMSCampaign,
    SMSTemplate,
    SMSRecipient,
)
from app.services.campaigns.subscriber_manager import (
    SubscriberManager,
    Subscriber,
    SubscriberList,
    SubscriberStatus,
    SubscriptionSource,
)

__all__ = [
    # Email
    "EmailCampaignBuilder",
    "EmailCampaign",
    "EmailTemplate",
    "EmailRecipient",
    "CampaignStatus",
    "SendResult",
    # SMS
    "SMSCampaignBuilder",
    "SMSCampaign",
    "SMSTemplate",
    "SMSRecipient",
    # Subscribers
    "SubscriberManager",
    "Subscriber",
    "SubscriberList",
    "SubscriberStatus",
    "SubscriptionSource",
]
