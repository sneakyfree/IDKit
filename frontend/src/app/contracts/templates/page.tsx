"use client";

import { useState, useEffect } from "react";
import { FileText, Plus, Download, Copy, Edit, Trash2, Search, Loader2, CheckCircle, Star } from "lucide-react";
import { contractTemplatesApi } from "@/lib/api";

/**
 * Contract Templates UI
 * 
 * Pre-built contract templates for common agreements
 */

interface ContractTemplate {
    id: string;
    name: string;
    category: "sponsorship" | "collaboration" | "licensing" | "nda" | "general";
    description: string;
    popularity: number;
    isCustom: boolean;
    sections: TemplateSection[];
    createdAt: string;
    updatedAt?: string;
}

interface TemplateSection {
    id: string;
    title: string;
    content: string;
    required: boolean;
    variables: string[];
}

const TEMPLATE_CATEGORIES = [
    { id: "all", label: "All Templates" },
    { id: "sponsorship", label: "Sponsorship" },
    { id: "collaboration", label: "Collaboration" },
    { id: "licensing", label: "Licensing" },
    { id: "nda", label: "NDA" },
    { id: "general", label: "General" },
];



export default function ContractTemplatesPage() {
    const [templates, setTemplates] = useState<ContractTemplate[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [category, setCategory] = useState("all");
    const [selectedTemplate, setSelectedTemplate] = useState<ContractTemplate | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchTemplates() {
            try {
                setLoading(true);
                const response = await contractTemplatesApi.list();
                setTemplates((response.templates || []).map((t: any) => ({
                    id: t.id as string,
                    name: (t.name as string) || "Template",
                    category: (t.category as ContractTemplate["category"]) || "general",
                    description: (t.description as string) || "",
                    popularity: (t.usage_count as number) || 0,
                    isCustom: !!t.is_custom,
                    sections: (t.variables || []).map((v: any, idx: number) => ({
                        id: String(idx),
                        title: v.name as string || "Section",
                        content: "",
                        required: !!v.required,
                        variables: [v.name as string],
                    })),
                    createdAt: t.created_at as string || new Date().toISOString(),
                })));
            } catch {
                setTemplates([]);
            } finally {
                setLoading(false);
            }
        }
        fetchTemplates();
    }, []);

    const filteredTemplates = templates
        .filter(t => category === "all" || t.category === category)
        .filter(t =>
            searchQuery === "" ||
            t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            t.description.toLowerCase().includes(searchQuery.toLowerCase())
        );

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Contract Templates</h1>
                        <p className="text-gray-400">Pre-built templates for common agreements</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700">
                        <Plus className="w-5 h-5" />
                        Create Template
                    </button>
                </div>

                {/* Search and Filter */}
                <div className="flex gap-4 mb-6">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                        <input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search templates..."
                            className="w-full pl-10 pr-4 py-3 bg-gray-900 rounded-xl border border-gray-800 focus:border-purple-500"
                        />
                    </div>
                </div>

                {/* Categories */}
                <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                    {TEMPLATE_CATEGORIES.map((cat) => (
                        <button
                            key={cat.id}
                            onClick={() => setCategory(cat.id)}
                            className={`px-4 py-2 rounded-lg whitespace-nowrap ${category === cat.id ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {cat.label}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : filteredTemplates.length === 0 ? (
                    <div className="bg-gray-900 rounded-xl p-12 text-center">
                        <FileText className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                        <h3 className="text-lg font-medium mb-2">No templates found</h3>
                        <p className="text-gray-500">Try adjusting your search or category filter.</p>
                    </div>
                ) : (
                    <div className="grid md:grid-cols-2 gap-4">
                        {filteredTemplates.map((template) => (
                            <TemplateCard
                                key={template.id}
                                template={template}
                                onClick={() => setSelectedTemplate(template)}
                            />
                        ))}
                    </div>
                )}

                {/* Template Detail Modal */}
                {selectedTemplate && (
                    <TemplateDetailModal
                        template={selectedTemplate}
                        onClose={() => setSelectedTemplate(null)}
                        onUse={() => {
                            // Navigate to create contract with template
                            alert("Would open contract creation with this template");
                            setSelectedTemplate(null);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function TemplateCard({ template, onClick }: { template: ContractTemplate; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className="bg-gray-900 rounded-xl p-5 hover:bg-gray-800/50 transition-colors cursor-pointer"
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
                        <FileText className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold">{template.name}</h3>
                        <p className="text-sm text-gray-500 capitalize">{template.category}</p>
                    </div>
                </div>
                {template.isCustom && (
                    <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">
                        Custom
                    </span>
                )}
            </div>

            <p className="text-sm text-gray-400 mb-4">{template.description}</p>

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Star className="w-4 h-4 text-yellow-400" />
                    {template.popularity}% popular
                </div>
                <span className="text-xs text-gray-500">
                    {template.sections.length} sections
                </span>
            </div>
        </div>
    );
}

function TemplateDetailModal({
    template,
    onClose,
    onUse,
}: {
    template: ContractTemplate;
    onClose: () => void;
    onUse: () => void;
}) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold">{template.name}</h2>
                            <p className="text-gray-400 capitalize">{template.category}</p>
                        </div>
                        <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {/* Description */}
                    <div>
                        <p className="text-gray-300">{template.description}</p>
                    </div>

                    {/* Sections Preview */}
                    <div>
                        <h3 className="font-medium mb-3">Template Sections</h3>
                        <div className="space-y-2">
                            {template.sections.map((section) => (
                                <div key={section.id} className="p-3 bg-gray-800 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                        <h4 className="font-medium">{section.title}</h4>
                                        {section.required && (
                                            <span className="text-xs text-red-400">Required</span>
                                        )}
                                    </div>
                                    <p className="text-sm text-gray-500">{section.content.substring(0, 100)}...</p>
                                    {section.variables.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-2">
                                            {section.variables.map((v) => (
                                                <span key={v} className="text-xs bg-purple-600/20 text-purple-400 px-2 py-0.5 rounded">
                                                    {`{{${v}}}`}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            onClick={onUse}
                            className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 flex items-center justify-center gap-2"
                        >
                            <CheckCircle className="w-4 h-4" />
                            Use This Template
                        </button>
                        <button className="p-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            <Copy className="w-5 h-5" />
                        </button>
                        <button className="p-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            <Download className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
