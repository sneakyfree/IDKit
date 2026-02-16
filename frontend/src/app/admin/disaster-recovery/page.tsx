"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Shield,
    RefreshCw,
    Server,
    Database,
    HardDrive,
    Cpu,
    Globe,
    CheckCircle,
    AlertTriangle,
    XCircle,
    Loader2,
    PlayCircle,
    BookOpen,
    ChevronDown,
    ChevronRight,
} from "lucide-react";

/**
 * Disaster Recovery Dashboard
 *
 * System health monitoring, replica status, runbook, and failover testing.
 * Closes Helix Scan gap D09.
 */

interface ComponentStatus {
    status: string;
    [key: string]: unknown;
}

interface DRStatus {
    overall_status: string;
    last_checked: string;
    rpo_minutes: number;
    rto_minutes: number;
    components: Record<string, ComponentStatus>;
}

interface Replica {
    id: string;
    type: string;
    region: string;
    status: string;
    replication_lag_seconds: number;
    last_heartbeat: string;
}

interface RunbookProcedure {
    name: string;
    trigger: string;
    steps: {
        order: number;
        title: string;
        description: string;
        automated: boolean;
        estimated_minutes: number;
        responsible_team: string;
    }[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const componentIcons: Record<string, React.ReactNode> = {
    database: <Database className="w-5 h-5" />,
    redis: <Server className="w-5 h-5" />,
    s3_storage: <HardDrive className="w-5 h-5" />,
    gpu_workers: <Cpu className="w-5 h-5" />,
    api_servers: <Globe className="w-5 h-5" />,
};

const statusColors: Record<string, string> = {
    healthy: "text-green-400 bg-green-400/10 border-green-500/30",
    degraded: "text-yellow-400 bg-yellow-400/10 border-yellow-500/30",
    down: "text-red-400 bg-red-400/10 border-red-500/30",
};

export default function DisasterRecoveryPage() {
    const [drStatus, setDrStatus] = useState<DRStatus | null>(null);
    const [replicas, setReplicas] = useState<Replica[]>([]);
    const [runbook, setRunbook] = useState<RunbookProcedure[]>([]);
    const [loading, setLoading] = useState(true);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<Record<string, unknown> | null>(null);
    const [expandedRunbook, setExpandedRunbook] = useState<number | null>(null);
    const [activeTab, setActiveTab] = useState<"overview" | "replicas" | "runbook">("overview");

    const headers = { Authorization: `Bearer ${localStorage.getItem("token")}` };

    const fetchAll = useCallback(async () => {
        try {
            const [statusRes, replicaRes, runbookRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/dr/status`, { headers }),
                fetch(`${API_BASE}/api/v1/dr/replicas`, { headers }),
                fetch(`${API_BASE}/api/v1/dr/runbook`, { headers }),
            ]);
            if (statusRes.ok) setDrStatus(await statusRes.json());
            if (replicaRes.ok) {
                const data = await replicaRes.json();
                setReplicas(data.replicas || []);
            }
            if (runbookRes.ok) {
                const data = await runbookRes.json();
                setRunbook(data.procedures || []);
            }
        } catch {
            // silent
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        fetchAll();
    }, [fetchAll]);

    const handleTestFailover = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const res = await fetch(`${API_BASE}/api/v1/dr/failover/test`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({ dry_run: true, components: ["database", "cache", "storage"] }),
            });
            if (res.ok) setTestResult(await res.json());
        } catch {
            // silent
        } finally {
            setTesting(false);
        }
    };

    const StatusBadge = ({ status }: { status: string }) => (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${statusColors[status] || statusColors.degraded}`}>
            {status === "healthy" ? <CheckCircle className="w-3 h-3" /> :
                status === "down" ? <XCircle className="w-3 h-3" /> :
                    <AlertTriangle className="w-3 h-3" />}
            {status}
        </span>
    );

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
                        <Shield className="w-8 h-8 text-green-400" />
                        <div>
                            <h1 className="text-2xl font-bold">Disaster Recovery</h1>
                            <p className="text-gray-400 text-sm">
                                RPO: {drStatus?.rpo_minutes}min · RTO: {drStatus?.rto_minutes}min
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchAll}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" /> Refresh
                        </button>
                        <button
                            onClick={handleTestFailover}
                            disabled={testing}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 rounded-lg hover:bg-green-500 transition-colors disabled:opacity-50"
                        >
                            {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />}
                            Test Failover
                        </button>
                    </div>
                </div>

                {/* Overall Status Banner */}
                {drStatus && (
                    <div className={`mb-6 p-4 rounded-xl border ${statusColors[drStatus.overall_status]}`}>
                        <div className="flex items-center gap-3">
                            <CheckCircle className="w-6 h-6" />
                            <div>
                                <p className="font-semibold capitalize">System: {drStatus.overall_status}</p>
                                <p className="text-sm opacity-75">
                                    Last checked: {new Date(drStatus.last_checked).toLocaleString()}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Test Result Banner */}
                {testResult && (
                    <div className="mb-6 p-4 rounded-xl border border-blue-500/30 bg-blue-400/10">
                        <div className="flex items-center gap-3 mb-2">
                            <CheckCircle className="w-5 h-5 text-blue-400" />
                            <p className="font-semibold text-blue-300">
                                Failover Test: {(testResult as Record<string, string>).overall_result?.toUpperCase()}
                            </p>
                        </div>
                        <p className="text-sm text-blue-200/70">
                            Dry run completed. Estimated RTO: {(testResult as Record<string, number>).estimated_rto_seconds?.toFixed(1)}s
                        </p>
                    </div>
                )}

                {/* Tabs */}
                <div className="flex gap-1 bg-gray-900 rounded-lg p-1 mb-6">
                    {(["overview", "replicas", "runbook"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors capitalize ${activeTab === tab ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Overview Tab */}
                {activeTab === "overview" && drStatus && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {Object.entries(drStatus.components).map(([name, comp]) => (
                            <div key={name} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2 text-gray-300">
                                        {componentIcons[name] || <Server className="w-5 h-5" />}
                                        <span className="font-medium capitalize">{name.replace(/_/g, " ")}</span>
                                    </div>
                                    <StatusBadge status={comp.status} />
                                </div>
                                <div className="space-y-1 text-sm text-gray-500">
                                    {Object.entries(comp)
                                        .filter(([k]) => k !== "status")
                                        .slice(0, 4)
                                        .map(([k, v]) => (
                                            <div key={k} className="flex justify-between">
                                                <span className="capitalize">{k.replace(/_/g, " ")}</span>
                                                <span className="text-gray-300">
                                                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                                                </span>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Replicas Tab */}
                {activeTab === "replicas" && (
                    <div className="space-y-4">
                        {replicas.map((r) => (
                            <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <Database className="w-5 h-5 text-purple-400" />
                                        <div>
                                            <p className="font-medium">{r.id}</p>
                                            <p className="text-sm text-gray-500">{r.type} · {r.region}</p>
                                        </div>
                                    </div>
                                    <StatusBadge status={r.status} />
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <p className="text-gray-500">Replication Lag</p>
                                        <p className={`font-mono ${r.replication_lag_seconds < 1 ? "text-green-400" : "text-yellow-400"}`}>
                                            {r.replication_lag_seconds.toFixed(1)}s
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-gray-500">Last Heartbeat</p>
                                        <p className="text-gray-300">{new Date(r.last_heartbeat).toLocaleTimeString()}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Runbook Tab */}
                {activeTab === "runbook" && (
                    <div className="space-y-4">
                        {runbook.map((proc, idx) => (
                            <div key={idx} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                                <button
                                    onClick={() => setExpandedRunbook(expandedRunbook === idx ? null : idx)}
                                    className="w-full flex items-center justify-between p-5 hover:bg-gray-800/50 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <BookOpen className="w-5 h-5 text-purple-400" />
                                        <div className="text-left">
                                            <p className="font-medium">{proc.name}</p>
                                            <p className="text-sm text-gray-500">Trigger: {proc.trigger}</p>
                                        </div>
                                    </div>
                                    {expandedRunbook === idx ? (
                                        <ChevronDown className="w-5 h-5 text-gray-500" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-gray-500" />
                                    )}
                                </button>
                                {expandedRunbook === idx && (
                                    <div className="border-t border-gray-800 p-5">
                                        <div className="space-y-3">
                                            {proc.steps.map((step) => (
                                                <div key={step.order} className="flex gap-4 items-start">
                                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm font-medium text-purple-400">
                                                        {step.order}
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2">
                                                            <p className="font-medium text-sm">{step.title}</p>
                                                            {step.automated && (
                                                                <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                                                                    Auto
                                                                </span>
                                                            )}
                                                        </div>
                                                        <p className="text-sm text-gray-500 mt-0.5">{step.description}</p>
                                                        <p className="text-xs text-gray-600 mt-1">
                                                            ~{step.estimated_minutes}min · {step.responsible_team}
                                                        </p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
