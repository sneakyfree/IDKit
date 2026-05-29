"use client";

import { useState, useEffect } from "react";
import { FileText, Plus, Upload, Eye, Download, Trash2, CheckCircle, Clock, AlertCircle, Loader2, Edit } from "lucide-react";
import { contractsApi } from "@/lib/api";

/**
 * Contract Management UI
 * 
 * Legal agreements and contract tracking
 */

interface Contract {
    id: string;
    title: string;
    type: "sponsorship" | "collaboration" | "licensing" | "nda" | "custom";
    status: "draft" | "pending" | "signed" | "expired" | "cancelled";
    parties: { name: string; email: string; signed?: boolean; signedAt?: string }[];
    value?: number;
    startDate: string;
    endDate?: string;
    createdAt: string;
    documentUrl?: string;
    notes?: string;
}

const CONTRACT_TYPES = [
    { id: "sponsorship", label: "Sponsorship Agreement" },
    { id: "collaboration", label: "Collaboration Agreement" },
    { id: "licensing", label: "Content Licensing" },
    { id: "nda", label: "Non-Disclosure Agreement" },
    { id: "custom", label: "Custom Contract" },
];


export default function ContractsPage() {
    const [contracts, setContracts] = useState<Contract[]>([]);
    const [filter, setFilter] = useState<"all" | Contract["status"]>("all");
    const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchContracts() {
            try {
                setLoading(true);
                const response = await contractsApi.list();
                // Transform API response to local interface
                const contractsList = Array.isArray(response) ? response : (response.contracts || []);
                setContracts(contractsList.map((c: { id: string; title: string; status: string; brand_name: string; value_cents: number; created_at: string; expires_at?: string }) => ({
                    id: c.id,
                    title: c.title,
                    type: "sponsorship" as const, // API returns brand_name, infer type
                    status: c.status === "active" ? "signed" : c.status === "pending" ? "pending" : c.status as Contract["status"],
                    parties: [
                        { name: "Creator (You)", email: "you@example.com", signed: true },
                        { name: c.brand_name, email: "", signed: c.status === "active" },
                    ],
                    value: c.value_cents / 100,
                    startDate: c.created_at,
                    endDate: c.expires_at,
                    createdAt: c.created_at,
                })));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load contracts');
            } finally {
                setLoading(false);
            }
        }
        fetchContracts();
    }, []);

    const stats = {
        active: contracts.filter(c => c.status === "signed" && (!c.endDate || new Date(c.endDate) > new Date())).length,
        pending: contracts.filter(c => c.status === "pending").length,
        totalValue: contracts.filter(c => c.status === "signed").reduce((sum, c) => sum + (c.value || 0), 0),
    };

    const filteredContracts = contracts.filter(c => filter === "all" || c.status === filter);

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Contract Management</h1>
                        <p className="text-gray-200">Track and manage your legal agreements</p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        New Contract
                    </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold text-green-400">{stats.active}</p>
                        <p className="text-sm text-gray-300">Active Contracts</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold text-yellow-400">{stats.pending}</p>
                        <p className="text-sm text-gray-300">Pending Signature</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <p className="text-2xl font-bold">${stats.totalValue.toLocaleString()}</p>
                        <p className="text-sm text-gray-300">Total Contract Value</p>
                    </div>
                </div>

                {/* Filters */}
                <div className="flex gap-2 mb-6">
                    {(["all", "draft", "pending", "signed", "expired", "cancelled"] as const).map((f) => (
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
                {!loading && filteredContracts.length === 0 && (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <FileText className="w-16 h-16 mx-auto text-gray-200 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No contracts found</h3>
                        <p className="text-gray-300 mb-6">Create your first contract or agreement.</p>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl"
                        >
                            <Plus className="w-5 h-5" />
                            Create Contract
                        </button>
                    </div>
                )}

                {/* Contract List */}
                {!loading && filteredContracts.length > 0 && (
                    <div className="space-y-4">
                        {filteredContracts.map((contract) => (
                            <ContractCard
                                key={contract.id}
                                contract={contract}
                                onClick={() => setSelectedContract(contract)}
                            />
                        ))}
                    </div>
                )}

                {/* Contract Detail Modal */}
                {selectedContract && (
                    <ContractDetailModal
                        contract={selectedContract}
                        onClose={() => setSelectedContract(null)}
                    />
                )}

                {/* Create Contract Modal */}
                {showCreateModal && (
                    <CreateContractModal
                        onClose={() => setShowCreateModal(false)}
                        onCreate={(contract) => {
                            setContracts(prev => [...prev, contract]);
                            setShowCreateModal(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function ContractCard({ contract, onClick }: { contract: Contract; onClick: () => void }) {
    const statusConfig = {
        draft: { color: "text-gray-200 bg-gray-400/10", icon: Edit },
        pending: { color: "text-yellow-400 bg-yellow-400/10", icon: Clock },
        signed: { color: "text-green-400 bg-green-400/10", icon: CheckCircle },
        expired: { color: "text-orange-400 bg-orange-400/10", icon: AlertCircle },
        cancelled: { color: "text-red-400 bg-red-400/10", icon: AlertCircle },
    };

    const { color, icon: StatusIcon } = statusConfig[contract.status];
    const typeLabel = CONTRACT_TYPES.find(t => t.id === contract.type)?.label;

    return (
        <div
            onClick={onClick}
            className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors cursor-pointer"
        >
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center">
                        <FileText className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold">{contract.title}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-300">
                            <span>{typeLabel}</span>
                            {contract.value && (
                                <span className="text-green-400">${contract.value.toLocaleString()}</span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {/* Signature Progress */}
                    <div className="text-sm text-gray-300">
                        {contract.parties.filter(p => p.signed).length}/{contract.parties.length} signed
                    </div>

                    {/* Status Badge */}
                    <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full capitalize ${color}`}>
                        <StatusIcon className="w-3 h-3" />
                        {contract.status}
                    </span>
                </div>
            </div>
        </div>
    );
}

function ContractDetailModal({ contract, onClose }: { contract: Contract; onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">{contract.title}</h2>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {/* Info Grid */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-sm text-gray-300">Type</p>
                            <p className="capitalize">{contract.type}</p>
                        </div>
                        <div>
                            <p className="text-sm text-gray-300">Status</p>
                            <p className="capitalize">{contract.status}</p>
                        </div>
                        {contract.value && (
                            <div>
                                <p className="text-sm text-gray-300">Value</p>
                                <p className="text-green-400">${contract.value.toLocaleString()}</p>
                            </div>
                        )}
                        <div>
                            <p className="text-sm text-gray-300">Start Date</p>
                            <p>{new Date(contract.startDate).toLocaleDateString()}</p>
                        </div>
                        {contract.endDate && (
                            <div>
                                <p className="text-sm text-gray-300">End Date</p>
                                <p>{new Date(contract.endDate).toLocaleDateString()}</p>
                            </div>
                        )}
                    </div>

                    {/* Parties */}
                    <div>
                        <h3 className="font-medium mb-3">Parties</h3>
                        <div className="space-y-2">
                            {contract.parties.map((party, i) => (
                                <div key={i} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                                    <div>
                                        <p className="font-medium">{party.name}</p>
                                        <p className="text-sm text-gray-300">{party.email}</p>
                                    </div>
                                    {party.signed ? (
                                        <span className="flex items-center gap-1 text-green-400 text-sm">
                                            <CheckCircle className="w-4 h-4" />
                                            Signed {party.signedAt && `on ${new Date(party.signedAt).toLocaleDateString()}`}
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-1 text-yellow-400 text-sm">
                                            <Clock className="w-4 h-4" />
                                            Pending
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                        {contract.documentUrl && (
                            <a
                                href={contract.documentUrl}
                                className="flex-1 flex items-center justify-center gap-2 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
                            >
                                <Download className="w-4 h-4" />
                                Download
                            </a>
                        )}
                        <button className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            View History
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CreateContractModal({
    onClose,
    onCreate,
}: {
    onClose: () => void;
    onCreate: (contract: Contract) => void;
}) {
    const [title, setTitle] = useState("");
    const [type, setType] = useState<Contract["type"]>("sponsorship");
    const [value, setValue] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [partyName, setPartyName] = useState("");
    const [partyEmail, setPartyEmail] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            id: Date.now().toString(),
            title,
            type,
            status: "draft",
            parties: [
                { name: "Creator (You)", email: "you@example.com", signed: false },
                { name: partyName, email: partyEmail, signed: false },
            ],
            value: value ? parseFloat(value) : undefined,
            startDate,
            endDate: endDate || undefined,
            createdAt: new Date().toISOString(),
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-6">Create Contract</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-200 mb-1">Contract Title *</label>
                        <input
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-gray-200 mb-1">Type</label>
                        <select aria-label="Filter or select option"
                            value={type}
                            onChange={(e) => setType(e.target.value as Contract["type"])}
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        >
                            {CONTRACT_TYPES.map((t) => (
                                <option key={t.id} value={t.id}>{t.label}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm text-gray-200 mb-1">Contract Value ($)</label>
                        <input
                            type="number"
                            value={value}
                            onChange={(e) => setValue(e.target.value)}
                            placeholder="5000"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">Start Date *</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-200 mb-1">End Date</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            />
                        </div>
                    </div>

                    <div className="border-t border-gray-800 pt-4">
                        <p className="text-sm text-gray-200 mb-2">Other Party</p>
                        <div className="space-y-2">
                            <input
                                value={partyName}
                                onChange={(e) => setPartyName(e.target.value)}
                                placeholder="Company/Person Name"
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            />
                            <input
                                type="email"
                                value={partyEmail}
                                onChange={(e) => setPartyEmail(e.target.value)}
                                placeholder="email@example.com"
                                className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                            />
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!title || !startDate}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-80"
                        >
                            Create
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
