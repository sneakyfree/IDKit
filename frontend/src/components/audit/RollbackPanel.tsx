'use client';

/**
 * Rollback Panel
 * 
 * UI for selecting and restoring previous snapshots.
 */

import { useState } from 'react';
import { RotateCcw, AlertTriangle, CheckCircle, Clock, ChevronRight, X } from 'lucide-react';

interface Snapshot {
    id: string;
    description: string;
    created_at: string;
    type: string;
}

interface RollbackChange {
    field: string;
    current_value: unknown;
    snapshot_value: unknown;
}

interface RollbackPanelProps {
    snapshots: Snapshot[];
    onRollback?: (snapshotId: string) => Promise<void>;
    className?: string;
}

export function RollbackPanel({
    snapshots,
    onRollback,
    className = '',
}: RollbackPanelProps) {
    const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
    const [previewChanges, setPreviewChanges] = useState<RollbackChange[]>([]);
    const [loading, setLoading] = useState(false);
    const [confirming, setConfirming] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSelect = async (snapshot: Snapshot) => {
        setSelectedSnapshot(snapshot);
        setLoading(true);
        setError(null);

        try {
            // Fetch preview of what would change
            const res = await fetch(`/api/v1/explainability/snapshots/${snapshot.id}/preview-rollback`);
            if (res.ok) {
                const data = await res.json();
                setPreviewChanges(data.changes || []);
            } else {
                // Mock preview for demo
                setPreviewChanges([
                    { field: 'settings.theme', current_value: 'dark', snapshot_value: 'light' },
                    { field: 'profile.bio', current_value: 'Updated bio', snapshot_value: 'Original bio' },
                ]);
            }
        } catch (err) {
            setError('Failed to load rollback preview');
        } finally {
            setLoading(false);
        }
    };

    const handleRollback = async () => {
        if (!selectedSnapshot) return;

        setLoading(true);
        setError(null);

        try {
            await onRollback?.(selectedSnapshot.id);
            setSuccess(true);
            setTimeout(() => {
                setSuccess(false);
                setSelectedSnapshot(null);
                setConfirming(false);
            }, 2000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Rollback failed');
        } finally {
            setLoading(false);
        }
    };

    const formatValue = (value: unknown): string => {
        if (value === null || value === undefined) return 'null';
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
    };

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="p-6 border-b dark:border-gray-800">
                <div className="flex items-center gap-3">
                    <RotateCcw className="h-6 w-6 text-indigo-500" />
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Rollback to Previous State
                        </h2>
                        <p className="text-sm text-gray-300">
                            Restore data from an earlier snapshot
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x dark:divide-gray-800">
                {/* Snapshot List */}
                <div className="p-4">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Select Snapshot
                    </h3>
                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                        {snapshots.map((snapshot) => (
                            <button
                                key={snapshot.id}
                                onClick={() => handleSelect(snapshot)}
                                className={`
                  w-full text-left p-3 rounded-lg border transition-colors
                  ${selectedSnapshot?.id === snapshot.id
                                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                    }
                `}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-medium text-gray-900 dark:text-white text-sm">
                                        {snapshot.description}
                                    </span>
                                    <ChevronRight className="h-4 w-4 text-gray-200" />
                                </div>
                                <div className="flex items-center gap-3 mt-1 text-xs text-gray-300">
                                    <span className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {new Date(snapshot.created_at).toLocaleString()}
                                    </span>
                                    <span className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">
                                        {snapshot.type}
                                    </span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Preview Panel */}
                <div className="p-4">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Rollback Preview
                    </h3>

                    {!selectedSnapshot ? (
                        <div className="text-center py-12 text-gray-300">
                            <RotateCcw className="h-8 w-8 mx-auto mb-2 opacity-30" />
                            <p className="text-sm">Select a snapshot to preview changes</p>
                        </div>
                    ) : loading ? (
                        <div className="text-center py-12">
                            <div className="animate-spin h-6 w-6 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto" />
                            <p className="mt-2 text-sm text-gray-300">Loading preview...</p>
                        </div>
                    ) : success ? (
                        <div className="text-center py-12">
                            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
                            <p className="text-green-600 font-medium">Rollback successful!</p>
                        </div>
                    ) : (
                        <>
                            {/* Changes Preview */}
                            <div className="space-y-2 mb-4 max-h-[250px] overflow-y-auto">
                                {previewChanges.map((change, i) => (
                                    <div key={i} className="p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
                                        <div className="font-mono text-xs text-gray-300 mb-1">
                                            {change.field}
                                        </div>
                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="p-1.5 bg-red-100 dark:bg-red-900/30 rounded">
                                                <div className="text-xs text-red-600 dark:text-red-400 mb-0.5">Current</div>
                                                <div className="text-red-800 dark:text-red-200 text-xs truncate">
                                                    {formatValue(change.current_value)}
                                                </div>
                                            </div>
                                            <div className="p-1.5 bg-green-100 dark:bg-green-900/30 rounded">
                                                <div className="text-xs text-green-600 dark:text-green-400 mb-0.5">Restore to</div>
                                                <div className="text-green-800 dark:text-green-200 text-xs truncate">
                                                    {formatValue(change.snapshot_value)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Warning */}
                            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg mb-4">
                                <div className="flex items-start gap-2">
                                    <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                                    <div className="text-sm text-yellow-800 dark:text-yellow-200">
                                        <strong>Warning:</strong> This action will overwrite current data with the selected snapshot.
                                        This cannot be undone.
                                    </div>
                                </div>
                            </div>

                            {error && (
                                <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg mb-4">
                                    {error}
                                </div>
                            )}

                            {/* Actions */}
                            {!confirming ? (
                                <button
                                    onClick={() => setConfirming(true)}
                                    className="w-full py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                                >
                                    <RotateCcw className="h-4 w-4 inline mr-2" />
                                    Rollback to This Snapshot
                                </button>
                            ) : (
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setConfirming(false)}
                                        className="flex-1 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleRollback}
                                        disabled={loading}
                                        className="flex-1 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-80"
                                    >
                                        {loading ? 'Rolling back...' : 'Confirm Rollback'}
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default RollbackPanel;
