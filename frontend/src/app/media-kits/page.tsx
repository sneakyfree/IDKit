"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface MediaKit {
    id: string;
    title: string;
    status: string;
    platforms: string[];
    total_followers: number;
    avg_engagement_rate: number;
    updated_at: string;
}

export default function MediaKitsPage() {
    const [kits, setKits] = useState<MediaKit[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: MediaKit[] } | MediaKit[]>(
                    "/api/v1/media-kits"
                );
                setKits(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading media kits...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Media Kits</h1>
            <p className="text-zinc-400 mb-6">Professional media kits to share with brands</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {kits.length > 0 ? (
                    kits.map((kit) => (
                        <div key={kit.id} className="bg-zinc-900 rounded-xl p-5 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-lg">{kit.title}</h3>
                                <span className={`text-xs px-2 py-1 rounded-full ${kit.status === "published" ? "bg-green-900/50 text-green-300" : "bg-zinc-800 text-zinc-400"
                                    }`}>{kit.status}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                                <div className="bg-zinc-800/50 rounded-lg p-3">
                                    <p className="text-zinc-500 text-xs">Total Followers</p>
                                    <p className="font-mono text-lg">{kit.total_followers?.toLocaleString()}</p>
                                </div>
                                <div className="bg-zinc-800/50 rounded-lg p-3">
                                    <p className="text-zinc-500 text-xs">Avg. Engagement</p>
                                    <p className="font-mono text-lg">{kit.avg_engagement_rate}%</p>
                                </div>
                            </div>
                            {kit.platforms && kit.platforms.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {kit.platforms.map((p) => (
                                        <span key={p} className="text-xs px-2 py-0.5 bg-zinc-800 rounded-full text-zinc-400">{p}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="col-span-2 text-center py-16">
                        <p className="text-zinc-300 text-lg">No media kits yet</p>
                        <p className="text-zinc-400 text-sm mt-2">Create a media kit to showcase your brand</p>
                    </div>
                )}
            </div>
        </main>
    );
}
