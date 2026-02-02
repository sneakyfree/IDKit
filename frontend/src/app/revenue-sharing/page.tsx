"use client";

import { useState, useEffect } from "react";
import { DollarSign, Users, PieChart, Plus, Loader2, CheckCircle, Clock, ArrowRight, Settings } from "lucide-react";

/**
 * Revenue Sharing UI
 * 
 * Split profits with collaborators automatically
 */

interface RevenueShare {
    id: string;
    name: string;
    type: "project" | "ongoing" | "affiliate";
    status: "active" | "paused" | "completed";
    participants: Participant[];
    totalRevenue: number;
    period: "monthly" | "per-project" | "lifetime";
    createdAt: string;
    lastPayout?: string;
}

interface Participant {
    id: string;
    name: string;
    email: string;
    percentage: number;
    earned: number;
    paidOut: number;
    pending: number;
}

const MOCK_SHARES: RevenueShare[] = [
    {
        id: "1",
        name: "Podcast Revenue Split",
        type: "ongoing",
        status: "active",
        participants: [
            { id: "1", name: "You", email: "you@example.com", percentage: 60, earned: 3600, paidOut: 3000, pending: 600 },
            { id: "2", name: "Co-Host", email: "cohost@example.com", percentage: 40, earned: 2400, paidOut: 2000, pending: 400 },
        ],
        totalRevenue: 6000,
        period: "monthly",
        createdAt: "2024-01-01",
        lastPayout: "2024-01-15",
    },
    {
        id: "2",
        name: "Collab Video Project",
        type: "project",
        status: "completed",
        participants: [
            { id: "1", name: "You", email: "you@example.com", percentage: 50, earned: 1500, paidOut: 1500, pending: 0 },
            { id: "3", name: "VideoEditor", email: "editor@example.com", percentage: 30, earned: 900, paidOut: 900, pending: 0 },
            { id: "4", name: "ThumbnailDesigner", email: "design@example.com", percentage: 20, earned: 600, paidOut: 600, pending: 0 },
        ],
        totalRevenue: 3000,
        period: "per-project",
        createdAt: "2023-12-01",
    },
];

export default function RevenueSharingPage() {
    const [shares, setShares] = useState<RevenueShare[]>([]);
    const [selectedShare, setSelectedShare] = useState<RevenueShare | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setTimeout(() => {
            setShares(MOCK_SHARES);
            setLoading(false);
        }, 800);
    }, []);

    const totals = {
        revenue: shares.reduce((sum, s) => sum + s.totalRevenue, 0),
        pending: shares.reduce((sum, s) => sum + s.participants.reduce((p, part) => p + part.pending, 0), 0),
        active: shares.filter(s => s.status === "active").length,
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Revenue Sharing</h1>
                        <p className="text-gray-400">Automatically split profits with collaborators</p>
                    </div>
                    <button
                        onClick={() => setShowCreate(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        New Revenue Split
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="bg-gradient-to-br from-green-600/20 to-emerald-600/20 rounded-xl p-5 border border-green-500/20">
                        <DollarSign className="w-8 h-8 text-green-400 mb-2" />
                        <p className="text-2xl font-bold">${totals.revenue.toLocaleString()}</p>
                        <p className="text-sm text-gray-400">Total Revenue Shared</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-5">
                        <Clock className="w-8 h-8 text-yellow-400 mb-2" />
                        <p className="text-2xl font-bold">${totals.pending.toLocaleString()}</p>
                        <p className="text-sm text-gray-400">Pending Payouts</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-5">
                        <Users className="w-8 h-8 text-purple-400 mb-2" />
                        <p className="text-2xl font-bold">{totals.active}</p>
                        <p className="text-sm text-gray-400">Active Agreements</p>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : shares.length === 0 ? (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <PieChart className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No revenue splits yet</h3>
                        <p className="text-gray-500 mb-6">Set up automatic profit sharing with collaborators.</p>
                        <button
                            onClick={() => setShowCreate(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Create Revenue Split
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {shares.map((share) => (
                            <ShareCard
                                key={share.id}
                                share={share}
                                onClick={() => setSelectedShare(share)}
                            />
                        ))}
                    </div>
                )}

                {/* Detail Modal */}
                {selectedShare && (
                    <ShareDetailModal
                        share={selectedShare}
                        onClose={() => setSelectedShare(null)}
                    />
                )}

                {/* Create Modal */}
                {showCreate && (
                    <CreateShareModal
                        onClose={() => setShowCreate(false)}
                        onCreate={(share) => {
                            setShares(prev => [...prev, share]);
                            setShowCreate(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function ShareCard({ share, onClick }: { share: RevenueShare; onClick: () => void }) {
    const statusColors = {
        active: "text-green-400 bg-green-400/10",
        paused: "text-yellow-400 bg-yellow-400/10",
        completed: "text-gray-400 bg-gray-400/10",
    };

    return (
        <div
            onClick={onClick}
            className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors cursor-pointer"
        >
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="font-semibold">{share.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{share.type} • {share.period}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full capitalize ${statusColors[share.status]}`}>
                    {share.status}
                </span>
            </div>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div>
                        <p className="text-lg font-bold text-green-400">${share.totalRevenue.toLocaleString()}</p>
                        <p className="text-xs text-gray-500">Total Revenue</p>
                    </div>
                    <div>
                        <p className="text-lg font-bold">{share.participants.length}</p>
                        <p className="text-xs text-gray-500">Participants</p>
                    </div>
                </div>

                {/* Split visualization */}
                <div className="flex h-2 w-32 rounded-full overflow-hidden">
                    {share.participants.map((p, i) => (
                        <div
                            key={p.id}
                            style={{ width: `${p.percentage}%` }}
                            className={`h-full ${i === 0 ? "bg-purple-500" : i === 1 ? "bg-blue-500" : i === 2 ? "bg-green-500" : "bg-yellow-500"
                                }`}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

function ShareDetailModal({ share, onClose }: { share: RevenueShare; onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold">{share.name}</h2>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {/* Summary */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-800 rounded-xl p-4">
                            <p className="text-sm text-gray-400">Total Revenue</p>
                            <p className="text-xl font-bold text-green-400">${share.totalRevenue.toLocaleString()}</p>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4">
                            <p className="text-sm text-gray-400">Period</p>
                            <p className="text-xl font-bold capitalize">{share.period}</p>
                        </div>
                    </div>

                    {/* Participants */}
                    <div>
                        <h3 className="font-medium mb-3">Revenue Split</h3>
                        <div className="space-y-3">
                            {share.participants.map((p) => (
                                <div key={p.id} className="bg-gray-800 rounded-xl p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <div>
                                            <p className="font-medium">{p.name}</p>
                                            <p className="text-sm text-gray-500">{p.email}</p>
                                        </div>
                                        <span className="text-lg font-bold text-purple-400">{p.percentage}%</span>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-sm">
                                        <div>
                                            <p className="text-gray-500">Earned</p>
                                            <p className="font-medium">${p.earned.toLocaleString()}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-500">Paid</p>
                                            <p className="font-medium text-green-400">${p.paidOut.toLocaleString()}</p>
                                        </div>
                                        <div>
                                            <p className="text-gray-500">Pending</p>
                                            <p className="font-medium text-yellow-400">${p.pending.toLocaleString()}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 flex items-center justify-center gap-2">
                            <DollarSign className="w-4 h-4" />
                            Process Payouts
                        </button>
                        <button className="p-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            <Settings className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CreateShareModal({ onClose, onCreate }: { onClose: () => void; onCreate: (s: RevenueShare) => void }) {
    const [name, setName] = useState("");
    const [type, setType] = useState<RevenueShare["type"]>("ongoing");
    const [period, setPeriod] = useState<RevenueShare["period"]>("monthly");
    const [participants, setParticipants] = useState([
        { name: "You", email: "you@example.com", percentage: 50 },
        { name: "", email: "", percentage: 50 },
    ]);

    const updateParticipant = (index: number, field: string, value: string | number) => {
        setParticipants(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
    };

    const addParticipant = () => {
        setParticipants(prev => [...prev, { name: "", email: "", percentage: 0 }]);
    };

    const totalPercentage = participants.reduce((sum, p) => sum + p.percentage, 0);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            id: Date.now().toString(),
            name,
            type,
            status: "active",
            participants: participants.filter(p => p.name).map((p, i) => ({
                id: String(i + 1),
                ...p,
                earned: 0,
                paidOut: 0,
                pending: 0,
            })),
            totalRevenue: 0,
            period,
            createdAt: new Date().toISOString(),
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6 my-8">
                <h2 className="text-xl font-bold mb-6">Create Revenue Split</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Agreement Name *</label>
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            placeholder="Podcast Revenue Split"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Type</label>
                            <select
                                value={type}
                                onChange={(e) => setType(e.target.value as RevenueShare["type"])}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            >
                                <option value="ongoing">Ongoing</option>
                                <option value="project">Per Project</option>
                                <option value="affiliate">Affiliate</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Period</label>
                            <select
                                value={period}
                                onChange={(e) => setPeriod(e.target.value as RevenueShare["period"])}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            >
                                <option value="monthly">Monthly</option>
                                <option value="per-project">Per Project</option>
                                <option value="lifetime">Lifetime</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-sm text-gray-400">Participants</label>
                            <span className={`text-sm ${totalPercentage === 100 ? "text-green-400" : "text-yellow-400"}`}>
                                {totalPercentage}%
                            </span>
                        </div>
                        <div className="space-y-2">
                            {participants.map((p, i) => (
                                <div key={i} className="flex gap-2">
                                    <input
                                        value={p.name}
                                        onChange={(e) => updateParticipant(i, "name", e.target.value)}
                                        placeholder="Name"
                                        className="flex-1 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700 text-sm"
                                    />
                                    <input
                                        type="number"
                                        value={p.percentage}
                                        onChange={(e) => updateParticipant(i, "percentage", parseInt(e.target.value) || 0)}
                                        min="0"
                                        max="100"
                                        className="w-20 px-3 py-2 bg-gray-800 rounded-lg border border-gray-700 text-sm text-center"
                                    />
                                    <span className="flex items-center text-gray-500">%</span>
                                </div>
                            ))}
                        </div>
                        <button
                            type="button"
                            onClick={addParticipant}
                            className="mt-2 text-sm text-purple-400 hover:text-purple-300"
                        >
                            + Add Participant
                        </button>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!name || totalPercentage !== 100}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50"
                        >
                            Create
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
