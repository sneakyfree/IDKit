"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface Competitor {
    id: string;
    name: string;
    platform: string;
    follower_count: number;
    engagement_rate: number;
    growth_rate: number;
    last_analyzed_at: string;
}

export default function CompetitorsPage() {
    const [competitors, setCompetitors] = useState<Competitor[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: Competitor[] } | Competitor[]>(
                    "/api/v1/competitors"
                );
                setCompetitors(Array.isArray(result) ? result : result?.items || []);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    if (loading)
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="animate-pulse text-lg">Analyzing competitors...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Competitor Analysis</h1>
            <p className="text-zinc-400 mb-6">Track and benchmark against your competitors</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {competitors.length > 0 ? (
                    competitors.map((c) => (
                        <div key={c.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-lg">{c.name}</h3>
                                <span className="text-xs px-2 py-1 rounded-full bg-indigo-900/50 text-indigo-300">{c.platform}</span>
                            </div>
                            <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                                <div><span className="text-zinc-500">Followers</span><p className="font-mono">{c.follower_count?.toLocaleString()}</p></div>
                                <div><span className="text-zinc-500">Engagement</span><p className="font-mono">{c.engagement_rate}%</p></div>
                                <div><span className="text-zinc-500">Growth</span><p className={`font-mono ${c.growth_rate >= 0 ? "text-green-400" : "text-red-400"}`}>{c.growth_rate > 0 ? "+" : ""}{c.growth_rate}%</p></div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-500 text-lg">No competitors tracked yet</p>
                        <p className="text-zinc-600 text-sm mt-2">Add competitors to benchmark your growth</p>
                    </div>
                )}
            </div>
        </main>
    );
}
