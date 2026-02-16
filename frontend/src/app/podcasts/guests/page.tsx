"use client";

import { useState, useEffect } from "react";
import { Users, Plus, Mail, Calendar, Phone, Globe, Trash2, Edit, CheckCircle, Clock, Loader2 } from "lucide-react";
import { apiRequest } from "@/lib/api";

/**
 * Podcast Guest Management UI
 * 
 * Coordinate and track podcast guests
 */

interface PodcastGuest {
    id: string;
    name: string;
    email: string;
    phone?: string;
    website?: string;
    bio: string;
    socialLinks?: { platform: string; url: string }[];
    status: "invited" | "confirmed" | "scheduled" | "recorded" | "published";
    episodes: GuestEpisode[];
    notes?: string;
    avatar?: string;
}

interface GuestEpisode {
    id: string;
    episodeTitle: string;
    recordingDate?: string;
    publishDate?: string;
    status: "planning" | "scheduled" | "recorded" | "editing" | "published";
}


export default function GuestManagementPage() {
    const [guests, setGuests] = useState<PodcastGuest[]>([]);
    const [filter, setFilter] = useState<"all" | PodcastGuest["status"]>("all");
    const [selectedGuest, setSelectedGuest] = useState<PodcastGuest | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchGuests() {
            try {
                const response = await apiRequest<PodcastGuest[]>("/api/v1/podcasts/guests");
                setGuests(Array.isArray(response) ? response : []);
            } catch {
                setGuests([]);
            } finally {
                setLoading(false);
            }
        }
        fetchGuests();
    }, []);

    const stats = {
        total: guests.length,
        confirmed: guests.filter(g => g.status === "confirmed").length,
        scheduled: guests.filter(g => g.status === "scheduled").length,
        recorded: guests.filter(g => g.status === "recorded").length,
    };

    const filteredGuests = guests.filter(g => filter === "all" || g.status === filter);

    const handleDeleteGuest = (guestId: string) => {
        if (!confirm("Are you sure you want to remove this guest?")) return;
        setGuests(prev => prev.filter(g => g.id !== guestId));
        setSelectedGuest(null);
    };

    const handleUpdateStatus = (guestId: string, status: PodcastGuest["status"]) => {
        setGuests(prev => prev.map(g =>
            g.id === guestId ? { ...g, status } : g
        ));
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Guest Management</h1>
                        <p className="text-gray-400">Coordinate your podcast guests</p>
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        Add Guest
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                    <StatCard label="Total Guests" value={stats.total} />
                    <StatCard label="Confirmed" value={stats.confirmed} color="text-green-400" />
                    <StatCard label="Scheduled" value={stats.scheduled} color="text-blue-400" />
                    <StatCard label="Recorded" value={stats.recorded} color="text-purple-400" />
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {(["all", "invited", "confirmed", "scheduled", "recorded", "published"] as const).map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg text-sm capitalize whitespace-nowrap ${filter === f ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>

                {/* Loading */}
                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                )}

                {/* Empty State */}
                {!loading && filteredGuests.length === 0 && (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <Users className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No guests yet</h3>
                        <p className="text-gray-500 mb-6">Start inviting guests to your podcast.</p>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Add Guest
                        </button>
                    </div>
                )}

                {/* Guest List */}
                {!loading && filteredGuests.length > 0 && (
                    <div className="space-y-4">
                        {filteredGuests.map((guest) => (
                            <GuestCard
                                key={guest.id}
                                guest={guest}
                                onClick={() => setSelectedGuest(guest)}
                                onUpdateStatus={handleUpdateStatus}
                            />
                        ))}
                    </div>
                )}

                {/* Guest Detail Modal */}
                {selectedGuest && (
                    <GuestDetailModal
                        guest={selectedGuest}
                        onClose={() => setSelectedGuest(null)}
                        onDelete={() => handleDeleteGuest(selectedGuest.id)}
                    />
                )}

                {/* Add Guest Modal */}
                {showAddModal && (
                    <AddGuestModal
                        onClose={() => setShowAddModal(false)}
                        onAdd={(guest) => {
                            setGuests(prev => [...prev, guest]);
                            setShowAddModal(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function StatCard({ label, value, color = "text-white" }: { label: string; value: number; color?: string }) {
    return (
        <div className="bg-gray-900 rounded-xl p-4">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-sm text-gray-500">{label}</p>
        </div>
    );
}

function GuestCard({ guest, onClick, onUpdateStatus }: {
    guest: PodcastGuest;
    onClick: () => void;
    onUpdateStatus: (id: string, status: PodcastGuest["status"]) => void;
}) {
    const statusColors = {
        invited: "text-yellow-400 bg-yellow-400/10",
        confirmed: "text-green-400 bg-green-400/10",
        scheduled: "text-blue-400 bg-blue-400/10",
        recorded: "text-purple-400 bg-purple-400/10",
        published: "text-gray-400 bg-gray-400/10",
    };

    return (
        <div className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors">
            <div className="flex items-center gap-4">
                {/* Avatar */}
                <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-xl font-bold flex-shrink-0">
                    {guest.name.charAt(0)}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 cursor-pointer" onClick={onClick} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick(); } }} role="button" tabIndex={0}>
                    <h3 className="font-semibold">{guest.name}</h3>
                    <p className="text-sm text-gray-400 truncate">{guest.bio}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                            <Mail className="w-3 h-3" />
                            {guest.email}
                        </span>
                        {guest.episodes.length > 0 && (
                            <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {guest.episodes.length} episode(s)
                            </span>
                        )}
                    </div>
                </div>

                {/* Status */}
                <div className="flex items-center gap-2">
                    <select
                        value={guest.status}
                        onChange={(e) => onUpdateStatus(guest.id, e.target.value as PodcastGuest["status"])}
                        onClick={(e) => e.stopPropagation()}
                        className={`px-3 py-1 rounded-full text-sm bg-transparent border-0 cursor-pointer ${statusColors[guest.status]}`}
                    >
                        <option value="invited">Invited</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="recorded">Recorded</option>
                        <option value="published">Published</option>
                    </select>
                </div>
            </div>
        </div>
    );
}

function GuestDetailModal({ guest, onClose, onDelete }: {
    guest: PodcastGuest;
    onClose: () => void;
    onDelete: () => void;
}) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-2xl font-bold">
                                {guest.name.charAt(0)}
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">{guest.name}</h2>
                                <p className="text-gray-400 capitalize">{guest.status}</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                </div>

                <div className="p-6 space-y-4">
                    <p className="text-gray-300">{guest.bio}</p>

                    {/* Contact Info */}
                    <div className="grid gap-3">
                        <a href={`mailto:${guest.email}`} className="flex items-center gap-2 text-purple-400 hover:text-purple-300">
                            <Mail className="w-4 h-4" />
                            {guest.email}
                        </a>
                        {guest.phone && (
                            <a href={`tel:${guest.phone}`} className="flex items-center gap-2 text-gray-400 hover:text-gray-300">
                                <Phone className="w-4 h-4" />
                                {guest.phone}
                            </a>
                        )}
                        {guest.website && (
                            <a href={guest.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-gray-400 hover:text-gray-300">
                                <Globe className="w-4 h-4" />
                                {guest.website}
                            </a>
                        )}
                    </div>

                    {/* Episodes */}
                    {guest.episodes.length > 0 && (
                        <div>
                            <h3 className="font-medium mb-3">Episodes</h3>
                            <div className="space-y-2">
                                {guest.episodes.map((ep) => (
                                    <div key={ep.id} className="bg-gray-800 rounded-lg p-3">
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium">{ep.episodeTitle}</span>
                                            <span className="text-xs text-gray-500 capitalize">{ep.status}</span>
                                        </div>
                                        {ep.recordingDate && (
                                            <p className="text-sm text-gray-500 mt-1">
                                                Recording: {new Date(ep.recordingDate).toLocaleDateString()}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-gray-800">
                        <button className="flex-1 py-2 bg-purple-600 rounded-xl hover:bg-purple-700 flex items-center justify-center gap-2">
                            <Calendar className="w-4 h-4" />
                            Schedule Recording
                        </button>
                        <button
                            onClick={onDelete}
                            className="p-2 bg-red-600/20 text-red-400 rounded-xl hover:bg-red-600/30"
                        >
                            <Trash2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function AddGuestModal({ onClose, onAdd }: { onClose: () => void; onAdd: (guest: PodcastGuest) => void }) {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [bio, setBio] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onAdd({
            id: Date.now().toString(),
            name,
            email,
            bio,
            status: "invited",
            episodes: [],
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-4">Add Guest</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Name *</label>
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Email *</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Bio</label>
                        <textarea
                            value={bio}
                            onChange={(e) => setBio(e.target.value)}
                            rows={3}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button type="submit" disabled={!name || !email} className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50">
                            Add Guest
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
