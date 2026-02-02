import React from 'react';

interface Contradiction {
    field: string;
    userValue: string | number;
    apiValue: string | number;
    source: string;
    severity: 'high' | 'medium' | 'low';
}

interface ContradictionAlertProps {
    contradictions: Contradiction[];
    onResolve?: (field: string, useApiValue: boolean) => void;
    onDismiss?: () => void;
}

export default function ContradictionAlert({ contradictions, onResolve, onDismiss }: ContradictionAlertProps) {
    if (contradictions.length === 0) return null;

    const getSeverityStyle = (severity: string) => {
        const styles = {
            high: { border: '#fca5a5', bg: '#fef2f2', icon: '⚠️' },
            medium: { border: '#fde047', bg: '#fefce8', icon: '⚡' },
            low: { border: '#93c5fd', bg: '#eff6ff', icon: 'ℹ️' },
        };
        return styles[severity as keyof typeof styles] || styles.medium;
    };

    return (
        <div style={{
            background: '#fef2f2',
            border: '2px solid #fca5a5',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '24px',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '24px' }}>⚠️</span>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#dc2626' }}>
                            Data Contradiction Detected
                        </h3>
                        <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#b91c1c' }}>
                            {contradictions.length} field{contradictions.length > 1 ? 's' : ''} differ from verified sources
                        </p>
                    </div>
                </div>
                {onDismiss && (
                    <button
                        onClick={onDismiss}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '20px',
                            color: '#9ca3af',
                        }}
                    >
                        ×
                    </button>
                )}
            </div>

            <div style={{ display: 'grid', gap: '12px' }}>
                {contradictions.map((c, i) => {
                    const style = getSeverityStyle(c.severity);
                    return (
                        <div
                            key={i}
                            style={{
                                background: 'white',
                                border: `1px solid ${style.border}`,
                                borderRadius: '8px',
                                padding: '16px',
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                <div>
                                    <span style={{ fontSize: '14px', fontWeight: 600 }}>{c.field}</span>
                                    <span style={{
                                        marginLeft: '8px',
                                        padding: '2px 8px',
                                        borderRadius: '9999px',
                                        fontSize: '11px',
                                        background: style.bg,
                                        color: '#6b7280',
                                    }}>
                                        {style.icon} {c.severity}
                                    </span>
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                                <div style={{
                                    padding: '12px',
                                    background: '#fee2e2',
                                    borderRadius: '6px',
                                    fontSize: '14px',
                                }}>
                                    <div style={{ fontSize: '11px', color: '#991b1b', marginBottom: '4px' }}>You entered:</div>
                                    <strong>{String(c.userValue)}</strong>
                                </div>
                                <div style={{
                                    padding: '12px',
                                    background: '#d1fae5',
                                    borderRadius: '6px',
                                    fontSize: '14px',
                                }}>
                                    <div style={{ fontSize: '11px', color: '#166534', marginBottom: '4px' }}>From {c.source}:</div>
                                    <strong>{String(c.apiValue)}</strong>
                                </div>
                            </div>

                            {onResolve && (
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        onClick={() => onResolve(c.field, false)}
                                        style={{
                                            flex: 1,
                                            padding: '8px 16px',
                                            background: 'transparent',
                                            border: '1px solid #e5e7eb',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            fontSize: '13px',
                                        }}
                                    >
                                        Keep My Value
                                    </button>
                                    <button
                                        onClick={() => onResolve(c.field, true)}
                                        style={{
                                            flex: 1,
                                            padding: '8px 16px',
                                            background: '#10b981',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                        }}
                                    >
                                        Use Verified Value
                                    </button>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export type { Contradiction };
