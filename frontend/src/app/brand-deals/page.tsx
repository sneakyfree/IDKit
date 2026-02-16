"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface BrandDeal {
    id: string;
    brand_name: string;
    title: string;
    status: string;
    budget: number;
    currency: string;
    created_at: string;
}

export default function BrandDealsPage() {
    const [deals, setDeals] = useState<BrandDeal[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: BrandDeal[] } | BrandDeal[]>(
                    "/api/v1/brand-deals"
                );
                setDeals(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading brand deals...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Brand Deals</h1>
            <p className="text-zinc-400 mb-6">Manage partnerships and sponsorship opportunities</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {deals.length > 0 ? (
                    deals.map((deal) => (
                        <div key={deal.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold text-lg">{deal.title || deal.brand_name}</h3>
                                <span className="text-xs px-2 py-1 rounded-full bg-purple-900/50 text-purple-300">{deal.status}</span>
                            </div>
                            <p className="text-zinc-400 text-sm">{deal.brand_name}</p>
                            {deal.budget > 0 && (
                                <p className="text-green-400 font-mono mt-1">${deal.budget.toLocaleString()} {deal.currency}</p>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-500 text-lg">No brand deals yet</p>
                        <p className="text-zinc-600 text-sm mt-2">Create your first deal to start monetizing</p>
                    </div>
                )}
            </div>
        </main>
    );
}
