"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface ComplianceItem {
    id: string;
    type: string;
    title: string;
    status: string;
    severity: string;
    description: string;
    due_date: string;
}

export default function CompliancePage() {
    const [items, setItems] = useState<ComplianceItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: ComplianceItem[] } | ComplianceItem[]>(
                    "/api/v1/compliance"
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
                <div className="animate-pulse text-lg">Loading compliance...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Compliance</h1>
            <p className="text-zinc-400 mb-6">GDPR, FTC, and platform compliance tracking</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {items.length > 0 ? (
                    items.map((item) => (
                        <div key={item.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="font-semibold">{item.title}</h3>
                                <div className="flex gap-2">
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${item.severity === "high" ? "bg-red-900/50 text-red-300" :
                                            item.severity === "medium" ? "bg-yellow-900/50 text-yellow-300" :
                                                "bg-green-900/50 text-green-300"
                                        }`}>{item.severity}</span>
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${item.status === "compliant" ? "bg-green-900/50 text-green-300" :
                                            item.status === "pending" ? "bg-yellow-900/50 text-yellow-300" :
                                                "bg-red-900/50 text-red-300"
                                        }`}>{item.status}</span>
                                </div>
                            </div>
                            <p className="text-zinc-400 text-sm">{item.description}</p>
                            <div className="flex items-center justify-between mt-2 text-xs text-zinc-500">
                                <span>{item.type}</span>
                                {item.due_date && <span>Due: {new Date(item.due_date).toLocaleDateString()}</span>}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-300 text-lg">All compliant ✓</p>
                        <p className="text-zinc-400 text-sm mt-2">No outstanding compliance items</p>
                    </div>
                )}
            </div>
        </main>
    );
}
