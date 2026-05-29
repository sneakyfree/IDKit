"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Database,
    Plus,
    RefreshCw,
    Trash2,
    Clock,
    CheckCircle,
    AlertCircle,
    Loader2,
    HardDrive,
    RotateCcw,
} from "lucide-react";

/**
 * Backup Management Admin UI
 *
 * Self-service backup creation, monitoring, and restoration.
 * Closes Helix Scan gap D08.
 */

interface Backup {
    id: string;
    name: string;
    backup_type: string;
    status: "pending" | "in_progress" | "completed" | "failed";
    size_bytes: number | null;
    created_at: string;
    completed_at: string | null;
    storage_path: string | null;
    include_media: boolean;
    description: string | null;
    created_by: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function BackupsPage() {
    const [backups, setBackups] = useState<Backup[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [showCreate, setShowCreate] = useState(false);
    const [restoreTarget, setRestoreTarget] = useState<Backup | null>(null);

    // Form state
    const [backupName, setBackupName] = useState("");
    const [backupType, setBackupType] = useState("full");
    const [includeMedia, setIncludeMedia] = useState(false);

    const fetchBackups = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/backups`, {
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
            });
            if (res.ok) {
                const data = await res.json();
                setBackups(data.backups || []);
            }
        } catch {
            // silent
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchBackups();
    }, [fetchBackups]);

    const handleCreate = async () => {
        setCreating(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/backups`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({
                    name: backupName || undefined,
                    backup_type: backupType,
                    include_media: includeMedia,
                }),
            });
            if (res.ok) {
                setShowCreate(false);
                setBackupName("");
                fetchBackups();
            }
        } catch {
            // silent
        } finally {
            setCreating(false);
        }
    };

    const handleRestore = async (backupId: string) => {
        try {
            await fetch(`${API_BASE}/api/v1/backups/${backupId}/restore`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({ target_environment: "staging", confirm: true }),
            });
            setRestoreTarget(null);
        } catch {
            // silent
        }
    };

    const handleDelete = async (backupId: string) => {
        try {
            await fetch(`${API_BASE}/api/v1/backups/${backupId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
            });
            fetchBackups();
        } catch {
            // silent
        }
    };

    const formatBytes = (bytes: number | null) => {
        if (!bytes) return "—";
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        if (bytes < 1024 * 1024 * 1024)
            return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
        return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    };

    const formatDate = (d: string | null) => {
        if (!d) return "—";
        return new Date(d).toLocaleString();
    };

    const statusIcon = (s: string) => {
        switch (s) {
            case "completed":
                return <CheckCircle className="w-4 h-4 text-green-400" />;
            case "in_progress":
                return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
            case "failed":
                return <AlertCircle className="w-4 h-4 text-red-400" />;
            default:
                return <Clock className="w-4 h-4 text-yellow-400" />;
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
                        <Database className="w-8 h-8 text-purple-400" />
                        <div>
                            <h1 className="text-2xl font-bold">Backup Management</h1>
                            <p className="text-gray-200 text-sm">
                                {backups.length} backups stored
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={() => fetchBackups()}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" /> Refresh
                        </button>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 transition-colors"
                        >
                            <Plus className="w-4 h-4" /> Create Backup
                        </button>
                    </div>
                </div>

                {/* Backup Table */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-800 text-gray-200 text-sm">
                                <th className="text-left p-4">Status</th>
                                <th className="text-left p-4">Name</th>
                                <th className="text-left p-4">Type</th>
                                <th className="text-left p-4">Size</th>
                                <th className="text-left p-4">Created</th>
                                <th className="text-right p-4">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {backups.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-12 text-gray-300">
                                        <HardDrive className="w-12 h-12 mx-auto mb-3 opacity-30" />
                                        <p>
                                            No backups yet. Create your first backup to get started.
                                        </p>
                                    </td>
                                </tr>
                            ) : (
                                backups.map((b) => (
                                    <tr
                                        key={b.id}
                                        className="border-b border-gray-800/50 hover:bg-gray-800/30"
                                    >
                                        <td className="p-4">{statusIcon(b.status)}</td>
                                        <td className="p-4 font-medium">{b.name}</td>
                                        <td className="p-4">
                                            <span className="px-2 py-1 bg-gray-800 rounded text-xs capitalize text-gray-300">
                                                {b.backup_type}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-200">
                                            {formatBytes(b.size_bytes)}
                                        </td>
                                        <td className="p-4 text-gray-200 text-sm">
                                            {formatDate(b.created_at)}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex gap-2 justify-end">
                                                {b.status === "completed" && (
                                                    <button
                                                        onClick={() => setRestoreTarget(b)}
                                                        className="p-2 hover:bg-gray-700 rounded transition-colors"
                                                        title="Restore"
                                                    >
                                                        <RotateCcw className="w-4 h-4 text-blue-400" />
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => handleDelete(b.id)}
                                                    className="p-2 hover:bg-gray-700 rounded transition-colors"
                                                    title="Delete"
                                                >
                                                    <Trash2 className="w-4 h-4 text-red-400" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Create Backup Modal */}
                {showCreate && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
                            <h2 className="text-xl font-bold mb-4">Create Backup</h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">
                                        Backup Name (optional)
                                    </label>
                                    <input
                                        type="text"
                                        value={backupName}
                                        onChange={(e) => setBackupName(e.target.value)}
                                        placeholder="Auto-generated if empty"
                                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-purple-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-200 mb-1">
                                        Backup Type
                                    </label>
                                    <select aria-label="Filter or select option"
                                        value={backupType}
                                        onChange={(e) => setBackupType(e.target.value)}
                                        className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white"
                                    >
                                        <option value="full">Full Backup</option>
                                        <option value="incremental">Incremental</option>
                                        <option value="schema-only">Schema Only</option>
                                    </select>
                                </div>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={includeMedia}
                                        onChange={(e) => setIncludeMedia(e.target.checked)}
                                        className="accent-purple-500"
                                    />
                                    <span className="text-sm text-gray-300">
                                        Include media assets (S3)
                                    </span>
                                </label>
                            </div>
                            <div className="flex gap-3 mt-6">
                                <button
                                    onClick={() => setShowCreate(false)}
                                    className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreate}
                                    disabled={creating}
                                    className="flex-1 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 disabled:opacity-80 flex items-center justify-center gap-2"
                                >
                                    {creating ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Plus className="w-4 h-4" />
                                    )}
                                    Create
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Restore Confirmation Modal */}
                {restoreTarget && (
                    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                        <div className="bg-gray-900 border border-red-800 rounded-xl p-6 w-full max-w-md">
                            <div className="flex items-center gap-3 mb-4">
                                <AlertCircle className="w-6 h-6 text-red-400" />
                                <h2 className="text-xl font-bold text-red-400">
                                    Confirm Restore
                                </h2>
                            </div>
                            <p className="text-gray-300 mb-2">
                                You are about to restore from:{" "}
                                <strong>{restoreTarget.name}</strong>
                            </p>
                            <p className="text-sm text-gray-300 mb-6">
                                This will restore the database to the state captured at{" "}
                                {formatDate(restoreTarget.created_at)}. This action targets the{" "}
                                <strong>staging</strong> environment.
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setRestoreTarget(null)}
                                    className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => handleRestore(restoreTarget.id)}
                                    className="flex-1 px-4 py-2 bg-red-600 rounded-lg hover:bg-red-500 flex items-center justify-center gap-2"
                                >
                                    <RotateCcw className="w-4 h-4" /> Restore
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
