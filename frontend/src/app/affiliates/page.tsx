"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface Affiliate {
    id: string;
    name: string;
    url: string;
    commission_rate: number;
    clicks: number;
    conversions: number;
    earnings: number;
    status: string;
}

export default function AffiliatesPage() {
    const [affiliates, setAffiliates] = useState<Affiliate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: Affiliate[] } | Affiliate[]>(
                    "/api/v1/affiliates/links"
                );
                setAffiliates(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading affiliates...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Affiliate Links</h1>
            <p className="text-zinc-400 mb-6">Track and manage your affiliate partnerships</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {affiliates.length > 0 ? (
                    affiliates.map((aff) => (
                        <div key={aff.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold">{aff.name}</h3>
                                <span className="text-xs px-2 py-1 rounded-full bg-emerald-900/50 text-emerald-300">{aff.status}</span>
                            </div>
                            <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                                <div><span className="text-zinc-500">Clicks</span><p className="font-mono">{aff.clicks}</p></div>
                                <div><span className="text-zinc-500">Conversions</span><p className="font-mono">{aff.conversions}</p></div>
                                <div><span className="text-zinc-500">Earnings</span><p className="font-mono text-green-400">${aff.earnings.toLocaleString()}</p></div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-500 text-lg">No affiliate links yet</p>
                        <p className="text-zinc-600 text-sm mt-2">Add affiliate links to start earning commissions</p>
                    </div>
                )}
            </div>
        </main>
    );
}
