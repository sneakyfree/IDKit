"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface RepurposedContent {
    id: string;
    original_title: string;
    original_platform: string;
    target_platform: string;
    status: string;
    content_type: string;
    created_at: string;
}

export default function RepurposePage() {
    const [items, setItems] = useState<RepurposedContent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: RepurposedContent[] } | RepurposedContent[]>(
                    "/api/v1/repurpose"
                );
                setItems(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading repurposed content...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Content Repurposing</h1>
            <p className="text-zinc-400 mb-6">Transform your content across platforms with AI</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {items.length > 0 ? (
                    items.map((item) => (
                        <div key={item.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <h3 className="font-semibold mb-2">{item.original_title}</h3>
                            <div className="flex items-center gap-2 text-sm">
                                <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{item.original_platform}</span>
                                <span className="text-zinc-600">→</span>
                                <span className="px-2 py-0.5 rounded bg-purple-900/30 text-purple-300">{item.target_platform}</span>
                            </div>
                            <div className="flex items-center justify-between mt-3 text-xs text-zinc-500">
                                <span>{item.content_type}</span>
                                <span className={`px-2 py-0.5 rounded-full ${item.status === "completed" ? "bg-green-900/30 text-green-400" :
                                        item.status === "processing" ? "bg-yellow-900/30 text-yellow-400" :
                                            "bg-zinc-800 text-zinc-400"
                                    }`}>{item.status}</span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-300 text-lg">No repurposed content yet</p>
                        <p className="text-zinc-400 text-sm mt-2">Transform your best content for new audiences</p>
                    </div>
                )}
            </div>
        </main>
    );
}
