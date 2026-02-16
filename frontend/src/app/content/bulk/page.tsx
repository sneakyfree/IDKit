"use client";

import { useState, useCallback, useEffect } from "react";
import { Upload, FileText, Loader2, Download, AlertCircle, CheckCircle } from "lucide-react";

/**
 * Bulk Content Generation UI
 * 
 * A 4-step wizard for generating 10-100 pieces of content from CSV/templates
 */

interface Template {
    id: string;
    name: string;
    description: string;
    variables: string[];
}

interface BulkJob {
    id: string;
    status: "pending" | "processing" | "completed" | "failed";
    total: number;
    completed: number;
    errors: { row: number; message: string }[];
}

export default function BulkGenerationPage() {
    const [step, setStep] = useState(1);
    const [templates, setTemplates] = useState<Template[]>([]);
    const [templatesLoading, setTemplatesLoading] = useState(true);
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
    const [csvData, setCsvData] = useState<string[][]>([]);
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [previews, setPreviews] = useState<string[]>([]);
    const [job, setJob] = useState<BulkJob | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load templates from API on mount
    useEffect(() => {
        const loadTemplates = async () => {
            setTemplatesLoading(true);
            try {
                const token = localStorage.getItem("token");
                const headers: Record<string, string> = {};
                if (token) headers["Authorization"] = `Bearer ${token}`;

                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/content/templates`,
                    { headers }
                );
                if (response.ok) {
                    const data = await response.json();
                    setTemplates(Array.isArray(data) ? data : (data.templates || []));
                } else {
                    setTemplates([]);
                }
            } catch {
                setTemplates([]);
            } finally {
                setTemplatesLoading(false);
            }
        };
        loadTemplates();
    }, []);

    // Step 1: Select Template
    const handleSelectTemplate = (template: Template) => {
        setSelectedTemplate(template);
        setStep(2);
    };

    // Step 2: Upload CSV
    const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (file.size > 10 * 1024 * 1024) {
            setError("File size must be less than 10MB");
            return;
        }

        setCsvFile(file);
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target?.result as string;
            const rows = text.split("\n").map(row => row.split(",").map(cell => cell.trim()));
            setCsvData(rows);
            setError(null);
        };
        reader.readAsText(file);
    }, []);

    // Step 3: Generate Previews
    const handleGeneratePreviews = async () => {
        if (!selectedTemplate || csvData.length < 2) return;

        setLoading(true);
        try {
            // Simulate API call for preview generation
            await new Promise(resolve => setTimeout(resolve, 1500));
            const samplePreviews = csvData.slice(1, 4).map((row, i) =>
                `Preview ${i + 1}: Generated content for "${row[0] || 'item'}" using ${selectedTemplate.name} template.`
            );
            setPreviews(samplePreviews);
            setStep(3);
        } catch (err) {
            setError("Failed to generate previews. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    // Step 4: Start Generation
    const handleStartGeneration = async () => {
        if (!selectedTemplate || csvData.length < 2) return;

        setLoading(true);
        setStep(4);

        try {
            // Simulate API call to start bulk generation
            const response = await fetch("/api/v1/content/bulk-generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify({
                    template_id: selectedTemplate.id,
                    data: csvData.slice(1), // Skip header row
                }),
            });

            if (!response.ok) throw new Error("Generation failed");

            const jobData: BulkJob = await response.json();
            setJob(jobData);

            // Poll for progress (in real app, use WebSocket)
            pollJobStatus(jobData.id);
        } catch (err) {
            setError("Failed to start generation. Please try again.");
            setLoading(false);
        }
    };

    const pollJobStatus = async (jobId: string) => {
        // Simulate progress updates
        let progress = 0;
        const total = csvData.length - 1;

        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 10) + 5;
            if (progress >= total) {
                progress = total;
                clearInterval(interval);
                setJob(prev => prev ? { ...prev, status: "completed", completed: total } : null);
                setLoading(false);
            } else {
                setJob(prev => prev ? { ...prev, status: "processing", completed: progress } : null);
            }
        }, 2000);
    };

    const handleDownloadResults = () => {
        // Trigger download of generated content
        alert("Download started! (In production, this would download a ZIP file)");
    };

    const handleCancel = () => {
        setJob(prev => prev ? { ...prev, status: "failed" } : null);
        setLoading(false);
    };

    const handleReset = () => {
        setStep(1);
        setSelectedTemplate(null);
        setCsvData([]);
        setCsvFile(null);
        setPreviews([]);
        setJob(null);
        setError(null);
        setLoading(false);
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            {/* Header */}
            <div className="max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold mb-2">Bulk Content Generation</h1>
                <p className="text-gray-400 mb-8">Generate 10-100 pieces of content from a template and CSV data</p>

                {/* Step Indicator */}
                <div className="flex items-center gap-2 mb-8" role="progressbar" aria-valuenow={step} aria-valuemin={1} aria-valuemax={4}>
                    {[1, 2, 3, 4].map((s) => (
                        <div key={s} className="flex items-center">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step >= s ? "bg-purple-600 text-white" : "bg-gray-800 text-gray-500"
                                }`}>
                                {step > s ? <CheckCircle className="w-4 h-4" /> : s}
                            </div>
                            {s < 4 && <div className={`w-12 h-1 mx-2 ${step > s ? "bg-purple-600" : "bg-gray-800"}`} />}
                        </div>
                    ))}
                    <span className="ml-4 text-sm text-gray-400">
                        {step === 1 && "Select Template"}
                        {step === 2 && "Upload Data"}
                        {step === 3 && "Preview"}
                        {step === 4 && "Generate"}
                    </span>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-6 flex items-center gap-3" role="alert">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-300">{error}</p>
                        <button
                            onClick={() => setError(null)}
                            className="ml-auto text-red-400 hover:text-red-300"
                            aria-label="Dismiss error"
                        >
                            ×
                        </button>
                    </div>
                )}

                {/* Step 1: Select Template */}
                {step === 1 && (
                    <section aria-labelledby="template-heading">
                        <h2 id="template-heading" className="text-lg font-semibold mb-4">Select a Template</h2>
                        {templatesLoading ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                            </div>
                        ) : templates.length === 0 ? (
                            <div className="bg-gray-900 rounded-xl p-8 text-center">
                                <FileText className="w-12 h-12 mx-auto text-gray-600 mb-4" />
                                <p className="text-gray-400 mb-4">No templates available</p>
                                <a href="/content/templates/new" className="text-purple-400 hover:text-purple-300">
                                    Create your first template →
                                </a>
                            </div>
                        ) : (
                            <div className="grid gap-4">
                                {templates.map((template: Template) => (
                                    <button
                                        key={template.id}
                                        onClick={() => handleSelectTemplate(template)}
                                        className="bg-gray-900 hover:bg-gray-800 rounded-xl p-5 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    >
                                        <h3 className="font-semibold mb-1">{template.name}</h3>
                                        <p className="text-sm text-gray-400 mb-2">{template.description}</p>
                                        <div className="flex flex-wrap gap-2">
                                            {template.variables.map((v) => (
                                                <span key={v} className="text-xs bg-gray-800 px-2 py-1 rounded">{v}</span>
                                            ))}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </section>
                )}

                {/* Step 2: Upload CSV */}
                {step === 2 && (
                    <section aria-labelledby="upload-heading">
                        <h2 id="upload-heading" className="text-lg font-semibold mb-4">Upload Your Data</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            Upload a CSV with columns: {selectedTemplate?.variables.join(", ")}
                        </p>

                        <div className="bg-gray-900 rounded-xl p-8 border-2 border-dashed border-gray-700 hover:border-purple-500 transition-colors text-center">
                            <input
                                type="file"
                                accept=".csv"
                                onChange={handleFileUpload}
                                className="hidden"
                                id="csv-upload"
                                aria-describedby="file-requirements"
                            />
                            <label htmlFor="csv-upload" className="cursor-pointer block">
                                <Upload className="w-12 h-12 mx-auto text-gray-500 mb-4" />
                                {csvFile ? (
                                    <p className="text-green-400">{csvFile.name} ({csvData.length - 1} rows)</p>
                                ) : (
                                    <>
                                        <p className="text-gray-300 mb-2">Drag and drop or click to upload</p>
                                        <p id="file-requirements" className="text-sm text-gray-500">CSV files only, max 10MB</p>
                                    </>
                                )}
                            </label>
                        </div>

                        {csvData.length > 1 && (
                            <div className="mt-6">
                                <h3 className="text-sm font-medium mb-2">Data Preview (first 3 rows)</h3>
                                <div className="bg-gray-900 rounded-lg overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-gray-800">
                                                {csvData[0]?.map((header, i) => (
                                                    <th key={i} className="px-4 py-2 text-left text-gray-400">{header}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {csvData.slice(1, 4).map((row, i) => (
                                                <tr key={i} className="border-b border-gray-800">
                                                    {row.map((cell, j) => (
                                                        <td key={j} className="px-4 py-2">{cell}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        <div className="flex gap-4 mt-8">
                            <button
                                onClick={() => setStep(1)}
                                className="px-6 py-3 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleGeneratePreviews}
                                disabled={csvData.length < 2 || loading}
                                className="flex-1 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : null}
                                Generate Previews
                            </button>
                        </div>
                    </section>
                )}

                {/* Step 3: Preview */}
                {step === 3 && (
                    <section aria-labelledby="preview-heading">
                        <h2 id="preview-heading" className="text-lg font-semibold mb-4">Preview Generated Content</h2>
                        <p className="text-sm text-gray-400 mb-4">
                            Review these samples before generating all {csvData.length - 1} items
                        </p>

                        <div className="space-y-4">
                            {previews.map((preview, i) => (
                                <div key={i} className="bg-gray-900 rounded-xl p-5">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-xs bg-purple-600 px-2 py-0.5 rounded">Sample {i + 1}</span>
                                    </div>
                                    <p className="text-gray-300">{preview}</p>
                                </div>
                            ))}
                        </div>

                        <div className="flex gap-4 mt-8">
                            <button
                                onClick={() => setStep(2)}
                                className="px-6 py-3 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleStartGeneration}
                                disabled={loading}
                                className="flex-1 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50 transition-colors"
                            >
                                Generate All ({csvData.length - 1} items)
                            </button>
                        </div>
                    </section>
                )}

                {/* Step 4: Progress & Results */}
                {step === 4 && (
                    <section aria-labelledby="progress-heading">
                        <h2 id="progress-heading" className="text-lg font-semibold mb-4">
                            {job?.status === "completed" ? "Generation Complete!" : "Generating Content..."}
                        </h2>

                        {job && (
                            <div className="bg-gray-900 rounded-xl p-8">
                                {/* Progress Ring */}
                                <div className="flex flex-col items-center mb-6">
                                    <div className="relative w-32 h-32">
                                        <svg className="w-full h-full -rotate-90">
                                            <circle
                                                cx="64"
                                                cy="64"
                                                r="56"
                                                stroke="currentColor"
                                                strokeWidth="8"
                                                fill="none"
                                                className="text-gray-800"
                                            />
                                            <circle
                                                cx="64"
                                                cy="64"
                                                r="56"
                                                stroke="currentColor"
                                                strokeWidth="8"
                                                fill="none"
                                                strokeDasharray={2 * Math.PI * 56}
                                                strokeDashoffset={2 * Math.PI * 56 * (1 - job.completed / job.total)}
                                                className="text-purple-500 transition-all duration-500"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="text-2xl font-bold">
                                                {Math.round((job.completed / job.total) * 100)}%
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-gray-400 mt-4">
                                        {job.completed} / {job.total} items
                                    </p>
                                    {job.status === "processing" && (
                                        <p className="text-sm text-gray-500">
                                            Estimated time: {Math.ceil((job.total - job.completed) / 5)} minutes
                                        </p>
                                    )}
                                </div>

                                {/* Actions */}
                                <div className="flex gap-4 justify-center">
                                    {job.status === "processing" && (
                                        <button
                                            onClick={handleCancel}
                                            className="px-6 py-3 bg-red-600 rounded-xl hover:bg-red-700 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                    )}
                                    {job.status === "completed" && (
                                        <>
                                            <button
                                                onClick={handleDownloadResults}
                                                className="px-6 py-3 bg-green-600 rounded-xl hover:bg-green-700 transition-colors flex items-center gap-2"
                                            >
                                                <Download className="w-5 h-5" />
                                                Download Results (ZIP)
                                            </button>
                                            <button
                                                onClick={handleReset}
                                                className="px-6 py-3 bg-gray-800 rounded-xl hover:bg-gray-700 transition-colors"
                                            >
                                                Start New Batch
                                            </button>
                                        </>
                                    )}
                                    {job.status === "failed" && (
                                        <button
                                            onClick={handleReset}
                                            className="px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 transition-colors"
                                        >
                                            Try Again
                                        </button>
                                    )}
                                </div>

                                {/* Error List */}
                                {job.errors.length > 0 && (
                                    <div className="mt-6 border-t border-gray-800 pt-4">
                                        <h3 className="text-sm font-medium text-red-400 mb-2">
                                            {job.errors.length} items failed
                                        </h3>
                                        <ul className="space-y-1 text-sm text-gray-400">
                                            {job.errors.slice(0, 5).map((err, i) => (
                                                <li key={i}>Row {err.row}: {err.message}</li>
                                            ))}
                                            {job.errors.length > 5 && (
                                                <li>...and {job.errors.length - 5} more errors</li>
                                            )}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        )}
                    </section>
                )}
            </div>
        </main>
    );
}
