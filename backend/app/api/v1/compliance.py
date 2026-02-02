"""
FTC Compliance API

Endpoints for checking FTC disclosure compliance and brand safety.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/compliance", tags=["Compliance"])


class FTCCheckRequest(BaseModel):
    """Request to check FTC compliance."""
    content: str
    is_sponsored: bool = False
    platform: str = "instagram"


class FTCCheckResponse(BaseModel):
    """FTC compliance check result."""
    is_compliant: bool
    has_disclosure: bool
    disclosure_position: Optional[int] = None
    issues: list
    warnings: list
    recommendations: list


class BrandSafetyRequest(BaseModel):
    """Request to check brand safety."""
    content: str
    brand_name: str = ""


class BrandSafetyResponse(BaseModel):
    """Brand safety assessment result."""
    safety_score: int
    is_safe: bool
    flags: list
    recommendation: str


class HashtagCheckRequest(BaseModel):
    """Request to check hashtag compliance."""
    content: str
    platform: str = "instagram"


class HashtagCheckResponse(BaseModel):
    """Hashtag check result."""
    hashtag_count: int
    limit: int
    is_compliant: bool
    hashtags: list
    issues: list


# FTC disclosure terms
FTC_DISCLOSURE_TERMS = [
    "#ad", "#sponsored", "#partner", "#paidpartnership",
    "paid partnership", "sponsored by", "in partnership with",
    "#advertisement", "ad:", "sponsored post",
]

# Platform hashtag limits
PLATFORM_HASHTAG_LIMITS = {
    "instagram": 30,
    "tiktok": 100,
    "twitter": 5,
    "youtube": 15,
    "linkedin": 5,
}


@router.post("/ftc/check", response_model=FTCCheckResponse)
async def check_ftc_compliance(
    request: FTCCheckRequest,
    current_user: User = Depends(get_current_user),
) -> FTCCheckResponse:
    """Check content for FTC disclosure compliance."""
    content_lower = request.content.lower()
    
    # Check for disclosure presence
    has_disclosure = any(term in content_lower for term in FTC_DISCLOSURE_TERMS)
    
    # Find disclosure position
    disclosure_position = None
    for term in FTC_DISCLOSURE_TERMS:
        pos = content_lower.find(term)
        if pos != -1:
            disclosure_position = pos
            break

    issues = []
    warnings = []
    
    if request.is_sponsored and not has_disclosure:
        issues.append({
            "type": "missing_disclosure",
            "severity": "critical",
            "message": "Sponsored content must include clear FTC disclosure (#ad, #sponsored, etc.)",
        })
    elif request.is_sponsored and disclosure_position and disclosure_position > 100:
        warnings.append({
            "type": "disclosure_placement",
            "severity": "warning",
            "message": "Disclosure should appear early in the content",
        })

    is_compliant = len(issues) == 0
    
    recommendations = []
    if not is_compliant:
        recommendations = [
            "Use #ad or #sponsored at the start of your caption",
            "Ensure disclosure is visible without clicking 'more'",
            "Verbal disclosure required for video content",
        ]

    return FTCCheckResponse(
        is_compliant=is_compliant,
        has_disclosure=has_disclosure,
        disclosure_position=disclosure_position,
        issues=issues,
        warnings=warnings,
        recommendations=recommendations,
    )


@router.post("/brand-safety/check", response_model=BrandSafetyResponse)
async def check_brand_safety(
    request: BrandSafetyRequest,
    current_user: User = Depends(get_current_user),
) -> BrandSafetyResponse:
    """Assess content for brand safety."""
    content_lower = request.content.lower()
    
    negative_terms = ["controversy", "scandal", "lawsuit", "boycott", "problematic"]
    sensitive_topics = ["politics", "religion", "violence"]
    
    flags = []
    
    for term in negative_terms:
        if term in content_lower:
            flags.append({
                "type": "negative_association",
                "term": term,
                "severity": "high",
            })

    for topic in sensitive_topics:
        if topic in content_lower:
            flags.append({
                "type": "sensitive_topic",
                "term": topic,
                "severity": "medium",
            })

    safety_score = max(0, 100 - len(flags) * 15)

    return BrandSafetyResponse(
        safety_score=safety_score,
        is_safe=safety_score >= 70,
        flags=flags,
        recommendation="Proceed" if safety_score >= 70 else "Review required",
    )


@router.post("/hashtags/check", response_model=HashtagCheckResponse)
async def check_hashtags(
    request: HashtagCheckRequest,
    current_user: User = Depends(get_current_user),
) -> HashtagCheckResponse:
    """Check hashtag usage for platform compliance."""
    import re
    
    hashtags = re.findall(r'#\w+', request.content)
    hashtag_count = len(hashtags)
    
    limit = PLATFORM_HASHTAG_LIMITS.get(request.platform.lower(), 30)
    
    issues = []
    if hashtag_count > limit:
        issues.append({
            "type": "hashtag_limit_exceeded",
            "message": f"{request.platform} limit is {limit}, found {hashtag_count}",
        })

    spam_hashtags = ["#follow4follow", "#f4f", "#like4like", "#l4l"]
    found_spam = [h for h in hashtags if h.lower() in spam_hashtags]
    if found_spam:
        issues.append({
            "type": "spam_hashtags",
            "message": f"Spam hashtags found: {found_spam}",
        })

    return HashtagCheckResponse(
        hashtag_count=hashtag_count,
        limit=limit,
        is_compliant=len(issues) == 0,
        hashtags=hashtags[:30],
        issues=issues,
    )


@router.get("/rules/{platform}")
async def get_platform_rules(
    platform: str,
    current_user: User = Depends(get_current_user),
):
    """Get compliance rules for a specific platform."""
    rules = {
        "instagram": {
            "hashtag_limit": 30,
            "disclosure_required": True,
            "disclosure_formats": ["#ad", "#sponsored", "Paid partnership"],
            "placement_rules": "Must be visible without expanding caption",
        },
        "tiktok": {
            "hashtag_limit": 100,
            "disclosure_required": True,
            "disclosure_formats": ["#ad", "#sponsored", "Branded content toggle"],
            "placement_rules": "Use TikTok's branded content toggle when available",
        },
        "youtube": {
            "hashtag_limit": 15,
            "disclosure_required": True,
            "disclosure_formats": ["Verbal disclosure", "Super Thanks", "Paid promotion checkbox"],
            "placement_rules": "Verbal disclosure in first 30 seconds for videos",
        },
        "twitter": {
            "hashtag_limit": 5,
            "disclosure_required": True,
            "disclosure_formats": ["#ad", "#sponsored"],
            "placement_rules": "Clear and conspicuous in tweet",
        },
    }
    
    return rules.get(platform.lower(), {
        "hashtag_limit": 30,
        "disclosure_required": True,
        "disclosure_formats": ["#ad", "#sponsored"],
        "placement_rules": "Standard FTC guidelines apply",
    })
