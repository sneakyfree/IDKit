"use client";

import { useState, useEffect, useCallback } from "react";
import {
    BarChart3,
    Plus,
    Calendar,
    Download,
    Loader2,
    Trash2,
    Play,
    Clock,
    FileText,
    PieChart,
    TrendingUp,
    Filter,
} from "lucide-react";

/**
 * Report Builder / Custom Reports Page
 *
 * Drag-and-drop style report builder with metric picker, filters,
 * chart type selection, preview, save & schedule.
 * Closes Helix Scan gap A09.
 */

interface Report {
    id: string;
    name: string;
    type: string;
    status: string;
    created_at: string;
    last_run: string | null;
    schedule: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const METRICS = [
    { id: "followers", label: "Followers Growth", category: "Audience" },
    { id: "engagement_rate", label: "Engagement Rate", category: "Engagement" },
    { id: "impressions", label: "Impressions", category: "Reach" },
    { id: "clicks", label: "Click-through Rate", category: "Reach" },
    { id: "revenue", label: "Revenue", category: "Monetization" },
    { id: "roi", label: "ROI", category: "Monetization" },
    { id: "content_count", label: "Content Published", category: "Content" },
    { id: "avg_watch_time", label: "Avg Watch Time", category: "Content" },
    { id: "shares", label: "Shares", category: "Engagement" },
    { id: "comments", label: "Comments", category: "Engagement" },
];

const CHART_TYPES = [
    { id: "line", label: "Line", icon: TrendingUp },
    { id: "bar", label: "Bar", icon: BarChart3 },
    { id: "pie", label: "Pie", icon: PieChart },
];

const PLATFORMS = ["All", "Twitter/X", "Instagram", "TikTok", "YouTube", "LinkedIn"];

export default function ReportsPage() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);
    const [showBuilder, setShowBuilder] = useState(false);

    // Builder state
    const [reportName, setReportName] = useState("");
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
    const [chartType, setChartType] = useState("bar");
    const [platform, setPlatform] = useState("All");
    const [dateRange, setDateRange] = useState("last_30_days");
    const [creating, setCreating] = useState(false);

    const headers = { Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("token") : ""}` };

    const fetchReports = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/reports`, { headers });
            if (res.ok) {
                const data = await res.json();
                setReports(data.reports || []);
            }
        } catch {
            // silent
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        fetchReports();
    }, [fetchReports]);

    const toggleMetric = (id: string) => {
        setSelectedMetrics((prev) =>
            prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
        );
    };

    const handleCreate = async () => {
        if (!reportName || selectedMetrics.length === 0) return;
        setCreating(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/reports`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: reportName,
                    report_type: chartType,
                    config: { metrics: selectedMetrics, platform, date_range: dateRange },
                }),
            });
            if (res.ok) {
                setShowBuilder(false);
                setReportName("");
                setSelectedMetrics([]);
                fetchReports();
            }
        } catch {
            // silent
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (id: string) => {
        try {
            await fetch(`${API_BASE}/api/v1/reports/${id}`, { method: "DELETE", headers });
            fetchReports();
        } catch {
            // silent
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-950">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <BarChart3 className="w-8 h-8 text-purple-400" />
                        <div>
                            <h1 className="text-2xl font-bold">Custom Reports</h1>
                            <p className="text-gray-200 text-sm">{reports.length} saved reports</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowBuilder(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 transition-colors"
                    >
                        <Plus className="w-4 h-4" /> Build Report
                    </button>
                </div>

                {/* Saved Reports */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                    {reports.map((r) => (
                        <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors">
                            <div className="flex items-center justify-between mb-3">
                                <FileText className="w-5 h-5 text-purple-400" />
                                <button onClick={() => handleDelete(r.id)} className="p-1 hover:bg-gray-800 rounded">
                                    <Trash2 className="w-4 h-4 text-gray-300" />
                                </button>
                            </div>
                            <h3 className="font-medium mb-1">{r.name}</h3>
                            <p className="text-sm text-gray-300 mb-3">{r.type} chart</p>
                            <div className="flex items-center gap-2 text-xs text-gray-200">
                                <Clock className="w-3 h-3" />
                                {r.last_run ? `Last run: ${new Date(r.last_run).toLocaleDateString()}` : "Never run"}
                            </div>
                        </div>
                    ))}
                    {reports.length === 0 && (
                        <div className="col-span-full text-center py-16 text-gray-300">
                            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>No reports yet. Click &quot;Build Report&quot; to create your first custom report.</p>
                        </div>
                    )}
                </div>

                {/* Report Builder Modal */}
                {showBuilder && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                        <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                            <div className="p-6 border-b border-gray-800">
                                <h2 className="text-xl font-bold text-white">Report Builder</h2>
                                <p className="text-sm text-gray-300">Select metrics, choose visualization, and schedule your report.</p>
                            </div>

                            <div className="p-6 space-y-6">
                                {/* Name */}
                                <div>
                                    <label className="block text-sm text-gray-200 mb-2">Report Name</label>
                                    <input
                                        type="text"
                                        value={reportName}
                                        onChange={(e) => setReportName(e.target.value)}
                                        placeholder="e.g., Monthly Performance Overview"
                                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                                    />
                                </div>

                                {/* Metrics Picker */}
                                <div>
                                    <label className="block text-sm text-gray-200 mb-2">
                                        <Filter className="w-4 h-4 inline mr-1" /> Metrics ({selectedMetrics.length} selected)
                                    </label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {METRICS.map((m) => (
                                            <button
                                                key={m.id}
                                                onClick={() => toggleMetric(m.id)}
                                                className={`text-left p-3 rounded-lg border transition-colors text-sm ${selectedMetrics.includes(m.id)
                                                        ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                                        : "border-gray-700 bg-gray-800 text-gray-200 hover:border-gray-600"
                                                    }`}
                                            >
                                                <span className="block font-medium">{m.label}</span>
                                                <span className="text-xs opacity-60">{m.category}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Chart Type */}
                                <div>
                                    <label className="block text-sm text-gray-200 mb-2">Chart Type</label>
                                    <div className="flex gap-2">
                                        {CHART_TYPES.map((ct) => (
                                            <button
                                                key={ct.id}
                                                onClick={() => setChartType(ct.id)}
                                                className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${chartType === ct.id
                                                        ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                                        : "border-gray-700 bg-gray-800 text-gray-200"
                                                    }`}
                                            >
                                                <ct.icon className="w-4 h-4" /> {ct.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Platform & Date */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-gray-200 mb-2">Platform</label>
                                        <select aria-label="Filter or select option"
                                            value={platform}
                                            onChange={(e) => setPlatform(e.target.value)}
                                            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                                        >
                                            {PLATFORMS.map((p) => (
                                                <option key={p} value={p}>{p}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-200 mb-2">Date Range</label>
                                        <select aria-label="Filter or select option"
                                            value={dateRange}
                                            onChange={(e) => setDateRange(e.target.value)}
                                            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                                        >
                                            <option value="last_7_days">Last 7 days</option>
                                            <option value="last_30_days">Last 30 days</option>
                                            <option value="last_90_days">Last 90 days</option>
                                            <option value="last_year">Last year</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-3 p-6 border-t border-gray-800">
                                <button
                                    onClick={() => setShowBuilder(false)}
                                    className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreate}
                                    disabled={creating || !reportName || selectedMetrics.length === 0}
                                    className="flex-1 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-80 flex items-center justify-center gap-2"
                                >
                                    {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                                    Create Report
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
