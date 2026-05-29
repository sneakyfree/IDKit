"use client";

import { useState } from "react";
import {
    Download,
    FileText,
    BarChart3,
    DollarSign,
    Users,
    Loader2,
    CheckCircle,
    Clock,
    Calendar,
} from "lucide-react";

/**
 * Unified Export Center
 *
 * Central location for exporting analytics, revenue, content, and audience data.
 * Closes Helix Scan gap A10.
 */

type ExportCategory = "analytics" | "revenue" | "content" | "audience";
type ExportFormat = "csv" | "json" | "pdf";

interface ExportJob {
    id: string;
    category: ExportCategory;
    format: ExportFormat;
    status: "pending" | "processing" | "completed";
    created_at: string;
    file_url: string | null;
}

const CATEGORIES: { id: ExportCategory; label: string; icon: React.ElementType; description: string }[] = [
    { id: "analytics", label: "Analytics", icon: BarChart3, description: "Engagement, reach, and performance data" },
    { id: "revenue", label: "Revenue", icon: DollarSign, description: "Earnings, payouts, and sponsorship data" },
    { id: "content", label: "Content", icon: FileText, description: "Published posts, drafts, and media" },
    { id: "audience", label: "Audience", icon: Users, description: "Follower demographics and growth" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExportsPage() {
    const [activeTab, setActiveTab] = useState<ExportCategory>("analytics");
    const [format, setFormat] = useState<ExportFormat>("csv");
    const [dateRange, setDateRange] = useState("last_30_days");
    const [exporting, setExporting] = useState(false);
    const [exports, setExports] = useState<ExportJob[]>([]);

    const handleExport = async () => {
        setExporting(true);
        const newExport: ExportJob = {
            id: Math.random().toString(36).slice(2),
            category: activeTab,
            format,
            status: "processing",
            created_at: new Date().toISOString(),
            file_url: null,
        };
        setExports((prev) => [newExport, ...prev]);

        try {
            const res = await fetch(`${API_BASE}/api/v1/operations/export`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({ category: activeTab, format, date_range: dateRange }),
            });
            if (res.ok) {
                const data = await res.json();
                setExports((prev) =>
                    prev.map((e) =>
                        e.id === newExport.id
                            ? { ...e, status: "completed", file_url: data.download_url || "#" }
                            : e
                    )
                );
            }
        } catch {
            // silent
        } finally {
            setExporting(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-3 mb-8">
                    <Download className="w-8 h-8 text-purple-400" />
                    <div>
                        <h1 className="text-2xl font-bold">Export Center</h1>
                        <p className="text-gray-200 text-sm">Download your data in any format</p>
                    </div>
                </div>

                {/* Category Tabs */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat.id}
                            onClick={() => setActiveTab(cat.id)}
                            className={`p-4 rounded-xl border text-left transition-all ${activeTab === cat.id
                                    ? "border-purple-500 bg-purple-500/10"
                                    : "border-gray-800 bg-gray-900 hover:border-gray-700"
                                }`}
                        >
                            <cat.icon className={`w-5 h-5 mb-2 ${activeTab === cat.id ? "text-purple-400" : "text-gray-300"}`} />
                            <p className="font-medium text-sm">{cat.label}</p>
                            <p className="text-xs text-gray-300 mt-0.5">{cat.description}</p>
                        </button>
                    ))}
                </div>

                {/* Export Options */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
                    <h3 className="font-medium mb-4">Export Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm text-gray-200 mb-2">Format</label>
                            <div className="flex gap-2">
                                {(["csv", "json", "pdf"] as ExportFormat[]).map((f) => (
                                    <button
                                        key={f}
                                        onClick={() => setFormat(f)}
                                        className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium uppercase transition-colors ${format === f
                                                ? "border-purple-500 bg-purple-500/10 text-purple-300"
                                                : "border-gray-700 bg-gray-800 text-gray-200"
                                            }`}
                                    >
                                        {f}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-200 mb-2">Date Range</label>
                            <select aria-label="Filter or select option"
                                value={dateRange}
                                onChange={(e) => setDateRange(e.target.value)}
                                className="w-full p-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white"
                            >
                                <option value="last_7_days">Last 7 days</option>
                                <option value="last_30_days">Last 30 days</option>
                                <option value="last_90_days">Last 90 days</option>
                                <option value="last_year">Last year</option>
                                <option value="all_time">All time</option>
                            </select>
                        </div>
                        <div className="flex items-end">
                            <button
                                onClick={handleExport}
                                disabled={exporting}
                                className="w-full px-4 py-2.5 bg-purple-600 rounded-lg hover:bg-purple-500 transition-colors disabled:opacity-80 flex items-center justify-center gap-2"
                            >
                                {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                                Export {CATEGORIES.find((c) => c.id === activeTab)?.label}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Export History */}
                {exports.length > 0 && (
                    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-gray-800">
                            <h3 className="font-medium">Recent Exports</h3>
                        </div>
                        <div className="divide-y divide-gray-800">
                            {exports.map((e) => (
                                <div key={e.id} className="flex items-center justify-between p-4">
                                    <div className="flex items-center gap-3">
                                        {e.status === "completed" ? (
                                            <CheckCircle className="w-5 h-5 text-green-400" />
                                        ) : e.status === "processing" ? (
                                            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                                        ) : (
                                            <Clock className="w-5 h-5 text-yellow-400" />
                                        )}
                                        <div>
                                            <p className="text-sm font-medium capitalize">{e.category} Export</p>
                                            <p className="text-xs text-gray-300">
                                                {e.format.toUpperCase()} · {new Date(e.created_at).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                    {e.status === "completed" && e.file_url && (
                                        <a
                                            href={e.file_url}
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 rounded-lg hover:bg-gray-700 text-sm"
                                        >
                                            <Download className="w-3.5 h-3.5" /> Download
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
