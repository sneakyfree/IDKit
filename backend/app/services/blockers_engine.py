"""
Blockers Engine

Detects issues and generates actionable fix plans.
Every blocker has evidence - we never accuse without proof.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.blockers import (
    BlockerAnalysis,
    BlockerCategory,
    BlockerSeverity,
    FixList,
    UnlockerAction,
    UnlockerEffort,
    UnlockerTimeframe,
)
from app.schemas.source_labeling import EvidenceItem


# =============================================================================
# BLOCKER LIBRARY - Common issues and their fixes
# =============================================================================

BLOCKER_LIBRARY = {
    # Profile issues
    "missing_bio_link": {
        "category": BlockerCategory.PROFILE,
        "severity": BlockerSeverity.HIGH,
        "title": "Missing Link in Bio",
        "why_not": "You're missing a link in your bio, losing click-through traffic",
        "impact": "Losing potential 5-10% of profile visitors who would click",
        "unlocker": {
            "title": "Add Link to Bio",
            "what_to_do": "Add your primary link (website, Linktree, etc.) to your bio",
            "timeframe": UnlockerTimeframe.QUICK_WIN,
            "effort": UnlockerEffort.LOW,
            "time": "5 minutes",
            "proof": ["Screenshot of updated bio with link"],
        },
    },
    "incomplete_profile": {
        "category": BlockerCategory.PROFILE,
        "severity": BlockerSeverity.MEDIUM,
        "title": "Incomplete Profile Information",
        "why_not": "Your profile is missing key information that builds trust",
        "impact": "Incomplete profiles convert 40% fewer visitors to followers",
        "unlocker": {
            "title": "Complete Your Profile",
            "what_to_do": "Fill in all profile fields: bio, location, contact, category",
            "timeframe": UnlockerTimeframe.QUICK_WIN,
            "effort": UnlockerEffort.LOW,
            "time": "15 minutes",
            "proof": ["All profile fields completed"],
        },
    },
    # Content issues
    "low_posting_frequency": {
        "category": BlockerCategory.CONTENT,
        "severity": BlockerSeverity.HIGH,
        "title": "Inconsistent Posting Schedule",
        "why_not": "Posting less than 3x/week hurts algorithm visibility",
        "impact": "Low frequency = 50% less reach vs consistent creators",
        "unlocker": {
            "title": "Create Content Calendar",
            "what_to_do": "Plan and schedule at least 3 posts per week for the next month",
            "timeframe": UnlockerTimeframe.THIRTY_DAYS,
            "effort": UnlockerEffort.MEDIUM,
            "time": "2 hours to plan, ongoing to execute",
            "proof": ["Content calendar created", "First week of posts scheduled"],
        },
    },
    "no_video_content": {
        "category": BlockerCategory.CONTENT,
        "severity": BlockerSeverity.MEDIUM,
        "title": "No Video Content",
        "why_not": "Video content gets 2-3x more engagement on most platforms",
        "impact": "Missing out on algorithm boost for video creators",
        "unlocker": {
            "title": "Start Creating Video",
            "what_to_do": "Create and publish at least 2 Reels/Shorts per week",
            "timeframe": UnlockerTimeframe.THIRTY_DAYS,
            "effort": UnlockerEffort.HIGH,
            "time": "1-2 hours per video",
            "proof": ["4+ videos published in first month"],
        },
    },
    # Engagement issues
    "low_engagement_rate": {
        "category": BlockerCategory.ENGAGEMENT,
        "severity": BlockerSeverity.HIGH,
        "title": "Below-Average Engagement Rate",
        "why_not": "Your engagement rate is below niche average, limiting reach",
        "impact": "Low engagement = lower algorithm priority = less reach",
        "unlocker": {
            "title": "Engagement Improvement Sprint",
            "what_to_do": "Reply to all comments within 1 hour, add CTAs to posts, use engagement hooks",
            "timeframe": UnlockerTimeframe.THIRTY_DAYS,
            "effort": UnlockerEffort.MEDIUM,
            "time": "30 min/day",
            "proof": ["Engagement rate increased by 20%+"],
        },
    },
    "no_community_interaction": {
        "category": BlockerCategory.ENGAGEMENT,
        "severity": BlockerSeverity.MEDIUM,
        "title": "Limited Community Interaction",
        "why_not": "Not engaging with your community reduces loyalty and reach",
        "impact": "Missed relationship-building = lower retention",
        "unlocker": {
            "title": "Daily Community Engagement",
            "what_to_do": "Spend 20 min/day engaging: respond to comments, DMs, engage with followers' content",
            "timeframe": UnlockerTimeframe.QUICK_WIN,
            "effort": UnlockerEffort.LOW,
            "time": "20 min/day",
            "proof": ["Response rate > 90%"],
        },
    },
    # Monetization issues
    "no_monetization_strategy": {
        "category": BlockerCategory.MONETIZATION,
        "severity": BlockerSeverity.HIGH,
        "title": "No Clear Monetization Path",
        "why_not": "You have audience but no system to convert to revenue",
        "impact": "Leaving significant money on the table",
        "unlocker": {
            "title": "Define Revenue Streams",
            "what_to_do": "Identify 2-3 monetization paths: affiliates, products, sponsorships",
            "timeframe": UnlockerTimeframe.THIRTY_DAYS,
            "effort": UnlockerEffort.MEDIUM,
            "time": "4 hours research + setup",
            "proof": ["First revenue stream active", "First dollar earned"],
        },
    },
    "underpriced_sponsorships": {
        "category": BlockerCategory.MONETIZATION,
        "severity": BlockerSeverity.MEDIUM,
        "title": "Underpricing Brand Deals",
        "why_not": "Your rates may be below market value for your engagement",
        "impact": "Potentially losing 30-50% revenue per deal",
        "unlocker": {
            "title": "Research Market Rates",
            "what_to_do": "Research going rates for your niche/tier, update your media kit with competitive pricing",
            "timeframe": UnlockerTimeframe.QUICK_WIN,
            "effort": UnlockerEffort.LOW,
            "time": "1 hour",
            "proof": ["Updated rate card", "Media kit updated"],
        },
    },
    # Compliance issues
    "missing_ftc_disclosure": {
        "category": BlockerCategory.COMPLIANCE,
        "severity": BlockerSeverity.CRITICAL,
        "title": "Missing FTC Disclosures",
        "why_not": "Sponsored content without proper disclosure violates FTC guidelines",
        "impact": "Legal risk + platform penalties + trust damage",
        "unlocker": {
            "title": "Add FTC Disclosures",
            "what_to_do": "Add clear '#ad' or '#sponsored' to all paid/gifted content",
            "timeframe": UnlockerTimeframe.QUICK_WIN,
            "effort": UnlockerEffort.LOW,
            "time": "30 minutes to update past posts",
            "proof": ["All sponsored posts have disclosures"],
        },
    },
}


class BlockersEngine:
    """
    Detects blockers and generates unlocker action plans.
    
    Key principles:
    - Every blocker has evidence (never accuses without proof)
    - Unlockers have clear success criteria
    - Prioritized by effort/impact ratio
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_blockers(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        metrics_data: Optional[Dict[str, Any]] = None,
        categories: Optional[List[BlockerCategory]] = None,
    ) -> List[BlockerAnalysis]:
        """
        Scan for blockers in user's profile and metrics.
        
        Args:
            user_id: The creator's ID
            profile_data: Profile information
            metrics_data: Performance metrics (if available)
            categories: Filter to specific categories
        """
        blockers = []
        
        # Profile checks
        if not categories or BlockerCategory.PROFILE in categories:
            blockers.extend(await self._check_profile_blockers(user_id, profile_data))
        
        # Content checks
        if not categories or BlockerCategory.CONTENT in categories:
            blockers.extend(await self._check_content_blockers(user_id, profile_data, metrics_data))
        
        # Engagement checks
        if not categories or BlockerCategory.ENGAGEMENT in categories:
            blockers.extend(await self._check_engagement_blockers(user_id, metrics_data))
        
        # Monetization checks
        if not categories or BlockerCategory.MONETIZATION in categories:
            blockers.extend(await self._check_monetization_blockers(user_id, profile_data))
        
        # Compliance checks
        if not categories or BlockerCategory.COMPLIANCE in categories:
            blockers.extend(await self._check_compliance_blockers(user_id, profile_data))

        # Sort by severity and impact
        blockers.sort(
            key=lambda b: (
                -self._severity_score(b.severity),
                -b.confidence_impact,
            )
        )

        return blockers

    async def _check_profile_blockers(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
    ) -> List[BlockerAnalysis]:
        """Check for profile-related blockers."""
        blockers = []

        # Check for missing bio link
        if not profile_data.get("bio_link"):
            lib = BLOCKER_LIBRARY["missing_bio_link"]
            blockers.append(self._create_blocker(
                key="missing_bio_link",
                library_entry=lib,
                evidence=[EvidenceItem(
                    evidence_id=uuid4(),
                    evidence_type="profile_scan",
                    source_name="ProfileAnalyzer",
                    data={"bio_link": None},
                    timestamp=datetime.utcnow(),
                    confidence=1.0,
                )],
            ))

        # Check for incomplete profile
        required_fields = ["bio", "category", "profile_picture"]
        missing = [f for f in required_fields if not profile_data.get(f)]
        if missing:
            lib = BLOCKER_LIBRARY["incomplete_profile"]
            blockers.append(self._create_blocker(
                key="incomplete_profile",
                library_entry=lib,
                evidence=[EvidenceItem(
                    evidence_id=uuid4(),
                    evidence_type="profile_scan",
                    source_name="ProfileAnalyzer",
                    data={"missing_fields": missing},
                    timestamp=datetime.utcnow(),
                    confidence=1.0,
                )],
            ))

        return blockers

    async def _check_content_blockers(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
        metrics_data: Optional[Dict[str, Any]],
    ) -> List[BlockerAnalysis]:
        """Check for content-related blockers."""
        blockers = []

        if metrics_data:
            posts_per_week = metrics_data.get("posts_per_week", 0)
            if posts_per_week < 3:
                lib = BLOCKER_LIBRARY["low_posting_frequency"]
                blockers.append(self._create_blocker(
                    key="low_posting_frequency",
                    library_entry=lib,
                    evidence=[EvidenceItem(
                        evidence_id=uuid4(),
                        evidence_type="metrics_analysis",
                        source_name="ContentAnalyzer",
                        data={"posts_per_week": posts_per_week},
                        timestamp=datetime.utcnow(),
                        confidence=0.95,
                    )],
                ))

            video_percentage = metrics_data.get("video_percentage", 0)
            if video_percentage < 20:
                lib = BLOCKER_LIBRARY["no_video_content"]
                blockers.append(self._create_blocker(
                    key="no_video_content",
                    library_entry=lib,
                    evidence=[EvidenceItem(
                        evidence_id=uuid4(),
                        evidence_type="metrics_analysis",
                        source_name="ContentAnalyzer",
                        data={"video_percentage": video_percentage},
                        timestamp=datetime.utcnow(),
                        confidence=0.90,
                    )],
                ))

        return blockers

    async def _check_engagement_blockers(
        self,
        user_id: UUID,
        metrics_data: Optional[Dict[str, Any]],
    ) -> List[BlockerAnalysis]:
        """Check for engagement-related blockers."""
        blockers = []

        if metrics_data:
            engagement_rate = metrics_data.get("engagement_rate", 0)
            niche_average = metrics_data.get("niche_engagement_average", 3.5)
            
            if engagement_rate < niche_average * 0.7:
                lib = BLOCKER_LIBRARY["low_engagement_rate"]
                blockers.append(self._create_blocker(
                    key="low_engagement_rate",
                    library_entry=lib,
                    evidence=[EvidenceItem(
                        evidence_id=uuid4(),
                        evidence_type="metrics_analysis",
                        source_name="EngagementAnalyzer",
                        data={
                            "engagement_rate": engagement_rate,
                            "niche_average": niche_average,
                        },
                        timestamp=datetime.utcnow(),
                        confidence=0.85,
                    )],
                ))

        return blockers

    async def _check_monetization_blockers(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
    ) -> List[BlockerAnalysis]:
        """Check for monetization-related blockers."""
        blockers = []

        revenue_streams = profile_data.get("revenue_streams", [])
        if not revenue_streams:
            lib = BLOCKER_LIBRARY["no_monetization_strategy"]
            blockers.append(self._create_blocker(
                key="no_monetization_strategy",
                library_entry=lib,
                evidence=[EvidenceItem(
                    evidence_id=uuid4(),
                    evidence_type="profile_scan",
                    source_name="RevenueAnalyzer",
                    data={"revenue_streams": []},
                    timestamp=datetime.utcnow(),
                    confidence=0.90,
                )],
            ))

        return blockers

    async def _check_compliance_blockers(
        self,
        user_id: UUID,
        profile_data: Dict[str, Any],
    ) -> List[BlockerAnalysis]:
        """Check for compliance-related blockers."""
        blockers = []

        has_sponsorships = profile_data.get("has_sponsorships", False)
        has_disclosures = profile_data.get("uses_ftc_disclosures", True)
        
        if has_sponsorships and not has_disclosures:
            lib = BLOCKER_LIBRARY["missing_ftc_disclosure"]
            blockers.append(self._create_blocker(
                key="missing_ftc_disclosure",
                library_entry=lib,
                evidence=[EvidenceItem(
                    evidence_id=uuid4(),
                    evidence_type="compliance_scan",
                    source_name="ComplianceChecker",
                    data={"sponsored_posts_without_disclosure": True},
                    timestamp=datetime.utcnow(),
                    confidence=0.95,
                )],
            ))

        return blockers

    def _create_blocker(
        self,
        key: str,
        library_entry: Dict[str, Any],
        evidence: List[EvidenceItem],
    ) -> BlockerAnalysis:
        """Create a blocker from library entry."""
        return BlockerAnalysis(
            blocker_id=uuid4(),
            category=library_entry["category"],
            severity=library_entry["severity"],
            title=library_entry["title"],
            why_not=library_entry["why_not"],
            impact_description=library_entry["impact"],
            evidence=evidence,
            confidence_impact=self._severity_to_impact(library_entry["severity"]),
        )

    def _severity_score(self, severity: BlockerSeverity) -> int:
        """Convert severity to numeric score."""
        scores = {
            BlockerSeverity.CRITICAL: 4,
            BlockerSeverity.HIGH: 3,
            BlockerSeverity.MEDIUM: 2,
            BlockerSeverity.LOW: 1,
        }
        return scores.get(severity, 2)

    def _severity_to_impact(self, severity: BlockerSeverity) -> float:
        """Convert severity to impact score."""
        impacts = {
            BlockerSeverity.CRITICAL: 0.9,
            BlockerSeverity.HIGH: 0.7,
            BlockerSeverity.MEDIUM: 0.5,
            BlockerSeverity.LOW: 0.3,
        }
        return impacts.get(severity, 0.5)

    async def generate_unlockers(
        self,
        blockers: List[BlockerAnalysis],
    ) -> List[UnlockerAction]:
        """Generate unlocker actions for given blockers."""
        unlockers = []

        for blocker in blockers:
            # Find matching unlocker from library
            for key, entry in BLOCKER_LIBRARY.items():
                if entry["title"] == blocker.title and "unlocker" in entry:
                    unlocker_data = entry["unlocker"]
                    unlockers.append(UnlockerAction(
                        action_id=uuid4(),
                        blocker_id=blocker.blocker_id,
                        title=unlocker_data["title"],
                        what_to_do=unlocker_data["what_to_do"],
                        why_it_helps=f"Fixes: {blocker.why_not}",
                        timeframe=unlocker_data["timeframe"],
                        effort_level=unlocker_data["effort"],
                        estimated_time=unlocker_data["time"],
                        proof_required=unlocker_data.get("proof", []),
                        priority_score=self._calculate_priority(
                            blocker.confidence_impact,
                            unlocker_data["effort"],
                        ),
                    ))
                    break

        # Sort by priority
        unlockers.sort(key=lambda u: u.priority_score, reverse=True)
        return unlockers

    def _calculate_priority(
        self,
        impact: float,
        effort: UnlockerEffort,
    ) -> float:
        """Calculate priority score based on impact/effort ratio."""
        effort_multipliers = {
            UnlockerEffort.LOW: 1.5,
            UnlockerEffort.MEDIUM: 1.0,
            UnlockerEffort.HIGH: 0.6,
        }
        multiplier = effort_multipliers.get(effort, 1.0)
        return min(impact * multiplier, 1.0)

    async def generate_fix_list(
        self,
        user_id: UUID,
        blockers: List[BlockerAnalysis],
    ) -> FixList:
        """Generate prioritized fix list organized by timeframe."""
        unlockers = await self.generate_unlockers(blockers)

        quick_wins = [u for u in unlockers if u.timeframe == UnlockerTimeframe.QUICK_WIN]
        thirty_day = [u for u in unlockers if u.timeframe == UnlockerTimeframe.THIRTY_DAYS]
        ninety_day = [u for u in unlockers if u.timeframe == UnlockerTimeframe.NINETY_DAYS]

        return FixList(
            user_id=user_id,
            quick_wins=quick_wins,
            thirty_day_actions=thirty_day,
            ninety_day_actions=ninety_day,
            total_actions=len(unlockers),
            total_blockers_addressed=len(blockers),
        )
