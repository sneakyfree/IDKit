"""
Explainability Engine

Multi-view rendering of insights for different audiences.
Same data, 4 different presentations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.schemas.explainability import (
    Insight,
    InsightType,
    RenderedInsight,
    ViewTemplate,
    ViewType,
)


# ============== View Templates ==============

VIEW_TEMPLATES: Dict[ViewType, ViewTemplate] = {
    ViewType.CREATOR: ViewTemplate(
        view_type=ViewType.CREATOR,
        name="Creator View",
        description="Plain language, actionable, mobile-friendly",
        include_statistics=False,
        include_evidence=False,
        include_timestamps=False,
        include_versions=False,
        max_headline_length=80,
        max_body_length=300,
        tone="casual",
    ),
    ViewType.MANAGER: ViewTemplate(
        view_type=ViewType.MANAGER,
        name="Manager View",
        description="Talk tracks, client-ready, compliant phrasing",
        include_statistics=False,
        include_evidence=True,
        include_timestamps=False,
        include_versions=False,
        max_headline_length=120,
        max_body_length=500,
        tone="professional",
    ),
    ViewType.TECHNICAL: ViewTemplate(
        view_type=ViewType.TECHNICAL,
        name="Technical View",
        description="Evidence chains, API sources, statistics",
        include_statistics=True,
        include_evidence=True,
        include_timestamps=True,
        include_versions=True,
        max_headline_length=200,
        max_body_length=1000,
        tone="technical",
    ),
    ViewType.AUDIT: ViewTemplate(
        view_type=ViewType.AUDIT,
        name="Audit View",
        description="Immutable logs, version history, complete provenance",
        include_statistics=True,
        include_evidence=True,
        include_timestamps=True,
        include_versions=True,
        max_headline_length=300,
        max_body_length=2000,
        tone="formal",
    ),
}


class ExplainabilityEngine:
    """
    Engine for rendering insights in multiple views.
    
    Same underlying data, different presentations:
    - creator: "Your engagement is 2x better when you post at 7 PM"
    - manager: "Recommend shifting client's posting schedule to 7 PM EST"
    - technical: "Engagement rate correlation r=0.73 (p<0.01)"
    - audit: "[timestamp] EngagementAnalysisJob completed"
    """

    def render_insight(
        self,
        insight: Insight,
        view: ViewType,
    ) -> RenderedInsight:
        """
        Render an insight for a specific view type.
        """
        template = VIEW_TEMPLATES[view]
        
        if view == ViewType.CREATOR:
            return self._render_creator_view(insight, template)
        elif view == ViewType.MANAGER:
            return self._render_manager_view(insight, template)
        elif view == ViewType.TECHNICAL:
            return self._render_technical_view(insight, template)
        elif view == ViewType.AUDIT:
            return self._render_audit_view(insight, template)
        else:
            return self._render_creator_view(insight, template)

    def render_all_views(
        self,
        insight: Insight,
    ) -> Dict[str, RenderedInsight]:
        """Render insight for all view types."""
        return {
            view.value: self.render_insight(insight, view)
            for view in ViewType
        }

    def _render_creator_view(
        self,
        insight: Insight,
        template: ViewTemplate,
    ) -> RenderedInsight:
        """
        Creator view: Plain language, actionable, mobile-friendly.
        
        Example: "Your engagement is 2x better when you post at 7 PM"
        """
        headline = self._format_creator_headline(insight)
        body = self._format_creator_body(insight)
        actions = self._extract_actions(insight, ViewType.CREATOR)

        return RenderedInsight(
            insight_id=insight.insight_id,
            view_type=ViewType.CREATOR,
            headline=headline[:template.max_headline_length],
            body=body[:template.max_body_length],
            action_items=actions,
            formatted_data=self._format_data_for_creator(insight.data),
        )

    def _render_manager_view(
        self,
        insight: Insight,
        template: ViewTemplate,
    ) -> RenderedInsight:
        """
        Manager view: Talk tracks, client-ready, compliant phrasing.
        
        Example: "Recommend shifting client's posting schedule to 7 PM EST"
        """
        headline = self._format_manager_headline(insight)
        body = self._format_manager_body(insight)
        actions = self._extract_actions(insight, ViewType.MANAGER)

        return RenderedInsight(
            insight_id=insight.insight_id,
            view_type=ViewType.MANAGER,
            headline=headline[:template.max_headline_length],
            body=body[:template.max_body_length],
            action_items=actions,
            formatted_data=self._format_data_for_manager(insight.data),
            evidence_summary=self._summarize_evidence(insight),
        )

    def _render_technical_view(
        self,
        insight: Insight,
        template: ViewTemplate,
    ) -> RenderedInsight:
        """
        Technical view: Evidence chains, API sources, statistics.
        
        Example: "Engagement rate correlation r=0.73 (p<0.01) with 7 PM posting"
        """
        headline = self._format_technical_headline(insight)
        body = self._format_technical_body(insight)
        actions = self._extract_actions(insight, ViewType.TECHNICAL)

        return RenderedInsight(
            insight_id=insight.insight_id,
            view_type=ViewType.TECHNICAL,
            headline=headline[:template.max_headline_length],
            body=body[:template.max_body_length],
            action_items=actions,
            formatted_data=insight.data,
            evidence_summary=self._detailed_evidence(insight),
            statistical_notes=self._format_statistics(insight),
            footnotes=self._generate_footnotes(insight),
        )

    def _render_audit_view(
        self,
        insight: Insight,
        template: ViewTemplate,
    ) -> RenderedInsight:
        """
        Audit view: Immutable logs, version history, complete provenance.
        
        Example: "[timestamp] EngagementAnalysisJob completed. Source: Instagram Graph API"
        """
        headline = self._format_audit_headline(insight)
        body = self._format_audit_body(insight)
        audit_trail = self._generate_audit_trail(insight)
        version_info = self._format_version_info(insight)

        return RenderedInsight(
            insight_id=insight.insight_id,
            view_type=ViewType.AUDIT,
            headline=headline[:template.max_headline_length],
            body=body[:template.max_body_length],
            action_items=[],  # Audit view doesn't have actions
            formatted_data=insight.data,
            evidence_summary=self._detailed_evidence(insight),
            statistical_notes=self._format_statistics(insight),
            audit_trail=audit_trail,
            version_info=version_info,
            footnotes=self._generate_footnotes(insight),
        )

    # ============== Headline Formatters ==============

    def _format_creator_headline(self, insight: Insight) -> str:
        """Format headline for creator view."""
        type_prefixes = {
            InsightType.PERFORMANCE: "📈 ",
            InsightType.RECOMMENDATION: "💡 ",
            InsightType.TREND: "🔥 ",
            InsightType.BLOCKER: "⚠️ ",
            InsightType.OPPORTUNITY: "🎯 ",
            InsightType.WARNING: "⚡ ",
            InsightType.METRIC: "📊 ",
        }
        prefix = type_prefixes.get(insight.insight_type, "")
        return f"{prefix}{insight.title}"

    def _format_manager_headline(self, insight: Insight) -> str:
        """Format headline for manager view."""
        return f"Client Insight: {insight.title}"

    def _format_technical_headline(self, insight: Insight) -> str:
        """Format headline for technical view."""
        conf = f" (confidence: {insight.confidence:.0%})" if insight.confidence else ""
        return f"[{insight.insight_type.value.upper()}] {insight.title}{conf}"

    def _format_audit_headline(self, insight: Insight) -> str:
        """Format headline for audit view."""
        timestamp = insight.generated_at.isoformat()
        return f"[{timestamp}] {insight.insight_type.value}: {insight.title}"

    # ============== Body Formatters ==============

    def _format_creator_body(self, insight: Insight) -> str:
        """Format body for creator view - plain language."""
        return insight.summary

    def _format_manager_body(self, insight: Insight) -> str:
        """Format body for manager view - professional tone."""
        return f"Based on our analysis, {insight.summary.lower()} This insight is derived from data analysis with {insight.confidence:.0%} confidence."

    def _format_technical_body(self, insight: Insight) -> str:
        """Format body for technical view - include statistics."""
        parts = [insight.summary]
        
        if insight.sample_size:
            parts.append(f"Sample size: n={insight.sample_size}")
        if insight.p_value:
            parts.append(f"Statistical significance: p={insight.p_value:.4f}")
        if insight.correlation:
            parts.append(f"Correlation coefficient: r={insight.correlation:.3f}")
        if insight.data_sources:
            parts.append(f"Data sources: {', '.join(insight.data_sources)}")
            
        return " | ".join(parts)

    def _format_audit_body(self, insight: Insight) -> str:
        """Format body for audit view - complete provenance."""
        lines = [
            f"Analysis Type: {insight.insight_type.value}",
            f"Generated: {insight.generated_at.isoformat()}",
            f"Confidence Score: {insight.confidence:.4f}",
            f"Model Version: {insight.model_version or 'N/A'}",
            f"Rule Version: {insight.rule_version or 'N/A'}",
            "",
            "Summary:",
            insight.summary,
        ]
        return "\n".join(lines)

    # ============== Helper Methods ==============

    def _extract_actions(self, insight: Insight, view: ViewType) -> List[str]:
        """Extract action items appropriate for view."""
        actions = insight.data.get("actions", [])
        
        if view == ViewType.CREATOR:
            return [a.get("simple", a.get("title", "")) for a in actions][:3]
        elif view == ViewType.MANAGER:
            return [a.get("professional", a.get("title", "")) for a in actions]
        else:
            return [a.get("technical", a.get("title", "")) for a in actions]

    def _format_data_for_creator(self, data: Dict) -> Dict:
        """Simplify data for creator view."""
        return {
            k: v for k, v in data.items()
            if k not in ["technical_details", "raw_data", "evidence"]
        }

    def _format_data_for_manager(self, data: Dict) -> Dict:
        """Format data for manager view."""
        return {
            k: v for k, v in data.items()
            if k not in ["raw_data"]
        }

    def _summarize_evidence(self, insight: Insight) -> str:
        """Brief evidence summary for manager view."""
        if not insight.evidence_chain:
            return "Based on platform analytics"
        
        sources = set(e.source_name for e in insight.evidence_chain)
        return f"Data sourced from: {', '.join(sources)}"

    def _detailed_evidence(self, insight: Insight) -> str:
        """Detailed evidence for technical view."""
        if not insight.evidence_chain:
            return "No evidence chain recorded"
        
        lines = []
        for e in insight.evidence_chain:
            lines.append(
                f"- [{e.evidence_type}] {e.source_name}: "
                f"confidence={e.confidence:.2f}, captured={e.timestamp.isoformat()}"
            )
        return "\n".join(lines)

    def _format_statistics(self, insight: Insight) -> str:
        """Format statistical notes."""
        parts = []
        if insight.sample_size:
            parts.append(f"n={insight.sample_size}")
        if insight.p_value:
            parts.append(f"p={insight.p_value:.4f}")
        if insight.correlation:
            parts.append(f"r={insight.correlation:.3f}")
        parts.append(f"confidence={insight.confidence:.2%}")
        return " | ".join(parts)

    def _generate_audit_trail(self, insight: Insight) -> str:
        """Generate complete audit trail."""
        lines = [
            f"Insight ID: {insight.insight_id}",
            f"Generated At: {insight.generated_at.isoformat()}",
            f"Data As Of: {insight.data_as_of.isoformat() if insight.data_as_of else 'N/A'}",
            "",
            "Evidence Chain:",
        ]
        
        for i, e in enumerate(insight.evidence_chain, 1):
            lines.append(f"  {i}. {e.source_name} ({e.evidence_type})")
            lines.append(f"     Timestamp: {e.timestamp.isoformat()}")
            lines.append(f"     Confidence: {e.confidence:.4f}")
        
        return "\n".join(lines)

    def _format_version_info(self, insight: Insight) -> str:
        """Format version information."""
        return f"Model: {insight.model_version or 'N/A'} | Rules: {insight.rule_version or 'N/A'}"

    def _generate_footnotes(self, insight: Insight) -> List[str]:
        """Generate footnotes for technical/audit views."""
        footnotes = []
        
        if insight.model_version:
            footnotes.append(f"¹ Generated using model version {insight.model_version}")
        
        if insight.data_sources:
            footnotes.append(f"² Data sourced from: {', '.join(insight.data_sources)}")
        
        return footnotes
