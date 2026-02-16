"use client";

import { useState, useEffect } from "react";
import { FileText, Download, AlertCircle, CheckCircle, Clock, Calendar, Loader2, DollarSign } from "lucide-react";
import { taxApi } from "@/lib/api";

/**
 * Tax Documentation UI
 * 
 * Tax forms and compliance documentation for creators
 */

interface TaxDocument {
    id: string;
    type: "1099-NEC" | "1099-K" | "W-9" | "Summary";
    year: number;
    status: "available" | "processing" | "pending";
    amount?: number;
    generatedAt?: string;
    downloadUrl?: string;
}

interface TaxInfo {
    taxId: string;
    taxIdType: "SSN" | "EIN";
    businessName?: string;
    businessType: "individual" | "llc" | "corporation" | "partnership";
    address: {
        street: string;
        city: string;
        state: string;
        zip: string;
        country: string;
    };
}



export default function TaxDocumentsPage() {
    const [documents, setDocuments] = useState<TaxDocument[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
    const [showTaxInfo, setShowTaxInfo] = useState(false);
    const [taxInfo, setTaxInfo] = useState<TaxInfo | null>(null);

    const years = [2026, 2025, 2024, 2023];

    useEffect(() => {
        async function fetchTaxData() {
            try {
                setLoading(true);
                const [docsResp, profileResp] = await Promise.all([
                    taxApi.listDocuments(),
                    taxApi.getTaxInfo().catch(() => null),
                ]);
                setDocuments((docsResp.documents || []).map((d: any) => ({
                    id: d.id as string,
                    type: (d.document_type as TaxDocument["type"]) || "Summary",
                    year: (d.tax_year as number) || new Date().getFullYear(),
                    status: (d.status as TaxDocument["status"]) || "pending",
                    amount: d.amount_cents ? (d.amount_cents as number) / 100 : undefined,
                    generatedAt: d.generated_at as string,
                    downloadUrl: d.download_url as string,
                })));
                if (profileResp) {
                    setTaxInfo({
                        taxId: (profileResp as any).tax_id_masked || "***-**-****",
                        taxIdType: ((profileResp as any).tax_id_type || "SSN") as TaxInfo["taxIdType"],
                        businessType: ((profileResp as any).business_type || "individual") as TaxInfo["businessType"],
                        address: {
                            street: (profileResp as any).address?.street || "",
                            city: (profileResp as any).address?.city || "",
                            state: (profileResp as any).address?.state || "",
                            zip: (profileResp as any).address?.zip || "",
                            country: (profileResp as any).address?.country || "United States",
                        },
                    });
                }
            } catch {
                setDocuments([]);
            } finally {
                setLoading(false);
            }
        }
        fetchTaxData();
    }, []);

    const filteredDocs = documents.filter(d => d.year === selectedYear);
    const totalEarnings = filteredDocs.reduce((sum, d) => sum + (d.amount || 0), 0);

    const getDocumentTypeLabel = (type: TaxDocument["type"]) => {
        const labels = {
            "1099-NEC": "Form 1099-NEC",
            "1099-K": "Form 1099-K",
            "W-9": "Form W-9",
            "Summary": "Annual Summary",
        };
        return labels[type];
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Tax Documents</h1>
                        <p className="text-gray-400">Download tax forms and earnings summaries</p>
                    </div>
                    <button
                        onClick={() => setShowTaxInfo(true)}
                        className="px-4 py-2 bg-gray-800 rounded-xl hover:bg-gray-700"
                    >
                        Tax Info
                    </button>
                </div>

                {/* Year Selector */}
                <div className="flex gap-2 mb-6">
                    {years.map((year) => (
                        <button
                            key={year}
                            onClick={() => setSelectedYear(year)}
                            className={`px-4 py-2 rounded-lg ${selectedYear === year ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {year}
                        </button>
                    ))}
                </div>

                {/* Summary Card */}
                <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 rounded-2xl p-6 mb-6 border border-purple-500/20">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-gray-400">Total Earnings ({selectedYear})</p>
                            <p className="text-3xl font-bold">${totalEarnings.toLocaleString()}</p>
                        </div>
                        <DollarSign className="w-12 h-12 text-purple-400 opacity-50" />
                    </div>
                </div>

                {/* Loading */}
                {loading && (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                )}

                {/* Documents */}
                {!loading && (
                    <div className="space-y-4">
                        {filteredDocs.length === 0 ? (
                            <div className="bg-gray-900 rounded-xl p-8 text-center">
                                <FileText className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                                <p className="text-gray-500">No tax documents for {selectedYear}</p>
                                <p className="text-sm text-gray-600 mt-2">
                                    Tax documents are generated after year-end processing
                                </p>
                            </div>
                        ) : (
                            filteredDocs.map((doc) => (
                                <div
                                    key={doc.id}
                                    className="bg-gray-900 rounded-xl p-5 flex items-center justify-between"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center">
                                            <FileText className="w-6 h-6 text-purple-400" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">{getDocumentTypeLabel(doc.type)}</h3>
                                            <div className="flex items-center gap-4 text-sm text-gray-500">
                                                <span>Tax Year {doc.year}</span>
                                                {doc.amount && (
                                                    <span className="text-green-400">
                                                        ${doc.amount.toLocaleString()}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <StatusBadge status={doc.status} />
                                        {doc.status === "available" && (
                                            <a
                                                href={doc.downloadUrl}
                                                className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-700"
                                            >
                                                <Download className="w-4 h-4" />
                                                Download
                                            </a>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {/* Notice */}
                <div className="mt-8 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                    <div className="flex gap-3">
                        <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm">
                            <p className="font-medium text-yellow-400">Important Tax Information</p>
                            <p className="text-gray-400 mt-1">
                                Tax documents are typically available by January 31st for the previous tax year.
                                Consult a tax professional for advice on your specific situation.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Tax Info Modal */}
                {showTaxInfo && taxInfo && (
                    <TaxInfoModal
                        taxInfo={taxInfo}
                        onClose={() => setShowTaxInfo(false)}
                        onUpdate={setTaxInfo}
                    />
                )}
            </div>
        </main>
    );
}

function StatusBadge({ status }: { status: TaxDocument["status"] }) {
    const config = {
        available: { icon: CheckCircle, text: "Available", color: "text-green-400 bg-green-400/10" },
        processing: { icon: Loader2, text: "Processing", color: "text-yellow-400 bg-yellow-400/10" },
        pending: { icon: Clock, text: "Pending", color: "text-gray-400 bg-gray-400/10" },
    };

    const { icon: Icon, text, color } = config[status];

    return (
        <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${color}`}>
            <Icon className={`w-3 h-3 ${status === "processing" ? "animate-spin" : ""}`} />
            {text}
        </span>
    );
}

function TaxInfoModal({
    taxInfo,
    onClose,
    onUpdate,
}: {
    taxInfo: TaxInfo;
    onClose: () => void;
    onUpdate: (info: TaxInfo) => void;
}) {
    const [editing, setEditing] = useState(false);
    const [formData, setFormData] = useState(taxInfo);

    const handleSave = async () => {
        // API call would go here
        onUpdate(formData);
        setEditing(false);
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">Tax Information</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Tax ID Type</label>
                        <p className="text-lg">{formData.taxIdType}</p>
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Tax ID</label>
                        <p className="text-lg">{formData.taxId}</p>
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Business Type</label>
                        <p className="text-lg capitalize">{formData.businessType}</p>
                    </div>
                    <div>
                        <label className="block text-sm text-gray-400 mb-1">Address</label>
                        <div className="text-gray-300">
                            <p>{formData.address.street}</p>
                            <p>{formData.address.city}, {formData.address.state} {formData.address.zip}</p>
                            <p>{formData.address.country}</p>
                        </div>
                    </div>
                </div>

                <div className="flex gap-4 mt-6 pt-6 border-t border-gray-800">
                    <button
                        onClick={onClose}
                        className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700"
                    >
                        Close
                    </button>
                    <button
                        onClick={() => setEditing(true)}
                        className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        Update Info
                    </button>
                </div>
            </div>
        </div>
    );
}
