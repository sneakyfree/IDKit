"use client";

import { useState, useEffect } from "react";
import { Globe, Plus, Trash2, CheckCircle, XCircle, Loader2, AlertCircle, RefreshCw, ExternalLink } from "lucide-react";
import { apiRequest } from "@/lib/api";

/**
 * TASK 5.1.4: Custom Domains UI
 * 
 * Manage custom domains for enterprise white-labeling
 */

interface CustomDomain {
    id: string;
    domain: string;
    status: "pending" | "verified" | "failed" | "active";
    sslStatus: "pending" | "active" | "expired" | "failed";
    createdAt: string;
    verifiedAt?: string;
    dnsRecords: DNSRecord[];
}

interface DNSRecord {
    type: "CNAME" | "A" | "TXT";
    name: string;
    value: string;
    verified: boolean;
}


export default function CustomDomainsPage() {
    const [domains, setDomains] = useState<CustomDomain[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedDomain, setSelectedDomain] = useState<CustomDomain | null>(null);
    const [verifying, setVerifying] = useState<string | null>(null);

    useEffect(() => {
        async function fetchDomains() {
            try {
                const response = await apiRequest<CustomDomain[]>("/api/v1/domains");
                setDomains(Array.isArray(response) ? response : []);
            } catch {
                setDomains([]);
            } finally {
                setLoading(false);
            }
        }
        fetchDomains();
    }, []);

    const handleAddDomain = async (domain: string) => {
        try {
            // API call would go here
            const newDomain: CustomDomain = {
                id: Date.now().toString(),
                domain,
                status: "pending",
                sslStatus: "pending",
                createdAt: new Date().toISOString(),
                dnsRecords: [
                    { type: "CNAME", name: domain.split(".")[0], value: "custom.idkit.io", verified: false },
                    { type: "TXT", name: "_idkit-verify", value: `idkit-verification=${Math.random().toString(36).substring(7)}`, verified: false },
                ],
            };
            setDomains(prev => [...prev, newDomain]);
            setShowAddModal(false);
            setSelectedDomain(newDomain);
        } catch (err) {
            setError("Failed to add domain");
        }
    };

    const handleVerifyDomain = async (domainId: string) => {
        setVerifying(domainId);
        try {
            // Simulate verification
            await new Promise(resolve => setTimeout(resolve, 2000));
            setDomains(prev => prev.map(d =>
                d.id === domainId
                    ? {
                        ...d,
                        status: "verified" as const,
                        dnsRecords: d.dnsRecords.map(r => ({ ...r, verified: true })),
                    }
                    : d
            ));
        } catch (err) {
            setError("Verification failed");
        } finally {
            setVerifying(null);
        }
    };

    const handleDeleteDomain = async (domainId: string) => {
        if (!confirm("Are you sure you want to delete this domain?")) return;
        setDomains(prev => prev.filter(d => d.id !== domainId));
        setSelectedDomain(null);
    };

    const getStatusColor = (status: CustomDomain["status"]) => {
        switch (status) {
            case "active": return "text-green-400 bg-green-400/10";
            case "verified": return "text-blue-400 bg-blue-400/10";
            case "pending": return "text-yellow-400 bg-yellow-400/10";
            case "failed": return "text-red-400 bg-red-400/10";
        }
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Custom Domains</h1>
                        <p className="text-gray-200">Connect your own domain for white-label branding</p>
                    </div>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <Plus className="w-5 h-5" />
                        Add Domain
                    </button>
                </div>

                {/* Enterprise Notice */}
                <div className="bg-purple-900/30 border border-purple-500/30 rounded-xl p-4 mb-6">
                    <div className="flex items-center gap-3">
                        <Globe className="w-5 h-5 text-purple-400" />
                        <div>
                            <p className="font-medium">Enterprise Feature</p>
                            <p className="text-sm text-gray-200">Custom domains are included in Enterprise plans.</p>
                        </div>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-6 flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <p className="text-red-300">{error}</p>
                        <button onClick={() => setError(null)} className="ml-auto text-red-400">×</button>
                    </div>
                )}

                {/* Loading */}
                {loading && (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                )}

                {/* Empty State */}
                {!loading && domains.length === 0 && (
                    <div className="bg-gray-900 rounded-2xl p-12 text-center">
                        <Globe className="w-16 h-16 mx-auto text-gray-200 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No custom domains</h3>
                        <p className="text-gray-300 mb-6">Add your first domain to enable white-label branding.</p>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
                        >
                            <Plus className="w-5 h-5" />
                            Add Domain
                        </button>
                    </div>
                )}

                {/* Domain List */}
                {!loading && domains.length > 0 && (
                    <div className="space-y-4">
                        {domains.map((domain) => (
                            <div
                                key={domain.id}
                                className={`bg-gray-900 rounded-xl p-5 cursor-pointer transition-colors hover:bg-gray-800/50 ${selectedDomain?.id === domain.id ? "ring-2 ring-purple-500" : ""
                                    }`}
                                onClick={() => setSelectedDomain(domain)}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <Globe className="w-5 h-5 text-gray-200" />
                                        <div>
                                            <h3 className="font-semibold">{domain.domain}</h3>
                                            <p className="text-sm text-gray-300">Added {new Date(domain.createdAt).toLocaleDateString()}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(domain.status)}`}>
                                            {domain.status}
                                        </span>
                                        {domain.status === "active" && (
                                            <a
                                                href={`https://${domain.domain}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-2 hover:bg-gray-700 rounded-lg"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Domain Details Panel */}
                {selectedDomain && (
                    <div className="mt-6 bg-gray-900 rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold">{selectedDomain.domain}</h3>
                            <div className="flex gap-2">
                                {selectedDomain.status === "pending" && (
                                    <button
                                        onClick={() => handleVerifyDomain(selectedDomain.id)}
                                        disabled={verifying === selectedDomain.id}
                                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-80"
                                    >
                                        {verifying === selectedDomain.id ? (
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <RefreshCw className="w-4 h-4" />
                                        )}
                                        Verify DNS
                                    </button>
                                )}
                                <button
                                    onClick={() => handleDeleteDomain(selectedDomain.id)}
                                    className="flex items-center gap-2 px-4 py-2 bg-red-600/20 text-red-400 rounded-lg hover:bg-red-600/30"
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Remove
                                </button>
                            </div>
                        </div>

                        {/* Status */}
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            <div className="bg-gray-800 rounded-xl p-4">
                                <p className="text-sm text-gray-200 mb-1">Domain Status</p>
                                <div className="flex items-center gap-2">
                                    {selectedDomain.status === "active" ? (
                                        <CheckCircle className="w-5 h-5 text-green-400" />
                                    ) : selectedDomain.status === "failed" ? (
                                        <XCircle className="w-5 h-5 text-red-400" />
                                    ) : (
                                        <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
                                    )}
                                    <span className="capitalize">{selectedDomain.status}</span>
                                </div>
                            </div>
                            <div className="bg-gray-800 rounded-xl p-4">
                                <p className="text-sm text-gray-200 mb-1">SSL Certificate</p>
                                <div className="flex items-center gap-2">
                                    {selectedDomain.sslStatus === "active" ? (
                                        <CheckCircle className="w-5 h-5 text-green-400" />
                                    ) : selectedDomain.sslStatus === "expired" ? (
                                        <XCircle className="w-5 h-5 text-red-400" />
                                    ) : (
                                        <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
                                    )}
                                    <span className="capitalize">{selectedDomain.sslStatus}</span>
                                </div>
                            </div>
                        </div>

                        {/* DNS Records */}
                        <div>
                            <h4 className="font-medium mb-3">DNS Records</h4>
                            <p className="text-sm text-gray-200 mb-4">
                                Add these records to your DNS provider:
                            </p>
                            <div className="space-y-3">
                                {selectedDomain.dnsRecords.map((record, i) => (
                                    <div key={i} className="bg-gray-800 rounded-xl p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs bg-gray-700 px-2 py-1 rounded">{record.type}</span>
                                            {record.verified ? (
                                                <span className="text-xs text-green-400 flex items-center gap-1">
                                                    <CheckCircle className="w-3 h-3" /> Verified
                                                </span>
                                            ) : (
                                                <span className="text-xs text-yellow-400">Pending</span>
                                            )}
                                        </div>
                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                            <div>
                                                <p className="text-gray-300 text-xs mb-1">Name</p>
                                                <code className="text-white">{record.name}</code>
                                            </div>
                                            <div>
                                                <p className="text-gray-300 text-xs mb-1">Value</p>
                                                <code className="text-white break-all">{record.value}</code>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Add Domain Modal */}
                {showAddModal && (
                    <AddDomainModal
                        onClose={() => setShowAddModal(false)}
                        onAdd={handleAddDomain}
                    />
                )}
            </div>
        </main>
    );
}

function AddDomainModal({ onClose, onAdd }: { onClose: () => void; onAdd: (domain: string) => void }) {
    const [domain, setDomain] = useState("");
    const [error, setError] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Validate domain
        const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/;
        if (!domainRegex.test(domain)) {
            setError("Please enter a valid domain (e.g., app.example.com)");
            return;
        }

        onAdd(domain);
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-4">Add Custom Domain</h2>

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-sm text-gray-200 mb-1">Domain</label>
                        <input
                            type="text"
                            value={domain}
                            onChange={(e) => { setDomain(e.target.value); setError(""); }}
                            placeholder="app.example.com"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700 focus:border-purple-500 focus:outline-none"
                            autoFocus
                        />
                        {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
                    </div>

                    <p className="text-sm text-gray-300 mb-6">
                        After adding, you&apos;ll need to configure DNS records with your provider.
                    </p>

                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!domain}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-80"
                        >
                            Add Domain
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
