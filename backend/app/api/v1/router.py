"""
API v1 Router Aggregation

Combines all API endpoint routers into a single router.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    affiliates,
    analytics,
    auth,
    automation,
    brand_deals,
    campaigns,
    collaborations,
    competitors,
    content,
    discovery,
    enterprise,
    feed,
    gpu,
    inbox,
    media,
    media_kits,
    moderation,
    notifications,
    payments,
    podcasts,
    posts,
    privacy,
    profiles,
    push,
    repurpose,
    search,
    smart_reply,
    social,
    subscribers,
    testing,
    trends,
    twins,
    viral,
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

# Content Moderation
api_router.include_router(moderation.router, prefix="/moderation", tags=["Moderation"])

# Admin Dashboard
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Search
api_router.include_router(search.router, prefix="/search", tags=["Search"])

# Privacy & GDPR
api_router.include_router(privacy.router, prefix="/privacy", tags=["Privacy"])
