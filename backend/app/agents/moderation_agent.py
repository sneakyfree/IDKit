"""
Moderation Agent

Handles content policy checking, FTC compliance, and brand safety.
HIGH autonomy - flagging only, no content modifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import re

from app.agents.base import (
    AgentContext,
    AgentResult,
    AgentTask,
    AgentType,
    AutonomyLevel,
    BaseAgent,
    EvidenceItem,
)


class ModerationAgent(BaseAgent):
    """
    Moderation agent with HIGH autonomy.
    
    All actions are read-only flagging, no modifications or deletions.
    
    Capabilities:
    - Check FTC compliance (sponsored content disclosure)
    - Verify platform TOS compliance
    - Brand safety assessment
    - Content policy checking
    """

    # FTC disclosure requirements
    FTC_DISCLOSURE_TERMS = [
        "#ad", "#sponsored", "#partner", "#paidpartnership",
        "paid partnership", "sponsored by", "in partnership with",
        "#advertisement", "ad:", "sponsored post",
    ]

    # Platform-specific hashtag limits
    PLATFORM_HASHTAG_LIMITS = {
        "instagram": 30,
        "tiktok": 100,
        "twitter": 5,
        "youtube": 15,
        "linkedin": 5,
    }

    def __init__(self):
        super().__init__(
            agent_type=AgentType.MODERATION,
            autonomy_level=AutonomyLevel.HIGH,
        )

    @property
    def name(self) -> str:
        return "Moderation Agent"

    @property
    def description(self) -> str:
        return "Content policy checking, FTC compliance, and brand safety (flagging only)"

    @property
    def capabilities(self) -> List[str]:
        return [
            "check_ftc_compliance",
            "check_platform_compliance",
            "assess_brand_safety",
            "flag_content_issues",
            "verify_disclosures",
            "check_hashtags",
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        """Check if this is a moderation-related task."""
        moderation_tasks = {
            "check_ftc_compliance",
            "check_platform_compliance",
            "assess_brand_safety",
            "flag_content_issues",
            "verify_disclosures",
            "check_hashtags",
            "moderate",
            "compliance_check",
        }
        return task.task_type.lower() in moderation_tasks

    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Execute moderation check task."""
        task_type = task.task_type.lower()

        if task_type in ("check_ftc_compliance", "verify_disclosures", "compliance_check"):
            return await self._check_ftc_compliance(task, context)
        elif task_type == "check_platform_compliance":
            return await self._check_platform_compliance(task, context)
        elif task_type == "assess_brand_safety":
            return await self._assess_brand_safety(task, context)
        elif task_type == "check_hashtags":
            return await self._check_hashtags(task, context)
        else:
            return self._create_error_result(
                action_type=task_type,
                error=f"Unknown moderation task type: {task_type}",
            )

    async def _check_ftc_compliance(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Check content for FTC disclosure compliance."""
        content = task.inputs.get("content", "")
        is_sponsored = task.inputs.get("is_sponsored", False)
        platform = task.inputs.get("platform", "unknown")

        content_lower = content.lower()
        
        # Check for disclosure presence
        has_disclosure = any(term in content_lower for term in self.FTC_DISCLOSURE_TERMS)
        
        # Check disclosure placement (should be early in content)
        disclosure_position = None
        for term in self.FTC_DISCLOSURE_TERMS:
            pos = content_lower.find(term)
            if pos != -1:
                disclosure_position = pos
                break

        # Determine compliance status
        issues = []
        warnings = []
        
        if is_sponsored and not has_disclosure:
            issues.append({
                "type": "missing_disclosure",
                "severity": "critical",
                "message": "Sponsored content must include clear FTC disclosure (#ad, #sponsored, etc.)",
                "action": "Add disclosure at the beginning of the content",
            })
        elif is_sponsored and disclosure_position and disclosure_position > 100:
            warnings.append({
                "type": "disclosure_placement",
                "severity": "warning",
                "message": "Disclosure should appear early in the content, not buried",
                "action": "Move disclosure to the first line or beginning of caption",
            })

        is_compliant = len(issues) == 0

        return self._create_result(
            action_type="check_ftc_compliance",
            output={
                "is_compliant": is_compliant,
                "is_sponsored": is_sponsored,
                "has_disclosure": has_disclosure,
                "disclosure_position": disclosure_position,
                "issues": issues,
                "warnings": warnings,
                "platform": platform,
                "recommendations": [
                    "Use #ad or #sponsored at the start of your caption",
                    "Ensure disclosure is visible without clicking 'more'",
                    "Verbal disclosure required for video content",
                ] if not is_compliant else [],
            },
            output_type="ftc_compliance_check",
            confidence=0.95,
            reasoning=f"FTC Compliance: {'PASS' if is_compliant else 'FAIL'} - {'Disclosure found' if has_disclosure else 'No disclosure'} for {'sponsored' if is_sponsored else 'organic'} content",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="compliance_check",
                    source_name="ModerationAgent",
                    data={
                        "has_disclosure": has_disclosure,
                        "is_sponsored": is_sponsored,
                        "issue_count": len(issues),
                    },
                    confidence=0.95,
                ),
            ],
        )

    async def _check_platform_compliance(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Check content for platform-specific TOS compliance."""
        content = task.inputs.get("content", "")
        platform = task.inputs.get("platform", "instagram")

        issues = []
        warnings = []

        # Check for common TOS violations
        content_lower = content.lower()

        # Check for engagement bait phrases
        engagement_bait = ["follow for follow", "f4f", "like for like", "l4l"]
        for phrase in engagement_bait:
            if phrase in content_lower:
                issues.append({
                    "type": "engagement_bait",
                    "severity": "warning",
                    "message": f"'{phrase}' may trigger platform spam filters",
                })

        # Check for prohibited content indicators
        prohibited_terms = ["giveaway manipulation", "fake followers", "buy followers"]
        for term in prohibited_terms:
            if term in content_lower:
                issues.append({
                    "type": "tos_violation",
                    "severity": "critical",
                    "message": f"Content references prohibited activity: {term}",
                })

        is_compliant = not any(i["severity"] == "critical" for i in issues)

        return self._create_result(
            action_type="check_platform_compliance",
            output={
                "is_compliant": is_compliant,
                "platform": platform,
                "issues": issues,
                "warnings": warnings,
            },
            output_type="platform_compliance_check",
            confidence=0.88,
            reasoning=f"Platform compliance check for {platform}: {'PASS' if is_compliant else 'FAIL'}",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="compliance_check",
                    source_name="ModerationAgent",
                    data={"platform": platform, "issue_count": len(issues)},
                    confidence=0.88,
                ),
            ],
        )

    async def _assess_brand_safety(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Assess content for brand safety."""
        content = task.inputs.get("content", "")
        brand_name = task.inputs.get("brand_name", "")

        content_lower = content.lower()
        
        # Simple sentiment/safety analysis
        negative_terms = ["controversy", "scandal", "lawsuit", "boycott", "problematic"]
        sensitive_topics = ["politics", "religion", "violence", "adult content"]

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

        return self._create_result(
            action_type="assess_brand_safety",
            output={
                "brand_name": brand_name,
                "safety_score": safety_score,
                "is_safe": safety_score >= 70,
                "flags": flags,
                "recommendation": "Proceed" if safety_score >= 70 else "Review required",
            },
            output_type="brand_safety_assessment",
            confidence=0.80,
            reasoning=f"Brand safety score: {safety_score}/100 with {len(flags)} flags",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="safety_analysis",
                    source_name="ModerationAgent",
                    data={"safety_score": safety_score, "flag_count": len(flags)},
                    confidence=0.80,
                ),
            ],
        )

    async def _check_hashtags(
        self,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult:
        """Check hashtag usage for platform compliance."""
        content = task.inputs.get("content", "")
        platform = task.inputs.get("platform", "instagram")

        # Extract hashtags
        hashtags = re.findall(r'#\w+', content)
        hashtag_count = len(hashtags)
        
        limit = self.PLATFORM_HASHTAG_LIMITS.get(platform.lower(), 30)
        
        issues = []
        if hashtag_count > limit:
            issues.append({
                "type": "hashtag_limit_exceeded",
                "message": f"{platform} limit is {limit} hashtags, found {hashtag_count}",
            })

        # Check for banned/spam hashtags (placeholder list)
        spam_hashtags = ["#follow4follow", "#f4f", "#like4like", "#l4l"]
        found_spam = [h for h in hashtags if h.lower() in spam_hashtags]
        if found_spam:
            issues.append({
                "type": "spam_hashtags",
                "message": f"Potentially shadowbanned hashtags found: {found_spam}",
            })

        return self._create_result(
            action_type="check_hashtags",
            output={
                "platform": platform,
                "hashtag_count": hashtag_count,
                "limit": limit,
                "hashtags": hashtags[:20],  # Limit output
                "issues": issues,
                "is_compliant": len(issues) == 0,
            },
            output_type="hashtag_check",
            confidence=0.92,
            reasoning=f"Hashtag check: {hashtag_count}/{limit} hashtags, {len(issues)} issues",
            requires_approval=False,
            evidence=[
                EvidenceItem(
                    source_type="hashtag_analysis",
                    source_name="ModerationAgent",
                    data={"count": hashtag_count, "limit": limit},
                    confidence=0.92,
                ),
            ],
        )
