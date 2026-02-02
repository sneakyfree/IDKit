"""
ROI Models

Database models for tracking ROI reports and creator analytics.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class ROIReport(Base):
    """
    Stored ROI report for a creator.
    
    Contains aggregated revenue, costs, and calculated metrics
    for a specific time period.
    """

    __tablename__ = "roi_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), default="monthly")  # daily, weekly, monthly, yearly

    # Revenue breakdown (all in cents)
    total_revenue_cents = Column(Integer, default=0)
    brand_deal_revenue_cents = Column(Integer, default=0)
    affiliate_revenue_cents = Column(Integer, default=0)
    subscription_revenue_cents = Column(Integer, default=0)
    royalty_revenue_cents = Column(Integer, default=0)
    other_revenue_cents = Column(Integer, default=0)

    # Cost breakdown (all in cents)
    total_costs_cents = Column(Integer, default=0)
    platform_fees_cents = Column(Integer, default=0)
    content_creation_costs_cents = Column(Integer, default=0)
    advertising_costs_cents = Column(Integer, default=0)
    software_costs_cents = Column(Integer, default=0)
    other_costs_cents = Column(Integer, default=0)

    # Calculated metrics
    net_profit_cents = Column(Integer, default=0)
    roi_percentage = Column(Float, default=0.0)
    profit_margin = Column(Float, default=0.0)

    # Engagement metrics
    total_views = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)
    new_followers = Column(Integer, default=0)
    content_pieces = Column(Integer, default=0)

    # Derived metrics
    revenue_per_content = Column(Float, default=0.0)  # Cents
    revenue_per_view = Column(Float, default=0.0)  # Cents
    revenue_per_follower = Column(Float, default=0.0)  # Cents
    engagement_rate = Column(Float, default=0.0)  # Percentage

    # Metadata
    calculation_notes = Column(Text, nullable=True)
    raw_data = Column(JSONB, nullable=True)  # Store raw data for recalculation

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_roi_reports_user_id", "user_id"),
        Index("ix_roi_reports_period", "user_id", "period_start", "period_end"),
    )


class CostEntry(Base):
    """
    Manual cost entry for ROI calculations.
    
    Allows creators to track expenses like equipment, software,
    advertising, and other business costs.
    """

    __tablename__ = "cost_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Cost details
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")
    category = Column(String(50), nullable=False)  # equipment, software, advertising, etc.
    description = Column(Text, nullable=True)

    # Date tracking
    expense_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_recurring = Column(Integer, default=0)  # Boolean as int
    recurrence_period = Column(String(20), nullable=True)  # monthly, yearly

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_cost_entries_user_id", "user_id"),
        Index("ix_cost_entries_date", "user_id", "expense_date"),
    )
