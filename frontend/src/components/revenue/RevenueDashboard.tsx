'use client';

/**
 * Revenue Dashboard Component
 * 
 * Unified view of revenue intelligence:
 * - ROI projections with confidence bands
 * - Payout summary
 * - Brand deal pipeline
 * - Pricing recommendations
 */

import React, { useEffect, useState } from 'react';
import { useRevenue, PayoutSummary, PipelineMetrics, BrandDeal } from '@/hooks/useRevenue';

interface RevenueDashboardProps {
    period?: '7d' | '30d' | '90d';
}

export function RevenueDashboard({ period = '30d' }: RevenueDashboardProps) {
    const { getPayoutSummary, getPipeline, loading, error } = useRevenue();
    const [summary, setSummary] = useState<PayoutSummary | null>(null);
    const [pipeline, setPipeline] = useState<{
        metrics: PipelineMetrics;
        deals_by_stage: Record<string, BrandDeal[]>;
    } | null>(null);

    useEffect(() => {
        async function load() {
            const [payoutData, pipelineData] = await Promise.all([
                getPayoutSummary(period),
                getPipeline(),
            ]);
            setSummary(payoutData);
            setPipeline(pipelineData);
        }
        load();
    }, [period, getPayoutSummary, getPipeline]);

    if (loading) {
        return (
            <div className="revenue-dashboard loading">
                <div className="loading-spinner" />
                <p>Loading revenue data...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="revenue-dashboard error">
                <p className="error-message">Error: {error}</p>
            </div>
        );
    }

    return (
        <div className="revenue-dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <h1>Revenue Intelligence</h1>
                <div className="period-selector">
                    <button className={period === '7d' ? 'active' : ''}>7D</button>
                    <button className={period === '30d' ? 'active' : ''}>30D</button>
                    <button className={period === '90d' ? 'active' : ''}>90D</button>
                </div>
            </header>

            {/* Payout Summary Cards */}
            {summary && (
                <section className="summary-cards">
                    <div className="card total-revenue">
                        <span className="label">Total Revenue</span>
                        <span className="value">${summary.total_net.toLocaleString()}</span>
                        <span className="sublabel">Net</span>
                    </div>

                    <div className="card pending">
                        <span className="label">Pending</span>
                        <span className="value">${summary.total_pending.toLocaleString()}</span>
                    </div>

                    <div className="card paid">
                        <span className="label">Paid Out</span>
                        <span className="value">${summary.total_paid.toLocaleString()}</span>
                    </div>

                    {summary.next_payout_amount && (
                        <div className="card next-payout">
                            <span className="label">Next Payout</span>
                            <span className="value">${summary.next_payout_amount.toLocaleString()}</span>
                            <span className="sublabel">
                                {summary.next_payout_date
                                    ? new Date(summary.next_payout_date).toLocaleDateString()
                                    : 'TBD'}
                            </span>
                        </div>
                    )}
                </section>
            )}

            {/* Revenue by Source */}
            {summary && summary.by_source.length > 0 && (
                <section className="revenue-breakdown">
                    <h2>Revenue by Source</h2>
                    <div className="breakdown-chart">
                        {summary.by_source.map((source) => (
                            <div key={source.source} className="source-bar">
                                <span className="source-name">{source.source}</span>
                                <div className="bar-container">
                                    <div
                                        className="bar-fill"
                                        style={{
                                            width: `${(source.total_net / summary.total_net) * 100}%`
                                        }}
                                    />
                                </div>
                                <span className="source-value">${source.total_net.toLocaleString()}</span>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Deal Pipeline */}
            {pipeline && (
                <section className="deal-pipeline">
                    <h2>Brand Deal Pipeline</h2>

                    <div className="pipeline-metrics">
                        <div className="metric">
                            <span className="metric-value">{pipeline.metrics.total_deals}</span>
                            <span className="metric-label">Total Deals</span>
                        </div>
                        <div className="metric">
                            <span className="metric-value">${pipeline.metrics.total_value.toLocaleString()}</span>
                            <span className="metric-label">Pipeline Value</span>
                        </div>
                        <div className="metric">
                            <span className="metric-value">{(pipeline.metrics.win_rate * 100).toFixed(0)}%</span>
                            <span className="metric-label">Win Rate</span>
                        </div>
                        <div className="metric">
                            <span className="metric-value">${pipeline.metrics.avg_deal_size.toLocaleString()}</span>
                            <span className="metric-label">Avg Deal Size</span>
                        </div>
                    </div>

                    <div className="pipeline-funnel">
                        {['lead', 'qualified', 'negotiating', 'contract', 'active'].map((stage) => (
                            <div key={stage} className={`stage stage-${stage}`}>
                                <h3>{stage.charAt(0).toUpperCase() + stage.slice(1)}</h3>
                                <span className="count">
                                    {pipeline.deals_by_stage[stage]?.length || 0} deals
                                </span>
                                <div className="deals-list">
                                    {pipeline.deals_by_stage[stage]?.slice(0, 3).map((deal) => (
                                        <div key={deal.deal_id} className="deal-card">
                                            <span className="brand">{deal.brand_name}</span>
                                            <span className="value">${deal.deal_value.toLocaleString()}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Stripe Connection Status */}
            {summary && !summary.stripe_connected && (
                <section className="stripe-cta">
                    <div className="cta-card">
                        <h3>Connect Stripe</h3>
                        <p>Connect your Stripe account to receive payouts directly.</p>
                        <button className="connect-btn">Connect Stripe →</button>
                    </div>
                </section>
            )}

            <style jsx>{`
        .revenue-dashboard {
          padding: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }

        .dashboard-header h1 {
          font-size: 28px;
          font-weight: 700;
          background: linear-gradient(135deg, #8B5CF6, #EC4899);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .period-selector {
          display: flex;
          gap: 8px;
        }

        .period-selector button {
          padding: 8px 16px;
          border: 1px solid #333;
          border-radius: 8px;
          background: transparent;
          color: #888;
          cursor: pointer;
          transition: all 0.2s;
        }

        .period-selector button.active,
        .period-selector button:hover {
          background: linear-gradient(135deg, #8B5CF6, #EC4899);
          color: white;
          border-color: transparent;
        }

        .summary-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .card {
          background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
          border: 1px solid #333;
          border-radius: 16px;
          padding: 24px;
          display: flex;
          flex-direction: column;
        }

        .card .label {
          font-size: 14px;
          color: #888;
          margin-bottom: 8px;
        }

        .card .value {
          font-size: 28px;
          font-weight: 700;
          color: #fff;
        }

        .card .sublabel {
          font-size: 12px;
          color: #666;
          margin-top: 4px;
        }

        .card.total-revenue .value {
          background: linear-gradient(135deg, #10B981, #34D399);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .revenue-breakdown,
        .deal-pipeline {
          background: #1A1A2E;
          border: 1px solid #333;
          border-radius: 16px;
          padding: 24px;
          margin-bottom: 24px;
        }

        .revenue-breakdown h2,
        .deal-pipeline h2 {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 20px;
        }

        .source-bar {
          display: grid;
          grid-template-columns: 100px 1fr 80px;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .source-name {
          font-size: 14px;
          color: #888;
          text-transform: capitalize;
        }

        .bar-container {
          height: 8px;
          background: #333;
          border-radius: 4px;
          overflow: hidden;
        }

        .bar-fill {
          height: 100%;
          background: linear-gradient(90deg, #8B5CF6, #EC4899);
          border-radius: 4px;
          transition: width 0.5s ease;
        }

        .source-value {
          font-size: 14px;
          font-weight: 600;
          text-align: right;
        }

        .pipeline-metrics {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        .metric {
          text-align: center;
        }

        .metric-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
          color: #8B5CF6;
        }

        .metric-label {
          font-size: 12px;
          color: #888;
        }

        .pipeline-funnel {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 12px;
        }

        .stage {
          background: #16213E;
          border-radius: 12px;
          padding: 16px;
        }

        .stage h3 {
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .stage .count {
          font-size: 12px;
          color: #888;
        }

        .deals-list {
          margin-top: 12px;
        }

        .deal-card {
          background: #1A1A2E;
          border-radius: 8px;
          padding: 8px 12px;
          margin-bottom: 8px;
          display: flex;
          justify-content: space-between;
          font-size: 12px;
        }

        .deal-card .brand {
          color: #fff;
        }

        .deal-card .value {
          color: #10B981;
          font-weight: 600;
        }

        .stripe-cta .cta-card {
          background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
          border: 1px solid #6366F1;
          border-radius: 16px;
          padding: 32px;
          text-align: center;
        }

        .stripe-cta h3 {
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .stripe-cta p {
          color: #888;
          margin-bottom: 16px;
        }

        .connect-btn {
          background: linear-gradient(135deg, #6366F1, #8B5CF6);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .connect-btn:hover {
          transform: translateY(-2px);
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #333;
          border-top-color: #8B5CF6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .error-message {
          color: #EF4444;
        }
      `}</style>
        </div>
    );
}

export default RevenueDashboard;
