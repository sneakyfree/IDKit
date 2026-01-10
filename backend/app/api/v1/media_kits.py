"""
Media Kit API Endpoints

REST API for media kit generation and management.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------

class SocialStatRequest(BaseModel):
    """Social stats for a platform."""
    platform: str
    username: str
    profile_url: str = ""
    follower_count: int = 0
    engagement_rate: float = 0.0
    avg_likes: int = 0
    avg_comments: int = 0
    avg_views: int = 0


class DemographicsRequest(BaseModel):
    """Audience demographics."""
    age_breakdown: dict[str, float] = Field(default_factory=dict)
    gender_breakdown: dict[str, float] = Field(default_factory=dict)
    top_locations: dict[str, float] = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)


class RateCardRequest(BaseModel):
    """Rate card item."""
    platform: str
    content_type: str
    rate: float
    currency: str = "USD"
    description: Optional[str] = None
    includes: list[str] = Field(default_factory=list)


class CollaborationRequest(BaseModel):
    """Past collaboration."""
    brand_name: str
    brand_logo_url: Optional[str] = None
    description: Optional[str] = None
    results: Optional[str] = None


class MediaKitContentRequest(BaseModel):
    """Content for media kit generation."""
    display_name: str
    username: str
    tagline: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    niches: list[str] = Field(default_factory=list)
    social_stats: list[SocialStatRequest] = Field(default_factory=list)
    demographics: Optional[DemographicsRequest] = None
    rate_cards: list[RateCardRequest] = Field(default_factory=list)
    collaborations: list[CollaborationRequest] = Field(default_factory=list)


class ColorsRequest(BaseModel):
    """Custom color scheme."""
    primary: str = "#6366F1"
    secondary: str = "#EC4899"
    accent: str = "#10B981"
    background: str = "#FFFFFF"
    text: str = "#1F2937"


class MediaKitGenerateRequest(BaseModel):
    """Request to generate media kit."""
    content: MediaKitContentRequest
    style: str = "minimal"
    custom_colors: Optional[ColorsRequest] = None
    sections: Optional[list[str]] = None


class MediaKitResponse(BaseModel):
    """Media kit response."""
    kit_id: str
    user_id: str
    style: str
    sections: list[str]
    pdf_url: Optional[str] = None
    web_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int


class StylePresetResponse(BaseModel):
    """Style preset info."""
    id: str
    name: str
    colors: dict


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.post("", response_model=MediaKitResponse)
async def generate_media_kit(
    request: MediaKitGenerateRequest,
):
    """
    Generate a new media kit.

    Create a professional media kit from provided content.
    """
    from app.services.monetization import (
        MediaKitGenerator,
        MediaKit,
        MediaKitStyle,
        MediaKitSection,
    )
    from app.services.monetization.media_kit import (
        MediaKitContent,
        MediaKitColors,
        SocialStats,
        AudienceDemographics,
        RateCard,
        CollaborationExample,
    )

    generator = MediaKitGenerator()

    # Build content
    content = MediaKitContent(
        display_name=request.content.display_name,
        username=request.content.username,
        tagline=request.content.tagline,
        bio=request.content.bio,
        profile_image_url=request.content.profile_image_url,
        cover_image_url=request.content.cover_image_url,
        email=request.content.email,
        website=request.content.website,
        location=request.content.location,
        niches=request.content.niches,
    )

    # Add social stats
    for stat in request.content.social_stats:
        content.social_stats.append(SocialStats(
            platform=stat.platform,
            username=stat.username,
            profile_url=stat.profile_url,
            follower_count=stat.follower_count,
            engagement_rate=stat.engagement_rate,
            avg_likes=stat.avg_likes,
            avg_comments=stat.avg_comments,
            avg_views=stat.avg_views,
        ))

    # Add demographics
    if request.content.demographics:
        demo = request.content.demographics
        content.demographics = AudienceDemographics(
            age_breakdown=demo.age_breakdown,
            gender_breakdown=demo.gender_breakdown,
            top_locations=demo.top_locations,
            interests=demo.interests,
        )

    # Add rate cards
    for rate in request.content.rate_cards:
        content.rate_cards.append(RateCard(
            platform=rate.platform,
            content_type=rate.content_type,
            rate=rate.rate,
            currency=rate.currency,
            description=rate.description,
            includes=rate.includes,
        ))

    # Add collaborations
    for collab in request.content.collaborations:
        content.past_collaborations.append(CollaborationExample(
            brand_name=collab.brand_name,
            brand_logo_url=collab.brand_logo_url,
            description=collab.description,
            results=collab.results,
        ))

    # Parse style
    try:
        style = MediaKitStyle(request.style)
    except ValueError:
        style = MediaKitStyle.MINIMAL

    # Parse custom colors
    custom_colors = None
    if request.custom_colors:
        custom_colors = MediaKitColors(
            primary=request.custom_colors.primary,
            secondary=request.custom_colors.secondary,
            accent=request.custom_colors.accent,
            background=request.custom_colors.background,
            text=request.custom_colors.text,
        )

    # Parse sections
    sections = None
    if request.sections:
        sections = [MediaKitSection(s) for s in request.sections]

    # Generate kit
    kit = await generator.generate(
        user_id="current_user",
        content=content,
        style=style,
        custom_colors=custom_colors,
        sections=sections,
    )

    return MediaKitResponse(
        kit_id=kit.kit_id,
        user_id=kit.user_id,
        style=kit.style.value,
        sections=[s.value for s in kit.sections],
        pdf_url=kit.pdf_url,
        web_url=kit.web_url,
        thumbnail_url=kit.thumbnail_url,
        created_at=kit.created_at,
        updated_at=kit.updated_at,
        version=kit.version,
    )


@router.post("/auto-generate", response_model=MediaKitResponse)
async def auto_generate_media_kit(
    style: str = Query(default="minimal"),
):
    """
    Auto-generate media kit from connected accounts.

    Pulls data from analytics and profile automatically.
    """
    from app.services.monetization import MediaKitGenerator, MediaKitStyle

    generator = MediaKitGenerator()

    # Mock profile and analytics data
    profile_data = {
        "display_name": "Demo Creator",
        "username": "democreator",
        "tagline": "Creating content that inspires",
        "bio": "Digital creator passionate about sharing stories and connecting with people.",
        "avatar_url": "https://example.com/avatar.jpg",
        "email": "demo@example.com",
        "website": "https://example.com",
        "location": "Los Angeles, CA",
        "niches": ["lifestyle", "tech", "travel"],
        "rates": [
            {"platform": "instagram", "content_type": "post", "rate": 500},
            {"platform": "instagram", "content_type": "reel", "rate": 750},
            {"platform": "tiktok", "content_type": "video", "rate": 600},
        ],
        "collaborations": [
            {"brand_name": "TechBrand", "description": "Product launch campaign"},
            {"brand_name": "TravelCo", "description": "Destination series"},
        ],
    }

    analytics_data = {
        "platforms": {
            "instagram": {
                "username": "democreator",
                "profile_url": "https://instagram.com/democreator",
                "follower_count": 150000,
                "engagement_rate": 4.5,
                "avg_likes": 6000,
                "avg_comments": 200,
            },
            "tiktok": {
                "username": "democreator",
                "profile_url": "https://tiktok.com/@democreator",
                "follower_count": 250000,
                "engagement_rate": 6.2,
                "avg_views": 50000,
            },
        },
        "demographics": {
            "age": {"18-24": 35, "25-34": 45, "35-44": 15, "45+": 5},
            "gender": {"female": 62, "male": 36, "other": 2},
            "locations": {"United States": 45, "United Kingdom": 15, "Canada": 10},
            "interests": ["Technology", "Travel", "Fashion", "Photography"],
        },
    }

    try:
        kit_style = MediaKitStyle(style)
    except ValueError:
        kit_style = MediaKitStyle.MINIMAL

    kit = await generator.generate_from_profile(
        user_id="current_user",
        profile_data=profile_data,
        analytics_data=analytics_data,
        style=kit_style,
    )

    return MediaKitResponse(
        kit_id=kit.kit_id,
        user_id=kit.user_id,
        style=kit.style.value,
        sections=[s.value for s in kit.sections],
        pdf_url=kit.pdf_url,
        web_url=kit.web_url,
        thumbnail_url=kit.thumbnail_url,
        created_at=kit.created_at,
        updated_at=kit.updated_at,
        version=kit.version,
    )


@router.get("/{kit_id}", response_model=MediaKitResponse)
async def get_media_kit(
    kit_id: str,
):
    """Get a media kit by ID."""
    # In production, fetch from database
    raise HTTPException(status_code=404, detail="Media kit not found")


@router.put("/{kit_id}", response_model=MediaKitResponse)
async def update_media_kit(
    kit_id: str,
    updates: dict,
):
    """Update an existing media kit."""
    # In production, update in database
    raise HTTPException(status_code=404, detail="Media kit not found")


@router.delete("/{kit_id}")
async def delete_media_kit(
    kit_id: str,
):
    """Delete a media kit."""
    # In production, delete from database
    return {"deleted": True, "kit_id": kit_id}


@router.get("/{kit_id}/pdf")
async def download_pdf(
    kit_id: str,
):
    """Download media kit as PDF."""
    from app.services.monetization import MediaKitGenerator

    generator = MediaKitGenerator()
    pdf_bytes = await generator.export_pdf(kit_id)

    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not available")

    # In production, return FileResponse
    return {"message": "PDF download", "kit_id": kit_id}


@router.post("/{kit_id}/share")
async def get_share_link(
    kit_id: str,
    expires_hours: int = Query(default=168, ge=1, le=720),
):
    """Get shareable link for media kit."""
    from app.services.monetization import MediaKitGenerator

    generator = MediaKitGenerator()
    share_link = await generator.get_share_link(kit_id, expires_hours)

    return {
        "share_link": share_link,
        "expires_in_hours": expires_hours,
    }


@router.get("/styles/presets", response_model=list[StylePresetResponse])
async def get_style_presets():
    """Get available style presets."""
    from app.services.monetization import MediaKitGenerator

    generator = MediaKitGenerator()
    styles = generator.get_available_styles()

    return [StylePresetResponse(**s) for s in styles]


@router.get("/sections/available")
async def get_available_sections():
    """Get list of available sections for media kits."""
    from app.services.monetization.media_kit import MediaKitSection

    return {
        "sections": [
            {
                "id": s.value,
                "name": s.value.replace("_", " ").title(),
                "description": _get_section_description(s),
            }
            for s in MediaKitSection
        ]
    }


def _get_section_description(section) -> str:
    """Get description for section."""
    from app.services.monetization.media_kit import MediaKitSection

    descriptions = {
        MediaKitSection.COVER: "Header with profile image and name",
        MediaKitSection.BIO: "About me and niche tags",
        MediaKitSection.STATS: "Follower counts and engagement",
        MediaKitSection.AUDIENCE: "Audience overview",
        MediaKitSection.DEMOGRAPHICS: "Age, gender, location breakdown",
        MediaKitSection.CONTENT: "Featured content samples",
        MediaKitSection.COLLABORATIONS: "Past brand partnerships",
        MediaKitSection.TESTIMONIALS: "Brand testimonials",
        MediaKitSection.RATES: "Pricing and rate cards",
        MediaKitSection.CONTACT: "Contact information",
        MediaKitSection.GALLERY: "Content gallery",
    }
    return descriptions.get(section, "")
