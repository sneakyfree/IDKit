'use client';

/**
 * Snapshot Browser
 * 
 * View and explore immutable audit snapshots for reproducibility.
 */

import { useState, useEffect } from 'react';
import { Camera, Search, Download, ChevronRight, Clock, Hash, Filter } from 'lucide-react';

interface Snapshot {
    id: string;
    type: string;
    created_at: string;
    content_hash: string;
    description: string;
    size_bytes: number;
    metadata: Record<string, unknown>;
}

interface SnapshotBrowserProps {
    className?: string;
}

export function SnapshotBrowser({ className = '' }: SnapshotBrowserProps) {
    const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
    const [filter, setFilter] = useState('');
    const [typeFilter, setTypeFilter] = useState<string | null>(null);

    useEffect(() => {
        fetchSnapshots();
    }, []);

    const fetchSnapshots = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/v1/explainability/snapshots');
            if (res.ok) {
                const data = await res.json();
                setSnapshots(data.snapshots || []);
            }
        } catch (error) {
            console.error('Failed to fetch snapshots:', error);
            // Mock data for demo
            setSnapshots([
                {
                    id: 'snap-001',
                    type: 'analytics_report',
                    created_at: '2026-01-25T12:00:00Z',
                    content_hash: 'sha256:abc123...',
                    description: 'Weekly analytics snapshot',
                    size_bytes: 45678,
                    metadata: { model_version: '2.3.1' },
                },
                {
                    id: 'snap-002',
                    type: 'recommendation',
                    created_at: '2026-01-24T15:30:00Z',
                    content_hash: 'sha256:def456...',
                    description: 'Content recommendation decision',
                    size_bytes: 12345,
                    metadata: { confidence: 0.87 },
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const downloadSnapshot = async (id: string) => {
        try {
            const res = await fetch(`/api/v1/explainability/snapshots/${id}/download`);
            if (res.ok) {
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `snapshot-${id}.json`;
                a.click();
            }
        } catch (error) {
            console.error('Failed to download:', error);
        }
    };

    const filteredSnapshots = snapshots.filter(s => {
        const matchesText = !filter ||
            s.description.toLowerCase().includes(filter.toLowerCase()) ||
            s.id.includes(filter);
        const matchesType = !typeFilter || s.type === typeFilter;
        return matchesText && matchesType;
    });

    const snapshotTypes = [...new Set(snapshots.map(s => s.type))];

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl ${className}`}>
            {/* Header */}
            <div className="p-6 border-b dark:border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <Camera className="h-6 w-6 text-indigo-500" />
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                Audit Snapshots
                            </h2>
                            <p className="text-sm text-gray-500">
                                Immutable state captures for reproducibility
                            </p>
                        </div>
                    </div>
                    <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-sm rounded-full">
                        {snapshots.length} snapshots
                    </span>
                </div>

                {/* Filters */}
                <div className="flex gap-3">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search snapshots..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border dark:border-gray-700 rounded-lg"
                        />
                    </div>
                    <select
                        value={typeFilter || ''}
                        onChange={(e) => setTypeFilter(e.target.value || null)}
                        className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border dark:border-gray-700 rounded-lg"
                    >
                        <option value="">All Types</option>
                        {snapshotTypes.map(type => (
                            <option key={type} value={type}>{type.replace('_', ' ')}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Snapshot List */}
            <div className="divide-y dark:divide-gray-800">
                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading snapshots...</div>
                ) : filteredSnapshots.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">No snapshots found</div>
                ) : (
                    filteredSnapshots.map((snapshot) => (
                        <div
                            key={snapshot.id}
                            className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors ${selectedSnapshot?.id === snapshot.id ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''
                                }`}
                            onClick={() => setSelectedSnapshot(
                                selectedSnapshot?.id === snapshot.id ? null : snapshot
                            )}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <ChevronRight
                                        className={`h-5 w-5 text-gray-400 transition-transform ${selectedSnapshot?.id === snapshot.id ? 'rotate-90' : ''
                                            }`}
                                    />
                                    <div>
                                        <div className="font-medium text-gray-900 dark:text-white">
                                            {snapshot.description}
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                                            <span className="flex items-center gap-1">
                                                <Clock className="h-3.5 w-3.5" />
                                                {new Date(snapshot.created_at).toLocaleString()}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Hash className="h-3.5 w-3.5" />
                                                {snapshot.content_hash.slice(0, 16)}...
                                            </span>
                                            <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                                                {snapshot.type.replace('_', ' ')}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        downloadSnapshot(snapshot.id);
                                    }}
                                    className="p-2 text-gray-500 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg"
                                    title="Download snapshot"
                                >
                                    <Download className="h-4 w-4" />
                                </button>
                            </div>

                            {/* Expanded details */}
                            {selectedSnapshot?.id === snapshot.id && (
                                <div className="mt-4 ml-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Snapshot Details
                                    </h4>
                                    <dl className="grid grid-cols-2 gap-2 text-sm">
                                        <dt className="text-gray-500">ID:</dt>
                                        <dd className="text-gray-900 dark:text-white font-mono">{snapshot.id}</dd>
                                        <dt className="text-gray-500">Full Hash:</dt>
                                        <dd className="text-gray-900 dark:text-white font-mono text-xs break-all">
                                            {snapshot.content_hash}
                                        </dd>
                                        <dt className="text-gray-500">Size:</dt>
                                        <dd className="text-gray-900 dark:text-white">
                                            {(snapshot.size_bytes / 1024).toFixed(2)} KB
                                        </dd>
                                    </dl>
                                    {snapshot.metadata && Object.keys(snapshot.metadata).length > 0 && (
                                        <>
                                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mt-3 mb-2">
                                                Metadata
                                            </h4>
                                            <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
                                                {JSON.stringify(snapshot.metadata, null, 2)}
                                            </pre>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default SnapshotBrowser;
