"use client";

import { useState, useEffect } from "react";
import { Radio, Plus, Search, TrendingUp, Users, MessageCircle, Loader2, AlertCircle, CheckCircle, Pause, Play } from "lucide-react";
import { listeningApi } from "@/lib/api";

/**
 * Social Listening UI
 * 
 * Brand monitoring and mention tracking
 */

interface ListeningQuery {
    id: string;
    name: string;
    keywords: string[];
    excludeKeywords: string[];
    platforms: string[];
    status: "active" | "paused";
    createdAt: string;
}

interface Mention {
    id: string;
    queryId: string;
    platform: "twitter" | "instagram" | "tiktok" | "youtube" | "reddit";
    content: string;
    author: {
        username: string;
        followers: number;
        avatar?: string;
    };
    sentiment: "positive" | "neutral" | "negative";
    engagement: { likes: number; comments: number; shares: number };
    url: string;
    publishedAt: string;
}

const PLATFORMS = [
    { id: "twitter", label: "Twitter/X", color: "text-blue-400" },
    { id: "instagram", label: "Instagram", color: "text-pink-400" },
    { id: "tiktok", label: "TikTok", color: "text-purple-400" },
    { id: "youtube", label: "YouTube", color: "text-red-400" },
    { id: "reddit", label: "Reddit", color: "text-orange-400" },
];



export default function SocialListeningPage() {
    const [queries, setQueries] = useState<ListeningQuery[]>([]);
    const [mentions, setMentions] = useState<Mention[]>([]);
    const [selectedQuery, setSelectedQuery] = useState<string | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [sentimentFilter, setSentimentFilter] = useState<"all" | Mention["sentiment"]>("all");

    useEffect(() => {
        async function fetchData() {
            try {
                setLoading(true);
                const response = await listeningApi.listQueries();
                const apiQueries: ListeningQuery[] = (response.queries || []).map((q: any) => ({
                    id: q.id as string,
                    name: q.name as string,
                    keywords: (q.keywords as string[]) || [],
                    excludeKeywords: [],
                    platforms: (q.platforms as string[]) || [],
                    status: (q.status as "active" | "paused") || "active",
                    createdAt: q.created_at as string || new Date().toISOString(),
                }));
                setQueries(apiQueries);
                if (apiQueries.length > 0) {
                    setSelectedQuery(apiQueries[0].id);
                    try {
                        const mentionsResp = await listeningApi.getMentions(apiQueries[0].id, { limit: 50 });
                        setMentions((mentionsResp.mentions || []).map((m: any) => ({
                            id: m.id as string,
                            queryId: apiQueries[0].id,
                            platform: (m.platform as Mention["platform"]) || "twitter",
                            content: m.content as string || "",
                            author: {
                                username: (m.author_name as string) || "unknown",
                                followers: (m.engagement as number) || 0,
                            },
                            sentiment: (m.sentiment as Mention["sentiment"]) || "neutral",
                            engagement: { likes: (m.engagement as number) || 0, comments: 0, shares: 0 },
                            url: (m.url as string) || "#",
                            publishedAt: (m.posted_at as string) || new Date().toISOString(),
                        })));
                    } catch { /* no mentions yet */ }
                }
            } catch {
                // fall back to empty state
                setQueries([]);
                setMentions([]);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const filteredMentions = mentions
        .filter(m => !selectedQuery || m.queryId === selectedQuery)
        .filter(m => sentimentFilter === "all" || m.sentiment === sentimentFilter);

    const stats = {
        totalMentions: mentions.length,
        positive: mentions.filter(m => m.sentiment === "positive").length,
        neutral: mentions.filter(m => m.sentiment === "neutral").length,
        negative: mentions.filter(m => m.sentiment === "negative").length,
        totalReach: mentions.reduce((sum, m) => sum + m.author.followers, 0),
    };

    const toggleQueryStatus = (queryId: string) => {
        setQueries(prev => prev.map(q =>
            q.id === queryId ? { ...q, status: q.status === "active" ? "paused" : "active" } : q
        ));
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Social Listening</h1>
                        <p className="text-gray-200">Monitor brand mentions and track conversations</p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        New Query
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
                    <StatCard label="Total Mentions" value={stats.totalMentions} icon={<MessageCircle />} />
                    <StatCard label="Positive" value={stats.positive} color="text-green-400" icon={<TrendingUp />} />
                    <StatCard label="Neutral" value={stats.neutral} color="text-gray-200" icon={<MessageCircle />} />
                    <StatCard label="Negative" value={stats.negative} color="text-red-400" icon={<AlertCircle />} />
                    <StatCard label="Total Reach" value={`${(stats.totalReach / 1000).toFixed(0)}K`} icon={<Users />} />
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : (
                    <div className="grid md:grid-cols-4 gap-6">
                        {/* Queries Sidebar */}
                        <div className="space-y-4">
                            <h2 className="text-lg font-semibold">Listening Queries</h2>
                            {queries.map((query) => (
                                <div
                                    key={query.id}
                                    onClick={() => setSelectedQuery(query.id)}
                                    onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSelectedQuery(query.id); } }}
                                    role="button"
                                    tabIndex={0}
                                    className={`p-4 rounded-xl cursor-pointer transition-all ${selectedQuery === query.id
                                        ? "bg-purple-600/20 border border-purple-500"
                                        : "bg-gray-900 hover:bg-gray-800"
                                        }`}
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-medium">{query.name}</h3>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); toggleQueryStatus(query.id); }}
                                            className={`p-1 rounded ${query.status === "active" ? "text-green-400" : "text-gray-300"}`}
                                        >
                                            {query.status === "active" ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                                        </button>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {query.keywords.slice(0, 3).map((kw) => (
                                            <span key={kw} className="text-xs bg-gray-800 px-2 py-0.5 rounded">{kw}</span>
                                        ))}
                                        {query.keywords.length > 3 && (
                                            <span className="text-xs text-gray-300">+{query.keywords.length - 3}</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Mentions Feed */}
                        <div className="md:col-span-3">
                            {/* Sentiment Filter */}
                            <div className="flex gap-2 mb-4">
                                {(["all", "positive", "neutral", "negative"] as const).map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => setSentimentFilter(s)}
                                        className={`px-3 py-1 rounded-lg text-sm capitalize ${sentimentFilter === s ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                            }`}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>

                            {filteredMentions.length === 0 ? (
                                <div className="bg-gray-900 rounded-xl p-8 text-center">
                                    <Radio className="w-12 h-12 mx-auto text-gray-200 mb-3" />
                                    <p className="text-gray-300">No mentions found</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {filteredMentions.map((mention) => (
                                        <MentionCard key={mention.id} mention={mention} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Create Query Modal */}
                {showCreateModal && (
                    <CreateQueryModal
                        onClose={() => setShowCreateModal(false)}
                        onCreate={(query) => {
                            setQueries(prev => [...prev, query]);
                            setShowCreateModal(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function StatCard({ label, value, color = "text-white", icon }: { label: string; value: string | number; color?: string; icon: React.ReactNode }) {
    return (
        <div className="bg-gray-900 rounded-xl p-4">
            <div className="flex items-center gap-2 text-gray-300 mb-1">
                {icon}
                <span className="text-sm">{label}</span>
            </div>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
    );
}

function MentionCard({ mention }: { mention: Mention }) {
    const platform = PLATFORMS.find(p => p.id === mention.platform);
    const sentimentConfig = {
        positive: { color: "text-green-400 bg-green-400/10", icon: TrendingUp },
        neutral: { color: "text-gray-200 bg-gray-400/10", icon: MessageCircle },
        negative: { color: "text-red-400 bg-red-400/10", icon: AlertCircle },
    };
    const sentiment = sentimentConfig[mention.sentiment];

    return (
        <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center">
                        {mention.author.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <p className="font-medium">@{mention.author.username}</p>
                        <p className="text-xs text-gray-300">
                            {mention.author.followers.toLocaleString()} followers • {platform?.label}
                        </p>
                    </div>
                </div>
                <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${sentiment.color}`}>
                    <sentiment.icon className="w-3 h-3" />
                    {mention.sentiment}
                </span>
            </div>

            <p className="text-gray-300 mb-3">{mention.content}</p>

            <div className="flex items-center justify-between">
                <div className="flex gap-4 text-sm text-gray-300">
                    <span>❤️ {mention.engagement.likes}</span>
                    <span>💬 {mention.engagement.comments}</span>
                    <span>🔄 {mention.engagement.shares}</span>
                </div>
                <a
                    href={mention.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-purple-400 hover:text-purple-300"
                >
                    View →
                </a>
            </div>
        </div>
    );
}

function CreateQueryModal({
    onClose,
    onCreate,
}: {
    onClose: () => void;
    onCreate: (query: ListeningQuery) => void;
}) {
    const [name, setName] = useState("");
    const [keywords, setKeywords] = useState("");
    const [excludeKeywords, setExcludeKeywords] = useState("");
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);

    const togglePlatform = (id: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            id: Date.now().toString(),
            name,
            keywords: keywords.split(",").map(k => k.trim()).filter(Boolean),
            excludeKeywords: excludeKeywords.split(",").map(k => k.trim()).filter(Boolean),
            platforms: selectedPlatforms,
            status: "active",
            createdAt: new Date().toISOString(),
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-6">Create Listening Query</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="query-name" className="block text-sm text-gray-200 mb-1">Query Name *</label>
                        <input
                            id="query-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            placeholder="Brand Mentions"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div>
                        <label htmlFor="keywords-input" className="block text-sm text-gray-200 mb-1">Keywords (comma-separated) *</label>
                        <textarea
                            id="keywords-input"
                            value={keywords}
                            onChange={(e) => setKeywords(e.target.value)}
                            required
                            placeholder="mybrand, @mybrand, #mybrand"
                            rows={2}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div>
                        <label htmlFor="exclude-keywords" className="block text-sm text-gray-200 mb-1">Exclude Keywords</label>
                        <input
                            id="exclude-keywords"
                            value={excludeKeywords}
                            onChange={(e) => setExcludeKeywords(e.target.value)}
                            placeholder="spam, bot, ad"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div>
                        <label id="platforms-label" className="block text-sm text-gray-200 mb-2">Platforms</label>
                        <div className="flex flex-wrap gap-2">
                            {PLATFORMS.map((p) => (
                                <button
                                    key={p.id}
                                    type="button"
                                    onClick={() => togglePlatform(p.id)}
                                    className={`px-3 py-2 rounded-lg text-sm ${selectedPlatforms.includes(p.id)
                                        ? "bg-purple-600"
                                        : "bg-gray-800 hover:bg-gray-700"
                                        }`}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!name || !keywords || selectedPlatforms.length === 0}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-80"
                        >
                            Create
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
