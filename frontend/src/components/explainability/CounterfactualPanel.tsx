'use client';

/**
 * What-If Counterfactual Panel
 * 
 * Interactive panel for exploring counterfactual scenarios
 * with real-time projections.
 */

import { useState, useEffect, useCallback } from 'react';
import { Lightbulb, RefreshCw, Save, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CounterfactualInput {
    key: string;
    label: string;
    type: 'slider' | 'number' | 'select';
    min?: number;
    max?: number;
    step?: number;
    options?: { value: string; label: string }[];
    currentValue: number | string;
    unit?: string;
}

interface Projection {
    metric: string;
    current: number;
    projected: number;
    change_pct: number;
    confidence: number;
}

interface CounterfactualPanelProps {
    title?: string;
    inputs: CounterfactualInput[];
    onCalculate?: (values: Record<string, number | string>) => Promise<Projection[]>;
    onSave?: (name: string, values: Record<string, number | string>) => void;
    className?: string;
}

export function CounterfactualPanel({
    title = 'What-If Analysis',
    inputs,
    onCalculate,
    onSave,
    className = '',
}: CounterfactualPanelProps) {
    const [values, setValues] = useState<Record<string, number | string>>(() => {
        const initial: Record<string, number | string> = {};
        inputs.forEach(input => {
            initial[input.key] = input.currentValue;
        });
        return initial;
    });

    const [projections, setProjections] = useState<Projection[]>([]);
    const [loading, setLoading] = useState(false);
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [scenarioName, setScenarioName] = useState('');

    // Debounced calculation
    const calculate = useCallback(async () => {
        if (!onCalculate) {
            // Mock projections for demo
            setProjections([
                { metric: 'Monthly Revenue', current: 5000, projected: 6500, change_pct: 30, confidence: 0.85 },
                { metric: 'Followers', current: 50000, projected: 62000, change_pct: 24, confidence: 0.78 },
                { metric: 'Engagement Rate', current: 4.2, projected: 5.1, change_pct: 21.4, confidence: 0.72 },
            ]);
            return;
        }

        setLoading(true);
        try {
            const result = await onCalculate(values);
            setProjections(result);
        } catch (error) {
            console.error('Calculation failed:', error);
        } finally {
            setLoading(false);
        }
    }, [values, onCalculate]);

    useEffect(() => {
        const timer = setTimeout(calculate, 500);
        return () => clearTimeout(timer);
    }, [calculate]);

    const handleValueChange = (key: string, value: number | string) => {
        setValues(prev => ({ ...prev, [key]: value }));
    };

    const handleReset = () => {
        const initial: Record<string, number | string> = {};
        inputs.forEach(input => {
            initial[input.key] = input.currentValue;
        });
        setValues(initial);
    };

    const handleSave = () => {
        if (scenarioName.trim()) {
            onSave?.(scenarioName, values);
            setShowSaveModal(false);
            setScenarioName('');
        }
    };

    const getChangeIcon = (change: number) => {
        if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
        if (change < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
        return <Minus className="h-4 w-4 text-gray-400" />;
    };

    const formatValue = (value: number, isPercentage: boolean = false): string => {
        if (isPercentage) return `${value.toFixed(1)}%`;
        if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
        return value.toLocaleString();
    };

    return (
        <div className={`bg-white dark:bg-gray-900 rounded-xl border dark:border-gray-800 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b dark:border-gray-800">
                <div className="flex items-center gap-3">
                    <Lightbulb className="h-6 w-6 text-yellow-500" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {title}
                    </h2>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleReset}
                        className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                        title="Reset to current values"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </button>
                    {onSave && (
                        <button
                            onClick={() => setShowSaveModal(true)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
                        >
                            <Save className="h-4 w-4" />
                            Save Scenario
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x dark:divide-gray-800">
                {/* Inputs */}
                <div className="p-6">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                        Adjust Variables
                    </h3>
                    <div className="space-y-6">
                        {inputs.map((input) => (
                            <div key={input.key}>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        {input.label}
                                    </label>
                                    <span className="text-sm text-indigo-600 dark:text-indigo-400 font-medium">
                                        {values[input.key]}{input.unit || ''}
                                    </span>
                                </div>

                                {input.type === 'slider' && (
                                    <input
                                        type="range"
                                        min={input.min}
                                        max={input.max}
                                        step={input.step || 1}
                                        value={values[input.key] as number}
                                        onChange={(e) => handleValueChange(input.key, Number(e.target.value))}
                                        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                                    />
                                )}

                                {input.type === 'number' && (
                                    <input
                                        type="number"
                                        min={input.min}
                                        max={input.max}
                                        step={input.step || 1}
                                        value={values[input.key] as number}
                                        onChange={(e) => handleValueChange(input.key, Number(e.target.value))}
                                        className="w-full px-3 py-2 border dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                                    />
                                )}

                                {input.type === 'select' && input.options && (
                                    <select
                                        value={values[input.key] as string}
                                        onChange={(e) => handleValueChange(input.key, e.target.value)}
                                        className="w-full px-3 py-2 border dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800"
                                    >
                                        {input.options.map(opt => (
                                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                                        ))}
                                    </select>
                                )}

                                {input.type === 'slider' && (
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>{input.min}{input.unit || ''}</span>
                                        <span>{input.max}{input.unit || ''}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Projections */}
                <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Projected Impact
                        </h3>
                        {loading && (
                            <div className="animate-spin h-4 w-4 border-2 border-indigo-500 border-t-transparent rounded-full" />
                        )}
                    </div>

                    <div className="space-y-4">
                        {projections.map((projection, i) => (
                            <div key={i} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium text-gray-900 dark:text-white">
                                        {projection.metric}
                                    </span>
                                    <div className="flex items-center gap-1">
                                        {getChangeIcon(projection.change_pct)}
                                        <span className={`text-sm font-medium ${projection.change_pct > 0 ? 'text-green-600' :
                                                projection.change_pct < 0 ? 'text-red-600' :
                                                    'text-gray-500'
                                            }`}>
                                            {projection.change_pct > 0 ? '+' : ''}{projection.change_pct.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>

                                <div className="flex items-center gap-4">
                                    <div className="flex-1">
                                        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full transition-all duration-500 ${projection.change_pct >= 0 ? 'bg-green-500' : 'bg-red-500'
                                                    }`}
                                                style={{
                                                    width: `${Math.min(Math.abs(projection.change_pct) + 50, 100)}%`
                                                }}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between mt-2 text-sm">
                                    <span className="text-gray-500">
                                        Current: {formatValue(projection.current)}
                                    </span>
                                    <span className="text-indigo-600 dark:text-indigo-400 font-medium">
                                        → {formatValue(projection.projected)}
                                    </span>
                                </div>

                                <div className="mt-2 text-xs text-gray-500">
                                    {Math.round(projection.confidence * 100)}% confidence
                                </div>
                            </div>
                        ))}
                    </div>

                    {projections.length > 0 && (
                        <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-sm text-indigo-700 dark:text-indigo-300">
                            <strong>Note:</strong> These projections are based on AI analysis and historical patterns.
                            Actual results may vary.
                        </div>
                    )}
                </div>
            </div>

            {/* Save Modal */}
            {showSaveModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                            Save Scenario
                        </h3>
                        <input
                            type="text"
                            placeholder="Scenario name..."
                            value={scenarioName}
                            onChange={(e) => setScenarioName(e.target.value)}
                            className="w-full px-3 py-2 border dark:border-gray-700 rounded-lg mb-4"
                            autoFocus
                        />
                        <div className="flex gap-2">
                            <button
                                onClick={() => setShowSaveModal(false)}
                                className="flex-1 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={!scenarioName.trim()}
                                className="flex-1 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50"
                            >
                                Save
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default CounterfactualPanel;
