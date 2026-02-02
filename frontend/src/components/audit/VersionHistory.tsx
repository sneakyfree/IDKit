'use client';

import { useState, useEffect } from 'react';
import {
    Clock,
    GitBranch,
    GitCommit,
    ChevronRight,
    ChevronDown,
    RefreshCw,
    Check,
    X,
    Diff,
    Eye,
    RotateCcw,
} from 'lucide-react';

interface VersionEntry {
    version_id: string;
    version_number: string;
    entity_type: 'model' | 'rule' | 'config' | 'snapshot';
    entity_name: string;
    created_at: string;
    created_by: string;
    changes: {
        field: string;
        old_value: any;
        new_value: any;
    }[];
    commit_message?: string;
    is_current: boolean;
    hash: string;
}

interface VersionHistoryProps {
    entityType?: 'model' | 'rule' | 'config' | 'snapshot' | 'all';
    entityId?: string;
    onRestore?: (versionId: string) => void;
    onCompare?: (versionA: string, versionB: string) => void;
    maxItems?: number;
}

// Mock data for demonstration
const mockVersions: VersionEntry[] = [
    {
        version_id: 'v-001',
        version_number: '3.2.1',
        entity_type: 'model',
        entity_name: 'Pricing Engine',
        created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        created_by: 'system',
        changes: [
            { field: 'base_rate_multiplier', old_value: 1.2, new_value: 1.25 },
            { field: 'engagement_weight', old_value: 0.3, new_value: 0.35 },
        ],
        commit_message: 'Updated pricing weights for Q1 2026',
        is_current: true,
        hash: 'a7f3d2e',
    },
    {
        version_id: 'v-002',
        version_number: '3.2.0',
        entity_type: 'model',
        entity_name: 'Pricing Engine',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        created_by: 'admin@idkit.io',
        changes: [
            { field: 'min_sponsorship', old_value: 500, new_value: 750 },
        ],
        commit_message: 'Raised minimum sponsorship threshold',
        is_current: false,
        hash: 'b8e4c3f',
    },
    {
        version_id: 'v-003',
        version_number: '2.1.0',
        entity_type: 'rule',
        entity_name: 'FTC Disclosure',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        created_by: 'system',
        changes: [
            { field: 'required_text', old_value: '#ad', new_value: '#ad #sponsored' },
        ],
        commit_message: 'Updated FTC disclosure requirements',
        is_current: true,
        hash: 'c9f5d4g',
    },
    {
        version_id: 'v-004',
        version_number: '1.5.0',
        entity_type: 'config',
        entity_name: 'Agent Guardrails',
        created_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
        created_by: 'creator@example.com',
        changes: [
            { field: 'auto_publish', old_value: true, new_value: false },
            { field: 'risk_tolerance', old_value: 'high', new_value: 'medium' },
        ],
        commit_message: 'Tightened agent permissions',
        is_current: true,
        hash: 'd0g6e5h',
    },
];

export function VersionHistory({
    entityType = 'all',
    entityId,
    onRestore,
    onCompare,
    maxItems = 50,
}: VersionHistoryProps) {
    const [versions, setVersions] = useState<VersionEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set());
    const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
    const [filter, setFilter] = useState<string>(entityType);

    useEffect(() => {
        // Simulated API call
        setLoading(true);
        setTimeout(() => {
            let filtered = mockVersions;
            if (entityType !== 'all') {
                filtered = mockVersions.filter((v) => v.entity_type === entityType);
            }
            setVersions(filtered.slice(0, maxItems));
            setLoading(false);
        }, 500);
    }, [entityType, entityId, maxItems]);

    const toggleExpanded = (versionId: string) => {
        const newExpanded = new Set(expandedVersions);
        if (newExpanded.has(versionId)) {
            newExpanded.delete(versionId);
        } else {
            newExpanded.add(versionId);
        }
        setExpandedVersions(newExpanded);
    };

    const toggleCompareSelect = (versionId: string) => {
        if (selectedForCompare.includes(versionId)) {
            setSelectedForCompare(selectedForCompare.filter((id) => id !== versionId));
        } else if (selectedForCompare.length < 2) {
            setSelectedForCompare([...selectedForCompare, versionId]);
        }
    };

    const handleCompare = () => {
        if (selectedForCompare.length === 2 && onCompare) {
            onCompare(selectedForCompare[0], selectedForCompare[1]);
        }
    };

    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    };

    const getEntityTypeColor = (type: string) => {
        switch (type) {
            case 'model': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
            case 'rule': return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400';
            case 'config': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
            case 'snapshot': return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400';
            default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';
        }
    };

    const renderDiffValue = (value: any) => {
        if (typeof value === 'boolean') {
            return value ? <Check className="w-4 h-4 text-green-500" /> : <X className="w-4 h-4 text-red-500" />;
        }
        if (typeof value === 'number') {
            return <span className="font-mono">{value}</span>;
        }
        return <span className="font-mono text-sm">{String(value)}</span>;
    };

    if (loading) {
        return (
            <div className="p-8 flex justify-center">
                <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                            <GitBranch className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white">Version History</h3>
                            <p className="text-sm text-gray-500">{versions.length} versions tracked</p>
                        </div>
                    </div>

                    {selectedForCompare.length === 2 && (
                        <button
                            onClick={handleCompare}
                            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                        >
                            <Diff className="w-4 h-4" />
                            Compare Selected
                        </button>
                    )}
                </div>

                {/* Filter */}
                <div className="flex gap-2 overflow-x-auto">
                    {['all', 'model', 'rule', 'config', 'snapshot'].map((type) => (
                        <button
                            key={type}
                            onClick={() => setFilter(type)}
                            className={`px-3 py-1.5 text-sm rounded-full whitespace-nowrap transition-colors ${filter === type
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                                }`}
                        >
                            {type.charAt(0).toUpperCase() + type.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Version List */}
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {versions
                    .filter((v) => filter === 'all' || v.entity_type === filter)
                    .map((version) => (
                        <div key={version.version_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                            {/* Version Header */}
                            <div className="p-4 flex items-center gap-3">
                                <button
                                    onClick={() => toggleExpanded(version.version_id)}
                                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                                >
                                    {expandedVersions.has(version.version_id) ? (
                                        <ChevronDown className="w-4 h-4 text-gray-500" />
                                    ) : (
                                        <ChevronRight className="w-4 h-4 text-gray-500" />
                                    )}
                                </button>

                                <input
                                    type="checkbox"
                                    checked={selectedForCompare.includes(version.version_id)}
                                    onChange={() => toggleCompareSelect(version.version_id)}
                                    disabled={selectedForCompare.length >= 2 && !selectedForCompare.includes(version.version_id)}
                                    className="w-4 h-4 rounded border-gray-300"
                                />

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <GitCommit className="w-4 h-4 text-gray-400" />
                                        <span className="font-mono text-sm text-gray-600 dark:text-gray-400">
                                            {version.hash}
                                        </span>
                                        <span className={`px-2 py-0.5 text-xs rounded-full ${getEntityTypeColor(version.entity_type)}`}>
                                            {version.entity_type}
                                        </span>
                                        <span className="font-medium text-gray-900 dark:text-white">
                                            {version.entity_name}
                                        </span>
                                        <span className="text-sm text-gray-500">v{version.version_number}</span>
                                        {version.is_current && (
                                            <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                                                Current
                                            </span>
                                        )}
                                    </div>
                                    {version.commit_message && (
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 truncate">
                                            {version.commit_message}
                                        </p>
                                    )}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-gray-500">
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        {formatTime(version.created_at)}
                                    </span>
                                    <span>{version.created_by}</span>
                                </div>

                                <div className="flex gap-1">
                                    <button
                                        onClick={() => toggleExpanded(version.version_id)}
                                        className="p-2 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg"
                                        title="View changes"
                                    >
                                        <Eye className="w-4 h-4" />
                                    </button>
                                    {!version.is_current && onRestore && (
                                        <button
                                            onClick={() => onRestore(version.version_id)}
                                            className="p-2 text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg"
                                            title="Restore this version"
                                        >
                                            <RotateCcw className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Expanded Changes */}
                            {expandedVersions.has(version.version_id) && (
                                <div className="px-4 pb-4 ml-12">
                                    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-2">
                                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                            Changes ({version.changes.length})
                                        </h4>
                                        {version.changes.map((change, i) => (
                                            <div
                                                key={i}
                                                className="flex items-center gap-4 p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                                            >
                                                <span className="font-mono text-sm text-gray-600 dark:text-gray-400 min-w-32">
                                                    {change.field}
                                                </span>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-red-600 dark:text-red-400 line-through">
                                                        {renderDiffValue(change.old_value)}
                                                    </span>
                                                    <ChevronRight className="w-4 h-4 text-gray-400" />
                                                    <span className="text-green-600 dark:text-green-400">
                                                        {renderDiffValue(change.new_value)}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
            </div>

            {versions.length === 0 && (
                <div className="p-8 text-center text-gray-500">
                    No version history available
                </div>
            )}
        </div>
    );
}

export default VersionHistory;
