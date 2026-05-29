"use client";

import { useState, useEffect } from "react";
import {
    BarChart3,
    TrendingUp,
    Users,
    DollarSign,
    ArrowUpRight,
    ArrowDownRight,
    Eye,
} from "lucide-react";

/**
 * Shared Analytics Component
 *
 * Combined metrics view for collaborators: split-screen comparison, shared revenue.
 * Closes Helix Scan gap L09-1.
 */

interface CollaboratorMetrics {
    id: string;
    name: string;
    avatar?: string;
    followers: number;
    engagement_rate: number;
    impressions: number;
    revenue_share: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Seed data for demo
const SEED_DATA: CollaboratorMetrics[] = [
    {
        id: "1",
        name: "You",
        followers: 125000,
        engagement_rate: 4.8,
        impressions: 2500000,
        revenue_share: 6240,
    },
    {
        id: "2",
        name: "Collaborator",
        followers: 89000,
        engagement_rate: 5.2,
        impressions: 1800000,
        revenue_share: 4820,
    },
];

interface SharedAnalyticsProps {
    collaborationId: string;
}

export default function SharedAnalytics({ collaborationId }: SharedAnalyticsProps) {
    const [metrics, setMetrics] = useState<CollaboratorMetrics[]>(SEED_DATA);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setLoading(true);
        fetch(`${API_BASE}/api/v1/collaborations/${collaborationId}/analytics`, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        })
            .then((r) => r.ok ? r.json() : null)
            .then((data) => { if (data?.metrics) setMetrics(data.metrics); })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [collaborationId]);

    const totalRevenue = metrics.reduce((sum, m) => sum + m.revenue_share, 0);
    const totalImpressions = metrics.reduce((sum, m) => sum + m.impressions, 0);

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <div className="flex items-center gap-3 mb-5">
                <BarChart3 className="w-6 h-6 text-purple-400" />
                <h3 className="font-bold text-lg">Shared Analytics</h3>
            </div>

            {/* Combined Summary */}
            <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <Eye className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                    <p className="text-lg font-bold">{(totalImpressions / 1e6).toFixed(1)}M</p>
                    <p className="text-xs text-gray-300">Combined Reach</p>
                </div>
                <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <TrendingUp className="w-5 h-5 text-green-400 mx-auto mb-1" />
                    <p className="text-lg font-bold">
                        {(metrics.reduce((s, m) => s + m.engagement_rate, 0) / metrics.length).toFixed(1)}%
                    </p>
                    <p className="text-xs text-gray-300">Avg Engagement</p>
                </div>
                <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <DollarSign className="w-5 h-5 text-yellow-400 mx-auto mb-1" />
                    <p className="text-lg font-bold">${totalRevenue.toLocaleString()}</p>
                    <p className="text-xs text-gray-300">Total Revenue</p>
                </div>
            </div>

            {/* Split-Screen Comparison */}
            <div className="space-y-2">
                {metrics.map((m) => (
                    <div key={m.id} className="bg-gray-800 rounded-xl p-4">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center text-xs text-purple-400 font-bold">
                                    {m.name.charAt(0)}
                                </div>
                                <span className="font-medium text-sm">{m.name}</span>
                            </div>
                            <span className="text-xs text-gray-300">
                                <Users className="w-3 h-3 inline mr-1" />
                                {(m.followers / 1000).toFixed(0)}K followers
                            </span>
                        </div>

                        <div className="grid grid-cols-3 gap-3">
                            <div>
                                <p className="text-xs text-gray-300 mb-0.5">Engagement</p>
                                <p className="font-medium text-sm">
                                    {m.engagement_rate}%
                                    <ArrowUpRight className="w-3 h-3 text-green-400 inline ml-1" />
                                </p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-300 mb-0.5">Impressions</p>
                                <p className="font-medium text-sm">{(m.impressions / 1e6).toFixed(1)}M</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-300 mb-0.5">Revenue Share</p>
                                <p className="font-medium text-sm text-green-400">${m.revenue_share.toLocaleString()}</p>
                            </div>
                        </div>

                        {/* Revenue Split Bar */}
                        <div className="mt-3">
                            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                                    style={{ width: `${(m.revenue_share / totalRevenue) * 100}%` }}
                                />
                            </div>
                            <p className="text-[10px] text-gray-200 mt-1">
                                {((m.revenue_share / totalRevenue) * 100).toFixed(0)}% of total revenue
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
