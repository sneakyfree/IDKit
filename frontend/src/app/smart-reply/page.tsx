"use client";

import { useState, useEffect } from "react";
import { apiRequest } from "@/lib/api";

interface SmartReply {
    id: string;
    original_message: string;
    suggested_reply: string;
    platform: string;
    confidence: number;
    status: string;
}

export default function SmartReplyPage() {
    const [replies, setReplies] = useState<SmartReply[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await apiRequest<{ items: SmartReply[] } | SmartReply[]>(
                    "/api/v1/smart-reply"
                );
                setReplies(Array.isArray(result) ? result : result?.items || []);
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
                <div className="animate-pulse text-lg">Loading smart replies...</div>
            </div>
        );

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-2">Smart Reply</h1>
            <p className="text-zinc-400 mb-6">AI-generated responses for your messages</p>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {replies.length > 0 ? (
                    replies.map((r) => (
                        <div key={r.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800">
                            <div className="mb-3">
                                <p className="text-xs text-zinc-500 mb-1">Original Message</p>
                                <p className="text-zinc-300 text-sm bg-zinc-800/50 rounded-lg p-3">{r.original_message}</p>
                            </div>
                            <div>
                                <p className="text-xs text-zinc-500 mb-1">Suggested Reply</p>
                                <p className="text-white text-sm bg-purple-900/20 border border-purple-800/30 rounded-lg p-3">{r.suggested_reply}</p>
                            </div>
                            <div className="flex items-center justify-between mt-3 text-xs text-zinc-500">
                                <span>{r.platform}</span>
                                <span>Confidence: {r.confidence}%</span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-16">
                        <p className="text-zinc-300 text-lg">No smart replies yet</p>
                        <p className="text-zinc-400 text-sm mt-2">Connect your inbox to get AI-generated replies</p>
                    </div>
                )}
            </div>
        </main>
    );
}
