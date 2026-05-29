"use client";

import { useState, useEffect } from "react";
import { Download, FileText, Database, Users, Calendar, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { apiRequest } from "@/lib/api";

/**
 * TASK 5.1.5: Admin Data Export UI
 * 
 * Export system data for administrators
 */

interface ExportJob {
    id: string;
    type: ExportType;
    status: "pending" | "processing" | "completed" | "failed";
    format: "csv" | "json" | "xlsx";
    createdAt: string;
    completedAt?: string;
    downloadUrl?: string;
    size?: string;
    error?: string;
}

type ExportType = "users" | "content" | "analytics" | "payments" | "audit_logs";

const EXPORT_TYPES: { type: ExportType; label: string; description: string; icon: React.ReactNode }[] = [
    { type: "users", label: "Users", description: "User accounts, profiles, and settings", icon: <Users className="w-5 h-5" /> },
    { type: "content", label: "Content", description: "All content, posts, and media metadata", icon: <FileText className="w-5 h-5" /> },
    { type: "analytics", label: "Analytics", description: "Platform analytics and metrics", icon: <Database className="w-5 h-5" /> },
    { type: "payments", label: "Payments", description: "Transaction history and billing", icon: <Database className="w-5 h-5" /> },
    { type: "audit_logs", label: "Audit Logs", description: "System activity and security events", icon: <Calendar className="w-5 h-5" /> },
];


export default function AdminExportPage() {
    const [jobs, setJobs] = useState<ExportJob[]>([]);
    const [selectedType, setSelectedType] = useState<ExportType | null>(null);
    const [format, setFormat] = useState<"csv" | "json" | "xlsx">("csv");
    const [dateRange, setDateRange] = useState({ start: "", end: "" });
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loadingJobs, setLoadingJobs] = useState(true);

    useEffect(() => {
        async function fetchJobs() {
            try {
                const response = await apiRequest<ExportJob[]>("/api/v1/admin/exports");
                setJobs(Array.isArray(response) ? response : []);
            } catch {
                setJobs([]);
            } finally {
                setLoadingJobs(false);
            }
        }
        fetchJobs();
    }, []);

    const handleStartExport = async () => {
        if (!selectedType) return;

        setProcessing(true);
        setError(null);

        try {
            // Create new job
            const newJob: ExportJob = {
                id: Date.now().toString(),
                type: selectedType,
                status: "processing",
                format,
                createdAt: new Date().toISOString(),
            };

            setJobs(prev => [newJob, ...prev]);

            // Simulate processing
            await new Promise(resolve => setTimeout(resolve, 3000));

            // Update to completed
            setJobs(prev => prev.map(j =>
                j.id === newJob.id
                    ? {
                        ...j,
                        status: "completed" as const,
                        completedAt: new Date().toISOString(),
                        downloadUrl: "#",
                        size: `${(Math.random() * 10 + 1).toFixed(1)} MB`,
                    }
                    : j
            ));

            setSelectedType(null);
        } catch (err) {
            setError("Export failed. Please try again.");
        } finally {
            setProcessing(false);
        }
    };

    const handleRetry = async (jobId: string) => {
        const job = jobs.find(j => j.id === jobId);
        if (!job) return;

        setJobs(prev => prev.map(j =>
            j.id === jobId ? { ...j, status: "processing" as const, error: undefined } : j
        ));

        // Simulate retry
        await new Promise(resolve => setTimeout(resolve, 2000));

        setJobs(prev => prev.map(j =>
            j.id === jobId
                ? {
                    ...j,
                    status: "completed" as const,
                    completedAt: new Date().toISOString(),
                    downloadUrl: "#",
                    size: `${(Math.random() * 10 + 1).toFixed(1)} MB`,
                }
                : j
        ));
    };

    const getStatusIcon = (status: ExportJob["status"]) => {
        switch (status) {
            case "completed": return <CheckCircle className="w-5 h-5 text-green-400" />;
            case "failed": return <AlertCircle className="w-5 h-5 text-red-400" />;
            case "processing": return <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />;
            default: return <Loader2 className="w-5 h-5 text-gray-200" />;
        }
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold">Data Export</h1>
                    <p className="text-gray-200">Export platform data for analysis or backup</p>
                </div>

                {/* Admin Notice */}
                <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-xl p-4 mb-6">
                    <div className="flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-400" />
                        <div>
                            <p className="font-medium">Administrator Access</p>
                            <p className="text-sm text-gray-200">Exports may contain sensitive data. Handle with care.</p>
                        </div>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-6">
                        <p className="text-red-300">{error}</p>
                    </div>
                )}

                {/* New Export */}
                <div className="bg-gray-900 rounded-2xl p-6 mb-8">
                    <h2 className="text-lg font-semibold mb-4">Create New Export</h2>

                    {/* Data Type Selection */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                        {EXPORT_TYPES.map(({ type, label, description, icon }) => (
                            <button
                                key={type}
                                onClick={() => setSelectedType(type)}
                                className={`p-4 rounded-xl text-left transition-colors ${selectedType === type
                                    ? "bg-purple-600 ring-2 ring-purple-400"
                                    : "bg-gray-800 hover:bg-gray-700"
                                    }`}
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    {icon}
                                    <span className="font-medium">{label}</span>
                                </div>
                                <p className="text-xs text-gray-200">{description}</p>
                            </button>
                        ))}
                    </div>

                    {selectedType && (
                        <>
                            {/* Format Selection */}
                            <div className="mb-6">
                                <label className="block text-sm text-gray-200 mb-2">Export Format</label>
                                <div className="flex gap-3">
                                    {(["csv", "json", "xlsx"] as const).map((f) => (
                                        <button
                                            key={f}
                                            onClick={() => setFormat(f)}
                                            className={`px-4 py-2 rounded-lg uppercase text-sm ${format === f ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                                }`}
                                        >
                                            {f}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Date Range */}
                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">Start Date (optional)</label>
                                    <input
                                        type="date"
                                        value={dateRange.start}
                                        onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                                        className="w-full px-4 py-2 bg-gray-800 rounded-lg border border-gray-700"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">End Date (optional)</label>
                                    <input
                                        type="date"
                                        value={dateRange.end}
                                        onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                                        className="w-full px-4 py-2 bg-gray-800 rounded-lg border border-gray-700"
                                    />
                                </div>
                            </div>

                            {/* Start Button */}
                            <button
                                onClick={handleStartExport}
                                disabled={processing}
                                className="w-full py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-80 flex items-center justify-center gap-2"
                            >
                                {processing ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        <Download className="w-5 h-5" />
                                        Start Export
                                    </>
                                )}
                            </button>
                        </>
                    )}
                </div>

                {/* Export History */}
                <div>
                    <h2 className="text-lg font-semibold mb-4">Export History</h2>

                    {jobs.length === 0 ? (
                        <div className="bg-gray-900 rounded-xl p-8 text-center">
                            <FileText className="w-12 h-12 mx-auto text-gray-200 mb-3" />
                            <p className="text-gray-300">No exports yet</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {jobs.map((job) => (
                                <div key={job.id} className="bg-gray-900 rounded-xl p-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            {getStatusIcon(job.status)}
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium capitalize">{job.type.replace("_", " ")}</span>
                                                    <span className="text-xs bg-gray-800 px-2 py-0.5 rounded uppercase">{job.format}</span>
                                                </div>
                                                <p className="text-sm text-gray-300">
                                                    {new Date(job.createdAt).toLocaleString()}
                                                    {job.size && ` · ${job.size}`}
                                                </p>
                                                {job.error && (
                                                    <p className="text-sm text-red-400 mt-1">{job.error}</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            {job.status === "completed" && job.downloadUrl && (
                                                <a
                                                    href={job.downloadUrl}
                                                    className="flex items-center gap-2 px-4 py-2 bg-green-600 rounded-lg hover:bg-green-700 text-sm"
                                                >
                                                    <Download className="w-4 h-4" />
                                                    Download
                                                </a>
                                            )}
                                            {job.status === "failed" && (
                                                <button
                                                    onClick={() => handleRetry(job.id)}
                                                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 text-sm"
                                                >
                                                    Retry
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}
