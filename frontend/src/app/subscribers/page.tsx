"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface Subscriber {
    id: string;
    email: string;
    name: string;
    tier: string;
    subscribed_at: string;
    is_active: boolean;
}

export default function SubscribersPage() {
    const [subscribers, setSubscribers] = useState<Subscriber[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: Subscriber[] } | Subscriber[]>(
                    "/api/v1/subscribers"
                );
                setSubscribers(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading subscribers...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Subscribers</h1>
            <p className="text-zinc-400 mb-6">Manage your subscriber base and engagement</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden">
                {subscribers.length > 0 ? (
                    <table className="w-full text-sm">
                        <thead className="border-b border-zinc-800 bg-zinc-900/50">
                            <tr>
                                <th className="text-left p-3 text-zinc-400 font-medium">Name</th>
                                <th className="text-left p-3 text-zinc-400 font-medium">Email</th>
                                <th className="text-left p-3 text-zinc-400 font-medium">Tier</th>
                                <th className="text-left p-3 text-zinc-400 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {subscribers.map((sub) => (
                                <tr key={sub.id} className="hover:bg-zinc-800/50 transition-colors">
                                    <td className="p-3">{sub.name || "—"}</td>
                                    <td className="p-3 text-zinc-400">{sub.email}</td>
                                    <td className="p-3"><span className="px-2 py-0.5 rounded-full bg-blue-900/30 text-blue-300 text-xs">{sub.tier}</span></td>
                                    <td className="p-3">{sub.is_active ? <span className="text-green-400">Active</span> : <span className="text-zinc-500">Inactive</span>}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-300 text-lg">No subscribers yet</p>
                        <p className="text-zinc-400 text-sm mt-2">Start building your audience</p>
                    </div>
                )}
            </div>
        </main>
    );
}
