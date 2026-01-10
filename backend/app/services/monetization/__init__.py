"""
Monetization Services

Brand deal matching, media kit generation, and affiliate management.
"""

from app.services.monetization.brand_matcher import (
    BrandDealMatcher,
    BrandOpportunity,
    MatchScore,
    BrandProfile,
    DealType,
    DealStatus,
)
from app.services.monetization.media_kit import (
    MediaKitGenerator,
    MediaKit,
    MediaKitSection,
    MediaKitStyle,
)
from app.services.monetization.affiliate_manager import (
    AffiliateLinkManager,
    AffiliateLink,
    AffiliateProgram,
    AffiliateNetwork,
    ClickEvent,
    ConversionEvent,
    LinkStatus,
)

__all__ = [
    # Brand Deals
    "BrandDealMatcher",
    "BrandOpportunity",
    "MatchScore",
    "BrandProfile",
    "DealType",
    "DealStatus",
    # Media Kit
    "MediaKitGenerator",
    "MediaKit",
    "MediaKitSection",
    "MediaKitStyle",
    # Affiliate
    "AffiliateLinkManager",
    "AffiliateLink",
    "AffiliateProgram",
    "AffiliateNetwork",
    "ClickEvent",
    "ConversionEvent",
    "LinkStatus",
]
