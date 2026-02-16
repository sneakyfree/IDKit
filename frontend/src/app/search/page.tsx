"use client";

import { useState } from "react";
import { apiRequest } from "@/lib/api";

interface SearchResult {
    id: string;
    type: string;
    title: string;
    snippet: string;
    score: number;
}

export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const result = await apiRequest<{ results: SearchResult[] } | SearchResult[]>(
                `/api/v1/search?q=${encodeURIComponent(query)}`
            );
            setResults(Array.isArray(result) ? result : result?.results || []);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Search failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-black text-white p-6 pb-24">
            <h1 className="text-2xl font-bold mb-6">Search</h1>

            <div className="flex gap-2 mb-6">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    placeholder="Search content, creators, trends..."
                    className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-purple-500 transition-colors"
                />
                <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50"
                >
                    {loading ? "..." : "Search"}
                </button>
            </div>

            {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            <div className="space-y-4">
                {results.map((r) => (
                    <div key={r.id} className="bg-zinc-900 rounded-xl p-4 border border-zinc-800 hover:border-zinc-700 transition-colors">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{r.type}</span>
                            <span className="text-xs text-zinc-600">Score: {r.score}</span>
                        </div>
                        <h3 className="font-semibold">{r.title}</h3>
                        <p className="text-zinc-400 text-sm mt-1">{r.snippet}</p>
                    </div>
                ))}
                {!loading && results.length === 0 && query && (
                    <p className="text-zinc-500 text-center py-8">No results found</p>
                )}
            </div>
        </main>
    );
}
