"""
Stripe Connect Configuration

Settings for Stripe Connect integration for creator payouts.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class StripeConnectSettings(BaseSettings):
    """Stripe Connect configuration settings."""

    # Connect credentials
    stripe_connect_client_id: str = ""
    stripe_connect_webhook_secret: str = ""

    # Payout settings
    payout_schedule_interval: str = "weekly"
    payout_schedule_day: int = 1  # Monday

    # Platform fee (percentage)
    platform_fee_percent: float = 10.0

    # Minimum payout amount (cents)
    minimum_payout_cents: int = 1000  # $10.00

    class Config:
        env_prefix = "STRIPE_"
        extra = "ignore"


stripe_connect_settings = StripeConnectSettings()
