"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface Trend {
    id: string;
    topic: string;
    platform: string;
    volume: number;
    growth_rate: number;
    relevance_score: number;
    category: string;
}

export default function TrendsPage() {
    const [trends, setTrends] = useState<Trend[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: Trend[] } | Trend[]>(
                    "/api/v1/trends"
                );
                setTrends(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Discovering trends...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Trends Analysis</h1>
            <p className="text-zinc-400 mb-6">Discover trending topics in your niche</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {trends.length > 0 ? (
                    trends.map((t) => (
                        <div key={t.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <div>
                                    <h3 className="font-semibold text-lg">{t.topic}</h3>
                                    <span className="text-xs text-zinc-500">{t.category} · {t.platform}</span>
                                </div>
                                <span className={`text-sm font-mono font-bold ${t.growth_rate >= 0 ? "text-green-400" : "text-red-400"}`}>
                                    {t.growth_rate > 0 ? "↑" : "↓"} {Math.abs(t.growth_rate)}%
                                </span>
                            </div>
                            <div className="flex items-center gap-4 mt-3 text-sm text-zinc-400">
                                <span>Volume: <span className="text-white font-mono">{t.volume?.toLocaleString()}</span></span>
                                <span>Relevance: <span className="text-white font-mono">{t.relevance_score}/100</span></span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-500 text-lg">No trends detected yet</p>
                        <p className="text-zinc-600 text-sm mt-2">Trends will appear as we analyze your niche</p>
                    </div>
                )}
            </div>
        </main>
    );
}
