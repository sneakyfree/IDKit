'use client';

/**
 * Blocker Card Component
 * 
 * Displays a single blocker with severity, impact, and action items.
 */

import { useState } from 'react';
import { AlertOctagon, ChevronDown, CheckCircle2, Circle, Lightbulb, ArrowRight } from 'lucide-react';

interface BlockerAction {
    id: string;
    title: string;
    completed: boolean;
    effort: 'low' | 'medium' | 'high';
}

interface Blocker {
    id: string;
    title: string;
    description: string;
    category: 'growth' | 'monetization' | 'content' | 'engagement' | 'technical';
    severity: 'critical' | 'high' | 'medium' | 'low';
    impact_score: number;
    actions: BlockerAction[];
    insight?: string;
}

const SEVERITY_STYLES = {
    critical: { bg: 'bg-red-100 dark:bg-red-900/20', border: 'border-red-500', text: 'text-red-600 dark:text-red-400' },
    high: { bg: 'bg-orange-100 dark:bg-orange-900/20', border: 'border-orange-500', text: 'text-orange-600 dark:text-orange-400' },
    medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/20', border: 'border-yellow-500', text: 'text-yellow-600 dark:text-yellow-400' },
    low: { bg: 'bg-blue-100 dark:bg-blue-900/20', border: 'border-blue-500', text: 'text-blue-600 dark:text-blue-400' },
};

const CATEGORY_ICONS: Record<string, string> = {
    growth: '📈',
    monetization: '💰',
    content: '📝',
    engagement: '💬',
    technical: '⚙️',
};

const EFFORT_COLORS = {
    low: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

interface BlockerCardProps {
    blocker: Blocker;
    onActionToggle?: (blockerId: string, actionId: string) => void;
    onViewDetails?: (blocker: Blocker) => void;
    className?: string;
}

export function BlockerCard({
    blocker,
    onActionToggle,
    onViewDetails,
    className = '',
}: BlockerCardProps) {
    const [expanded, setExpanded] = useState(false);
    const styles = SEVERITY_STYLES[blocker.severity];
    const completedActions = blocker.actions.filter(a => a.completed).length;
    const progress = blocker.actions.length > 0
        ? (completedActions / blocker.actions.length) * 100
        : 0;

    return (
        <div className={`rounded-xl border-l-4 ${styles.border} ${styles.bg} overflow-hidden ${className}`}>
            {/* Header */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full p-4 text-left"
            >
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                        <span className="text-2xl">{CATEGORY_ICONS[blocker.category]}</span>
                        <div>
                            <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                    {blocker.title}
                                </h3>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium uppercase ${styles.text}`}>
                                    {blocker.severity}
                                </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                {blocker.description}
                            </p>
                        </div>
                    </div>
                    <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
                </div>

                {/* Progress Bar */}
                <div className="mt-4 flex items-center gap-3">
                    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-green-500 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span className="text-sm text-gray-500 whitespace-nowrap">
                        {completedActions}/{blocker.actions.length} actions
                    </span>
                </div>
            </button>

            {/* Expanded Content */}
            {expanded && (
                <div className="px-4 pb-4 border-t dark:border-gray-800/50">
                    {/* AI Insight */}
                    {blocker.insight && (
                        <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg flex items-start gap-2">
                            <Lightbulb className="h-5 w-5 text-indigo-500 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-indigo-700 dark:text-indigo-300">
                                {blocker.insight}
                            </p>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="mt-4 space-y-2">
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Action Items
                        </h4>
                        {blocker.actions.map((action) => (
                            <label
                                key={action.id}
                                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/50 dark:hover:bg-gray-800/30 cursor-pointer"
                            >
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        onActionToggle?.(blocker.id, action.id);
                                    }}
                                    className="flex-shrink-0"
                                >
                                    {action.completed ? (
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                    ) : (
                                        <Circle className="h-5 w-5 text-gray-400" />
                                    )}
                                </button>
                                <span className={`flex-1 text-sm ${action.completed ? 'line-through text-gray-500' : 'text-gray-700 dark:text-gray-300'}`}>
                                    {action.title}
                                </span>
                                <span className={`px-2 py-0.5 rounded text-xs ${EFFORT_COLORS[action.effort]}`}>
                                    {action.effort}
                                </span>
                            </label>
                        ))}
                    </div>

                    {/* View Details */}
                    {onViewDetails && (
                        <button
                            onClick={() => onViewDetails(blocker)}
                            className="mt-4 w-full flex items-center justify-center gap-2 py-2 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            View Full Analysis <ArrowRight className="h-4 w-4" />
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

/**
 * Blockers List Component
 */
interface BlockersListProps {
    blockers: Blocker[];
    onActionToggle?: (blockerId: string, actionId: string) => void;
    onViewDetails?: (blocker: Blocker) => void;
    className?: string;
}

export function BlockersList({
    blockers,
    onActionToggle,
    onViewDetails,
    className = '',
}: BlockersListProps) {
    // Sort by severity
    const sortedBlockers = [...blockers].sort((a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 };
        return order[a.severity] - order[b.severity];
    });

    const criticalCount = blockers.filter(b => b.severity === 'critical').length;
    const highCount = blockers.filter(b => b.severity === 'high').length;

    return (
        <div className={className}>
            {/* Summary */}
            <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                    <AlertOctagon className="h-5 w-5 text-gray-500" />
                    <span className="font-medium text-gray-900 dark:text-white">
                        {blockers.length} Blockers
                    </span>
                </div>
                {criticalCount > 0 && (
                    <span className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-full">
                        {criticalCount} critical
                    </span>
                )}
                {highCount > 0 && (
                    <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-sm rounded-full">
                        {highCount} high
                    </span>
                )}
            </div>

            {/* Blockers */}
            <div className="space-y-4">
                {sortedBlockers.map((blocker) => (
                    <BlockerCard
                        key={blocker.id}
                        blocker={blocker}
                        onActionToggle={onActionToggle}
                        onViewDetails={onViewDetails}
                    />
                ))}
            </div>
        </div>
    );
}

export default BlockerCard;
