"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface ViralPrediction {
    id: string;
    content_title: string;
    predicted_score: number;
    confidence: number;
    platform: string;
    factors: string[];
    created_at: string;
}

export default function ViralPage() {
    const [predictions, setPredictions] = useState<ViralPrediction[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: ViralPrediction[] } | ViralPrediction[]>(
                    "/api/v1/viral"
                );
                setPredictions(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Analyzing viral potential...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Viral Prediction</h1>
            <p className="text-zinc-400 mb-6">AI-powered predictions for content virality</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {predictions.length > 0 ? (
                    predictions.map((p) => (
                        <div key={p.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold">{p.content_title}</h3>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-zinc-500">{p.platform}</span>
                                    <span className={`text-lg font-bold ${p.predicted_score >= 80 ? "text-green-400" :
                                            p.predicted_score >= 50 ? "text-yellow-400" :
                                                "text-zinc-400"
                                        }`}>{p.predicted_score}%</span>
                                </div>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-2 mb-3">
                                <div className="bg-gradient-to-r from-purple-600 to-pink-500 h-2 rounded-full transition-all" style={{ width: `${p.predicted_score}%` }} />
                            </div>
                            {p.factors && p.factors.length > 0 && (
                                <div className="flex flex-wrap gap-2">
                                    {p.factors.map((f, i) => (
                                        <span key={i} className="text-xs px-2 py-1 bg-zinc-800 rounded-full text-zinc-400">{f}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-300 text-lg">No predictions yet</p>
                        <p className="text-zinc-400 text-sm mt-2">Create content to get viral predictions</p>
                    </div>
                )}
            </div>
        </main>
    );
}
