"""
API v1 Router Aggregation

Combines all API endpoint routers into a single router.
"""

from fastapi import APIRouter

import logging
_router_logger = logging.getLogger(__name__)

from app.api.v1 import (
    admin,
    affiliates,
    agent_memory,
    agents,
    analytics,
    auth,
    automation,
    blockers,
    brand_deals,
    campaigns,
    co_creation,
    collaborations,
    compliance,
    competitors,
    content,
    contracts,
    developer_keys,
    discovery,
    enterprise,
    explainability,
    feed,
    gpu,
    inbox,
    intake,
    media,
    media_kits,
    moderation,
    notifications,
    operations,
    payments,
    payouts,
    performance,
    podcasts,
    posts,
    privacy,
    profiles,
    push,
    reports,
    repurpose,
    revenue_sharing,
    roi,
    scenarios,
    schedule,
    search,
    smart_reply,
    social,
    social_listening,
    sponsorships,
    subscribers,
    tax,
    testing,
    trends,
    twins,
    viral,
    revenue,
)

api_router = APIRouter()


# Health endpoint for the API version
@api_router.get("/health")
async def api_health() -> dict:
    """API v1 health check."""
    return {"status": "healthy", "api_version": "v1"}


# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(feed.router, prefix="/feed", tags=["Feed"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(discovery.router, prefix="/discover", tags=["Discovery"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(content.router, prefix="/content", tags=["Content"])
api_router.include_router(podcasts.router, prefix="/podcasts", tags=["Podcasts"])
api_router.include_router(twins.router, prefix="/twins", tags=["AI Twins"])
api_router.include_router(social.router, prefix="/social", tags=["Social Integration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])
api_router.include_router(repurpose.router, prefix="/repurpose", tags=["Content Repurposing"])
api_router.include_router(automation.router, prefix="/automation", tags=["Automation"])
api_router.include_router(testing.router, prefix="/tests", tags=["A/B Testing"])
api_router.include_router(trends.router, prefix="/trends", tags=["Trends"])
api_router.include_router(gpu.router, prefix="/gpu", tags=["GPU"])

# Phase 8: Additional Features
api_router.include_router(competitors.router, prefix="/competitors", tags=["Competitor Analysis"])
api_router.include_router(viral.router, prefix="/viral", tags=["Viral Prediction"])
api_router.include_router(brand_deals.router, prefix="/brand-deals", tags=["Brand Deals"])
api_router.include_router(media_kits.router, prefix="/media-kits", tags=["Media Kits"])
api_router.include_router(push.router, prefix="/push", tags=["Push Notifications"])

# Phase 8: Engagement Tools
api_router.include_router(smart_reply.router, prefix="/smart-reply", tags=["Smart Reply"])
api_router.include_router(collaborations.router, prefix="/collaborations", tags=["Collaborations"])

# Phase 8: Monetization Tools
api_router.include_router(affiliates.router, prefix="/affiliates", tags=["Affiliate Links"])

# Phase 8: Email & SMS Campaigns
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(subscribers.router, prefix="/subscribers", tags=["Subscribers"])

# Sprint 17+: Enterprise Features
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["Enterprise"])

# Payments & Subscriptions
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# Creator Payouts
api_router.include_router(payouts.router, prefix="/payouts", tags=["Payouts"])

# Content Moderation
api_router.include_router(moderation.router, prefix="/moderation", tags=["Moderation"])

# FTC Compliance & Brand Safety
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])

# Admin Dashboard
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Search
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# Privacy & GDPR
api_router.include_router(privacy.router, prefix="/privacy", tags=["Privacy"])

# ROI Calculator
api_router.include_router(roi.router, prefix="/roi", tags=["ROI"])

# Performance Monitoring
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])

# Content Scheduling
api_router.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])

# Creator Onboarding (TurboTax-style Intake)
api_router.include_router(intake.router, prefix="/intake", tags=["Intake"])

# AI Agent Crew
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])

# Scenario Universe & Blockers Engine
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(blockers.router, prefix="/blockers", tags=["Blockers"])

# Multi-View Explainability & Audit
api_router.include_router(explainability.router, prefix="/api/v1", tags=["Explainability", "Audit"])

# Revenue Intelligence (Phase 6)
api_router.include_router(revenue.router, tags=["Revenue Intelligence"])

# Agent Memory & Guardrails (Gap Closure)
api_router.include_router(agent_memory.router, tags=["Agent Memory"])

# Content Calendar (Gap Closure)
try:
    from app.api.v1 import calendar
    api_router.include_router(calendar.router, tags=["Calendar"])
except ImportError:
    _router_logger.warning("Calendar routes not loaded — module import failed", exc_info=True)
except Exception as e:
    _router_logger.error(f"Calendar routes failed to load: {e}", exc_info=True)

# ==================== Gap Closure — Real Routes (replacing stubs.py) ====================

# Sponsorship Management (FEAT-052)
api_router.include_router(sponsorships.router, tags=["Sponsorships"])

# Contract Management (FEAT-058/078)
api_router.include_router(contracts.router, tags=["Contracts"])

# Tax Documentation (FEAT-057)
api_router.include_router(tax.router, tags=["Tax"])

# Social Listening (FEAT-048)
api_router.include_router(social_listening.router, tags=["Social Listening"])

# Custom Reporting (FEAT-067)
api_router.include_router(reports.router, tags=["Reports"])

# Compliance & Backups (FEAT-106/108)
api_router.include_router(operations.router, tags=["Operations"])

# Content Co-Creation (FEAT-075)
api_router.include_router(co_creation.router, tags=["Co-Creation"])

# Revenue Sharing (FEAT-076)
api_router.include_router(revenue_sharing.router, tags=["Revenue Sharing"])

# Developer API Keys (FEAT-083)
api_router.include_router(developer_keys.router, tags=["API Keys"])

# Backup Management (Helix Repair D08)
try:
    from app.api.v1 import backups
    api_router.include_router(backups.router, tags=["Backups"])
except ImportError:
    _router_logger.warning("Backups routes not loaded — module import failed", exc_info=True)
except Exception as e:
    _router_logger.error(f"Backups routes failed to load: {e}", exc_info=True)

# Disaster Recovery (Helix Repair D09)
try:
    from app.api.v1 import disaster_recovery
    api_router.include_router(disaster_recovery.router, tags=["Disaster Recovery"])
except ImportError:
    _router_logger.warning("Disaster Recovery routes not loaded — module import failed", exc_info=True)
except Exception as e:
    _router_logger.error(f"Disaster Recovery routes failed to load: {e}", exc_info=True)

