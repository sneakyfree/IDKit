"""
Affiliate Link Manager Service

Manage affiliate links, track clicks and conversions,
and optimize affiliate marketing campaigns.
"""

import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse


class AffiliateNetwork(str, Enum):
    """Supported affiliate networks."""
    AMAZON = "amazon"
    SHAREASALE = "shareasale"
    CJ_AFFILIATE = "cj_affiliate"
    RAKUTEN = "rakuten"
    IMPACT = "impact"
    PARTNERIZE = "partnerize"
    AWIN = "awin"
    CLICKBANK = "clickbank"
    CUSTOM = "custom"


class LinkStatus(str, Enum):
    """Status of affiliate links."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    BROKEN = "broken"


@dataclass
class AffiliateProgram:
    """Affiliate program configuration."""
    program_id: str
    user_id: str
    network: AffiliateNetwork
    program_name: str
    affiliate_id: str
    tracking_param: str = "ref"
    commission_rate: float = 0.0
    commission_type: str = "percentage"  # 'percentage' or 'flat'
    cookie_days: int = 30
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AffiliateLink:
    """An affiliate link with tracking."""
    link_id: str
    user_id: str
    program_id: str
    original_url: str
    affiliate_url: str
    short_url: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    product_name: Optional[str] = None
    product_image_url: Optional[str] = None
    product_price: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    status: LinkStatus = LinkStatus.ACTIVE
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    last_clicked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ClickEvent:
    """A click event on an affiliate link."""
    click_id: str
    link_id: str
    user_id: str
    timestamp: datetime
    ip_hash: str  # Hashed for privacy
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    device_type: Optional[str] = None
    platform: Optional[str] = None  # Where the link was shared
    converted: bool = False
    conversion_value: float = 0.0


@dataclass
class ConversionEvent:
    """A conversion (sale) event."""
    conversion_id: str
    link_id: str
    click_id: Optional[str]
    user_id: str
    timestamp: datetime
    order_id: Optional[str] = None
    order_value: float = 0.0
    commission: float = 0.0
    status: str = "pending"  # 'pending', 'approved', 'rejected'
    network_data: Dict[str, Any] = field(default_factory=dict)


class AffiliateLinkManager:
    """
    Affiliate link management and tracking service.

    Features:
    - Multi-network affiliate program management
    - Link creation with automatic tagging
    - Click and conversion tracking
    - Short URL generation
    - Performance analytics
    - Link health monitoring
    """

    # Network-specific URL patterns
    NETWORK_PATTERNS = {
        AffiliateNetwork.AMAZON: {
            "domain": "amazon.com",
            "param": "tag",
            "format": "{url}?tag={affiliate_id}",
        },
        AffiliateNetwork.SHAREASALE: {
            "domain": "shareasale.com",
            "param": "afftrack",
            "format": "https://shareasale.com/r.cfm?b={merchant_id}&u={affiliate_id}&m={merchant_id}&urllink={url}",
        },
        AffiliateNetwork.IMPACT: {
            "domain": "impact.com",
            "param": "subId1",
        },
    }

    def __init__(self):
        self._programs: Dict[str, AffiliateProgram] = {}
        self._links: Dict[str, AffiliateLink] = {}
        self._clicks: List[ClickEvent] = []
        self._conversions: List[ConversionEvent] = []

    # =========================================================================
    # PROGRAM MANAGEMENT
    # =========================================================================

    async def create_program(
        self,
        user_id: str,
        network: AffiliateNetwork,
        program_name: str,
        affiliate_id: str,
        tracking_param: Optional[str] = None,
        commission_rate: float = 0.0,
        commission_type: str = "percentage",
        cookie_days: int = 30,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> AffiliateProgram:
        """
        Register a new affiliate program.
        """
        program = AffiliateProgram(
            program_id=str(uuid.uuid4()),
            user_id=user_id,
            network=network,
            program_name=program_name,
            affiliate_id=affiliate_id,
            tracking_param=tracking_param or self._get_default_param(network),
            commission_rate=commission_rate,
            commission_type=commission_type,
            cookie_days=cookie_days,
            api_key=api_key,
            api_secret=api_secret,
        )

        self._programs[program.program_id] = program
        return program

    async def get_programs(
        self,
        user_id: str,
        active_only: bool = True,
    ) -> List[AffiliateProgram]:
        """Get all affiliate programs for a user."""
        programs = [
            p for p in self._programs.values()
            if p.user_id == user_id
        ]

        if active_only:
            programs = [p for p in programs if p.is_active]

        return programs

    async def update_program(
        self,
        user_id: str,
        program_id: str,
        **updates,
    ) -> Optional[AffiliateProgram]:
        """Update an affiliate program."""
        program = self._programs.get(program_id)
        if not program or program.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(program, key):
                setattr(program, key, value)

        return program

    async def delete_program(
        self,
        user_id: str,
        program_id: str,
    ) -> bool:
        """Delete an affiliate program."""
        program = self._programs.get(program_id)
        if not program or program.user_id != user_id:
            return False

        del self._programs[program_id]
        return True

    def _get_default_param(self, network: AffiliateNetwork) -> str:
        """Get default tracking parameter for a network."""
        defaults = {
            AffiliateNetwork.AMAZON: "tag",
            AffiliateNetwork.SHAREASALE: "afftrack",
            AffiliateNetwork.CJ_AFFILIATE: "sid",
            AffiliateNetwork.RAKUTEN: "u1",
            AffiliateNetwork.IMPACT: "subId1",
            AffiliateNetwork.PARTNERIZE: "pubref",
            AffiliateNetwork.AWIN: "clickref",
            AffiliateNetwork.CLICKBANK: "tid",
            AffiliateNetwork.CUSTOM: "ref",
        }
        return defaults.get(network, "ref")

    # =========================================================================
    # LINK MANAGEMENT
    # =========================================================================

    async def create_link(
        self,
        user_id: str,
        program_id: str,
        original_url: str,
        title: str = "",
        description: Optional[str] = None,
        product_name: Optional[str] = None,
        product_image_url: Optional[str] = None,
        product_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        custom_tracking_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        generate_short_url: bool = True,
    ) -> AffiliateLink:
        """
        Create a new affiliate link.
        """
        program = self._programs.get(program_id)
        if not program or program.user_id != user_id:
            raise ValueError("Program not found or not authorized")

        # Generate affiliate URL
        affiliate_url = self._build_affiliate_url(
            original_url=original_url,
            program=program,
            custom_tracking_id=custom_tracking_id,
        )

        # Generate short URL
        short_url = None
        if generate_short_url:
            short_url = await self._generate_short_url(affiliate_url)

        link = AffiliateLink(
            link_id=str(uuid.uuid4()),
            user_id=user_id,
            program_id=program_id,
            original_url=original_url,
            affiliate_url=affiliate_url,
            short_url=short_url,
            title=title or self._extract_title_from_url(original_url),
            description=description,
            product_name=product_name,
            product_image_url=product_image_url,
            product_price=product_price,
            tags=tags or [],
            expires_at=expires_at,
        )

        self._links[link.link_id] = link
        return link

    async def get_links(
        self,
        user_id: str,
        program_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[LinkStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AffiliateLink]:
        """Get affiliate links with filtering."""
        links = [
            l for l in self._links.values()
            if l.user_id == user_id
        ]

        if program_id:
            links = [l for l in links if l.program_id == program_id]

        if tags:
            links = [l for l in links if any(t in l.tags for t in tags)]

        if status:
            links = [l for l in links if l.status == status]

        # Sort by created_at descending
        links.sort(key=lambda l: l.created_at, reverse=True)

        return links[offset:offset + limit]

    async def get_link(
        self,
        link_id: str,
    ) -> Optional[AffiliateLink]:
        """Get a specific link by ID."""
        return self._links.get(link_id)

    async def update_link(
        self,
        user_id: str,
        link_id: str,
        **updates,
    ) -> Optional[AffiliateLink]:
        """Update an affiliate link."""
        link = self._links.get(link_id)
        if not link or link.user_id != user_id:
            return None

        for key, value in updates.items():
            if hasattr(link, key) and key not in ['link_id', 'user_id', 'created_at']:
                setattr(link, key, value)

        link.updated_at = datetime.now(timezone.utc)
        return link

    async def delete_link(
        self,
        user_id: str,
        link_id: str,
    ) -> bool:
        """Delete an affiliate link."""
        link = self._links.get(link_id)
        if not link or link.user_id != user_id:
            return False

        del self._links[link_id]
        return True

    async def bulk_create_links(
        self,
        user_id: str,
        program_id: str,
        urls: List[Dict[str, Any]],
    ) -> List[AffiliateLink]:
        """Create multiple affiliate links at once."""
        links = []
        for url_data in urls:
            link = await self.create_link(
                user_id=user_id,
                program_id=program_id,
                original_url=url_data.get("url"),
                title=url_data.get("title", ""),
                product_name=url_data.get("product_name"),
                product_price=url_data.get("price"),
                tags=url_data.get("tags", []),
            )
            links.append(link)
        return links

    def _build_affiliate_url(
        self,
        original_url: str,
        program: AffiliateProgram,
        custom_tracking_id: Optional[str] = None,
    ) -> str:
        """Build the affiliate URL with tracking parameters."""
        parsed = urlparse(original_url)
        query_params = parse_qs(parsed.query)

        # Add affiliate tracking parameter
        tracking_value = custom_tracking_id or program.affiliate_id
        query_params[program.tracking_param] = [tracking_value]

        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))

        return new_url

    async def _generate_short_url(self, url: str) -> str:
        """Generate a short URL for the affiliate link."""
        # In production, use a URL shortening service
        # For now, generate a mock short URL
        hash_val = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"https://idkit.link/{hash_val}"

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a title from the URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if path_parts:
            return path_parts[-1].replace("-", " ").replace("_", " ").title()[:50]
        return parsed.netloc

    # =========================================================================
    # CLICK TRACKING
    # =========================================================================

    async def track_click(
        self,
        link_id: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Optional[ClickEvent]:
        """
        Track a click on an affiliate link.
        """
        link = self._links.get(link_id)
        if not link or link.status != LinkStatus.ACTIVE:
            return None

        # Hash IP for privacy
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()[:16]

        # Detect device type from user agent
        device_type = self._detect_device_type(user_agent)

        # Detect country (in production, use GeoIP)
        country = "US"  # Mock

        click = ClickEvent(
            click_id=str(uuid.uuid4()),
            link_id=link_id,
            user_id=link.user_id,
            timestamp=datetime.now(timezone.utc),
            ip_hash=ip_hash,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            device_type=device_type,
            platform=platform,
        )

        self._clicks.append(click)

        # Update link stats
        link.clicks += 1
        link.last_clicked_at = click.timestamp
        link.updated_at = click.timestamp

        return click

    async def track_conversion(
        self,
        link_id: str,
        click_id: Optional[str] = None,
        order_id: Optional[str] = None,
        order_value: float = 0.0,
        network_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConversionEvent]:
        """
        Track a conversion (sale) from an affiliate link.
        """
        link = self._links.get(link_id)
        if not link:
            return None

        program = self._programs.get(link.program_id)
        if not program:
            return None

        # Calculate commission
        if program.commission_type == "percentage":
            commission = order_value * (program.commission_rate / 100)
        else:
            commission = program.commission_rate

        conversion = ConversionEvent(
            conversion_id=str(uuid.uuid4()),
            link_id=link_id,
            click_id=click_id,
            user_id=link.user_id,
            timestamp=datetime.now(timezone.utc),
            order_id=order_id,
            order_value=order_value,
            commission=commission,
            network_data=network_data or {},
        )

        self._conversions.append(conversion)

        # Update link stats
        link.conversions += 1
        link.revenue += commission
        link.updated_at = conversion.timestamp

        # Mark click as converted if provided
        if click_id:
            for click in self._clicks:
                if click.click_id == click_id:
                    click.converted = True
                    click.conversion_value = order_value
                    break

        return conversion

    def _detect_device_type(self, user_agent: Optional[str]) -> str:
        """Detect device type from user agent."""
        if not user_agent:
            return "unknown"

        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            return "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"
        else:
            return "desktop"

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    async def get_link_stats(
        self,
        user_id: str,
        link_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get detailed statistics for a link."""
        link = self._links.get(link_id)
        if not link or link.user_id != user_id:
            return {}

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get clicks for this link in the period
        link_clicks = [
            c for c in self._clicks
            if c.link_id == link_id and c.timestamp >= cutoff
        ]

        # Get conversions for this link in the period
        link_conversions = [
            c for c in self._conversions
            if c.link_id == link_id and c.timestamp >= cutoff
        ]

        # Calculate metrics
        total_clicks = len(link_clicks)
        total_conversions = len(link_conversions)
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        total_revenue = sum(c.commission for c in link_conversions)

        # Click distribution by device
        device_breakdown = {}
        for click in link_clicks:
            device_breakdown[click.device_type] = device_breakdown.get(click.device_type, 0) + 1

        # Click distribution by country
        country_breakdown = {}
        for click in link_clicks:
            if click.country:
                country_breakdown[click.country] = country_breakdown.get(click.country, 0) + 1

        # Clicks by day
        clicks_by_day = {}
        for click in link_clicks:
            day = click.timestamp.strftime("%Y-%m-%d")
            clicks_by_day[day] = clicks_by_day.get(day, 0) + 1

        return {
            "link_id": link_id,
            "period_days": days,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "conversion_rate": round(conversion_rate, 2),
            "total_revenue": round(total_revenue, 2),
            "avg_order_value": round(
                sum(c.order_value for c in link_conversions) / max(total_conversions, 1), 2
            ),
            "device_breakdown": device_breakdown,
            "country_breakdown": country_breakdown,
            "clicks_by_day": clicks_by_day,
            "all_time_clicks": link.clicks,
            "all_time_conversions": link.conversions,
            "all_time_revenue": link.revenue,
        }

    async def get_dashboard_stats(
        self,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get overall affiliate dashboard statistics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get user's links
        user_links = [l for l in self._links.values() if l.user_id == user_id]
        link_ids = {l.link_id for l in user_links}

        # Get clicks and conversions
        user_clicks = [c for c in self._clicks if c.link_id in link_ids and c.timestamp >= cutoff]
        user_conversions = [c for c in self._conversions if c.link_id in link_ids and c.timestamp >= cutoff]

        # Calculate metrics
        total_clicks = len(user_clicks)
        total_conversions = len(user_conversions)
        total_revenue = sum(c.commission for c in user_conversions)

        # Top performing links
        link_performance = {}
        for link in user_links:
            link_clicks = sum(1 for c in user_clicks if c.link_id == link.link_id)
            link_conversions = sum(1 for c in user_conversions if c.link_id == link.link_id)
            link_revenue = sum(c.commission for c in user_conversions if c.link_id == link.link_id)

            link_performance[link.link_id] = {
                "link_id": link.link_id,
                "title": link.title,
                "clicks": link_clicks,
                "conversions": link_conversions,
                "revenue": link_revenue,
                "conversion_rate": (link_conversions / link_clicks * 100) if link_clicks > 0 else 0,
            }

        top_links = sorted(
            link_performance.values(),
            key=lambda x: x["revenue"],
            reverse=True,
        )[:10]

        # Revenue by program
        revenue_by_program = {}
        for conv in user_conversions:
            link = self._links.get(conv.link_id)
            if link:
                program = self._programs.get(link.program_id)
                if program:
                    revenue_by_program[program.program_name] = (
                        revenue_by_program.get(program.program_name, 0) + conv.commission
                    )

        return {
            "period_days": days,
            "total_links": len(user_links),
            "active_links": sum(1 for l in user_links if l.status == LinkStatus.ACTIVE),
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "conversion_rate": round((total_conversions / total_clicks * 100) if total_clicks > 0 else 0, 2),
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_click": round(total_revenue / max(total_clicks, 1), 4),
            "top_performing_links": top_links,
            "revenue_by_program": revenue_by_program,
        }

    async def get_earnings_report(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Generate earnings report for a date range."""
        user_link_ids = {l.link_id for l in self._links.values() if l.user_id == user_id}

        conversions = [
            c for c in self._conversions
            if c.link_id in user_link_ids and start_date <= c.timestamp <= end_date
        ]

        # Group by status
        pending = [c for c in conversions if c.status == "pending"]
        approved = [c for c in conversions if c.status == "approved"]
        rejected = [c for c in conversions if c.status == "rejected"]

        # Daily breakdown
        daily_earnings = {}
        for conv in conversions:
            day = conv.timestamp.strftime("%Y-%m-%d")
            if day not in daily_earnings:
                daily_earnings[day] = {"conversions": 0, "revenue": 0}
            daily_earnings[day]["conversions"] += 1
            daily_earnings[day]["revenue"] += conv.commission

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_conversions": len(conversions),
            "total_earnings": round(sum(c.commission for c in conversions), 2),
            "pending_earnings": round(sum(c.commission for c in pending), 2),
            "approved_earnings": round(sum(c.commission for c in approved), 2),
            "rejected_earnings": round(sum(c.commission for c in rejected), 2),
            "daily_breakdown": daily_earnings,
        }

    # =========================================================================
    # LINK HEALTH
    # =========================================================================

    async def check_link_health(
        self,
        user_id: str,
        link_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Check health of affiliate links."""
        if link_id:
            links = [self._links.get(link_id)]
            links = [l for l in links if l and l.user_id == user_id]
        else:
            links = [l for l in self._links.values() if l.user_id == user_id]

        results = []
        for link in links:
            health = await self._check_single_link_health(link)
            results.append(health)

        return results

    async def _check_single_link_health(
        self,
        link: AffiliateLink,
    ) -> Dict[str, Any]:
        """Check health of a single link."""
        issues = []
        status = "healthy"

        # Check if expired
        if link.expires_at and link.expires_at < datetime.now(timezone.utc):
            issues.append("Link has expired")
            status = "expired"

        # Check if link is performing poorly
        if link.clicks > 100 and link.conversions == 0:
            issues.append("High clicks but no conversions - consider updating")
            status = "warning"

        # In production, also check if URL returns 404

        return {
            "link_id": link.link_id,
            "title": link.title,
            "status": status,
            "issues": issues,
            "last_clicked": link.last_clicked_at.isoformat() if link.last_clicked_at else None,
            "clicks": link.clicks,
            "conversions": link.conversions,
        }

    async def get_optimization_suggestions(
        self,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get suggestions to optimize affiliate performance."""
        user_links = [l for l in self._links.values() if l.user_id == user_id]
        suggestions = []

        # Find underperforming links
        for link in user_links:
            if link.clicks > 50 and link.conversions == 0:
                suggestions.append({
                    "type": "low_conversion",
                    "link_id": link.link_id,
                    "title": link.title,
                    "message": f"'{link.title}' has {link.clicks} clicks but no conversions. Consider updating the product or placement.",
                    "priority": "high",
                })

        # Find inactive links
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        for link in user_links:
            if link.status == LinkStatus.ACTIVE and (
                not link.last_clicked_at or link.last_clicked_at < thirty_days_ago
            ):
                suggestions.append({
                    "type": "inactive",
                    "link_id": link.link_id,
                    "title": link.title,
                    "message": f"'{link.title}' hasn't been clicked in 30+ days. Consider refreshing or removing.",
                    "priority": "medium",
                })

        # Find top performers to replicate
        top_performers = sorted(
            [l for l in user_links if l.conversions > 0],
            key=lambda l: l.revenue,
            reverse=True,
        )[:3]

        if top_performers:
            suggestions.append({
                "type": "replicate_success",
                "message": f"Your top performing links are in: {', '.join(l.tags[0] if l.tags else 'uncategorized' for l in top_performers)}. Consider creating more content in these areas.",
                "priority": "low",
            })

        return suggestions
