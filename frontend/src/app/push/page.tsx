"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface PushNotification {
    id: string;
    title: string;
    message: string;
    status: string;
    sent_at: string;
    delivered_count: number;
    opened_count: number;
}

export default function PushPage() {
    const [notifications, setNotifications] = useState<PushNotification[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: PushNotification[] } | PushNotification[]>(
                    "/api/v1/push"
                );
                setNotifications(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading notifications...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Push Notifications</h1>
            <p className="text-zinc-400 mb-6">Send and track push notifications to your audience</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {notifications.length > 0 ? (
                    notifications.map((n) => (
                        <div key={n.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                            <div className="flex items-center justify-between mb-1">
                                <h3 className="font-semibold">{n.title}</h3>
                                <span className="text-xs text-zinc-500">{n.sent_at ? new Date(n.sent_at).toLocaleDateString() : "Draft"}</span>
                            </div>
                            <p className="text-zinc-400 text-sm mb-3">{n.message}</p>
                            <div className="flex gap-6 text-sm">
                                <span className="text-zinc-500">Delivered: <span className="text-white font-mono">{n.delivered_count}</span></span>
                                <span className="text-zinc-500">Opened: <span className="text-white font-mono">{n.opened_count}</span></span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-500 text-lg">No notifications sent yet</p>
                        <p className="text-zinc-600 text-sm mt-2">Engage your audience with push notifications</p>
                    </div>
                )}
            </div>
        </main>
    );
}
