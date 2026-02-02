import React from 'react';

type SourceType = 'api' | 'user_input' | 'calculated' | 'estimated' | 'unknown';

interface SourceBadgeProps {
    source: SourceType;
    timestamp?: string;
    showTooltip?: boolean;
}

const SOURCE_CONFIG: Record<SourceType, { label: string; color: string; bg: string; icon: string }> = {
    api: { label: 'API Verified', color: '#059669', bg: '#d1fae5', icon: '✓' },
    user_input: { label: 'User Input', color: '#2563eb', bg: '#dbeafe', icon: '✎' },
    calculated: { label: 'Calculated', color: '#7c3aed', bg: '#ede9fe', icon: '∑' },
    estimated: { label: 'Estimated', color: '#d97706', bg: '#fef3c7', icon: '~' },
    unknown: { label: 'Unknown', color: '#6b7280', bg: '#f3f4f6', icon: '?' },
};

export default function SourceBadge({ source, timestamp, showTooltip = true }: SourceBadgeProps) {
    const config = SOURCE_CONFIG[source] || SOURCE_CONFIG.unknown;

    return (
        <span
            title={showTooltip ? `${config.label}${timestamp ? ` • ${timestamp}` : ''}` : undefined}
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 8px',
                borderRadius: '9999px',
                fontSize: '11px',
                fontWeight: 500,
                color: config.color,
                background: config.bg,
                cursor: showTooltip ? 'help' : 'default',
            }}
        >
            <span>{config.icon}</span>
            <span>{config.label}</span>
        </span>
    );
}

export { SOURCE_CONFIG };
export type { SourceType };
