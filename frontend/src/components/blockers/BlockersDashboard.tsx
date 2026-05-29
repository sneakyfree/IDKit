'use client';

import { useState, useEffect } from 'react';

import { apiRequest } from '@/lib/api';

interface Blocker {
    id: string;
    title: string;
    category: 'technical' | 'content' | 'monetization' | 'compliance' | 'growth';
    severity: 'critical' | 'high' | 'medium' | 'low';
    whyNot: string;
    evidence: Array<{
        source: string;
        data: string;
        confidence: number;
    }>;
    impact: number; // 0-100
    detectedAt: string;
}

interface Unlocker {
    id: string;
    blockerId: string;
    title: string;
    whatToDo: string;
    timeframe: 'quick_win' | '30_days' | '90_days';
    effort: 'low' | 'medium' | 'high';
    proofRequired: string[];
    status: 'pending' | 'in_progress' | 'completed';
}

export default function BlockersDashboard() {
    const [blockers, setBlockers] = useState<Blocker[]>([]);
    const [unlockers, setUnlockers] = useState<Unlocker[]>([]);
    const [selectedBlocker, setSelectedBlocker] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>('all');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [blockersRes, unlockersRes] = await Promise.allSettled([
                    apiRequest<Blocker[]>('/api/v1/blockers'),
                    apiRequest<Unlocker[]>('/api/v1/unlockers'),
                ]);
                if (blockersRes.status === 'fulfilled') {
                    setBlockers(Array.isArray(blockersRes.value) ? blockersRes.value : []);
                }
                if (unlockersRes.status === 'fulfilled') {
                    setUnlockers(Array.isArray(unlockersRes.value) ? unlockersRes.value : []);
                }
            } catch {
                // silently fail
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const getSeverityColor = (severity: string) => {
        const colors: Record<string, { bg: string; text: string; border: string }> = {
            critical: { bg: '#fef2f2', text: '#dc2626', border: '#fca5a5' },
            high: { bg: '#fff7ed', text: '#ea580c', border: '#fdba74' },
            medium: { bg: '#fefce8', text: '#ca8a04', border: '#fde047' },
            low: { bg: '#f0fdf4', text: '#16a34a', border: '#86efac' },
        };
        return colors[severity] || colors.medium;
    };

    const getCategoryIcon = (category: string) => {
        const icons: Record<string, string> = {
            technical: '⚙️',
            content: '📝',
            monetization: '💰',
            compliance: '⚠️',
            growth: '📈',
        };
        return icons[category] || '❓';
    };

    const getTimeframeBadge = (timeframe: string) => {
        const labels: Record<string, { label: string; color: string }> = {
            quick_win: { label: '⚡ Quick Win (<1 hr)', color: '#10b981' },
            '30_days': { label: '📅 30 Days', color: '#3b82f6' },
            '90_days': { label: '🎯 90 Days', color: '#8b5cf6' },
        };
        return labels[timeframe] || { label: timeframe, color: '#6b7280' };
    };

    const filteredBlockers = blockers.filter(b =>
        filter === 'all' || b.category === filter || b.severity === filter
    );

    const handleStartUnlocker = (id: string) => {
        setUnlockers(prev => prev.map(u => u.id === id ? { ...u, status: 'in_progress' } : u));
    };

    const handleCompleteUnlocker = (id: string) => {
        setUnlockers(prev => prev.map(u => u.id === id ? { ...u, status: 'completed' } : u));
    };

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            <header style={{ marginBottom: '32px' }}>
                <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>
                    🚧 Blockers & Unlockers
                </h1>
                <p style={{ color: '#6b7280', fontSize: '16px' }}>
                    Identified obstacles preventing growth and the actions to overcome them
                </p>
            </header>

            {/* Summary Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div style={{ background: '#fef2f2', padding: '16px', borderRadius: '12px', border: '1px solid #fca5a5' }}>
                    <div style={{ fontSize: '14px', color: '#dc2626' }}>Critical</div>
                    <div style={{ fontSize: '28px', fontWeight: 700, color: '#dc2626' }}>
                        {blockers.filter(b => b.severity === 'critical').length}
                    </div>
                </div>
                <div style={{ background: '#fff7ed', padding: '16px', borderRadius: '12px', border: '1px solid #fdba74' }}>
                    <div style={{ fontSize: '14px', color: '#ea580c' }}>High</div>
                    <div style={{ fontSize: '28px', fontWeight: 700, color: '#ea580c' }}>
                        {blockers.filter(b => b.severity === 'high').length}
                    </div>
                </div>
                <div style={{ background: '#f0fdf4', padding: '16px', borderRadius: '12px', border: '1px solid #86efac' }}>
                    <div style={{ fontSize: '14px', color: '#16a34a' }}>Quick Wins</div>
                    <div style={{ fontSize: '28px', fontWeight: 700, color: '#16a34a' }}>
                        {unlockers.filter(u => u.timeframe === 'quick_win').length}
                    </div>
                </div>
                <div style={{ background: '#eff6ff', padding: '16px', borderRadius: '12px', border: '1px solid #93c5fd' }}>
                    <div style={{ fontSize: '14px', color: '#2563eb' }}>In Progress</div>
                    <div style={{ fontSize: '28px', fontWeight: 700, color: '#2563eb' }}>
                        {unlockers.filter(u => u.status === 'in_progress').length}
                    </div>
                </div>
            </div>

            {/* Filter */}
            <div style={{ marginBottom: '24px' }}>
                <select aria-label="Filter or select option"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '14px' }}
                >
                    <option value="all">All Blockers</option>
                    <option value="critical">Critical Only</option>
                    <option value="high">High Priority</option>
                    <option value="compliance">Compliance</option>
                    <option value="growth">Growth</option>
                    <option value="monetization">Monetization</option>
                    <option value="content">Content</option>
                </select>
            </div>

            {/* Blockers List */}
            <div style={{ display: 'grid', gap: '16px' }}>
                {filteredBlockers.map(blocker => {
                    const colors = getSeverityColor(blocker.severity);
                    const relatedUnlockers = unlockers.filter(u => u.blockerId === blocker.id);

                    return (
                        <div
                            key={blocker.id}
                            style={{
                                background: 'white',
                                borderRadius: '12px',
                                border: `2px solid ${colors.border}`,
                                overflow: 'hidden',
                            }}
                        >
                            {/* Blocker Header */}
                            <div
                                style={{
                                    background: colors.bg,
                                    padding: '20px',
                                    cursor: 'pointer',
                                }}
                                onClick={() => setSelectedBlocker(selectedBlocker === blocker.id ? null : blocker.id)}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span style={{ fontSize: '24px' }}>{getCategoryIcon(blocker.category)}</span>
                                        <div>
                                            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0, color: colors.text }}>
                                                {blocker.title}
                                            </h3>
                                            <p style={{ fontSize: '14px', color: '#6b7280', margin: '4px 0 0 0' }}>
                                                {blocker.category.charAt(0).toUpperCase() + blocker.category.slice(1)} • Impact: {blocker.impact}%
                                            </p>
                                        </div>
                                    </div>
                                    <span style={{
                                        padding: '4px 12px',
                                        borderRadius: '9999px',
                                        fontSize: '12px',
                                        fontWeight: 600,
                                        background: colors.text,
                                        color: 'white',
                                        textTransform: 'uppercase',
                                    }}>
                                        {blocker.severity}
                                    </span>
                                </div>
                            </div>

                            {/* Expanded Content */}
                            {selectedBlocker === blocker.id && (
                                <div style={{ padding: '20px', borderTop: `1px solid ${colors.border}` }}>
                                    <div style={{ marginBottom: '20px' }}>
                                        <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Why This is Blocking You</h4>
                                        <p style={{ color: '#4b5563', lineHeight: 1.6 }}>{blocker.whyNot}</p>
                                    </div>

                                    <div style={{ marginBottom: '20px' }}>
                                        <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>Evidence</h4>
                                        {blocker.evidence.map((e, i) => (
                                            <div key={i} style={{
                                                background: '#f9fafb',
                                                padding: '12px',
                                                borderRadius: '8px',
                                                marginBottom: '8px',
                                                fontSize: '14px',
                                            }}>
                                                <strong>{e.source}</strong>: {e.data}
                                                <span style={{ color: '#9ca3af', marginLeft: '8px' }}>({(e.confidence * 100).toFixed(0)}% confidence)</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Unlockers */}
                                    <div>
                                        <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>
                                            🔓 Actions to Fix This ({relatedUnlockers.length})
                                        </h4>
                                        {relatedUnlockers.map(unlocker => {
                                            const timeframe = getTimeframeBadge(unlocker.timeframe);
                                            return (
                                                <div
                                                    key={unlocker.id}
                                                    style={{
                                                        background: '#f9fafb',
                                                        padding: '16px',
                                                        borderRadius: '8px',
                                                        marginBottom: '8px',
                                                        border: '1px solid #e5e7eb',
                                                    }}
                                                >
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                                                        <h5 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>{unlocker.title}</h5>
                                                        <span style={{
                                                            padding: '4px 10px',
                                                            borderRadius: '9999px',
                                                            fontSize: '11px',
                                                            color: 'white',
                                                            background: timeframe.color,
                                                        }}>
                                                            {timeframe.label}
                                                        </span>
                                                    </div>
                                                    <p style={{ fontSize: '14px', color: '#4b5563', margin: '0 0 12px 0' }}>{unlocker.whatToDo}</p>

                                                    <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '12px' }}>
                                                        <strong>Proof needed:</strong> {unlocker.proofRequired.join(', ')}
                                                    </div>

                                                    {unlocker.status === 'pending' && (
                                                        <button
                                                            onClick={() => handleStartUnlocker(unlocker.id)}
                                                            style={{
                                                                padding: '8px 16px',
                                                                background: '#3b82f6',
                                                                color: 'white',
                                                                border: 'none',
                                                                borderRadius: '6px',
                                                                cursor: 'pointer',
                                                                fontSize: '13px',
                                                                fontWeight: 500,
                                                            }}
                                                        >
                                                            Start This Action
                                                        </button>
                                                    )}
                                                    {unlocker.status === 'in_progress' && (
                                                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                            <span style={{ color: '#3b82f6', fontWeight: 500 }}>🚀 In Progress</span>
                                                            <button
                                                                onClick={() => handleCompleteUnlocker(unlocker.id)}
                                                                style={{
                                                                    padding: '6px 12px',
                                                                    background: '#10b981',
                                                                    color: 'white',
                                                                    border: 'none',
                                                                    borderRadius: '6px',
                                                                    cursor: 'pointer',
                                                                    fontSize: '12px',
                                                                }}
                                                            >
                                                                Mark Complete
                                                            </button>
                                                        </div>
                                                    )}
                                                    {unlocker.status === 'completed' && (
                                                        <span style={{ color: '#10b981', fontWeight: 500 }}>✅ Completed</span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
