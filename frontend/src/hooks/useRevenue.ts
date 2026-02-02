/**
 * useRevenue Hook
 * 
 * React hook for Revenue Intelligence APIs:
 * - ROI projections with confidence intervals
 * - Pricing recommendations with market benchmarks
 * - Brand Deal CRM pipeline
 * - Payout dashboard
 */

import { useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface ConfidenceInterval {
    lower: number;
    estimate: number;
    upper: number;
    confidence_level: number;
}

export interface ROIProjection {
    projection_id: string;
    scenario_name: string;
    scenario_type: string;
    time_horizon_days: number;
    investment: ConfidenceInterval;
    projected_revenue: ConfidenceInterval;
    roi_percent: ConfidenceInterval;
    payback_period_days?: ConfidenceInterval;
    assumptions: string[];
    data_sources: string[];
    comparable_cases: number;
}

export interface MarketBenchmark {
    metric_name: string;
    p25: number;
    median: number;
    p75: number;
    sample_size: number;
    niche: string;
    tier: string;
    data_period: string;
    source: string;
}

export interface PricingRecommendation {
    recommendation_id: string;
    content_type: string;
    platform: string;
    recommended_rate: ConfidenceInterval;
    rate_per_1k_followers: number;
    benchmarks: MarketBenchmark[];
    your_percentile: number;
    factors: Record<string, number>;
    reasoning: string;
    comparable_creators: number;
}

export interface BrandDeal {
    deal_id: string;
    brand_name: string;
    title: string;
    description?: string;
    deal_type: string;
    deal_value: number;
    currency: string;
    stage: string;
    probability: number;
    deliverables: Array<{
        deliverable_id: string;
        type: string;
        description: string;
        status: string;
        due_date?: string;
    }>;
    created_at: string;
    updated_at: string;
}

export interface PayoutSummary {
    user_id: string;
    period_start: string;
    period_end: string;
    total_gross: number;
    total_net: number;
    total_pending: number;
    total_paid: number;
    by_source: Array<{
        source: string;
        total_net: number;
        count: number;
    }>;
    stripe_connected: boolean;
    next_payout_date?: string;
    next_payout_amount?: number;
}

export interface PipelineMetrics {
    total_deals: number;
    total_value: number;
    win_rate: number;
    avg_deal_size: number;
    deals_closed_this_month: number;
    revenue_this_month: number;
}

export function useRevenue() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getAuthHeaders = useCallback(() => {
        const token = localStorage.getItem('token');
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
        };
    }, []);

    // ============== ROI Projections ==============

    const projectROI = useCallback(async (
        scenarioName: string,
        scenarioType: string,
        investmentAmount: number,
        options?: {
            timeHorizonDays?: number;
            confidenceLevel?: number;
            investmentBreakdown?: Record<string, number>;
        }
    ): Promise<ROIProjection | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/revenue/roi/project`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    scenario_name: scenarioName,
                    scenario_type: scenarioType,
                    investment_amount: investmentAmount,
                    time_horizon_days: options?.timeHorizonDays ?? 90,
                    confidence_level: options?.confidenceLevel ?? 0.80,
                    investment_breakdown: options?.investmentBreakdown,
                }),
            });

            if (!response.ok) throw new Error('Failed to project ROI');
            const data = await response.json();
            return data.projection;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const compareScenarios = useCallback(async (
        scenarios: Array<{
            name: string;
            type: string;
            investment: number;
            time_horizon?: number;
        }>
    ) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/revenue/roi/compare`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(scenarios),
            });

            if (!response.ok) throw new Error('Failed to compare scenarios');
            return await response.json();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    // ============== Pricing ==============

    const getPricingRecommendation = useCallback(async (
        contentType: string,
        platform: string,
        followerCount: number,
        engagementRate: number,
        niche?: string
    ): Promise<PricingRecommendation | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/revenue/pricing/recommend`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    content_type: contentType,
                    platform,
                    follower_count: followerCount,
                    engagement_rate: engagementRate,
                    niche,
                }),
            });

            if (!response.ok) throw new Error('Failed to get pricing');
            const data = await response.json();
            return data.recommendation;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getMarketBenchmarks = useCallback(async (
        platform: string,
        contentType: string,
        tier?: string
    ): Promise<MarketBenchmark[]> => {
        try {
            const params = new URLSearchParams({
                platform,
                content_type: contentType,
                ...(tier && { tier }),
            });
            const response = await fetch(
                `${API_BASE}/revenue/pricing/benchmarks?${params}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) throw new Error('Failed to get benchmarks');
            const data = await response.json();
            return data.benchmarks;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    // ============== Brand Deals ==============

    const createDeal = useCallback(async (deal: {
        brand_name: string;
        title: string;
        deal_type: string;
        deal_value: number;
        description?: string;
        expected_close_date?: string;
    }): Promise<BrandDeal | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/revenue/deals`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify(deal),
            });

            if (!response.ok) throw new Error('Failed to create deal');
            const data = await response.json();
            return data.deal;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    const getDeals = useCallback(async (
        stage?: string,
        limit = 50
    ): Promise<BrandDeal[]> => {
        try {
            const params = new URLSearchParams({ limit: String(limit) });
            if (stage) params.append('stage', stage);

            const response = await fetch(
                `${API_BASE}/revenue/deals?${params}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) throw new Error('Failed to get deals');
            const data = await response.json();
            return data.deals;
        } catch {
            return [];
        }
    }, [getAuthHeaders]);

    const getPipeline = useCallback(async (): Promise<{
        metrics: PipelineMetrics;
        deals_by_stage: Record<string, BrandDeal[]>;
    } | null> => {
        try {
            const response = await fetch(
                `${API_BASE}/revenue/deals/pipeline`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) throw new Error('Failed to get pipeline');
            return await response.json();
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    const updateDealStage = useCallback(async (
        dealId: string,
        newStage: string,
        note?: string
    ): Promise<BrandDeal | null> => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/revenue/deals/${dealId}/stage`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ new_stage: newStage, note }),
            });

            if (!response.ok) throw new Error('Failed to update stage');
            const data = await response.json();
            return data.deal;
        } catch {
            return null;
        } finally {
            setLoading(false);
        }
    }, [getAuthHeaders]);

    // ============== Payouts ==============

    const getPayoutSummary = useCallback(async (
        period = '30d'
    ): Promise<PayoutSummary | null> => {
        try {
            const response = await fetch(
                `${API_BASE}/revenue/payouts?period=${period}`,
                { headers: getAuthHeaders() }
            );

            if (!response.ok) throw new Error('Failed to get payouts');
            const data = await response.json();
            return data.summary;
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    const connectStripe = useCallback(async (): Promise<{ url: string } | null> => {
        try {
            const response = await fetch(`${API_BASE}/revenue/payouts/connect`, {
                method: 'POST',
                headers: getAuthHeaders(),
            });

            if (!response.ok) throw new Error('Failed to get Stripe URL');
            return await response.json();
        } catch {
            return null;
        }
    }, [getAuthHeaders]);

    return {
        loading,
        error,
        // ROI
        projectROI,
        compareScenarios,
        // Pricing
        getPricingRecommendation,
        getMarketBenchmarks,
        // Brand Deals
        createDeal,
        getDeals,
        getPipeline,
        updateDealStage,
        // Payouts
        getPayoutSummary,
        connectStripe,
    };
}
