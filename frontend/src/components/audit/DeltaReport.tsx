'use client';

/**
 * Delta Report Component
 * 
 * Before/after comparison visualization for audit changes.
 */

import { useState } from 'react';
import { GitCompare, ChevronDown, ChevronRight, Plus, Minus, Equal } from 'lucide-react';

interface DeltaChange {
    path: string;
    field: string;
    before: unknown;
    after: unknown;
    change_type: 'added' | 'removed' | 'modified' | 'unchanged';
}

interface DeltaReportProps {
    beforeLabel: string;
    afterLabel: string;
    beforeTimestamp: string;
    afterTimestamp: string;
    changes: DeltaChange[];
    className?: string;
}

function ChangeIcon({ type }: { type: DeltaChange['change_type'] }) {
    switch (type) {
        case 'added':
            return <Plus className="h-4 w-4 text-green-500" />;
        case 'removed':
            return <Minus className="h-4 w-4 text-red-500" />;
        case 'modified':
            return <GitCompare className="h-4 w-4 text-yellow-500" />;
        default:
            return <Equal className="h-4 w-4 text-gray-200" />;
    }
}

function formatValue(value: unknown): string {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
}

export function DeltaReport({
    beforeLabel,
    afterLabel,
    beforeTimestamp,
    afterTimestamp,
    changes,
    className = '',
}: DeltaReportProps) {
    const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
    const [showUnchanged, setShowUnchanged] = useState(false);

    const togglePath = (path: string) => {
        const newExpanded = new Set(expandedPaths);
        if (newExpanded.has(path)) {
            newExpanded.delete(path);
        } else {
            newExpanded.add(path);
        }
        setExpandedPaths(newExpanded);
    };

    const addedCount = changes.filter(c => c.change_type === 'added').length;
    const removedCount = changes.filter(c => c.change_type === 'removed').length;
    const modifiedCount = changes.filter(c => c.change_type === 'modified').length;

    const filteredChanges = showUnchanged
        ? changes
        : changes.filter(c => c.change_type !== 'unchanged');

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="p-6 border-b dark:border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <GitCompare className="h-6 w-6 text-indigo-500" />
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Delta Report
                        </h2>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={showUnchanged}
                            onChange={(e) => setShowUnchanged(e.target.checked)}
                            className="rounded"
                        />
                        <span className="text-gray-200 dark:text-gray-200">Show unchanged</span>
                    </label>
                </div>

                {/* Timestamps */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <div className="text-red-600 dark:text-red-400 font-medium">{beforeLabel}</div>
                        <div className="text-gray-300">{new Date(beforeTimestamp).toLocaleString()}</div>
                    </div>
                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="text-green-600 dark:text-green-400 font-medium">{afterLabel}</div>
                        <div className="text-gray-300">{new Date(afterTimestamp).toLocaleString()}</div>
                    </div>
                </div>

                {/* Summary */}
                <div className="flex items-center gap-4 mt-4 text-sm">
                    <span className="flex items-center gap-1 text-green-600">
                        <Plus className="h-4 w-4" />
                        {addedCount} added
                    </span>
                    <span className="flex items-center gap-1 text-red-600">
                        <Minus className="h-4 w-4" />
                        {removedCount} removed
                    </span>
                    <span className="flex items-center gap-1 text-yellow-600">
                        <GitCompare className="h-4 w-4" />
                        {modifiedCount} modified
                    </span>
                </div>
            </div>

            {/* Changes List */}
            <div className="divide-y dark:divide-gray-800">
                {filteredChanges.length === 0 ? (
                    <div className="p-8 text-center text-gray-300">
                        No changes to display
                    </div>
                ) : (
                    filteredChanges.map((change, index) => (
                        <div
                            key={index}
                            className={`${change.change_type === 'added' ? 'bg-green-50/50 dark:bg-green-900/10' :
                                    change.change_type === 'removed' ? 'bg-red-50/50 dark:bg-red-900/10' :
                                        change.change_type === 'modified' ? 'bg-yellow-50/50 dark:bg-yellow-900/10' :
                                            ''
                                }`}
                        >
                            {/* Change Header */}
                            <button
                                onClick={() => togglePath(change.path)}
                                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/30"
                            >
                                <div className="flex items-center gap-3">
                                    <ChangeIcon type={change.change_type} />
                                    <span className="font-mono text-sm text-gray-700 dark:text-gray-300">
                                        {change.path}
                                    </span>
                                    <span className="text-sm text-gray-300">
                                        .{change.field}
                                    </span>
                                </div>
                                {expandedPaths.has(change.path) ? (
                                    <ChevronDown className="h-5 w-5 text-gray-200" />
                                ) : (
                                    <ChevronRight className="h-5 w-5 text-gray-200" />
                                )}
                            </button>

                            {/* Expanded Diff */}
                            {expandedPaths.has(change.path) && (
                                <div className="px-4 pb-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        {/* Before */}
                                        <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
                                            <div className="text-xs font-medium text-red-700 dark:text-red-400 mb-1">
                                                Before
                                            </div>
                                            <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre-wrap">
                                                {change.change_type === 'added'
                                                    ? <span className="text-gray-200 italic">Not present</span>
                                                    : formatValue(change.before)
                                                }
                                            </pre>
                                        </div>

                                        {/* After */}
                                        <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                            <div className="text-xs font-medium text-green-700 dark:text-green-400 mb-1">
                                                After
                                            </div>
                                            <pre className="text-sm text-gray-800 dark:text-gray-200 overflow-x-auto whitespace-pre-wrap">
                                                {change.change_type === 'removed'
                                                    ? <span className="text-gray-200 italic">Removed</span>
                                                    : formatValue(change.after)
                                                }
                                            </pre>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default DeltaReport;
