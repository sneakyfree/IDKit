"use client";

import { useState, useEffect } from "react";
import { Shield, FileText, Download, CheckCircle, AlertCircle, Clock, Loader2, ChevronRight } from "lucide-react";

/**
 * Compliance Reporting UI
 * 
 * Regulatory reports and compliance documentation
 */

interface ComplianceReport {
    id: string;
    name: string;
    type: "gdpr" | "ccpa" | "hipaa" | "sox" | "pci" | "audit";
    status: "compliant" | "warning" | "non-compliant" | "pending";
    lastGenerated?: string;
    nextDue?: string;
    findings: number;
    criticalFindings: number;
}

interface ComplianceCheck {
    id: string;
    category: string;
    name: string;
    status: "pass" | "warning" | "fail";
    description: string;
    recommendation?: string;
}

const MOCK_REPORTS: ComplianceReport[] = [
    {
        id: "1",
        name: "GDPR Compliance Report",
        type: "gdpr",
        status: "compliant",
        lastGenerated: "2024-01-15",
        nextDue: "2024-04-15",
        findings: 2,
        criticalFindings: 0,
    },
    {
        id: "2",
        name: "CCPA Privacy Assessment",
        type: "ccpa",
        status: "compliant",
        lastGenerated: "2024-01-10",
        nextDue: "2024-07-10",
        findings: 1,
        criticalFindings: 0,
    },
    {
        id: "3",
        name: "Security Audit Report",
        type: "audit",
        status: "warning",
        lastGenerated: "2024-01-05",
        findings: 5,
        criticalFindings: 1,
    },
    {
        id: "4",
        name: "PCI DSS Assessment",
        type: "pci",
        status: "pending",
        nextDue: "2024-02-01",
        findings: 0,
        criticalFindings: 0,
    },
];

const MOCK_CHECKS: ComplianceCheck[] = [
    { id: "1", category: "Data Protection", name: "Encryption at Rest", status: "pass", description: "All sensitive data is encrypted using AES-256" },
    { id: "2", category: "Data Protection", name: "Encryption in Transit", status: "pass", description: "TLS 1.3 enabled for all connections" },
    { id: "3", category: "Access Control", name: "MFA Enforcement", status: "pass", description: "Multi-factor authentication enabled for all admin accounts" },
    { id: "4", category: "Access Control", name: "Role-Based Access", status: "pass", description: "RBAC implemented with principle of least privilege" },
    { id: "5", category: "Audit", name: "Activity Logging", status: "warning", description: "Audit logs retained for 90 days", recommendation: "Extend retention to 1 year for SOC2 compliance" },
    { id: "6", category: "Privacy", name: "Data Retention Policy", status: "pass", description: "Automated data deletion after retention period" },
    { id: "7", category: "Privacy", name: "Consent Management", status: "pass", description: "Explicit consent collected and tracked" },
    { id: "8", category: "Security", name: "Vulnerability Scanning", status: "warning", description: "Last scan: 15 days ago", recommendation: "Schedule weekly automated scans" },
];

export default function ComplianceReportingPage() {
    const [reports, setReports] = useState<ComplianceReport[]>([]);
    const [checks, setChecks] = useState<ComplianceCheck[]>([]);
    const [selectedReport, setSelectedReport] = useState<ComplianceReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState<string | null>(null);

    useEffect(() => {
        setTimeout(() => {
            setReports(MOCK_REPORTS);
            setChecks(MOCK_CHECKS);
            setLoading(false);
        }, 800);
    }, []);

    const stats = {
        compliant: reports.filter(r => r.status === "compliant").length,
        warnings: reports.filter(r => r.status === "warning").length,
        pending: reports.filter(r => r.status === "pending").length,
        totalChecks: checks.length,
        passedChecks: checks.filter(c => c.status === "pass").length,
    };

    const handleGenerate = async (reportId: string) => {
        setGenerating(reportId);
        await new Promise(r => setTimeout(r, 2000));
        setReports(prev => prev.map(r =>
            r.id === reportId ? { ...r, lastGenerated: new Date().toISOString(), status: "compliant" as const } : r
        ));
        setGenerating(null);
    };

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Compliance Reporting</h1>
                        <p className="text-gray-400">Regulatory reports and compliance status</p>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-green-600/10 border border-green-500/20 rounded-xl p-4">
                        <CheckCircle className="w-6 h-6 text-green-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.compliant}</p>
                        <p className="text-sm text-gray-400">Compliant</p>
                    </div>
                    <div className="bg-yellow-600/10 border border-yellow-500/20 rounded-xl p-4">
                        <AlertCircle className="w-6 h-6 text-yellow-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.warnings}</p>
                        <p className="text-sm text-gray-400">Warnings</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <Clock className="w-6 h-6 text-gray-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.pending}</p>
                        <p className="text-sm text-gray-400">Pending</p>
                    </div>
                    <div className="bg-gray-900 rounded-xl p-4">
                        <Shield className="w-6 h-6 text-purple-400 mb-2" />
                        <p className="text-2xl font-bold">{stats.passedChecks}/{stats.totalChecks}</p>
                        <p className="text-sm text-gray-400">Checks Passed</p>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : (
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Reports */}
                        <div>
                            <h2 className="text-lg font-semibold mb-4">Compliance Reports</h2>
                            <div className="space-y-4">
                                {reports.map((report) => (
                                    <ReportCard
                                        key={report.id}
                                        report={report}
                                        generating={generating === report.id}
                                        onGenerate={() => handleGenerate(report.id)}
                                        onClick={() => setSelectedReport(report)}
                                    />
                                ))}
                            </div>
                        </div>

                        {/* Compliance Checks */}
                        <div>
                            <h2 className="text-lg font-semibold mb-4">Compliance Checks</h2>
                            <div className="bg-gray-900 rounded-xl overflow-hidden">
                                {Object.entries(
                                    checks.reduce((acc, check) => {
                                        if (!acc[check.category]) acc[check.category] = [];
                                        acc[check.category].push(check);
                                        return acc;
                                    }, {} as Record<string, ComplianceCheck[]>)
                                ).map(([category, categoryChecks]) => (
                                    <div key={category} className="border-b border-gray-800 last:border-0">
                                        <div className="px-4 py-3 bg-gray-800/50">
                                            <h3 className="font-medium text-sm">{category}</h3>
                                        </div>
                                        {categoryChecks.map((check) => (
                                            <div key={check.id} className="px-4 py-3 flex items-center justify-between">
                                                <div className="flex items-center gap-3">
                                                    <StatusIcon status={check.status} />
                                                    <div>
                                                        <p className="text-sm">{check.name}</p>
                                                        {check.recommendation && (
                                                            <p className="text-xs text-yellow-400">{check.recommendation}</p>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Report Detail Modal */}
                {selectedReport && (
                    <ReportDetailModal
                        report={selectedReport}
                        onClose={() => setSelectedReport(null)}
                    />
                )}
            </div>
        </main>
    );
}

function StatusIcon({ status }: { status: "pass" | "warning" | "fail" }) {
    if (status === "pass") return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (status === "warning") return <AlertCircle className="w-4 h-4 text-yellow-400" />;
    return <AlertCircle className="w-4 h-4 text-red-400" />;
}

function ReportCard({
    report,
    generating,
    onGenerate,
    onClick,
}: {
    report: ComplianceReport;
    generating: boolean;
    onGenerate: () => void;
    onClick: () => void;
}) {
    const statusConfig = {
        compliant: { color: "text-green-400 bg-green-400/10", icon: CheckCircle },
        warning: { color: "text-yellow-400 bg-yellow-400/10", icon: AlertCircle },
        "non-compliant": { color: "text-red-400 bg-red-400/10", icon: AlertCircle },
        pending: { color: "text-gray-400 bg-gray-400/10", icon: Clock },
    };

    const { color, icon: StatusIcon } = statusConfig[report.status];

    return (
        <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <h3 className="font-semibold">{report.name}</h3>
                    <p className="text-sm text-gray-500 uppercase">{report.type}</p>
                </div>
                <span className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${color}`}>
                    <StatusIcon className="w-3 h-3" />
                    {report.status}
                </span>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                {report.lastGenerated && (
                    <span>Last: {new Date(report.lastGenerated).toLocaleDateString()}</span>
                )}
                {report.nextDue && (
                    <span>Due: {new Date(report.nextDue).toLocaleDateString()}</span>
                )}
            </div>

            <div className="flex gap-2">
                <button
                    onClick={onGenerate}
                    disabled={generating}
                    className="flex-1 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                    {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                    {generating ? "Generating..." : "Generate"}
                </button>
                <button
                    onClick={onClick}
                    className="px-4 py-2 bg-gray-800 rounded-lg hover:bg-gray-700"
                >
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}

function ReportDetailModal({ report, onClose }: { report: ComplianceReport; onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold">{report.name}</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">×</button>
                </div>

                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-800 p-3 rounded-lg">
                            <p className="text-sm text-gray-500">Status</p>
                            <p className="font-medium capitalize">{report.status}</p>
                        </div>
                        <div className="bg-gray-800 p-3 rounded-lg">
                            <p className="text-sm text-gray-500">Type</p>
                            <p className="font-medium uppercase">{report.type}</p>
                        </div>
                        <div className="bg-gray-800 p-3 rounded-lg">
                            <p className="text-sm text-gray-500">Findings</p>
                            <p className="font-medium">{report.findings}</p>
                        </div>
                        <div className="bg-gray-800 p-3 rounded-lg">
                            <p className="text-sm text-gray-500">Critical</p>
                            <p className={`font-medium ${report.criticalFindings > 0 ? "text-red-400" : "text-green-400"}`}>
                                {report.criticalFindings}
                            </p>
                        </div>
                    </div>

                    <button className="w-full py-3 bg-purple-600 rounded-xl hover:bg-purple-700 flex items-center justify-center gap-2">
                        <Download className="w-4 h-4" />
                        Download Full Report
                    </button>
                </div>
            </div>
        </div>
    );
}
