"use client";

import { useEffect, useState } from "react";
import {
    initWebVitals,
    getFormattedMetrics,
    getPerformanceScore,
    logMetrics,
    type WebVitalsMetric,
} from "@/lib/web-vitals";

interface PerformanceMetric {
    name: string;
    displayValue: string;
    rating: string;
    description: string;
}

/**
 * PerformanceDashboard - Display Web Vitals metrics
 * 
 * Use in development or admin sections to monitor performance.
 */
export function PerformanceDashboard() {
    const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
    const [score, setScore] = useState<number>(100);
    const [isInitialized, setIsInitialized] = useState(false);

    useEffect(() => {
        const handleMetric = () => {
            setMetrics(getFormattedMetrics());
            setScore(getPerformanceScore());
        };

        initWebVitals(handleMetric).then(() => {
            setIsInitialized(true);
            // Initial update
            setTimeout(handleMetric, 100);
        });
    }, []);

    const getScoreColor = () => {
        if (score >= 90) return "text-green-400";
        if (score >= 50) return "text-yellow-400";
        return "text-red-400";
    };

    const getRatingColor = (rating: string) => {
        switch (rating) {
            case "good":
                return "bg-green-500/20 text-green-400 border-green-500/30";
            case "needs-improvement":
                return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
            case "poor":
                return "bg-red-500/20 text-red-400 border-red-500/30";
            default:
                return "bg-gray-500/20 text-gray-200 border-gray-500/30";
        }
    };

    return (
        <div className="bg-gray-900 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-lg font-semibold">Performance</h2>
                    <p className="text-sm text-gray-300">Core Web Vitals</p>
                </div>
                <div className="text-right">
                    <div className={`text-3xl font-bold ${getScoreColor()}`}>{score}</div>
                    <p className="text-xs text-gray-300">Score</p>
                </div>
            </div>

            {!isInitialized ? (
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full" />
                </div>
            ) : metrics.length === 0 ? (
                <div className="text-center py-8 text-gray-300">
                    <p>Collecting metrics...</p>
                    <p className="text-xs mt-1">Interact with the page to generate data</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {metrics.map((metric) => (
                        <div
                            key={metric.name}
                            className={`p-4 rounded-xl border ${getRatingColor(metric.rating)}`}
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium">{metric.name}</div>
                                    <div className="text-xs opacity-70">{metric.description}</div>
                                </div>
                                <div className="text-right">
                                    <div className="font-mono font-bold">{metric.displayValue}</div>
                                    <div className="text-xs capitalize">{metric.rating.replace("-", " ")}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {process.env.NODE_ENV === "development" && (
                <button
                    onClick={logMetrics}
                    className="mt-4 w-full py-2 text-sm text-gray-300 hover:text-gray-300 transition-colors"
                >
                    Log to Console
                </button>
            )}
        </div>
    );
}

/**
 * PerformanceBadge - Compact performance indicator
 */
export function PerformanceBadge() {
    const [score, setScore] = useState<number | null>(null);

    useEffect(() => {
        initWebVitals(() => {
            setScore(getPerformanceScore());
        });

        // Update periodically
        const interval = setInterval(() => {
            setScore(getPerformanceScore());
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    if (score === null) return null;

    const getColor = () => {
        if (score >= 90) return "bg-green-500";
        if (score >= 50) return "bg-yellow-500";
        return "bg-red-500";
    };

    return (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-full">
            <div className={`w-2 h-2 rounded-full ${getColor()}`} />
            <span className="text-sm font-medium">{score}</span>
        </div>
    );
}

/**
 * useWebVitals - Hook for accessing Web Vitals data
 */
export function useWebVitals() {
    const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
    const [score, setScore] = useState(100);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        const update = () => {
            setMetrics(getFormattedMetrics());
            setScore(getPerformanceScore());
        };

        initWebVitals(update).then(() => {
            setIsReady(true);
        });

        const interval = setInterval(update, 2000);
        return () => clearInterval(interval);
    }, []);

    return { metrics, score, isReady };
}

export default PerformanceDashboard;
