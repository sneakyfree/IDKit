'use client';

/**
 * Revenue Overview Card
 * 
 * Summary card showing key revenue metrics with trends.
 */

import { DollarSign, TrendingUp, TrendingDown, ArrowRight, Clock } from 'lucide-react';

interface RevenueMetrics {
    total_revenue: number;
    change_pct: number;
    period: string;
    breakdown: {
        brand_deals: number;
        affiliates: number;
        royalties: number;
        other: number;
    };
    pending_payouts: number;
    next_payout_date?: string;
}

interface RevenueOverviewCardProps {
    metrics: RevenueMetrics;
    onViewDetails?: () => void;
    className?: string;
}

export function RevenueOverviewCard({
    metrics,
    onViewDetails,
    className = '',
}: RevenueOverviewCardProps) {
    const formatCurrency = (amount: number): string => {
        if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
        if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
        return `$${amount.toFixed(2)}`;
    };

    const isPositive = metrics.change_pct >= 0;
    const TrendIcon = isPositive ? TrendingUp : TrendingDown;

    const breakdownTotal =
        metrics.breakdown.brand_deals +
        metrics.breakdown.affiliates +
        metrics.breakdown.royalties +
        metrics.breakdown.other;

    const getPercentage = (value: number) =>
        breakdownTotal > 0 ? ((value / breakdownTotal) * 100).toFixed(0) : 0;

    return (
        <div className={`bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 text-white ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 opacity-80" />
                    <span className="text-sm font-medium opacity-90">Revenue · {metrics.period}</span>
                </div>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-sm ${isPositive ? 'bg-white/20' : 'bg-red-400/30'
                    }`}>
                    <TrendIcon className="h-4 w-4" />
                    <span>{isPositive ? '+' : ''}{metrics.change_pct.toFixed(1)}%</span>
                </div>
            </div>

            {/* Total */}
            <div className="mb-6">
                <div className="text-4xl font-bold">
                    {formatCurrency(metrics.total_revenue)}
                </div>
                <div className="text-sm opacity-75 mt-1">Total earnings</div>
            </div>

            {/* Breakdown */}
            <div className="space-y-2 mb-6">
                {[
                    { label: 'Brand Deals', value: metrics.breakdown.brand_deals, color: 'bg-white' },
                    { label: 'Affiliates', value: metrics.breakdown.affiliates, color: 'bg-white/70' },
                    { label: 'Royalties', value: metrics.breakdown.royalties, color: 'bg-white/50' },
                    { label: 'Other', value: metrics.breakdown.other, color: 'bg-white/30' },
                ].map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                        <div className="flex-1">
                            <div className="flex items-center justify-between text-sm mb-1">
                                <span className="opacity-90">{item.label}</span>
                                <span className="font-medium">{formatCurrency(item.value)}</span>
                            </div>
                            <div className="h-1.5 bg-white/20 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${item.color} rounded-full transition-all duration-500`}
                                    style={{ width: `${getPercentage(item.value)}%` }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Pending Payouts */}
            {metrics.pending_payouts > 0 && (
                <div className="flex items-center justify-between p-3 bg-white/10 rounded-lg mb-4">
                    <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 opacity-70" />
                        <span className="text-sm">Pending payout</span>
                    </div>
                    <span className="font-semibold">{formatCurrency(metrics.pending_payouts)}</span>
                </div>
            )}

            {/* CTA */}
            {onViewDetails && (
                <button
                    onClick={onViewDetails}
                    className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                >
                    <span className="font-medium">View Revenue Details</span>
                    <ArrowRight className="h-4 w-4" />
                </button>
            )}
        </div>
    );
}

/**
 * Revenue Intelligence Insights
 */
interface RevenueInsight {
    id: string;
    type: 'opportunity' | 'warning' | 'info';
    title: string;
    description: string;
    potential_value?: number;
    action?: string;
}

interface RevenueInsightsProps {
    insights: RevenueInsight[];
    onTakeAction?: (insight: RevenueInsight) => void;
    className?: string;
}

export function RevenueInsights({
    insights,
    onTakeAction,
    className = '',
}: RevenueInsightsProps) {
    const typeStyles = {
        opportunity: 'border-green-500 bg-green-50 dark:bg-green-900/10',
        warning: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10',
        info: 'border-blue-500 bg-blue-50 dark:bg-blue-900/10',
    };

    const typeIcons = {
        opportunity: '💰',
        warning: '⚠️',
        info: 'ℹ️',
    };

    return (
        <div className={`space-y-3 ${className}`}>
            {insights.map((insight) => (
                <div
                    key={insight.id}
                    className={`p-4 rounded-lg border-l-4 ${typeStyles[insight.type]}`}
                >
                    <div className="flex items-start gap-3">
                        <span className="text-xl">{typeIcons[insight.type]}</span>
                        <div className="flex-1">
                            <h4 className="font-medium text-gray-900 dark:text-white">
                                {insight.title}
                            </h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                {insight.description}
                            </p>
                            {insight.potential_value && (
                                <div className="mt-2 text-sm font-medium text-green-600 dark:text-green-400">
                                    Potential: ${insight.potential_value.toLocaleString()}
                                </div>
                            )}
                            {insight.action && onTakeAction && (
                                <button
                                    onClick={() => onTakeAction(insight)}
                                    className="mt-3 text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
                                >
                                    {insight.action} →
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default RevenueOverviewCard;
