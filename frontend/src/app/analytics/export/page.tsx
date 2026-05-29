"use client";

import { useState } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

type ExportFormat = "csv" | "json";
type TimeRange = "7d" | "30d" | "90d" | "365d";

export default function AnalyticsExportPage() {
    const [format, setFormat] = useState<ExportFormat>("csv");
    const [timeRange, setTimeRange] = useState<TimeRange>("30d");
    const [includeTimeSeries, setIncludeTimeSeries] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const getDateRange = () => {
        const end = new Date();
        const start = new Date();
        const days = parseInt(timeRange.replace("d", ""));
        start.setDate(start.getDate() - days);
        return { start, end };
    };

    const handleExport = async () => {
        setIsExporting(true);
        setError(null);
        setSuccess(false);

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Not authenticated");

            const { start, end } = getDateRange();
            const params = new URLSearchParams({
                format,
                start_date: start.toISOString(),
                end_date: end.toISOString(),
                include_timeseries: includeTimeSeries.toString(),
            });

            const response = await fetch(
                `${API_URL}/api/v1/analytics/export?${params}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (!response.ok) {
                throw new Error("Export failed");
            }

            const data = await response.json();

            // Download the file
            let blob: Blob;
            let filename = data.filename;

            if (format === "csv") {
                // Decode base64
                const csvContent = atob(data.data);
                blob = new Blob([csvContent], { type: "text/csv" });
            } else {
                blob = new Blob([data.data], { type: "application/json" });
            }

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            setSuccess(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Export failed");
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <main className="min-h-screen bg-black pb-20">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
                <div className="flex items-center gap-3 px-4 py-3">
                    <Link href="/analytics" className="text-gray-200 hover:text-white" aria-label="Back">
                        <BackIcon className="w-6 h-6" />
                    </Link>
                    <h1 className="text-xl font-bold text-white">Export Analytics</h1>
                </div>
            </header>

            <div className="p-4 space-y-6">
                {/* Format Selection */}
                <section className="bg-gray-900 rounded-2xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Export Format</h2>
                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={() => setFormat("csv")}
                            className={`p-4 rounded-xl border-2 transition-colors ${format === "csv"
                                    ? "border-purple-500 bg-purple-500/10"
                                    : "border-gray-700 hover:border-gray-600"
                                }`}
                        >
                            <CSVIcon className="w-8 h-8 mx-auto mb-2 text-green-400" />
                            <p className="font-medium">CSV</p>
                            <p className="text-xs text-gray-300">Spreadsheet format</p>
                        </button>
                        <button
                            onClick={() => setFormat("json")}
                            className={`p-4 rounded-xl border-2 transition-colors ${format === "json"
                                    ? "border-purple-500 bg-purple-500/10"
                                    : "border-gray-700 hover:border-gray-600"
                                }`}
                        >
                            <JSONIcon className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                            <p className="font-medium">JSON</p>
                            <p className="text-xs text-gray-300">Developer format</p>
                        </button>
                    </div>
                </section>

                {/* Time Range */}
                <section className="bg-gray-900 rounded-2xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Time Period</h2>
                    <div className="grid grid-cols-4 gap-2">
                        {(["7d", "30d", "90d", "365d"] as TimeRange[]).map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`py-2 px-3 rounded-xl text-sm font-medium transition-colors ${timeRange === range
                                        ? "bg-purple-600 text-white"
                                        : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                                    }`}
                            >
                                {range === "365d" ? "1 Year" : range.replace("d", " Days")}
                            </button>
                        ))}
                    </div>
                </section>

                {/* Options */}
                <section className="bg-gray-900 rounded-2xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Export Options</h2>
                    <div className="space-y-4">
                        <label className="flex items-center justify-between">
                            <div>
                                <p className="font-medium">Overview Metrics</p>
                                <p className="text-sm text-gray-300">
                                    Total impressions, engagement, followers
                                </p>
                            </div>
                            <div className="w-10 h-6 bg-purple-600 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full" />
                            </div>
                        </label>
                        <label className="flex items-center justify-between">
                            <div>
                                <p className="font-medium">Platform Breakdown</p>
                                <p className="text-sm text-gray-300">Per-platform statistics</p>
                            </div>
                            <div className="w-10 h-6 bg-purple-600 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full" />
                            </div>
                        </label>
                        <label
                            className="flex items-center justify-between cursor-pointer"
                            onClick={() => setIncludeTimeSeries(!includeTimeSeries)}
                        >
                            <div>
                                <p className="font-medium">Daily Time Series</p>
                                <p className="text-sm text-gray-300">
                                    Day-by-day engagement data
                                </p>
                            </div>
                            <div
                                className={`w-10 h-6 rounded-full flex items-center px-1 transition-colors ${includeTimeSeries ? "bg-purple-600 justify-end" : "bg-gray-700 justify-start"
                                    }`}
                            >
                                <div className="w-4 h-4 bg-white rounded-full" />
                            </div>
                        </label>
                    </div>
                </section>

                {/* Preview */}
                <section className="bg-gray-900 rounded-2xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Export Preview</h2>
                    <div className="bg-gray-800 rounded-xl p-4 text-sm text-gray-200 font-mono">
                        <p>📄 analytics_{getDateRange().start.toISOString().split("T")[0]}.{format}</p>
                        <p className="mt-2 text-xs">
                            Includes: Overview metrics, Platform breakdown
                            {includeTimeSeries ? ", Daily time series" : ""}
                        </p>
                    </div>
                </section>

                {/* Error/Success Messages */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 text-green-400">
                        ✓ Export downloaded successfully!
                    </div>
                )}

                {/* Export Button */}
                <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-80 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-2"
                >
                    {isExporting ? (
                        <>
                            <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                            Exporting...
                        </>
                    ) : (
                        <>
                            <DownloadIcon className="w-5 h-5" />
                            Download Export
                        </>
                    )}
                </button>
            </div>

            <BottomNav />
        </main>
    );
}

// Icons
function BackIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
    );
}

function DownloadIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
    );
}

function CSVIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    );
}

function JSONIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
    );
}
