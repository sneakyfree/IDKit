'use client';

import { useState } from 'react';

type ViewType = 'creator' | 'manager' | 'technical' | 'audit';

interface ViewSwitcherProps {
    activeView: ViewType;
    onViewChange: (view: ViewType) => void;
}

const VIEW_CONFIG: Record<ViewType, { label: string; icon: string; description: string }> = {
    creator: {
        label: 'Creator',
        icon: '👤',
        description: 'Simple, actionable insights',
    },
    manager: {
        label: 'Manager',
        icon: '📋',
        description: 'Client-ready reports',
    },
    technical: {
        label: 'Technical',
        icon: '⚙️',
        description: 'Data sources & statistics',
    },
    audit: {
        label: 'Audit',
        icon: '📊',
        description: 'Full provenance trail',
    },
};

export default function ViewSwitcher({ activeView, onViewChange }: ViewSwitcherProps) {
    return (
        <div style={{
            display: 'flex',
            gap: '8px',
            padding: '4px',
            background: '#f3f4f6',
            borderRadius: '12px',
            width: 'fit-content',
        }}>
            {(Object.keys(VIEW_CONFIG) as ViewType[]).map(view => {
                const config = VIEW_CONFIG[view];
                const isActive = view === activeView;

                return (
                    <button
                        key={view}
                        onClick={() => onViewChange(view)}
                        title={config.description}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '10px 16px',
                            border: 'none',
                            borderRadius: '8px',
                            background: isActive ? 'white' : 'transparent',
                            boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: isActive ? 600 : 400,
                            color: isActive ? '#1f2937' : '#6b7280',
                            transition: 'all 0.2s',
                        }}
                    >
                        <span>{config.icon}</span>
                        <span>{config.label}</span>
                    </button>
                );
            })}
        </div>
    );
}

export { VIEW_CONFIG };
export type { ViewType };
