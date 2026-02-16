"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Package,
    Search,
    Star,
    Download,
    Trash2,
    Loader2,
    Grid3X3,
    List,
    ExternalLink,
    Check,
} from "lucide-react";

/**
 * Plugin Marketplace
 *
 * Install/uninstall plugins with ratings, category filters, and search.
 * Closes Helix Scan gap X05-1.
 */

interface Plugin {
    id: string;
    name: string;
    description: string;
    version: string;
    author: string;
    category: string;
    rating: number;
    installs: number;
    installed: boolean;
    icon?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CATEGORIES = ["All", "Analytics", "Content", "Social", "Monetization", "Automation", "AI"];

// Seed data for demo
const SEED_PLUGINS: Plugin[] = [
    { id: "1", name: "Instagram Insights Pro", description: "Advanced Instagram analytics with Stories and Reels breakdown", version: "2.1.0", author: "IDKit Labs", category: "Analytics", rating: 4.8, installs: 12500, installed: true },
    { id: "2", name: "TikTok Auto-Poster", description: "Schedule and auto-post content to TikTok with optimal timing", version: "1.5.2", author: "SocialStack", category: "Automation", rating: 4.5, installs: 8300, installed: false },
    { id: "3", name: "Brand Deal Finder", description: "AI-powered brand deal matching based on your audience", version: "3.0.1", author: "IDKit Labs", category: "Monetization", rating: 4.9, installs: 15200, installed: true },
    { id: "4", name: "Content Repurposer", description: "Auto-convert long-form content into shorts, threads, carousels", version: "1.2.0", author: "CreatorTools", category: "Content", rating: 4.3, installs: 6100, installed: false },
    { id: "5", name: "Hashtag Optimizer", description: "ML-powered hashtag suggestions for maximum reach", version: "2.0.0", author: "IDKit Labs", category: "Social", rating: 4.6, installs: 9800, installed: false },
    { id: "6", name: "Revenue Forecaster", description: "Predict future earnings based on growth trends", version: "1.1.0", author: "FinTools", category: "Monetization", rating: 4.4, installs: 4200, installed: false },
    { id: "7", name: "Sentiment Analyzer", description: "Real-time sentiment analysis on comments and mentions", version: "1.8.0", author: "AI Vision", category: "AI", rating: 4.7, installs: 7600, installed: true },
    { id: "8", name: "YouTube SEO Toolkit", description: "Optimize titles, descriptions, and tags for YouTube discovery", version: "2.3.1", author: "TubeTools", category: "Content", rating: 4.5, installs: 11000, installed: false },
];

export default function PluginsPage() {
    const [plugins, setPlugins] = useState<Plugin[]>(SEED_PLUGINS);
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("All");
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [installing, setInstalling] = useState<string | null>(null);

    const handleInstall = async (pluginId: string) => {
        setInstalling(pluginId);
        try {
            await fetch(`${API_BASE}/api/v1/plugins/${pluginId}/install`, {
                method: "POST",
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
            });
        } catch {
            // silent
        }
        // Optimistic update
        setPlugins((prev) =>
            prev.map((p) => (p.id === pluginId ? { ...p, installed: true } : p))
        );
        setInstalling(null);
    };

    const handleUninstall = async (pluginId: string) => {
        try {
            await fetch(`${API_BASE}/api/v1/plugins/${pluginId}/uninstall`, {
                method: "POST",
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
            });
        } catch {
            // silent
        }
        setPlugins((prev) =>
            prev.map((p) => (p.id === pluginId ? { ...p, installed: false } : p))
        );
    };

    const filtered = plugins.filter((p) => {
        if (category !== "All" && p.category !== category) return false;
        if (search && !p.name.toLowerCase().includes(search.toLowerCase()) && !p.description.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <Package className="w-8 h-8 text-purple-400" />
                        <div>
                            <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
                            <p className="text-gray-400 text-sm">{plugins.filter((p) => p.installed).length} installed · {plugins.length} available</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setViewMode("grid")}
                            className={`p-2 rounded-lg border ${viewMode === "grid" ? "border-purple-500 bg-purple-500/10" : "border-gray-700 bg-gray-800"}`}
                        >
                            <Grid3X3 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setViewMode("list")}
                            className={`p-2 rounded-lg border ${viewMode === "list" ? "border-purple-500 bg-purple-500/10" : "border-gray-700 bg-gray-800"}`}
                        >
                            <List className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex gap-3 mb-6">
                    <div className="flex-1 relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search plugins..."
                            className="w-full pl-9 pr-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                        />
                    </div>
                    <div className="flex gap-1.5 overflow-x-auto">
                        {CATEGORIES.map((c) => (
                            <button
                                key={c}
                                onClick={() => setCategory(c)}
                                className={`px-3 py-2 rounded-lg border text-sm whitespace-nowrap transition-colors ${category === c
                                        ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                        : "border-gray-700 bg-gray-800 text-gray-400"
                                    }`}
                            >
                                {c}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Plugin Grid */}
                <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-3"}>
                    {filtered.map((plugin) => (
                        <div key={plugin.id} className={`bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-700 transition-colors ${viewMode === "list" ? "flex items-center gap-4 p-4" : "p-5"}`}>
                            {/* Plugin icon */}
                            <div className={`w-12 h-12 rounded-xl bg-purple-600/20 flex items-center justify-center text-lg font-bold text-purple-400 ${viewMode === "list" ? "flex-shrink-0" : "mb-3"}`}>
                                {plugin.name.charAt(0)}
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className={`flex items-start justify-between ${viewMode === "grid" ? "mb-2" : ""}`}>
                                    <div>
                                        <h3 className="font-medium truncate">{plugin.name}</h3>
                                        <p className="text-xs text-gray-500">{plugin.author} · v{plugin.version}</p>
                                    </div>
                                    {plugin.installed && (
                                        <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">
                                            <Check className="w-3 h-3" /> Installed
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-gray-400 mb-3 line-clamp-2">{plugin.description}</p>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3 text-xs text-gray-500">
                                        <span className="flex items-center gap-1">
                                            <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" /> {plugin.rating}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Download className="w-3 h-3" /> {(plugin.installs / 1000).toFixed(1)}k
                                        </span>
                                        <span className="px-2 py-0.5 border border-gray-700 rounded text-gray-400">{plugin.category}</span>
                                    </div>
                                    {plugin.installed ? (
                                        <button
                                            onClick={() => handleUninstall(plugin.id)}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs hover:bg-red-500/20"
                                        >
                                            <Trash2 className="w-3 h-3" /> Remove
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleInstall(plugin.id)}
                                            disabled={installing === plugin.id}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 rounded-lg text-xs hover:bg-purple-500 disabled:opacity-50"
                                        >
                                            {installing === plugin.id ? (
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                            ) : (
                                                <Download className="w-3 h-3" />
                                            )}
                                            Install
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {filtered.length === 0 && (
                    <div className="text-center py-16 text-gray-500">
                        <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                        <p>No plugins match your search.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
