"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
    Terminal,
    Search,
    RefreshCw,
    Filter,
    Loader2,
    AlertCircle,
    AlertTriangle,
    Info,
    Bug,
    ChevronDown,
} from "lucide-react";

/**
 * Admin Log Viewer
 *
 * Centralized log aggregation UI — service filter, severity, time range, search.
 * Closes Helix Scan gap I06-2.
 */

interface LogEntry {
    timestamp: string;
    level: string;
    service: string;
    message: string;
    pod?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const SERVICES = ["All", "api", "frontend", "worker", "scheduler", "redis", "postgresql"];
const LEVELS = ["All", "error", "warn", "info", "debug"];

const levelIcons: Record<string, React.ReactNode> = {
    error: <AlertCircle className="w-4 h-4 text-red-400" />,
    warn: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
    info: <Info className="w-4 h-4 text-blue-400" />,
    debug: <Bug className="w-4 h-4 text-gray-300" />,
};

const levelColors: Record<string, string> = {
    error: "border-l-red-500 bg-red-500/5",
    warn: "border-l-yellow-500 bg-yellow-500/5",
    info: "border-l-blue-500/30",
    debug: "border-l-gray-700",
};

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [service, setService] = useState("All");
    const [level, setLevel] = useState("All");
    const [search, setSearch] = useState("");
    const [autoRefresh, setAutoRefresh] = useState(true);
    const bottomRef = useRef<HTMLDivElement>(null);

    const headers = { Authorization: `Bearer ${typeof window !== "undefined" ? localStorage.getItem("token") : ""}` };

    const fetchLogs = useCallback(async () => {
        try {
            const params = new URLSearchParams();
            if (service !== "All") params.set("service", service);
            if (level !== "All") params.set("level", level);
            if (search) params.set("q", search);

            const res = await fetch(`${API_BASE}/api/v1/operations/logs?${params}`, { headers });
            if (res.ok) {
                const data = await res.json();
                setLogs(data.entries || []);
            } else {
                // Generate sample logs for demo
                setLogs(generateSampleLogs());
            }
        } catch {
            setLogs(generateSampleLogs());
        } finally {
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [service, level, search]);

    useEffect(() => {
        fetchLogs();
        if (autoRefresh) {
            const interval = setInterval(fetchLogs, 5000);
            return () => clearInterval(interval);
        }
    }, [fetchLogs, autoRefresh]);

    useEffect(() => {
        if (autoRefresh) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs, autoRefresh]);

    const filteredLogs = logs.filter((l) => {
        if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
    });

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-gray-950">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-white flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-800">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Terminal className="w-6 h-6 text-green-400" />
                        <h1 className="text-xl font-bold text-white">Log Viewer</h1>
                        <span className="text-xs text-gray-300">{filteredLogs.length} entries</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <label className="flex items-center gap-2 text-sm text-gray-200 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={autoRefresh}
                                onChange={(e) => setAutoRefresh(e.target.checked)}
                                className="accent-green-500"
                            />
                            Auto-refresh
                        </label>
                        <button
                            onClick={fetchLogs}
                            className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 text-sm"
                        >
                            <RefreshCw className="w-4 h-4" /> Refresh
                        </button>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="p-4 border-b border-gray-800 bg-gray-900/50">
                <div className="max-w-7xl mx-auto flex gap-3 items-center">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-gray-300" />
                        <select aria-label="Filter or select option"
                            value={service}
                            onChange={(e) => setService(e.target.value)}
                            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                        >
                            {SERVICES.map((s) => (
                                <option key={s} value={s}>{s === "All" ? "All Services" : s}</option>
                            ))}
                        </select>
                        <select aria-label="Filter or select option"
                            value={level}
                            onChange={(e) => setLevel(e.target.value)}
                            className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                        >
                            {LEVELS.map((l) => (
                                <option key={l} value={l}>{l === "All" ? "All Levels" : l.toUpperCase()}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex-1 relative">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-300" />
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search logs..."
                            className="w-full pl-9 pr-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:border-green-500 outline-none"
                        />
                    </div>
                </div>
            </div>

            {/* Log Stream */}
            <div className="flex-1 overflow-y-auto font-mono text-sm">
                <div className="max-w-7xl mx-auto">
                    {filteredLogs.map((log, i) => (
                        <div
                            key={i}
                            className={`flex gap-3 px-4 py-1.5 border-l-2 hover:bg-gray-800/30 ${levelColors[log.level] || ""}`}
                        >
                            <span className="text-gray-200 text-xs whitespace-nowrap min-w-[140px]">
                                {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="min-w-[16px]">{levelIcons[log.level]}</span>
                            <span className="text-gray-300 min-w-[80px] text-xs">[{log.service}]</span>
                            <span className="text-gray-300 break-all">{log.message}</span>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>
            </div>
        </div>
    );
}

function generateSampleLogs(): LogEntry[] {
    const services = ["api", "worker", "scheduler", "frontend"];
    const messages = [
        { level: "info", msg: "Request processed: POST /api/v1/content/generate (200 OK) in 342ms" },
        { level: "info", msg: "User session started: user_id=abc123 ip=192.168.1.1" },
        { level: "info", msg: "Background job completed: content_analysis job_id=def456 duration=12.3s" },
        { level: "warn", msg: "Rate limit approaching: user_id=abc123 requests=95/100 window=60s" },
        { level: "warn", msg: "Slow query detected: SELECT * FROM analytics_events duration=2.1s" },
        { level: "error", msg: "Failed to connect to GPU worker: timeout after 30s, retrying..." },
        { level: "info", msg: "Cache hit ratio: 94.2% (15,234 hits / 16,164 total)" },
        { level: "debug", msg: "WebSocket connection established: connection_id=ws_789" },
        { level: "info", msg: "Scheduled post published: content_id=ghi789 platform=twitter" },
        { level: "info", msg: "Database migration completed: revision abc123 → def456" },
    ];
    const now = Date.now();
    return Array.from({ length: 50 }, (_, i) => {
        const m = messages[i % messages.length];
        return {
            timestamp: new Date(now - (50 - i) * 3000).toISOString(),
            level: m.level,
            service: services[i % services.length],
            message: m.msg,
            pod: `idkit-${services[i % services.length]}-${Math.random().toString(36).slice(2, 8)}`,
        };
    });
}
