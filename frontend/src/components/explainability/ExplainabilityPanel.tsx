'use client';

import { useState } from 'react';
import ViewSwitcher, { ViewType, VIEW_CONFIG } from './ViewSwitcher';

interface Insight {
    id: string;
    title: string;
    views: Record<ViewType, {
        summary: string;
        details: string[];
        action?: string;
    }>;
    confidence: number;
    sources: Array<{
        name: string;
        timestamp: string;
        dataPoint: string;
    }>;
}

interface ExplainabilityPanelProps {
    insight: Insight;
}

// Demo insight
const DEMO_INSIGHT: Insight = {
    id: '1',
    title: 'Your engagement peaks at 7 PM EST',
    views: {
        creator: {
            summary: 'Your audience is most active at 7 PM. Posts at this time get 2x more engagement!',
            details: [
                '📈 7 PM posts get 8.2% engagement vs 3.7% average',
                "🎯 This is when your followers are scrolling after work",
                '💡 Try scheduling your best content for this time',
            ],
            action: 'Schedule your next post for 7 PM EST',
        },
        manager: {
            summary: "Client's optimal posting window is 7 PM EST based on 30-day engagement analysis. Recommend shifting content calendar.",
            details: [
                'Engagement rate correlation with 7 PM posting: +122%',
                "Aligns with audience demographics (25-34 working professionals)",
                'Competitor analysis shows similar pattern',
            ],
            action: 'Update content calendar to prioritize 7 PM slot',
        },
        technical: {
            summary: 'Engagement rate correlation r=0.73 (p<0.01) with 7 PM EST posting, n=47 posts over 30 days.',
            details: [
                'Sample size: 47 posts analyzed',
                'Control group avg engagement: 3.7%',
                '7 PM cohort avg engagement: 8.2%',
                'Statistical significance: p < 0.01',
                'Confidence interval: 95%',
            ],
        },
        audit: {
            summary: '[2026-01-24T16:00:00Z] EngagementAnalysisJob completed. Source: Instagram Graph API. Model: engagement_predictor_v2.1',
            details: [
                'Job ID: ea-47829-2026-01-24',
                'Data source: Instagram Graph API v18.0',
                'Model version: engagement_predictor_v2.1',
                'Processing time: 2.3s',
                'Data freshness: <1 hour',
            ],
        },
    },
    confidence: 0.92,
    sources: [
        { name: 'Instagram Graph API', timestamp: '2026-01-24T15:58:00Z', dataPoint: '47 posts analyzed' },
        { name: 'Engagement Predictor v2.1', timestamp: '2026-01-24T16:00:00Z', dataPoint: 'r=0.73 correlation' },
        { name: 'Audience Insights', timestamp: '2026-01-24T15:55:00Z', dataPoint: '68% 25-34 age group' },
    ],
};

export default function ExplainabilityPanel({ insight = DEMO_INSIGHT }: Partial<ExplainabilityPanelProps>) {
    const [activeView, setActiveView] = useState<ViewType>('creator');
    const [showSources, setShowSources] = useState(false);

    const currentView = insight.views[activeView];

    return (
        <div style={{
            background: 'white',
            borderRadius: '16px',
            border: '1px solid #e5e7eb',
            overflow: 'hidden',
        }}>
            {/* Header */}
            <div style={{
                padding: '20px 24px',
                borderBottom: '1px solid #e5e7eb',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '16px',
            }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>{insight.title}</h3>
                    <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
                        {(insight.confidence * 100).toFixed(0)}% confidence • {insight.sources.length} sources
                    </p>
                </div>
                <ViewSwitcher activeView={activeView} onViewChange={setActiveView} />
            </div>

            {/* Content based on view */}
            <div style={{ padding: '24px' }}>
                {/* View-specific summary */}
                <div style={{
                    background: activeView === 'audit' ? '#f9fafb' : '#eff6ff',
                    padding: '16px 20px',
                    borderRadius: '12px',
                    marginBottom: '20px',
                    fontFamily: activeView === 'audit' ? 'monospace' : 'inherit',
                    fontSize: activeView === 'audit' ? '13px' : '15px',
                }}>
                    {currentView.summary}
                </div>

                {/* Details */}
                <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
                        {VIEW_CONFIG[activeView].icon} {VIEW_CONFIG[activeView].label} Details
                    </h4>
                    <ul style={{
                        margin: 0,
                        paddingLeft: activeView === 'audit' ? '0' : '20px',
                        listStyle: activeView === 'audit' ? 'none' : 'disc',
                    }}>
                        {currentView.details.map((detail, i) => (
                            <li key={i} style={{
                                marginBottom: '8px',
                                color: '#4b5563',
                                fontSize: activeView === 'audit' ? '13px' : '14px',
                                fontFamily: activeView === 'audit' ? 'monospace' : 'inherit',
                            }}>
                                {detail}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Action button (for creator/manager views) */}
                {currentView.action && (
                    <button style={{
                        padding: '12px 24px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: 500,
                        marginBottom: '20px',
                    }}>
                        {currentView.action}
                    </button>
                )}

                {/* Sources (expandable) */}
                <div>
                    <button
                        onClick={() => setShowSources(!showSources)}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '14px',
                            color: '#6b7280',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: 0,
                        }}
                    >
                        📊 {showSources ? 'Hide' : 'Show'} Data Sources ({insight.sources.length})
                    </button>

                    {showSources && (
                        <div style={{
                            marginTop: '12px',
                            padding: '16px',
                            background: '#f9fafb',
                            borderRadius: '8px',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                        }}>
                            {insight.sources.map((source, i) => (
                                <div key={i} style={{ marginBottom: '8px' }}>
                                    <strong>{source.name}</strong>
                                    <span style={{ color: '#9ca3af', marginLeft: '8px' }}>
                                        [{source.timestamp}]
                                    </span>
                                    <div style={{ color: '#4b5563', marginTop: '2px' }}>{source.dataPoint}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
