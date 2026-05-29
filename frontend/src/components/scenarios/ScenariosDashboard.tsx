'use client';

import { useState, useEffect } from 'react';

import { apiRequest } from '@/lib/api';

interface Scenario {
    id: string;
    title: string;
    description: string;
    type: 'content' | 'monetization' | 'growth' | 'collaboration';
    confidence: number;
    timeframe: string;
    potentialRevenue?: number;
    effort: 'low' | 'medium' | 'high';
    status: 'new' | 'in_progress' | 'completed' | 'dismissed';
    evidence: Array<{
        source: string;
        data: string;
        confidence: number;
    }>;
}

interface ScenarioStats {
    total: number;
    byType: Record<string, number>;
    averageConfidence: number;
    totalPotentialRevenue: number;
}

export default function ScenariosDashboard() {
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [filter, setFilter] = useState<string>('all');
    const [sortBy, setSortBy] = useState<'confidence' | 'revenue' | 'effort'>('confidence');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchScenarios() {
            try {
                const response = await apiRequest<Scenario[]>('/api/v1/scenarios');
                setScenarios(Array.isArray(response) ? response : []);
            } catch {
                setScenarios([]);
            } finally {
                setLoading(false);
            }
        }
        fetchScenarios();
    }, []);

    const stats: ScenarioStats = {
        total: scenarios.length,
        byType: scenarios.reduce((acc, s) => {
            acc[s.type] = (acc[s.type] || 0) + 1;
            return acc;
        }, {} as Record<string, number>),
        averageConfidence: scenarios.length ? scenarios.reduce((sum, s) => sum + s.confidence, 0) / scenarios.length : 0,
        totalPotentialRevenue: scenarios.reduce((sum, s) => sum + (s.potentialRevenue || 0), 0),
    };

    const filteredScenarios = scenarios
        .filter(s => filter === 'all' || s.type === filter)
        .sort((a, b) => {
            if (sortBy === 'confidence') return b.confidence - a.confidence;
            if (sortBy === 'revenue') return (b.potentialRevenue || 0) - (a.potentialRevenue || 0);
            const effortOrder = { low: 1, medium: 2, high: 3 };
            return effortOrder[a.effort] - effortOrder[b.effort];
        });

    const getTypeColor = (type: string) => {
        const colors: Record<string, string> = {
            content: '#10b981',
            monetization: '#f59e0b',
            growth: '#3b82f6',
            collaboration: '#8b5cf6',
        };
        return colors[type] || '#6b7280';
    };

    const getEffortBadge = (effort: string) => {
        const styles: Record<string, string> = {
            low: 'background: #dcfce7; color: #166534;',
            medium: 'background: #fef3c7; color: #92400e;',
            high: 'background: #fee2e2; color: #991b1b;',
        };
        return styles[effort] || '';
    };

    const handleAction = (id: string, action: 'start' | 'dismiss') => {
        setScenarios(prev => prev.map(s =>
            s.id === id
                ? { ...s, status: action === 'start' ? 'in_progress' : 'dismissed' }
                : s
        ));
    };

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            <header style={{ marginBottom: '32px' }}>
                <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
                    🎯 Scenario Universe
                </h1>
                <p style={{ color: '#6b7280', fontSize: '16px' }}>
                    AI-generated opportunities based on your performance data and market analysis
                </p>
            </header>

            {/* Stats Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div style={{ background: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', padding: '20px', borderRadius: '12px', color: 'white' }}>
                    <div style={{ fontSize: '14px', opacity: 0.9 }}>Total Scenarios</div>
                    <div style={{ fontSize: '32px', fontWeight: 700 }}>{stats.total}</div>
                </div>
                <div style={{ background: 'linear-gradient(135deg, #10b981, #059669)', padding: '20px', borderRadius: '12px', color: 'white' }}>
                    <div style={{ fontSize: '14px', opacity: 0.9 }}>Avg Confidence</div>
                    <div style={{ fontSize: '32px', fontWeight: 700 }}>{(stats.averageConfidence * 100).toFixed(0)}%</div>
                </div>
                <div style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', padding: '20px', borderRadius: '12px', color: 'white' }}>
                    <div style={{ fontSize: '14px', opacity: 0.9 }}>Potential Revenue</div>
                    <div style={{ fontSize: '32px', fontWeight: 700 }}>${stats.totalPotentialRevenue.toLocaleString()}</div>
                </div>
                <div style={{ background: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', padding: '20px', borderRadius: '12px', color: 'white' }}>
                    <div style={{ fontSize: '14px', opacity: 0.9 }}>Quick Wins</div>
                    <div style={{ fontSize: '32px', fontWeight: 700 }}>{scenarios.filter(s => s.effort === 'low').length}</div>
                </div>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <select aria-label="Filter or select option"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '14px' }}
                >
                    <option value="all">All Types</option>
                    <option value="content">Content</option>
                    <option value="monetization">Monetization</option>
                    <option value="growth">Growth</option>
                    <option value="collaboration">Collaboration</option>
                </select>
                <select aria-label="Filter or select option"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                    style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '14px' }}
                >
                    <option value="confidence">Sort by Confidence</option>
                    <option value="revenue">Sort by Revenue</option>
                    <option value="effort">Sort by Effort (Low First)</option>
                </select>
            </div>

            {/* Scenario Cards */}
            <div style={{ display: 'grid', gap: '16px' }}>
                {filteredScenarios.map(scenario => (
                    <div
                        key={scenario.id}
                        style={{
                            background: 'white',
                            borderRadius: '12px',
                            border: '1px solid #e5e7eb',
                            padding: '24px',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <span
                                    style={{
                                        width: '12px',
                                        height: '12px',
                                        borderRadius: '50%',
                                        background: getTypeColor(scenario.type),
                                    }}
                                />
                                <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>{scenario.title}</h3>
                                <span style={{
                                    padding: '4px 12px',
                                    borderRadius: '9999px',
                                    fontSize: '12px',
                                    textTransform: 'capitalize',
                                    background: '#f3f4f6',
                                }}>
                                    {scenario.type}
                                </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{
                                    padding: '4px 12px',
                                    borderRadius: '9999px',
                                    fontSize: '12px',
                                    ...Object.fromEntries(getEffortBadge(scenario.effort).split(';').filter(Boolean).map(s => s.split(':').map(x => x.trim()))),
                                }}>
                                    {scenario.effort} effort
                                </span>
                                <span style={{
                                    padding: '4px 12px',
                                    borderRadius: '9999px',
                                    fontSize: '12px',
                                    background: scenario.confidence > 0.8 ? '#dcfce7' : scenario.confidence > 0.6 ? '#fef3c7' : '#fee2e2',
                                    color: scenario.confidence > 0.8 ? '#166534' : scenario.confidence > 0.6 ? '#92400e' : '#991b1b',
                                }}>
                                    {(scenario.confidence * 100).toFixed(0)}% confidence
                                </span>
                            </div>
                        </div>

                        <p style={{ color: '#4b5563', marginBottom: '16px', lineHeight: 1.6 }}>{scenario.description}</p>

                        <div style={{ display: 'flex', gap: '24px', marginBottom: '16px', fontSize: '14px', color: '#6b7280' }}>
                            <span>⏱️ {scenario.timeframe}</span>
                            {scenario.potentialRevenue && <span>💰 ${scenario.potentialRevenue.toLocaleString()} potential</span>}
                        </div>

                        {/* Evidence */}
                        <details style={{ marginBottom: '16px' }}>
                            <summary style={{ cursor: 'pointer', fontSize: '14px', fontWeight: 500, color: '#4b5563' }}>
                                📊 View Evidence ({scenario.evidence.length} sources)
                            </summary>
                            <div style={{ marginTop: '12px', paddingLeft: '16px', borderLeft: '2px solid #e5e7eb' }}>
                                {scenario.evidence.map((e, i) => (
                                    <div key={i} style={{ marginBottom: '8px', fontSize: '14px' }}>
                                        <strong>{e.source}</strong>: {e.data}
                                        <span style={{ color: '#9ca3af', marginLeft: '8px' }}>({(e.confidence * 100).toFixed(0)}%)</span>
                                    </div>
                                ))}
                            </div>
                        </details>

                        {/* Actions */}
                        {scenario.status === 'new' && (
                            <div style={{ display: 'flex', gap: '12px' }}>
                                <button
                                    onClick={() => handleAction(scenario.id, 'start')}
                                    style={{
                                        padding: '10px 20px',
                                        background: '#3b82f6',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                        fontWeight: 500,
                                    }}
                                >
                                    Start Working on This
                                </button>
                                <button
                                    onClick={() => handleAction(scenario.id, 'dismiss')}
                                    style={{
                                        padding: '10px 20px',
                                        background: 'transparent',
                                        color: '#6b7280',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '8px',
                                        cursor: 'pointer',
                                    }}
                                >
                                    Not Interested
                                </button>
                            </div>
                        )}
                        {scenario.status === 'in_progress' && (
                            <span style={{ color: '#3b82f6', fontWeight: 500 }}>🚀 In Progress</span>
                        )}
                        {scenario.status === 'dismissed' && (
                            <span style={{ color: '#9ca3af' }}>Dismissed</span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
