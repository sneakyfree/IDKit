"use client";

import { useState, useEffect } from "react";
import { Database, Plus, Download, Trash2, Clock, CheckCircle, AlertCircle, Loader2, Play, RefreshCw, HardDrive } from "lucide-react";

/**
 * Backup Management UI
 * 
 * System backups and disaster recovery
 */

interface Backup {
    id: string;
    name: string;
    type: "full" | "incremental" | "differential";
    status: "completed" | "in-progress" | "failed" | "scheduled";
    size: string;
    createdAt: string;
    duration?: string;
    retentionDays: number;
    components: string[];
}

interface BackupSchedule {
    id: string;
    name: string;
    frequency: "hourly" | "daily" | "weekly" | "monthly";
    type: "full" | "incremental";
    time: string;
    enabled: boolean;
    lastRun?: string;
    nextRun: string;
}

const MOCK_BACKUPS: Backup[] = [
    {
        id: "1",
        name: "Daily Full Backup",
        type: "full",
        status: "completed",
        size: "2.4 GB",
        createdAt: "2024-01-15T03:00:00Z",
        duration: "12 min",
        retentionDays: 30,
        components: ["database", "media", "config"],
    },
    {
        id: "2",
        name: "Hourly Incremental",
        type: "incremental",
        status: "completed",
        size: "145 MB",
        createdAt: "2024-01-15T12:00:00Z",
        duration: "2 min",
        retentionDays: 7,
        components: ["database"],
    },
    {
        id: "3",
        name: "Weekly Archive",
        type: "full",
        status: "in-progress",
        size: "—",
        createdAt: "2024-01-15T14:30:00Z",
        retentionDays: 90,
        components: ["database", "media", "config", "logs"],
    },
];

const MOCK_SCHEDULES: BackupSchedule[] = [
    {
        id: "1",
        name: "Daily Database Backup",
        frequency: "daily",
        type: "full",
        time: "03:00",
        enabled: true,
        lastRun: "2024-01-15T03:00:00Z",
        nextRun: "2024-01-16T03:00:00Z",
    },
    {
        id: "2",
        name: "Hourly Incremental",
        frequency: "hourly",
        type: "incremental",
        time: ":00",
        enabled: true,
        lastRun: "2024-01-15T12:00:00Z",
        nextRun: "2024-01-15T13:00:00Z",
    },
    {
        id: "3",
        name: "Weekly Full Archive",
        frequency: "weekly",
        type: "full",
        time: "Sunday 02:00",
        enabled: true,
        lastRun: "2024-01-14T02:00:00Z",
        nextRun: "2024-01-21T02:00:00Z",
    },
];

export default function BackupManagementPage() {
    const [backups, setBackups] = useState<Backup[]>([]);
    const [schedules, setSchedules] = useState<BackupSchedule[]>([]);
    const [activeTab, setActiveTab] = useState<"backups" | "schedules" | "restore">("backups");
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        setTimeout(() => {
            setBackups(MOCK_BACKUPS);
            setSchedules(MOCK_SCHEDULES);
            setLoading(false);
        }, 800);
    }, []);

    const stats = {
        total: backups.length,
        completed: backups.filter(b => b.status === "completed").length,
        inProgress: backups.filter(b => b.status === "in-progress").length,
        totalSize: "12.8 GB",
    };

    const handleCreateBackup = async () => {
        setCreating(true);
        await new Promise(r => setTimeout(r, 2000));
        setBackups(prev => [{
            id: Date.now().toString(),
            name: "Manual Backup",
            type: "full",
            status: "in-progress",
            size: "—",
            createdAt: new Date().toISOString(),
            retentionDays: 30,
            components: ["database", "media", "config"],
        }, ...prev]);
        setCreating(false);
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Backup Management</h1>
                        <p className="text-gray-400">System backups and disaster recovery</p>
                    </div>
                    <button
                        onClick={handleCreateBackup}
                        disabled={creating}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50"
                    >
                        {creating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                        {creating ? "Creating..." : "Create Backup"}
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-gray-900 rounded-xl p-4">
                        <Database className="w-6 h-6 text-purple-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.total}</p>
                        <p className="text-sm text-gray-400">Total Backups</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <CheckCircle className="w-6 h-6 text-green-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.completed}</p>
                        <p className="text-sm text-gray-400">Completed</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <RefreshCw className="w-6 h-6 text-blue-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.inProgress}</p>
                        <p className="text-sm text-gray-400">In Progress</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <HardDrive className="w-6 h-6 text-orange-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.totalSize}</p>
                        <p className="text-sm text-gray-400">Total Size</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {(["backups", "schedules", "restore"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-lg capitalize ${activeTab === tab ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : (
                    <>
                        {/* Backups Tab */}
                        {activeTab === "backups" && (
                            <div className="space-y-4">
                                {backups.map((backup) => (
                                    <BackupCard key={backup.id} backup={backup} />
                                ))}
                            </div>
                        )}

                        {/* Schedules Tab */}
                        {activeTab === "schedules" && (
                            <div className="space-y-4">
                                {schedules.map((schedule) => (
                                    <ScheduleCard
                                        key={schedule.id}
                                        schedule={schedule}
                                        onToggle={() => {
                                            setSchedules(prev => prev.map(s =>
                                                s.id === schedule.id ? { ...s, enabled: !s.enabled } : s
                                            ));
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        {/* Restore Tab */}
                        {activeTab === "restore" && (
                            <div className="bg-gray-900 rounded-xl p-6">
                                <h3 className="text-lg font-semibold mb-4">Restore from Backup</h3>
                                <p className="text-gray-400 mb-6">
                                    Select a backup to restore your system. This will replace all current data with the backup data.
                                </p>

                                <div className="space-y-4">
                                    {backups.filter(b => b.status === "completed").map((backup) => (
                                        <div key={backup.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-xl">
                                            <div>
                                                <p className="font-medium">{backup.name}</p>
                                                <p className="text-sm text-gray-500">
                                                    {new Date(backup.createdAt).toLocaleString()} • {backup.size}
                                                </p>
                                            </div>
                                            <button className="px-4 py-2 bg-orange-600 rounded-lg hover:bg-orange-700 text-sm">
                                                Restore
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                                    <div className="flex gap-3">
                                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                                        <div className="text-sm">
                                            <p className="font-medium text-red-400">Warning</p>
                                            <p className="text-gray-400">
                                                Restoring from a backup will overwrite all current data. This action cannot be undone.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}

function BackupCard({ backup }: { backup: Backup }) {
    const statusConfig = {
        completed: { color: "text-green-400 bg-green-400/10", icon: CheckCircle },
        "in-progress": { color: "text-blue-400 bg-blue-400/10", icon: RefreshCw },
        failed: { color: "text-red-400 bg-red-400/10", icon: AlertCircle },
        scheduled: { color: "text-gray-400 bg-gray-400/10", icon: Clock },
    };

    const { color, icon: StatusIcon } = statusConfig[backup.status];

    return (
        <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
                        <Database className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-medium">{backup.name}</h3>
                        <p className="text-sm text-gray-500 capitalize">{backup.type} backup</p>
                    </div>
                </div>
                <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${color}`}>
                    <StatusIcon className={`w-3 h-3 ${backup.status === "in-progress" ? "animate-spin" : ""}`} />
                    {backup.status}
                </span>
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
                {backup.components.map((comp) => (
                    <span key={comp} className="text-xs bg-gray-800 px-2 py-1 rounded capitalize">
                        {comp}
                    </span>
                ))}
            </div>

            <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex gap-4">
                    <span>{new Date(backup.createdAt).toLocaleString()}</span>
                    <span>{backup.size}</span>
                    {backup.duration && <span>{backup.duration}</span>}
                </div>
                {backup.status === "completed" && (
                    <button className="flex items-center gap-1 text-purple-400 hover:text-purple-300">
                        <Download className="w-4 h-4" />
                        Download
                    </button>
                )}
            </div>
        </div>
    );
}

function ScheduleCard({ schedule, onToggle }: { schedule: BackupSchedule; onToggle: () => void }) {
    return (
        <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="font-medium">{schedule.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">
                        {schedule.frequency} • {schedule.type} backup • {schedule.time}
                    </p>
                </div>
                <button
                    onClick={onToggle}
                    className={`w-12 h-6 rounded-full transition-colors ${schedule.enabled ? "bg-green-500" : "bg-gray-700"
                        }`}
                >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${schedule.enabled ? "translate-x-6" : "translate-x-1"
                        }`} />
                </button>
            </div>
            <div className="flex gap-4 mt-3 text-sm text-gray-500">
                {schedule.lastRun && (
                    <span>Last: {new Date(schedule.lastRun).toLocaleString()}</span>
                )}
                <span>Next: {new Date(schedule.nextRun).toLocaleString()}</span>
            </div>
        </div>
    );
}
