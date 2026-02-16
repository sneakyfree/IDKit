"use client";

import { useState, useRef } from "react";
import {
    Layers,
    Upload,
    Play,
    Pause,
    RotateCcw,
    Loader2,
    CheckCircle,
    XCircle,
    AlertCircle,
    Trash2,
    Plus,
} from "lucide-react";

/**
 * Bulk Content Generator
 *
 * Multi-item content queue with progress, pause/resume, retry, and CSV import.
 * Closes Helix Scan gap G05-1.
 */

interface QueueItem {
    id: string;
    prompt: string;
    platform: string;
    status: "pending" | "generating" | "completed" | "failed";
    progress: number;
    result?: string;
    error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const PLATFORMS = ["twitter", "instagram", "tiktok", "youtube", "linkedin"];

export default function BulkGenerator() {
    const [queue, setQueue] = useState<QueueItem[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [newPrompt, setNewPrompt] = useState("");
    const [newPlatform, setNewPlatform] = useState("twitter");
    const fileInputRef = useRef<HTMLInputElement>(null);
    const abortRef = useRef(false);

    const addItem = () => {
        if (!newPrompt.trim()) return;
        setQueue((prev) => [
            ...prev,
            {
                id: Math.random().toString(36).slice(2),
                prompt: newPrompt,
                platform: newPlatform,
                status: "pending",
                progress: 0,
            },
        ]);
        setNewPrompt("");
    };

    const handleCSVImport = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            const text = ev.target?.result as string;
            const lines = text.split("\n").filter((l) => l.trim());
            // Skip header if present
            const start = lines[0]?.toLowerCase().includes("prompt") ? 1 : 0;
            const items: QueueItem[] = lines.slice(start).map((line) => {
                const parts = line.split(",");
                return {
                    id: Math.random().toString(36).slice(2),
                    prompt: parts[0]?.trim() || "",
                    platform: parts[1]?.trim() || "twitter",
                    status: "pending" as const,
                    progress: 0,
                };
            });
            setQueue((prev) => [...prev, ...items.filter((i) => i.prompt)]);
        };
        reader.readAsText(file);
        e.target.value = "";
    };

    const processQueue = async () => {
        setIsRunning(true);
        abortRef.current = false;
        const headers = {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
        };

        for (let i = 0; i < queue.length; i++) {
            if (abortRef.current) break;
            if (queue[i].status === "completed") continue;

            setQueue((prev) =>
                prev.map((item, idx) => (idx === i ? { ...item, status: "generating", progress: 30 } : item))
            );

            try {
                const res = await fetch(`${API_BASE}/api/v1/content/generate`, {
                    method: "POST",
                    headers,
                    body: JSON.stringify({ prompt: queue[i].prompt, platform: queue[i].platform }),
                });

                setQueue((prev) =>
                    prev.map((item, idx) => (idx === i ? { ...item, progress: 70 } : item))
                );

                if (res.ok) {
                    const data = await res.json();
                    setQueue((prev) =>
                        prev.map((item, idx) =>
                            idx === i ? { ...item, status: "completed", progress: 100, result: data.content || "Generated" } : item
                        )
                    );
                } else {
                    throw new Error(`HTTP ${res.status}`);
                }
            } catch (err: any) {
                setQueue((prev) =>
                    prev.map((item, idx) =>
                        idx === i ? { ...item, status: "failed", progress: 0, error: err.message } : item
                    )
                );
            }

            // Small delay between items
            await new Promise((r) => setTimeout(r, 500));
        }
        setIsRunning(false);
    };

    const pauseQueue = () => {
        abortRef.current = true;
        setIsRunning(false);
    };

    const retryFailed = () => {
        setQueue((prev) =>
            prev.map((item) => (item.status === "failed" ? { ...item, status: "pending", progress: 0, error: undefined } : item))
        );
    };

    const removeItem = (id: string) => {
        setQueue((prev) => prev.filter((item) => item.id !== id));
    };

    const clearCompleted = () => {
        setQueue((prev) => prev.filter((item) => item.status !== "completed"));
    };

    const stats = {
        total: queue.length,
        completed: queue.filter((i) => i.status === "completed").length,
        failed: queue.filter((i) => i.status === "failed").length,
        pending: queue.filter((i) => i.status === "pending").length,
    };

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            {/* Header */}
            <div className="p-5 border-b border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <Layers className="w-6 h-6 text-purple-400" />
                        <div>
                            <h2 className="font-bold text-lg">Bulk Generator</h2>
                            <p className="text-xs text-gray-500">{stats.completed}/{stats.total} completed</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".csv"
                            onChange={handleCSVImport}
                            className="hidden"
                        />
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm hover:border-gray-600"
                        >
                            <Upload className="w-4 h-4" /> Import CSV
                        </button>
                        {stats.completed > 0 && (
                            <button
                                onClick={clearCompleted}
                                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm hover:border-gray-600"
                            >
                                Clear Done
                            </button>
                        )}
                    </div>
                </div>

                {/* Add Item */}
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={newPrompt}
                        onChange={(e) => setNewPrompt(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && addItem()}
                        placeholder="Enter content prompt..."
                        className="flex-1 p-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:border-purple-500 outline-none"
                    />
                    <select
                        value={newPlatform}
                        onChange={(e) => setNewPlatform(e.target.value)}
                        className="px-3 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                    >
                        {PLATFORMS.map((p) => (
                            <option key={p} value={p}>{p}</option>
                        ))}
                    </select>
                    <button
                        onClick={addItem}
                        disabled={!newPrompt.trim()}
                        className="px-3 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50"
                    >
                        <Plus className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Queue */}
            <div className="max-h-96 overflow-y-auto divide-y divide-gray-800">
                {queue.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 p-4">
                        {/* Status Icon */}
                        {item.status === "completed" ? (
                            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                        ) : item.status === "failed" ? (
                            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        ) : item.status === "generating" ? (
                            <Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
                        ) : (
                            <AlertCircle className="w-5 h-5 text-gray-500 flex-shrink-0" />
                        )}

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm truncate">{item.prompt}</p>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-gray-500 capitalize">{item.platform}</span>
                                {item.error && <span className="text-xs text-red-400">{item.error}</span>}
                            </div>
                            {item.status === "generating" && (
                                <div className="h-1 bg-gray-800 rounded mt-1.5 overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500 rounded transition-all duration-500"
                                        style={{ width: `${item.progress}%` }}
                                    />
                                </div>
                            )}
                        </div>

                        {/* Remove */}
                        <button
                            onClick={() => removeItem(item.id)}
                            className="p-1.5 hover:bg-gray-800 rounded text-gray-600 hover:text-gray-400"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                ))}

                {queue.length === 0 && (
                    <div className="p-8 text-center text-gray-600 text-sm">
                        <Layers className="w-8 h-8 mx-auto mb-2 opacity-30" />
                        Add prompts or import a CSV to start bulk generation
                    </div>
                )}
            </div>

            {/* Actions */}
            {queue.length > 0 && (
                <div className="p-4 border-t border-gray-800 flex gap-2">
                    {isRunning ? (
                        <button
                            onClick={pauseQueue}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-yellow-600 rounded-lg hover:bg-yellow-500"
                        >
                            <Pause className="w-4 h-4" /> Pause
                        </button>
                    ) : (
                        <button
                            onClick={processQueue}
                            disabled={stats.pending === 0 && stats.failed === 0}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-50"
                        >
                            <Play className="w-4 h-4" /> {stats.failed > 0 ? "Resume" : "Generate All"}
                        </button>
                    )}
                    {stats.failed > 0 && (
                        <button
                            onClick={retryFailed}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 text-sm"
                        >
                            <RotateCcw className="w-4 h-4" /> Retry Failed ({stats.failed})
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
