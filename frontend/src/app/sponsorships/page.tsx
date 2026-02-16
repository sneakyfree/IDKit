"use client";

import { useState, useEffect } from "react";
import { DollarSign, Plus, Calendar, Building2, Loader2, MoreVertical, FileText, CheckCircle, Clock, AlertCircle, TrendingUp } from "lucide-react";
import { sponsorshipsApi } from "@/lib/api";

/**
 * Sponsorship Management UI
 * 
 * Track sponsor relationships, deals, and revenue
 */

interface Sponsor {
    id: string;
    name: string;
    logo?: string;
    industry: string;
    status: "active" | "negotiating" | "completed" | "paused";
    totalValue: number;
    deals: SponsorshipDeal[];
    contactName?: string;
    contactEmail?: string;
    notes?: string;
}

interface SponsorshipDeal {
    id: string;
    sponsorId: string;
    name: string;
    type: "one-time" | "recurring" | "campaign";
    value: number;
    startDate: string;
    endDate?: string;
    deliverables: Deliverable[];
    status: "draft" | "active" | "completed" | "cancelled";
    paidAmount: number;
}

interface Deliverable {
    id: string;
    description: string;
    dueDate: string;
    completed: boolean;
}


export default function SponsorshipPage() {
    const [sponsors, setSponsors] = useState<Sponsor[]>([]);
    const [filter, setFilter] = useState<"all" | Sponsor["status"]>("all");
    const [selectedSponsor, setSelectedSponsor] = useState<Sponsor | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchSponsors() {
            try {
                setLoading(true);
                const response = await sponsorshipsApi.list();
                // Transform API response to local interface
                const sponsorsList = Array.isArray(response) ? response : (response.sponsorships || []);
                setSponsors(sponsorsList.map((s: { id: string; brand_name: string; brand_logo?: string; status: string; value_cents: number }) => ({
                    id: s.id,
                    name: s.brand_name,
                    logo: s.brand_logo,
                    industry: "Technology", // API doesn't provide this yet
                    status: s.status as Sponsor["status"],
                    totalValue: s.value_cents / 100,
                    deals: [],
                })));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load sponsorships');
            } finally {
                setLoading(false);
            }
        }
        fetchSponsors();
    }, []);

    const stats = {
        totalRevenue: sponsors.reduce((sum, s) => sum + s.totalValue, 0),
        activeDeals: sponsors.flatMap(s => s.deals).filter(d => d.status === "active").length,
        pendingPayments: sponsors.flatMap(s => s.deals).reduce((sum, d) => sum + (d.value - d.paidAmount), 0),
        sponsors: sponsors.length,
    };

    const filteredSponsors = sponsors.filter(s => filter === "all" || s.status === filter);

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Sponsorship Management</h1>
                        <p className="text-gray-400">Track sponsors, deals, and revenue</p>
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        Add Sponsor
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <StatCard icon={<DollarSign />} label="Total Revenue" value={`$${stats.totalRevenue.toLocaleString()}`} />
                    <StatCard icon={<FileText />} label="Active Deals" value={stats.activeDeals} />
                    <StatCard icon={<Clock />} label="Pending Payments" value={`$${stats.pendingPayments.toLocaleString()}`} />
                    <StatCard icon={<Building2 />} label="Sponsors" value={stats.sponsors} />
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6">
                    {(["all", "active", "negotiating", "completed", "paused"] as const).map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-4 py-2 rounded-lg text-sm capitalize ${filter === f ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
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
                {!loading && filteredSponsors.length === 0 && (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <Building2 className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No sponsors yet</h3>
                        <p className="text-gray-500 mb-6">Start tracking your sponsorship relationships.</p>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Add Sponsor
                        </button>
                    </div>
                )}

                {/* Sponsor List */}
                {!loading && filteredSponsors.length > 0 && (
                    <div className="grid md:grid-cols-2 gap-4">
                        {filteredSponsors.map((sponsor) => (
                            <SponsorCard
                                key={sponsor.id}
                                sponsor={sponsor}
                                onClick={() => setSelectedSponsor(sponsor)}
                            />
                        ))}
                    </div>
                )}

                {/* Sponsor Detail Modal */}
                {selectedSponsor && (
                    <SponsorDetailModal
                        sponsor={selectedSponsor}
                        onClose={() => setSelectedSponsor(null)}
                    />
                )}

                {/* Add Sponsor Modal */}
                {showAddModal && (
                    <AddSponsorModal
                        onClose={() => setShowAddModal(false)}
                        onAdd={(sponsor) => {
                            setSponsors(prev => [...prev, sponsor]);
                            setShowAddModal(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
    return (
        <div className="bg-gray-900 rounded-xl p-4">
            <div className="flex items-center gap-3">
                <div className="text-purple-400">{icon}</div>
                <div>
                    <p className="text-2xl font-bold">{value}</p>
                    <p className="text-sm text-gray-500">{label}</p>
                </div>
            </div>
        </div>
    );
}

function SponsorCard({ sponsor, onClick }: { sponsor: Sponsor; onClick: () => void }) {
    const statusColors = {
        active: "text-green-400 bg-green-400/10",
        negotiating: "text-yellow-400 bg-yellow-400/10",
        completed: "text-blue-400 bg-blue-400/10",
        paused: "text-gray-400 bg-gray-400/10",
    };

    const activeDeals = sponsor.deals.filter(d => d.status === "active").length;

    return (
        <div
            onClick={onClick}
            className="bg-gray-900 rounded-xl p-5 cursor-pointer hover:bg-gray-800/50 transition-colors"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center">
                        <Building2 className="w-6 h-6 text-gray-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold">{sponsor.name}</h3>
                        <p className="text-sm text-gray-500">{sponsor.industry}</p>
                    </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full capitalize ${statusColors[sponsor.status]}`}>
                    {sponsor.status}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <p className="text-gray-500">Total Value</p>
                    <p className="font-semibold">${sponsor.totalValue.toLocaleString()}</p>
                </div>
                <div>
                    <p className="text-gray-500">Active Deals</p>
                    <p className="font-semibold">{activeDeals}</p>
                </div>
            </div>
        </div>
    );
}

function SponsorDetailModal({ sponsor, onClose }: { sponsor: Sponsor; onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-gray-800 rounded-xl flex items-center justify-center">
                                <Building2 className="w-8 h-8 text-gray-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">{sponsor.name}</h2>
                                <p className="text-gray-400">{sponsor.industry}</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                </div>

                <div className="p-6">
                    {/* Contact */}
                    {(sponsor.contactName || sponsor.contactEmail) && (
                        <div className="mb-6">
                            <h3 className="font-medium mb-2">Contact</h3>
                            <div className="bg-gray-800 rounded-xl p-4">
                                {sponsor.contactName && <p>{sponsor.contactName}</p>}
                                {sponsor.contactEmail && (
                                    <a href={`mailto:${sponsor.contactEmail}`} className="text-purple-400">{sponsor.contactEmail}</a>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Deals */}
                    <div>
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-medium">Deals</h3>
                            <button className="text-sm text-purple-400">+ Add Deal</button>
                        </div>

                        {sponsor.deals.length === 0 ? (
                            <div className="bg-gray-800 rounded-xl p-6 text-center">
                                <p className="text-gray-500">No deals yet</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {sponsor.deals.map((deal) => (
                                    <div key={deal.id} className="bg-gray-800 rounded-xl p-4">
                                        <div className="flex justify-between mb-2">
                                            <h4 className="font-medium">{deal.name}</h4>
                                            <span className="text-sm text-gray-400 capitalize">{deal.type}</span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                                            <div>
                                                <p className="text-gray-500">Value</p>
                                                <p>${deal.value.toLocaleString()}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Paid</p>
                                                <p>${deal.paidAmount.toLocaleString()}</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500">Status</p>
                                                <p className="capitalize">{deal.status}</p>
                                            </div>
                                        </div>

                                        {/* Deliverables */}
                                        <div className="border-t border-gray-700 pt-3">
                                            <p className="text-sm text-gray-400 mb-2">Deliverables</p>
                                            <div className="space-y-2">
                                                {deal.deliverables.map((d) => (
                                                    <div key={d.id} className="flex items-center gap-2 text-sm">
                                                        {d.completed ? (
                                                            <CheckCircle className="w-4 h-4 text-green-400" />
                                                        ) : (
                                                            <Clock className="w-4 h-4 text-gray-500" />
                                                        )}
                                                        <span className={d.completed ? "text-gray-500 line-through" : ""}>
                                                            {d.description}
                                                        </span>
                                                        <span className="text-gray-600 text-xs ml-auto">
                                                            {new Date(d.dueDate).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function AddSponsorModal({ onClose, onAdd }: { onClose: () => void; onAdd: (sponsor: Sponsor) => void }) {
    const [name, setName] = useState("");
    const [industry, setIndustry] = useState("");
    const [contactName, setContactName] = useState("");
    const [contactEmail, setContactEmail] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onAdd({
            id: Date.now().toString(),
            name,
            industry,
            status: "negotiating",
            totalValue: 0,
            deals: [],
            contactName,
            contactEmail,
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-4">Add Sponsor</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Company Name *</label>
                        <input
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Industry</label>
                        <input
                            value={industry}
                            onChange={(e) => setIndustry(e.target.value)}
                            placeholder="e.g., Technology, Fashion"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Contact Name</label>
                        <input
                            value={contactName}
                            onChange={(e) => setContactName(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Contact Email</label>
                        <input
                            type="email"
                            value={contactEmail}
                            onChange={(e) => setContactEmail(e.target.value)}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>
                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button type="submit" disabled={!name} className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50">
                            Add Sponsor
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
