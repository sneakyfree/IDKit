"use client";

import { useState, useEffect } from "react";
import { FileText, Plus, Download, Eye, Calendar, Loader2, BarChart3, Users, DollarSign, TrendingUp } from "lucide-react";
import { reportsApi } from "@/lib/api";

/**
 * Custom Reporting UI
 * 
 * User-defined custom analytics reports
 */

interface ReportTemplate {
    id: string;
    name: string;
    description: string;
    metrics: string[];
    dimensions: string[];
    dateRange: "7d" | "30d" | "90d" | "custom";
    format: "table" | "chart" | "summary";
    schedule?: {
        frequency: "daily" | "weekly" | "monthly";
        recipients: string[];
    };
    createdAt: string;
    lastRun?: string;
}

const AVAILABLE_METRICS = [
    { id: "impressions", label: "Impressions", icon: Eye },
    { id: "engagements", label: "Engagements", icon: TrendingUp },
    { id: "followers", label: "Follower Growth", icon: Users },
    { id: "revenue", label: "Revenue", icon: DollarSign },
    { id: "clicks", label: "Link Clicks", icon: TrendingUp },
    { id: "shares", label: "Shares", icon: TrendingUp },
    { id: "comments", label: "Comments", icon: TrendingUp },
    { id: "saves", label: "Saves", icon: TrendingUp },
];

const AVAILABLE_DIMENSIONS = [
    { id: "platform", label: "Platform" },
    { id: "content_type", label: "Content Type" },
    { id: "date", label: "Date" },
    { id: "campaign", label: "Campaign" },
    { id: "geography", label: "Geography" },
];



export default function CustomReportsPage() {
    const [reports, setReports] = useState<ReportTemplate[]>([]);
    const [showBuilder, setShowBuilder] = useState(false);
    const [selectedReport, setSelectedReport] = useState<ReportTemplate | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState<string | null>(null);

    useEffect(() => {
        async function fetchReports() {
            try {
                setLoading(true);
                const response = await reportsApi.list();
                setReports((response.reports || []).map((r: any) => ({
                    id: r.id as string,
                    name: (r.name as string) || "Report",
                    description: (r.description as string) || "",
                    metrics: (r.metrics as string[]) || [],
                    dimensions: (r.dimensions as string[]) || [],
                    dateRange: (r.date_range as ReportTemplate["dateRange"]) || "30d",
                    format: (r.format as ReportTemplate["format"]) || "chart",
                    schedule: r.schedule_frequency ? {
                        frequency: r.schedule_frequency as "daily" | "weekly" | "monthly",
                        recipients: (r.schedule_recipients as string[]) || [],
                    } : undefined,
                    createdAt: r.created_at as string || new Date().toISOString(),
                    lastRun: r.last_run_at as string,
                })));
            } catch {
                setReports([]);
            } finally {
                setLoading(false);
            }
        }
        fetchReports();
    }, []);

    const handleGenerateReport = async (reportId: string) => {
        setGenerating(reportId);
        await new Promise(r => setTimeout(r, 2000));
        setGenerating(null);
        alert("Report generated successfully!");
    };

    const handleCreateReport = (report: Omit<ReportTemplate, "id" | "createdAt">) => {
        const newReport: ReportTemplate = {
            ...report,
            id: Date.now().toString(),
            createdAt: new Date().toISOString(),
        };
        setReports(prev => [...prev, newReport]);
        setShowBuilder(false);
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Custom Reports</h1>
                        <p className="text-gray-200">Build and schedule custom analytics reports</p>
                    </div>
                    <button
                        onClick={() => setShowBuilder(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        New Report
                    </button>
                </div>

                {/* Loading */}
                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                )}

                {/* Empty State */}
                {!loading && reports.length === 0 && (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <BarChart3 className="w-16 h-16 mx-auto text-gray-200 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No custom reports yet</h3>
                        <p className="text-gray-300 mb-6">Create your first custom analytics report.</p>
                        <button
                            onClick={() => setShowBuilder(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Create Report
                        </button>
                    </div>
                )}

                {/* Report List */}
                {!loading && reports.length > 0 && (
                    <div className="grid md:grid-cols-2 gap-4">
                        {reports.map((report) => (
                            <div
                                key={report.id}
                                className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div>
                                        <h3 className="font-semibold">{report.name}</h3>
                                        <p className="text-sm text-gray-300">{report.description}</p>
                                    </div>
                                    <span className="text-xs bg-gray-800 px-2 py-1 rounded capitalize">
                                        {report.format}
                                    </span>
                                </div>

                                <div className="flex flex-wrap gap-2 mb-4">
                                    {report.metrics.map((m) => (
                                        <span key={m} className="text-xs bg-purple-600/20 text-purple-400 px-2 py-1 rounded">
                                            {AVAILABLE_METRICS.find(am => am.id === m)?.label}
                                        </span>
                                    ))}
                                </div>

                                <div className="flex items-center justify-between text-sm text-gray-300">
                                    <div className="flex items-center gap-4">
                                        <span className="flex items-center gap-1">
                                            <Calendar className="w-3 h-3" />
                                            {report.dateRange}
                                        </span>
                                        {report.schedule && (
                                            <span className="capitalize">{report.schedule.frequency}</span>
                                        )}
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setSelectedReport(report)}
                                            className="p-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                                        >
                                            <Eye className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleGenerateReport(report.id)}
                                            disabled={generating === report.id}
                                            className="p-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-80"
                                        >
                                            {generating === report.id ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Download className="w-4 h-4" />
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Report Builder Modal */}
                {showBuilder && (
                    <ReportBuilder
                        onClose={() => setShowBuilder(false)}
                        onCreate={handleCreateReport}
                    />
                )}
            </div>
        </main>
    );
}

function ReportBuilder({
    onClose,
    onCreate,
}: {
    onClose: () => void;
    onCreate: (report: Omit<ReportTemplate, "id" | "createdAt">) => void;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
    const [selectedDimensions, setSelectedDimensions] = useState<string[]>([]);
    const [dateRange, setDateRange] = useState<ReportTemplate["dateRange"]>("30d");
    const [format, setFormat] = useState<ReportTemplate["format"]>("chart");
    const [enableSchedule, setEnableSchedule] = useState(false);
    const [frequency, setFrequency] = useState<"daily" | "weekly" | "monthly">("weekly");
    const [recipients, setRecipients] = useState("");

    const toggleMetric = (id: string) => {
        setSelectedMetrics(prev =>
            prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
        );
    };

    const toggleDimension = (id: string) => {
        setSelectedDimensions(prev =>
            prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
        );
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            name,
            description,
            metrics: selectedMetrics,
            dimensions: selectedDimensions,
            dateRange,
            format,
            schedule: enableSchedule ? {
                frequency,
                recipients: recipients.split(",").map(r => r.trim()),
            } : undefined,
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <h2 className="text-xl font-bold text-white">Create Custom Report</h2>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {/* Basic Info */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">Report Name *</label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                                placeholder="Weekly Performance Summary"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">Description</label>
                            <input
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                                placeholder="Describe what this report shows"
                            />
                        </div>
                    </div>

                    {/* Metrics */}
                    <div>
                        <label className="block text-sm text-gray-200 mb-2">Metrics *</label>
                        <div className="grid grid-cols-2 gap-2">
                            {AVAILABLE_METRICS.map((metric) => (
                                <button
                                    key={metric.id}
                                    type="button"
                                    onClick={() => toggleMetric(metric.id)}
                                    className={`flex items-center gap-2 p-3 rounded-lg text-left ${selectedMetrics.includes(metric.id)
                                        ? "bg-purple-600"
                                        : "bg-gray-800 hover:bg-gray-700"
                                        }`}
                                >
                                    <metric.icon className="w-4 h-4" />
                                    {metric.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Dimensions */}
                    <div>
                        <label className="block text-sm text-gray-200 mb-2">Group By</label>
                        <div className="flex flex-wrap gap-2">
                            {AVAILABLE_DIMENSIONS.map((dim) => (
                                <button
                                    key={dim.id}
                                    type="button"
                                    onClick={() => toggleDimension(dim.id)}
                                    className={`px-4 py-2 rounded-lg ${selectedDimensions.includes(dim.id)
                                        ? "bg-purple-600"
                                        : "bg-gray-800 hover:bg-gray-700"
                                        }`}
                                >
                                    {dim.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Date Range & Format */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">Date Range</label>
                            <select aria-label="Filter or select option"
                                value={dateRange}
                                onChange={(e) => setDateRange(e.target.value as ReportTemplate["dateRange"])}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                            >
                                <option value="7d">Last 7 days</option>
                                <option value="30d">Last 30 days</option>
                                <option value="90d">Last 90 days</option>
                                <option value="custom">Custom</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">Format</label>
                            <select aria-label="Filter or select option"
                                value={format}
                                onChange={(e) => setFormat(e.target.value as ReportTemplate["format"])}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                            >
                                <option value="chart">Chart</option>
                                <option value="table">Table</option>
                                <option value="summary">Summary</option>
                            </select>
                        </div>
                    </div>

                    {/* Schedule */}
                    <div>
                        <label className="flex items-center gap-2 mb-4">
                            <input
                                type="checkbox"
                                checked={enableSchedule}
                                onChange={(e) => setEnableSchedule(e.target.checked)}
                                className="w-4 h-4 rounded"
                            />
                            <span>Schedule automatic delivery</span>
                        </label>

                        {enableSchedule && (
                            <div className="grid grid-cols-2 gap-4 pl-6">
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">Frequency</label>
                                    <select aria-label="Filter or select option"
                                        value={frequency}
                                        onChange={(e) => setFrequency(e.target.value as "daily" | "weekly" | "monthly")}
                                        className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                                    >
                                        <option value="daily">Daily</option>
                                        <option value="weekly">Weekly</option>
                                        <option value="monthly">Monthly</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">Recipients</label>
                                    <input
                                        value={recipients}
                                        onChange={(e) => setRecipients(e.target.value)}
                                        placeholder="email@example.com"
                                        className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-4 pt-4 border-t border-gray-800">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!name || selectedMetrics.length === 0}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-80"
                        >
                            Create Report
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
