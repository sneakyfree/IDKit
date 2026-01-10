"""
Media Kit Generator Service

Generates professional media kits for influencers.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MediaKitStyle(str, Enum):
    """Visual style presets for media kits."""
    MINIMAL = "minimal"
    BOLD = "bold"
    ELEGANT = "elegant"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    DARK = "dark"
    LIGHT = "light"


class MediaKitSection(str, Enum):
    """Sections available in a media kit."""
    COVER = "cover"
    BIO = "bio"
    STATS = "stats"
    AUDIENCE = "audience"
    DEMOGRAPHICS = "demographics"
    CONTENT = "content"
    COLLABORATIONS = "collaborations"
    TESTIMONIALS = "testimonials"
    RATES = "rates"
    CONTACT = "contact"
    GALLERY = "gallery"


@dataclass
class MediaKitColors:
    """Color scheme for media kit."""
    primary: str = "#6366F1"  # Indigo
    secondary: str = "#EC4899"  # Pink
    accent: str = "#10B981"  # Green
    background: str = "#FFFFFF"
    text: str = "#1F2937"
    text_secondary: str = "#6B7280"


@dataclass
class SocialStats:
    """Social media statistics for a platform."""
    platform: str
    username: str
    profile_url: str
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    engagement_rate: float = 0.0
    avg_likes: int = 0
    avg_comments: int = 0
    avg_views: int = 0
    growth_rate: float = 0.0  # Monthly growth %


@dataclass
class AudienceDemographics:
    """Audience demographics data."""
    age_breakdown: dict[str, float] = field(default_factory=dict)
    # e.g., {"18-24": 35, "25-34": 45, "35-44": 15, "45+": 5}

    gender_breakdown: dict[str, float] = field(default_factory=dict)
    # e.g., {"female": 65, "male": 33, "other": 2}

    top_locations: dict[str, float] = field(default_factory=dict)
    # e.g., {"United States": 45, "United Kingdom": 15, "Canada": 10}

    top_cities: list[str] = field(default_factory=list)

    interests: list[str] = field(default_factory=list)

    active_hours: dict[str, float] = field(default_factory=dict)
    # e.g., {"morning": 20, "afternoon": 30, "evening": 40, "night": 10}


@dataclass
class CollaborationExample:
    """Past collaboration example."""
    brand_name: str
    brand_logo_url: Optional[str] = None
    campaign_name: Optional[str] = None
    description: Optional[str] = None
    results: Optional[str] = None
    content_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    date: Optional[str] = None


@dataclass
class Testimonial:
    """Brand testimonial."""
    brand_name: str
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    quote: str = ""
    rating: Optional[int] = None  # 1-5


@dataclass
class RateCard:
    """Rate card for services."""
    platform: str
    content_type: str  # post, story, video, etc.
    rate: float
    currency: str = "USD"
    description: Optional[str] = None
    includes: list[str] = field(default_factory=list)


@dataclass
class MediaKitContent:
    """Content for a media kit."""
    # Creator info
    display_name: str
    username: str
    tagline: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None

    # Contact
    email: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    # Niches/categories
    niches: list[str] = field(default_factory=list)
    content_types: list[str] = field(default_factory=list)

    # Social stats
    social_stats: list[SocialStats] = field(default_factory=list)
    total_reach: int = 0
    total_engagement: int = 0

    # Demographics
    demographics: Optional[AudienceDemographics] = None

    # Content samples
    featured_content: list[dict] = field(default_factory=list)
    # [{"url": "...", "thumbnail": "...", "type": "video", "views": 1000000}]

    # Collaborations
    past_collaborations: list[CollaborationExample] = field(default_factory=list)
    brand_logos: list[str] = field(default_factory=list)  # URLs

    # Testimonials
    testimonials: list[Testimonial] = field(default_factory=list)

    # Rates
    rate_cards: list[RateCard] = field(default_factory=list)


@dataclass
class MediaKit:
    """Generated media kit."""
    kit_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    content: Optional[MediaKitContent] = None

    # Style configuration
    style: MediaKitStyle = MediaKitStyle.MINIMAL
    colors: MediaKitColors = field(default_factory=MediaKitColors)
    font_family: str = "Inter"

    # Sections to include
    sections: list[MediaKitSection] = field(default_factory=lambda: [
        MediaKitSection.COVER,
        MediaKitSection.BIO,
        MediaKitSection.STATS,
        MediaKitSection.AUDIENCE,
        MediaKitSection.CONTENT,
        MediaKitSection.RATES,
        MediaKitSection.CONTACT,
    ])

    # Generated outputs
    pdf_url: Optional[str] = None
    web_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


class MediaKitGenerator:
    """
    Generates professional media kits for influencers.

    Features:
    - Multiple style templates
    - Auto-populated from analytics
    - PDF and web export
    - Custom branding
    - Rate card management
    """

    STYLE_CONFIGS = {
        MediaKitStyle.MINIMAL: {
            "font_family": "Inter",
            "colors": MediaKitColors(
                primary="#1F2937",
                secondary="#6B7280",
                accent="#3B82F6",
                background="#FFFFFF",
                text="#1F2937",
                text_secondary="#6B7280",
            ),
        },
        MediaKitStyle.BOLD: {
            "font_family": "Poppins",
            "colors": MediaKitColors(
                primary="#7C3AED",
                secondary="#EC4899",
                accent="#F59E0B",
                background="#FFFFFF",
                text="#1F2937",
                text_secondary="#6B7280",
            ),
        },
        MediaKitStyle.ELEGANT: {
            "font_family": "Playfair Display",
            "colors": MediaKitColors(
                primary="#1F2937",
                secondary="#B8860B",
                accent="#B8860B",
                background="#FEFEFE",
                text="#1F2937",
                text_secondary="#4B5563",
            ),
        },
        MediaKitStyle.PLAYFUL: {
            "font_family": "Nunito",
            "colors": MediaKitColors(
                primary="#F472B6",
                secondary="#34D399",
                accent="#FBBF24",
                background="#FFF7ED",
                text="#1F2937",
                text_secondary="#6B7280",
            ),
        },
        MediaKitStyle.PROFESSIONAL: {
            "font_family": "Roboto",
            "colors": MediaKitColors(
                primary="#1E40AF",
                secondary="#3B82F6",
                accent="#059669",
                background="#FFFFFF",
                text="#111827",
                text_secondary="#4B5563",
            ),
        },
        MediaKitStyle.DARK: {
            "font_family": "Inter",
            "colors": MediaKitColors(
                primary="#8B5CF6",
                secondary="#EC4899",
                accent="#10B981",
                background="#111827",
                text="#F9FAFB",
                text_secondary="#9CA3AF",
            ),
        },
    }

    def __init__(
        self,
        storage_client: Optional[Any] = None,
        pdf_generator: Optional[Any] = None,
    ):
        """
        Initialize media kit generator.

        Args:
            storage_client: Storage client for file uploads
            pdf_generator: PDF generation service
        """
        self.storage_client = storage_client
        self.pdf_generator = pdf_generator

    async def generate(
        self,
        user_id: str,
        content: MediaKitContent,
        style: MediaKitStyle = MediaKitStyle.MINIMAL,
        custom_colors: Optional[MediaKitColors] = None,
        sections: Optional[list[MediaKitSection]] = None,
    ) -> MediaKit:
        """
        Generate a media kit.

        Args:
            user_id: User ID
            content: Media kit content
            style: Visual style preset
            custom_colors: Optional custom color scheme
            sections: Sections to include

        Returns:
            Generated media kit
        """
        # Get style configuration
        style_config = self.STYLE_CONFIGS.get(style, self.STYLE_CONFIGS[MediaKitStyle.MINIMAL])

        # Create media kit
        kit = MediaKit(
            user_id=user_id,
            content=content,
            style=style,
            colors=custom_colors or style_config["colors"],
            font_family=style_config["font_family"],
            sections=sections or [
                MediaKitSection.COVER,
                MediaKitSection.BIO,
                MediaKitSection.STATS,
                MediaKitSection.AUDIENCE,
                MediaKitSection.CONTENT,
                MediaKitSection.RATES,
                MediaKitSection.CONTACT,
            ],
        )

        # Calculate totals
        kit.content.total_reach = sum(s.follower_count for s in content.social_stats)

        # Generate outputs
        kit.web_url = f"/media-kit/{kit.kit_id}"

        # Generate PDF (async in production)
        if self.pdf_generator:
            kit.pdf_url = await self._generate_pdf(kit)

        # Generate thumbnail
        kit.thumbnail_url = await self._generate_thumbnail(kit)

        return kit

    async def generate_from_profile(
        self,
        user_id: str,
        profile_data: dict,
        analytics_data: dict,
        style: MediaKitStyle = MediaKitStyle.MINIMAL,
    ) -> MediaKit:
        """
        Generate media kit automatically from profile and analytics.

        Args:
            user_id: User ID
            profile_data: User profile data
            analytics_data: Analytics data from all platforms
            style: Visual style

        Returns:
            Generated media kit
        """
        # Build content from data
        content = MediaKitContent(
            display_name=profile_data.get("display_name", ""),
            username=profile_data.get("username", ""),
            tagline=profile_data.get("tagline"),
            bio=profile_data.get("bio"),
            profile_image_url=profile_data.get("avatar_url"),
            cover_image_url=profile_data.get("cover_image_url"),
            email=profile_data.get("email"),
            website=profile_data.get("website"),
            location=profile_data.get("location"),
            niches=profile_data.get("niches", []),
        )

        # Add social stats
        for platform, data in analytics_data.get("platforms", {}).items():
            content.social_stats.append(SocialStats(
                platform=platform,
                username=data.get("username", ""),
                profile_url=data.get("profile_url", ""),
                follower_count=data.get("follower_count", 0),
                engagement_rate=data.get("engagement_rate", 0),
                avg_likes=data.get("avg_likes", 0),
                avg_comments=data.get("avg_comments", 0),
                avg_views=data.get("avg_views", 0),
                growth_rate=data.get("growth_rate", 0),
            ))

        # Add demographics
        demo_data = analytics_data.get("demographics", {})
        if demo_data:
            content.demographics = AudienceDemographics(
                age_breakdown=demo_data.get("age", {}),
                gender_breakdown=demo_data.get("gender", {}),
                top_locations=demo_data.get("locations", {}),
                top_cities=demo_data.get("cities", []),
                interests=demo_data.get("interests", []),
            )

        # Add featured content
        content.featured_content = analytics_data.get("top_content", [])[:6]

        # Add past collaborations
        for collab in profile_data.get("collaborations", []):
            content.past_collaborations.append(CollaborationExample(
                brand_name=collab.get("brand_name", ""),
                brand_logo_url=collab.get("brand_logo"),
                description=collab.get("description"),
                results=collab.get("results"),
            ))

        # Add rates
        for rate in profile_data.get("rates", []):
            content.rate_cards.append(RateCard(
                platform=rate.get("platform", ""),
                content_type=rate.get("content_type", ""),
                rate=rate.get("rate", 0),
                currency=rate.get("currency", "USD"),
                description=rate.get("description"),
                includes=rate.get("includes", []),
            ))

        return await self.generate(user_id, content, style)

    async def update(
        self,
        kit: MediaKit,
        updates: dict,
    ) -> MediaKit:
        """
        Update an existing media kit.

        Args:
            kit: Existing media kit
            updates: Fields to update

        Returns:
            Updated media kit
        """
        # Update content
        if "content" in updates:
            for key, value in updates["content"].items():
                if hasattr(kit.content, key):
                    setattr(kit.content, key, value)

        # Update style
        if "style" in updates:
            kit.style = MediaKitStyle(updates["style"])
            style_config = self.STYLE_CONFIGS.get(kit.style)
            if style_config:
                kit.colors = style_config["colors"]
                kit.font_family = style_config["font_family"]

        # Update colors
        if "colors" in updates:
            kit.colors = MediaKitColors(**updates["colors"])

        # Update sections
        if "sections" in updates:
            kit.sections = [MediaKitSection(s) for s in updates["sections"]]

        kit.updated_at = datetime.utcnow()
        kit.version += 1

        # Regenerate outputs
        if self.pdf_generator:
            kit.pdf_url = await self._generate_pdf(kit)

        return kit

    async def _generate_pdf(self, kit: MediaKit) -> Optional[str]:
        """Generate PDF version of media kit."""
        if not self.pdf_generator:
            return None

        try:
            # Convert to HTML
            html_content = self._render_html(kit)

            # Generate PDF
            pdf_bytes = await self.pdf_generator.html_to_pdf(html_content)

            # Upload to storage
            if self.storage_client:
                url = await self.storage_client.upload(
                    pdf_bytes,
                    f"media-kits/{kit.kit_id}/kit.pdf",
                    content_type="application/pdf",
                )
                return url

            return None
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None

    async def _generate_thumbnail(self, kit: MediaKit) -> Optional[str]:
        """Generate thumbnail preview of media kit."""
        # In production, this would generate an image preview
        return f"/api/v1/media-kits/{kit.kit_id}/thumbnail"

    def _render_html(self, kit: MediaKit) -> str:
        """Render media kit as HTML."""
        content = kit.content
        colors = kit.colors

        # Basic HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{content.display_name} - Media Kit</title>
            <link href="https://fonts.googleapis.com/css2?family={kit.font_family.replace(' ', '+')}&display=swap" rel="stylesheet">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: '{kit.font_family}', sans-serif;
                    background: {colors.background};
                    color: {colors.text};
                    line-height: 1.6;
                }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
                .header {{
                    text-align: center;
                    padding: 60px 0;
                    background: linear-gradient(135deg, {colors.primary}, {colors.secondary});
                    color: white;
                    border-radius: 16px;
                    margin-bottom: 40px;
                }}
                .profile-image {{
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    border: 4px solid white;
                    margin-bottom: 20px;
                }}
                h1 {{ font-size: 2.5rem; margin-bottom: 8px; }}
                .tagline {{ font-size: 1.2rem; opacity: 0.9; }}
                .section {{
                    background: white;
                    border-radius: 12px;
                    padding: 30px;
                    margin-bottom: 24px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                }}
                .section-title {{
                    font-size: 1.25rem;
                    color: {colors.primary};
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid {colors.primary};
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                }}
                .stat-card {{
                    text-align: center;
                    padding: 20px;
                    background: {colors.background};
                    border-radius: 8px;
                }}
                .stat-value {{
                    font-size: 2rem;
                    font-weight: bold;
                    color: {colors.primary};
                }}
                .stat-label {{
                    color: {colors.text_secondary};
                    font-size: 0.875rem;
                }}
                .niches {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 16px;
                }}
                .niche-tag {{
                    background: {colors.primary};
                    color: white;
                    padding: 6px 16px;
                    border-radius: 20px;
                    font-size: 0.875rem;
                }}
                .contact-info {{
                    display: grid;
                    gap: 12px;
                }}
                .contact-item {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
        """

        # Cover section
        if MediaKitSection.COVER in kit.sections:
            html += f"""
                <div class="header">
                    {f'<img src="{content.profile_image_url}" class="profile-image" />' if content.profile_image_url else ''}
                    <h1>{content.display_name}</h1>
                    {f'<p class="tagline">{content.tagline}</p>' if content.tagline else ''}
                </div>
            """

        # Bio section
        if MediaKitSection.BIO in kit.sections and content.bio:
            html += f"""
                <div class="section">
                    <h2 class="section-title">About Me</h2>
                    <p>{content.bio}</p>
                    <div class="niches">
                        {''.join(f'<span class="niche-tag">{niche}</span>' for niche in content.niches)}
                    </div>
                </div>
            """

        # Stats section
        if MediaKitSection.STATS in kit.sections and content.social_stats:
            total_followers = sum(s.follower_count for s in content.social_stats)
            avg_engagement = sum(s.engagement_rate for s in content.social_stats) / len(content.social_stats)

            html += f"""
                <div class="section">
                    <h2 class="section-title">Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">{self._format_number(total_followers)}</div>
                            <div class="stat-label">Total Followers</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{avg_engagement:.1f}%</div>
                            <div class="stat-label">Avg Engagement</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{len(content.social_stats)}</div>
                            <div class="stat-label">Platforms</div>
                        </div>
                    </div>
                </div>
            """

        # Rates section
        if MediaKitSection.RATES in kit.sections and content.rate_cards:
            html += f"""
                <div class="section">
                    <h2 class="section-title">Rates</h2>
                    <div class="stats-grid">
            """
            for rate in content.rate_cards[:6]:
                html += f"""
                        <div class="stat-card">
                            <div class="stat-value">${rate.rate:,.0f}</div>
                            <div class="stat-label">{rate.platform.title()} {rate.content_type.title()}</div>
                        </div>
                """
            html += """
                    </div>
                </div>
            """

        # Contact section
        if MediaKitSection.CONTACT in kit.sections:
            html += f"""
                <div class="section">
                    <h2 class="section-title">Contact</h2>
                    <div class="contact-info">
                        {f'<div class="contact-item">📧 {content.email}</div>' if content.email else ''}
                        {f'<div class="contact-item">🌐 {content.website}</div>' if content.website else ''}
                        {f'<div class="contact-item">📍 {content.location}</div>' if content.location else ''}
                    </div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html

    def _format_number(self, num: int) -> str:
        """Format large numbers with K/M suffix."""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)

    async def export_pdf(self, kit_id: str) -> Optional[bytes]:
        """Export media kit as PDF bytes."""
        # In production, fetch from storage or regenerate
        return None

    async def get_share_link(self, kit_id: str, expires_hours: int = 168) -> str:
        """Generate shareable link for media kit."""
        return f"/media-kit/{kit_id}?share=true"

    def get_available_styles(self) -> list[dict]:
        """Get list of available style presets."""
        return [
            {
                "id": style.value,
                "name": style.value.replace("_", " ").title(),
                "colors": {
                    "primary": config["colors"].primary,
                    "secondary": config["colors"].secondary,
                    "accent": config["colors"].accent,
                },
            }
            for style, config in self.STYLE_CONFIGS.items()
        ]
