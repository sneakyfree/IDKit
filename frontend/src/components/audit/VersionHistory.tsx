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
import { apiRequest } from '@/lib/api';

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
        async function fetchVersions() {
            setLoading(true);
            try {
                const params = new URLSearchParams();
                if (entityType !== 'all') params.set('entity_type', entityType);
                if (entityId) params.set('entity_id', entityId);
                params.set('limit', String(maxItems));
                const response = await apiRequest<VersionEntry[]>(`/api/v1/versions?${params.toString()}`);
                setVersions(Array.isArray(response) ? response : []);
            } catch {
                setVersions([]);
            } finally {
                setLoading(false);
            }
        }
        fetchVersions();
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
            default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200';
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
                <RefreshCw className="w-6 h-6 animate-spin text-gray-200" />
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
                            <p className="text-sm text-gray-300">{versions.length} versions tracked</p>
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
                                : 'bg-gray-100 dark:bg-gray-700 text-gray-200 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
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
                                        <ChevronDown className="w-4 h-4 text-gray-300" />
                                    ) : (
                                        <ChevronRight className="w-4 h-4 text-gray-300" />
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
                                        <GitCommit className="w-4 h-4 text-gray-200" />
                                        <span className="font-mono text-sm text-gray-200 dark:text-gray-200">
                                            {version.hash}
                                        </span>
                                        <span className={`px-2 py-0.5 text-xs rounded-full ${getEntityTypeColor(version.entity_type)}`}>
                                            {version.entity_type}
                                        </span>
                                        <span className="font-medium text-gray-900 dark:text-white">
                                            {version.entity_name}
                                        </span>
                                        <span className="text-sm text-gray-300">v{version.version_number}</span>
                                        {version.is_current && (
                                            <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                                                Current
                                            </span>
                                        )}
                                    </div>
                                    {version.commit_message && (
                                        <p className="text-sm text-gray-200 dark:text-gray-200 mt-1 truncate">
                                            {version.commit_message}
                                        </p>
                                    )}
                                </div>

                                <div className="flex items-center gap-4 text-sm text-gray-300">
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        {formatTime(version.created_at)}
                                    </span>
                                    <span>{version.created_by}</span>
                                </div>

                                <div className="flex gap-1">
                                    <button
                                        onClick={() => toggleExpanded(version.version_id)}
                                        className="p-2 text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg"
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
                                                <span className="font-mono text-sm text-gray-200 dark:text-gray-200 min-w-32">
                                                    {change.field}
                                                </span>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-red-600 dark:text-red-400 line-through">
                                                        {renderDiffValue(change.old_value)}
                                                    </span>
                                                    <ChevronRight className="w-4 h-4 text-gray-200" />
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
                <div className="p-8 text-center text-gray-300">
                    No version history available
                </div>
            )}
        </div>
    );
}

export default VersionHistory;
