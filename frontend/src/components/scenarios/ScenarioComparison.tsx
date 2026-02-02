'use client';

/**
 * Scenario Comparison Component
 * 
 * Side-by-side comparison of what-if scenarios for decision making.
 */

import { useState } from 'react';
import { Scale, TrendingUp, Clock, DollarSign, Users, Star, Check, X } from 'lucide-react';

interface Scenario {
    id: string;
    title: string;
    type: string;
    description: string;
    impact_score: number;
    confidence: number;
    time_horizon: string;
    metrics: {
        revenue?: { current: number; projected: number; change_pct: number };
        followers?: { current: number; projected: number; change_pct: number };
        engagement?: { current: number; projected: number; change_pct: number };
    };
    assumptions: string[];
    risks: string[];
}

interface ScenarioComparisonProps {
    scenarios: Scenario[];
    onSelect?: (scenario: Scenario) => void;
    onClose?: () => void;
    className?: string;
}

export function ScenarioComparison({
    scenarios,
    onSelect,
    onClose,
    className = '',
}: ScenarioComparisonProps) {
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const handleSelect = (scenario: Scenario) => {
        setSelectedId(scenario.id);
        onSelect?.(scenario);
    };

    const formatNumber = (n: number) => {
        if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
        if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
        return n.toString();
    };

    const formatChange = (pct: number) => {
        const sign = pct >= 0 ? '+' : '';
        return `${sign}${pct.toFixed(1)}%`;
    };

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b dark:border-gray-800">
                <div className="flex items-center gap-3">
                    <Scale className="h-6 w-6 text-indigo-500" />
                    <div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Compare Scenarios
                        </h2>
                        <p className="text-sm text-gray-500">
                            Analyze projections side-by-side
                        </p>
                    </div>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                    >
                        <X className="h-5 w-5" />
                    </button>
                )}
            </div>

            {/* Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-0 divide-x dark:divide-gray-800">
                {scenarios.map((scenario) => (
                    <div
                        key={scenario.id}
                        className={`p-6 transition-colors ${selectedId === scenario.id
                                ? 'bg-indigo-50 dark:bg-indigo-900/20'
                                : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                            }`}
                    >
                        {/* Scenario Header */}
                        <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${scenario.type === 'growth' ? 'bg-green-100 text-green-700' :
                                        scenario.type === 'monetization' ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-blue-100 text-blue-700'
                                    }`}>
                                    {scenario.type}
                                </span>
                                <div className="flex items-center gap-1">
                                    <Star className="h-4 w-4 text-yellow-500" />
                                    <span className="text-sm font-medium">
                                        {Math.round(scenario.impact_score * 100)}/100
                                    </span>
                                </div>
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                {scenario.title}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">
                                {scenario.description}
                            </p>
                        </div>

                        {/* Key Metrics */}
                        <div className="space-y-3 mb-4">
                            {scenario.metrics.revenue && (
                                <div className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <div className="flex items-center gap-2">
                                        <DollarSign className="h-4 w-4 text-green-500" />
                                        <span className="text-sm text-gray-600 dark:text-gray-400">Revenue</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-gray-900 dark:text-white">
                                            ${formatNumber(scenario.metrics.revenue.projected)}
                                        </div>
                                        <div className={`text-xs ${scenario.metrics.revenue.change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {formatChange(scenario.metrics.revenue.change_pct)}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {scenario.metrics.followers && (
                                <div className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <div className="flex items-center gap-2">
                                        <Users className="h-4 w-4 text-blue-500" />
                                        <span className="text-sm text-gray-600 dark:text-gray-400">Followers</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-gray-900 dark:text-white">
                                            {formatNumber(scenario.metrics.followers.projected)}
                                        </div>
                                        <div className={`text-xs ${scenario.metrics.followers.change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {formatChange(scenario.metrics.followers.change_pct)}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {scenario.metrics.engagement && (
                                <div className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                                    <div className="flex items-center gap-2">
                                        <TrendingUp className="h-4 w-4 text-purple-500" />
                                        <span className="text-sm text-gray-600 dark:text-gray-400">Engagement</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-semibold text-gray-900 dark:text-white">
                                            {scenario.metrics.engagement.projected.toFixed(1)}%
                                        </div>
                                        <div className={`text-xs ${scenario.metrics.engagement.change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                            }`}>
                                            {formatChange(scenario.metrics.engagement.change_pct)}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Time Horizon & Confidence */}
                        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                            <span className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                {scenario.time_horizon}
                            </span>
                            <span>
                                {Math.round(scenario.confidence * 100)}% confidence
                            </span>
                        </div>

                        {/* Assumptions */}
                        <div className="mb-4">
                            <div className="text-xs font-medium text-gray-500 uppercase mb-2">
                                Key Assumptions
                            </div>
                            <ul className="space-y-1">
                                {scenario.assumptions.slice(0, 3).map((assumption, i) => (
                                    <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                                        <span className="text-gray-400">•</span>
                                        {assumption}
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Select Button */}
                        <button
                            onClick={() => handleSelect(scenario)}
                            className={`w-full py-2 rounded-lg font-medium transition-colors ${selectedId === scenario.id
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/20'
                                }`}
                        >
                            {selectedId === scenario.id ? (
                                <span className="flex items-center justify-center gap-2">
                                    <Check className="h-4 w-4" />
                                    Selected
                                </span>
                            ) : (
                                'Select Scenario'
                            )}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default ScenarioComparison;
