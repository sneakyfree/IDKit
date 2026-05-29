'use client';

/**
 * Evidence Card Component
 * 
 * Displays evidence items with accessibility features for AI explainability.
 */

import { useState } from 'react';
import { FileText, Database, Calculator, Search, ExternalLink, ChevronDown, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface EvidenceItem {
    id: string;
    source_type: 'api_data' | 'user_input' | 'calculation' | 'research' | 'external';
    source_name: string;
    data: unknown;
    confidence: number;
    timestamp: string;
    description?: string;
    url?: string;
}

interface EvidenceCardProps {
    evidence: EvidenceItem;
    expanded?: boolean;
    onToggle?: () => void;
    className?: string;
}

const SOURCE_ICONS = {
    api_data: Database,
    user_input: FileText,
    calculation: Calculator,
    research: Search,
    external: ExternalLink,
};

const SOURCE_LABELS = {
    api_data: 'API Data',
    user_input: 'User Input',
    calculation: 'Calculated',
    research: 'Research',
    external: 'External Source',
};

const SOURCE_COLORS = {
    api_data: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
    user_input: 'text-green-500 bg-green-100 dark:bg-green-900/30',
    calculation: 'text-purple-500 bg-purple-100 dark:bg-purple-900/30',
    research: 'text-orange-500 bg-orange-100 dark:bg-orange-900/30',
    external: 'text-gray-300 bg-gray-100 dark:bg-gray-800',
};

export function EvidenceCard({
    evidence,
    expanded: controlledExpanded,
    onToggle,
    className = '',
}: EvidenceCardProps) {
    const [internalExpanded, setInternalExpanded] = useState(false);
    const expanded = controlledExpanded ?? internalExpanded;

    const handleToggle = () => {
        if (onToggle) {
            onToggle();
        } else {
            setInternalExpanded(!internalExpanded);
        }
    };

    const Icon = SOURCE_ICONS[evidence.source_type] || FileText;
    const colorClass = SOURCE_COLORS[evidence.source_type] || SOURCE_COLORS.external;

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return 'text-green-600';
        if (confidence >= 0.5) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getConfidenceIcon = (confidence: number) => {
        if (confidence >= 0.8) return CheckCircle;
        if (confidence >= 0.5) return Clock;
        return AlertCircle;
    };

    const ConfidenceIcon = getConfidenceIcon(evidence.confidence);

    const formatData = (data: unknown): string => {
        if (data === null || data === undefined) return 'No data';
        if (typeof data === 'object') return JSON.stringify(data, null, 2);
        return String(data);
    };

    return (
        <div
            className={`
        border dark:border-gray-800 rounded-lg overflow-hidden
        transition-all duration-200
        ${expanded ? 'shadow-md' : 'hover:shadow-sm'}
        ${className}
      `}
            role="article"
            aria-label={`Evidence from ${evidence.source_name}`}
        >
            {/* Header (always visible) */}
            <button
                onClick={handleToggle}
                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                aria-expanded={expanded}
            >
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${colorClass}`}>
                        <Icon className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                            {evidence.source_name}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-300">
                            <span className="sr-only">Source type: </span>
                            {SOURCE_LABELS[evidence.source_type]}
                            <span aria-hidden="true">•</span>
                            <span className="sr-only">Captured: </span>
                            <time dateTime={evidence.timestamp}>
                                {new Date(evidence.timestamp).toLocaleDateString()}
                            </time>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {/* Confidence indicator */}
                    <div className={`flex items-center gap-1 ${getConfidenceColor(evidence.confidence)}`}>
                        <ConfidenceIcon className="h-4 w-4" aria-hidden="true" />
                        <span className="text-sm font-medium">
                            {Math.round(evidence.confidence * 100)}%
                            <span className="sr-only"> confidence</span>
                        </span>
                    </div>

                    <ChevronDown
                        className={`h-5 w-5 text-gray-200 transition-transform ${expanded ? 'rotate-180' : ''}`}
                        aria-hidden="true"
                    />
                </div>
            </button>

            {/* Expanded Content */}
            {expanded && (
                <div className="px-4 pb-4 border-t dark:border-gray-800">
                    {/* Description */}
                    {evidence.description && (
                        <div className="mt-3">
                            <h4 className="text-xs font-medium text-gray-300 uppercase mb-1">
                                Description
                            </h4>
                            <p className="text-sm text-gray-700 dark:text-gray-300">
                                {evidence.description}
                            </p>
                        </div>
                    )}

                    {/* Data */}
                    <div className="mt-3">
                        <h4 className="text-xs font-medium text-gray-300 uppercase mb-1">
                            Evidence Data
                        </h4>
                        <pre
                            className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto max-h-48"
                            aria-label="Evidence data content"
                        >
                            {formatData(evidence.data)}
                        </pre>
                    </div>

                    {/* External Link */}
                    {evidence.url && (
                        <a
                            href={evidence.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-3 inline-flex items-center gap-2 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                        >
                            <ExternalLink className="h-4 w-4" aria-hidden="true" />
                            View Original Source
                            <span className="sr-only">(opens in new tab)</span>
                        </a>
                    )}

                    {/* Metadata */}
                    <div className="mt-3 pt-3 border-t dark:border-gray-800 flex flex-wrap gap-4 text-xs text-gray-300">
                        <span>
                            <span className="font-medium">ID:</span> {evidence.id}
                        </span>
                        <span>
                            <span className="font-medium">Confidence:</span> {(evidence.confidence * 100).toFixed(1)}%
                        </span>
                        <span>
                            <span className="font-medium">Captured:</span>{' '}
                            {new Date(evidence.timestamp).toLocaleString()}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}

/**
 * Evidence List Component
 * 
 * Displays a list of evidence items with group headers.
 */
interface EvidenceListProps {
    evidence: EvidenceItem[];
    title?: string;
    showConfidenceFilter?: boolean;
    className?: string;
}

export function EvidenceList({
    evidence,
    title = 'Supporting Evidence',
    showConfidenceFilter = true,
    className = '',
}: EvidenceListProps) {
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [minConfidence, setMinConfidence] = useState(0);

    const filteredEvidence = evidence.filter(e => e.confidence >= minConfidence);

    return (
        <div className={className}>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {title}
                    <span className="ml-2 text-sm font-normal text-gray-300">
                        ({filteredEvidence.length} items)
                    </span>
                </h3>

                {showConfidenceFilter && (
                    <div className="flex items-center gap-2">
                        <label htmlFor="confidence-filter" className="text-sm text-gray-300">
                            Min confidence:
                        </label>
                        <select aria-label="Filter or select option"
                            id="confidence-filter"
                            value={minConfidence}
                            onChange={(e) => setMinConfidence(Number(e.target.value))}
                            className="text-sm border dark:border-gray-700 rounded px-2 py-1 bg-white dark:bg-gray-800"
                        >
                            <option value={0}>All</option>
                            <option value={0.5}>50%+</option>
                            <option value={0.7}>70%+</option>
                            <option value={0.9}>90%+</option>
                        </select>
                    </div>
                )}
            </div>

            <div className="space-y-3" role="list" aria-label="Evidence items">
                {filteredEvidence.map((item) => (
                    <EvidenceCard
                        key={item.id}
                        evidence={item}
                        expanded={expandedId === item.id}
                        onToggle={() => setExpandedId(expandedId === item.id ? null : item.id)}
                    />
                ))}

                {filteredEvidence.length === 0 && (
                    <p className="text-center py-8 text-gray-300">
                        No evidence items match the current filter.
                    </p>
                )}
            </div>
        </div>
    );
}

export default EvidenceCard;
