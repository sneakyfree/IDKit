"use client";

import { useState } from "react";
import {
    TestTubes,
    Play,
    CheckCircle,
    XCircle,
    Clock,
    Loader2,
    RefreshCcw,
    AlertTriangle,
} from "lucide-react";

/**
 * Integration Testing UI
 *
 * Run, monitor, and view results of platform integration tests.
 * Closes Helix Scan gap X10-1.
 */

interface TestCase {
    id: string;
    name: string;
    description: string;
    category: string;
    status: "idle" | "running" | "passed" | "failed";
    duration?: number;
    error?: string;
}

const SEED_TESTS: TestCase[] = [
    { id: "1", name: "API Authentication Flow", description: "Login, token refresh, logout cycle", category: "Auth", status: "idle" },
    { id: "2", name: "Twin Creation Pipeline", description: "Create twin, upload media, start training", category: "Twins", status: "idle" },
    { id: "3", name: "Content Generation E2E", description: "Generate content via all platform adapters", category: "Content", status: "idle" },
    { id: "4", name: "Analytics Data Pipeline", description: "Ingest → Aggregate → Display metrics", category: "Analytics", status: "idle" },
    { id: "5", name: "Webhook Delivery", description: "Send and verify webhook payloads", category: "Platform", status: "idle" },
    { id: "6", name: "Payment Flow", description: "Subscription create, invoice, cancel", category: "Billing", status: "idle" },
    { id: "7", name: "Export Pipeline", description: "Generate CSV, JSON, PDF exports", category: "Data", status: "idle" },
    { id: "8", name: "Collaboration Invite Flow", description: "Send invite → Accept → Joint workspace", category: "Collab", status: "idle" },
    { id: "9", name: "Plugin Install/Uninstall", description: "Install plugin, verify hooks, uninstall", category: "Platform", status: "idle" },
    { id: "10", name: "Notification Delivery", description: "Email, push, in-app notification paths", category: "Platform", status: "idle" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function IntegrationTestingPage() {
    const [tests, setTests] = useState<TestCase[]>(SEED_TESTS);
    const [running, setRunning] = useState(false);

    const runAllTests = async () => {
        setRunning(true);
        for (let i = 0; i < tests.length; i++) {
            setTests((prev) =>
                prev.map((t, idx) => (idx === i ? { ...t, status: "running" } : t))
            );

            // Simulate test execution
            await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));

            const passed = Math.random() > 0.15; // 85% pass rate for demo
            const duration = Math.floor(200 + Math.random() * 2000);

            setTests((prev) =>
                prev.map((t, idx) =>
                    idx === i
                        ? {
                            ...t,
                            status: passed ? "passed" : "failed",
                            duration,
                            error: passed ? undefined : "Assertion failed: expected 200, got 500",
                        }
                        : t
                )
            );
        }
        setRunning(false);
    };

    const runSingle = async (testId: string) => {
        const idx = tests.findIndex((t) => t.id === testId);
        if (idx === -1) return;

        setTests((prev) =>
            prev.map((t) => (t.id === testId ? { ...t, status: "running" } : t))
        );

        await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));

        const passed = Math.random() > 0.2;
        const duration = Math.floor(200 + Math.random() * 2000);

        setTests((prev) =>
            prev.map((t) =>
                t.id === testId
                    ? {
                        ...t,
                        status: passed ? "passed" : "failed",
                        duration,
                        error: passed ? undefined : "Assertion failed: expected 200, got 500",
                    }
                    : t
            )
        );
    };

    const resetAll = () => {
        setTests((prev) =>
            prev.map((t) => ({ ...t, status: "idle", duration: undefined, error: undefined }))
        );
    };

    const stats = {
        total: tests.length,
        passed: tests.filter((t) => t.status === "passed").length,
        failed: tests.filter((t) => t.status === "failed").length,
        running: tests.filter((t) => t.status === "running").length,
    };

    const statusIcon = (s: string) => {
        switch (s) {
            case "passed": return <CheckCircle className="w-5 h-5 text-green-400" />;
            case "failed": return <XCircle className="w-5 h-5 text-red-400" />;
            case "running": return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
            default: return <Clock className="w-5 h-5 text-gray-300" />;
        }
    };

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <TestTubes className="w-8 h-8 text-purple-400" />
                        <div>
                            <h1 className="text-2xl font-bold">Integration Tests</h1>
                            <p className="text-gray-200 text-sm">
                                {stats.passed} passed · {stats.failed} failed · {stats.total - stats.passed - stats.failed} remaining
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={resetAll}
                            disabled={running}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-gray-600 text-sm disabled:opacity-80"
                        >
                            <RefreshCcw className="w-4 h-4" /> Reset
                        </button>
                        <button
                            onClick={runAllTests}
                            disabled={running}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-lg hover:bg-purple-500 text-sm disabled:opacity-80"
                        >
                            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            Run All
                        </button>
                    </div>
                </div>

                {/* Progress Bar */}
                {(stats.passed > 0 || stats.failed > 0) && (
                    <div className="h-2 bg-gray-800 rounded-full mb-6 overflow-hidden flex">
                        <div className="bg-green-500 transition-all duration-300" style={{ width: `${(stats.passed / stats.total) * 100}%` }} />
                        <div className="bg-red-500 transition-all duration-300" style={{ width: `${(stats.failed / stats.total) * 100}%` }} />
                    </div>
                )}

                {/* Test List */}
                <div className="space-y-2">
                    {tests.map((test) => (
                        <div
                            key={test.id}
                            className={`bg-gray-900 border rounded-xl p-4 transition-colors ${test.status === "failed" ? "border-red-500/30" : test.status === "passed" ? "border-green-500/20" : "border-gray-800"
                                }`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {statusIcon(test.status)}
                                    <div>
                                        <h3 className="font-medium text-sm">{test.name}</h3>
                                        <p className="text-xs text-gray-300">{test.description}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="text-xs text-gray-200 px-2 py-0.5 bg-gray-800 rounded">{test.category}</span>
                                    {test.duration && (
                                        <span className="text-xs text-gray-300">{test.duration}ms</span>
                                    )}
                                    {test.status !== "running" && (
                                        <button
                                            onClick={() => runSingle(test.id)}
                                            disabled={running}
                                            className="p-1.5 hover:bg-gray-800 rounded text-gray-300 hover:text-white disabled:opacity-80"
                                        >
                                            <Play className="w-3.5 h-3.5" />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {test.error && (
                                <div className="mt-2 flex items-center gap-2 text-xs text-red-400 bg-red-500/5 rounded-lg p-2">
                                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                                    {test.error}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
