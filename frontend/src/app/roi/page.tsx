"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { BottomNav } from "@/components/nav/BottomNav";
import {
    roi,
    ROISummaryResponse,
    ROIReportResponse,
    CostEntryListResponse,
} from "@/lib/api";

export default function ROICalculatorPage() {
    const [summary, setSummary] = useState<ROISummaryResponse | null>(null);
    const [history, setHistory] = useState<ROIReportResponse[]>([]);
    const [costs, setCosts] = useState<CostEntryListResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"overview" | "costs" | "history">("overview");
    const [showAddCost, setShowAddCost] = useState(false);
    const [newCost, setNewCost] = useState({
        amount: "",
        category: "software",
        description: "",
        date: new Date().toISOString().split("T")[0],
    });

    const loadData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [summaryData, historyData, costsData] = await Promise.all([
                roi.getSummary().catch(() => null),
                roi.getHistory(12).catch(() => []),
                roi.getCosts().catch(() => null),
            ]);
            setSummary(summaryData);
            setHistory(historyData);
            setCosts(costsData);
        } catch (err) {
            console.error("Failed to load ROI data:", err);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const formatCurrency = (cents: number) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
        }).format(cents / 100);
    };

    const formatPercent = (value: number) => {
        const sign = value >= 0 ? "+" : "";
        return `${sign}${value.toFixed(1)}%`;
    };

    const handleAddCost = async () => {
        if (!newCost.amount || parseFloat(newCost.amount) <= 0) return;

        try {
            await roi.addCost({
                amount_cents: Math.round(parseFloat(newCost.amount) * 100),
                category: newCost.category,
                description: newCost.description || undefined,
                expense_date: newCost.date,
            });
            setShowAddCost(false);
            setNewCost({
                amount: "",
                category: "software",
                description: "",
                date: new Date().toISOString().split("T")[0],
            });
            loadData();
        } catch (err) {
            console.error("Failed to add cost:", err);
        }
    };

    const handleDeleteCost = async (id: string) => {
        try {
            await roi.deleteCost(id);
            loadData();
        } catch (err) {
            console.error("Failed to delete cost:", err);
        }
    };

    const current = summary?.current_period;
    const previous = summary?.previous_period;

    return (
        <main className="min-h-screen bg-black pb-20">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
                <div className="flex items-center gap-3 px-4 py-3">
                    <Link href="/analytics" className="text-gray-400 hover:text-white">
                        <BackIcon className="w-6 h-6" />
                    </Link>
                    <h1 className="text-xl font-bold">ROI Calculator</h1>
                </div>
                {/* Tabs */}
                <div className="flex border-b border-gray-800">
                    {(["overview", "costs", "history"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 py-3 text-sm font-medium capitalize transition-colors ${activeTab === tab
                                    ? "text-purple-400 border-b-2 border-purple-400"
                                    : "text-gray-500 hover:text-gray-300"
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>
            </header>

            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
                </div>
            ) : (
                <div className="p-4 space-y-6">
                    {/* Overview Tab */}
                    {activeTab === "overview" && (
                        <>
                            {/* Key Metrics */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gradient-to-br from-green-900/40 to-green-800/20 rounded-2xl p-4 border border-green-500/30">
                                    <p className="text-gray-400 text-sm">Revenue</p>
                                    <p className="text-2xl font-bold text-green-400">
                                        {formatCurrency(current?.revenue.total || 0)}
                                    </p>
                                    {summary && (
                                        <p className={`text-xs mt-1 ${summary.revenue_change_percent >= 0 ? "text-green-400" : "text-red-400"
                                            }`}>
                                            {formatPercent(summary.revenue_change_percent)} vs last month
                                        </p>
                                    )}
                                </div>
                                <div className="bg-gradient-to-br from-red-900/40 to-red-800/20 rounded-2xl p-4 border border-red-500/30">
                                    <p className="text-gray-400 text-sm">Costs</p>
                                    <p className="text-2xl font-bold text-red-400">
                                        {formatCurrency(current?.costs.total || 0)}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-1">This period</p>
                                </div>
                                <div className="bg-gradient-to-br from-purple-900/40 to-purple-800/20 rounded-2xl p-4 border border-purple-500/30">
                                    <p className="text-gray-400 text-sm">Net Profit</p>
                                    <p className={`text-2xl font-bold ${(current?.metrics.net_profit_cents || 0) >= 0 ? "text-green-400" : "text-red-400"
                                        }`}>
                                        {formatCurrency(current?.metrics.net_profit_cents || 0)}
                                    </p>
                                    {summary && (
                                        <p className={`text-xs mt-1 ${summary.profit_change_percent >= 0 ? "text-green-400" : "text-red-400"
                                            }`}>
                                            {formatPercent(summary.profit_change_percent)} vs last month
                                        </p>
                                    )}
                                </div>
                                <div className="bg-gradient-to-br from-blue-900/40 to-blue-800/20 rounded-2xl p-4 border border-blue-500/30">
                                    <p className="text-gray-400 text-sm">ROI</p>
                                    <p className="text-2xl font-bold text-blue-400">
                                        {current?.metrics.roi_percentage.toFixed(1) || 0}%
                                    </p>
                                    <p className={`text-xs mt-1 ${(summary?.roi_change_percent || 0) >= 0 ? "text-green-400" : "text-red-400"
                                        }`}>
                                        {formatPercent(summary?.roi_change_percent || 0)} vs last month
                                    </p>
                                </div>
                            </div>

                            {/* Revenue Breakdown */}
                            <section className="bg-gray-900 rounded-2xl p-5">
                                <h2 className="text-lg font-semibold mb-4">Revenue Breakdown</h2>
                                <div className="space-y-3">
                                    {[
                                        { label: "Brand Deals", value: current?.revenue.brand_deals || 0, color: "bg-purple-500" },
                                        { label: "Affiliate", value: current?.revenue.affiliate || 0, color: "bg-blue-500" },
                                        { label: "Subscriptions", value: current?.revenue.subscriptions || 0, color: "bg-green-500" },
                                        { label: "Royalties", value: current?.revenue.royalties || 0, color: "bg-yellow-500" },
                                        { label: "Other", value: current?.revenue.other || 0, color: "bg-gray-500" },
                                    ].map((item) => {
                                        const total = current?.revenue.total || 1;
                                        const percent = (item.value / total) * 100;
                                        return (
                                            <div key={item.label}>
                                                <div className="flex justify-between text-sm mb-1">
                                                    <span className="text-gray-400">{item.label}</span>
                                                    <span>{formatCurrency(item.value)}</span>
                                                </div>
                                                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${item.color} transition-all`}
                                                        style={{ width: `${Math.min(percent, 100)}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </section>

                            {/* Performance Metrics */}
                            <section className="bg-gray-900 rounded-2xl p-5">
                                <h2 className="text-lg font-semibold mb-4">Performance Metrics</h2>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="text-center p-3 bg-gray-800 rounded-xl">
                                        <p className="text-2xl font-bold">{current?.content_pieces || 0}</p>
                                        <p className="text-xs text-gray-500">Content Pieces</p>
                                    </div>
                                    <div className="text-center p-3 bg-gray-800 rounded-xl">
                                        <p className="text-2xl font-bold">
                                            {formatCurrency(current?.metrics.revenue_per_content || 0)}
                                        </p>
                                        <p className="text-xs text-gray-500">Revenue per Content</p>
                                    </div>
                                    <div className="text-center p-3 bg-gray-800 rounded-xl">
                                        <p className="text-2xl font-bold">
                                            {(current?.metrics.profit_margin || 0).toFixed(1)}%
                                        </p>
                                        <p className="text-xs text-gray-500">Profit Margin</p>
                                    </div>
                                    <div className="text-center p-3 bg-gray-800 rounded-xl">
                                        <p className="text-2xl font-bold">
                                            {(current?.metrics.engagement_rate || 0).toFixed(1)}%
                                        </p>
                                        <p className="text-xs text-gray-500">Engagement Rate</p>
                                    </div>
                                </div>
                            </section>
                        </>
                    )}

                    {/* Costs Tab */}
                    {activeTab === "costs" && (
                        <>
                            {/* Add Cost Button */}
                            <button
                                onClick={() => setShowAddCost(true)}
                                className="w-full py-3 bg-purple-600 hover:bg-purple-700 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                            >
                                <PlusIcon className="w-5 h-5" />
                                Add Expense
                            </button>

                            {/* Costs Summary */}
                            {costs && (
                                <section className="bg-gray-900 rounded-2xl p-5">
                                    <div className="flex justify-between items-center mb-4">
                                        <h2 className="text-lg font-semibold">Total Expenses</h2>
                                        <span className="text-xl font-bold text-red-400">
                                            {formatCurrency(costs.total_cents)}
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {Object.entries(costs.by_category).map(([category, amount]) => (
                                            <div key={category} className="flex justify-between text-sm">
                                                <span className="text-gray-400 capitalize">{category.replace("_", " ")}</span>
                                                <span>{formatCurrency(amount)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Cost Entries */}
                            <section className="bg-gray-900 rounded-2xl overflow-hidden">
                                <div className="p-4 border-b border-gray-800">
                                    <h2 className="font-semibold">Recent Expenses</h2>
                                </div>
                                {costs?.entries.length === 0 ? (
                                    <div className="p-8 text-center text-gray-500">
                                        No expenses recorded yet
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-800">
                                        {costs?.entries.map((entry) => (
                                            <div key={entry.id} className="flex items-center justify-between p-4">
                                                <div>
                                                    <p className="font-medium capitalize">
                                                        {entry.category.replace("_", " ")}
                                                    </p>
                                                    {entry.description && (
                                                        <p className="text-sm text-gray-500">{entry.description}</p>
                                                    )}
                                                    <p className="text-xs text-gray-600">
                                                        {new Date(entry.expense_date).toLocaleDateString()}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="font-medium text-red-400">
                                                        -{formatCurrency(entry.amount_cents)}
                                                    </span>
                                                    <button
                                                        onClick={() => handleDeleteCost(entry.id)}
                                                        className="p-1 text-gray-500 hover:text-red-400"
                                                    >
                                                        <TrashIcon className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        </>
                    )}

                    {/* History Tab */}
                    {activeTab === "history" && (
                        <section className="space-y-4">
                            {history.length === 0 ? (
                                <div className="bg-gray-900 rounded-2xl p-8 text-center text-gray-500">
                                    No historical data yet
                                </div>
                            ) : (
                                history.map((report) => (
                                    <div key={report.id} className="bg-gray-900 rounded-2xl p-4">
                                        <div className="flex justify-between items-center mb-3">
                                            <p className="text-sm text-gray-400">
                                                {new Date(report.period_start).toLocaleDateString()} -{" "}
                                                {new Date(report.period_end).toLocaleDateString()}
                                            </p>
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${report.metrics.roi_percentage >= 0
                                                    ? "bg-green-500/20 text-green-400"
                                                    : "bg-red-500/20 text-red-400"
                                                }`}>
                                                ROI: {report.metrics.roi_percentage.toFixed(1)}%
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-4 text-center">
                                            <div>
                                                <p className="text-lg font-bold text-green-400">
                                                    {formatCurrency(report.revenue.total)}
                                                </p>
                                                <p className="text-xs text-gray-500">Revenue</p>
                                            </div>
                                            <div>
                                                <p className="text-lg font-bold text-red-400">
                                                    {formatCurrency(report.costs.total)}
                                                </p>
                                                <p className="text-xs text-gray-500">Costs</p>
                                            </div>
                                            <div>
                                                <p className={`text-lg font-bold ${report.metrics.net_profit_cents >= 0 ? "text-green-400" : "text-red-400"
                                                    }`}>
                                                    {formatCurrency(report.metrics.net_profit_cents)}
                                                </p>
                                                <p className="text-xs text-gray-500">Profit</p>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </section>
                    )}
                </div>
            )}

            {/* Add Cost Modal */}
            {showAddCost && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
                    <div className="bg-gray-900 rounded-2xl w-full max-w-md p-6">
                        <h2 className="text-xl font-bold mb-4">Add Expense</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Amount</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                                    <input
                                        type="number"
                                        value={newCost.amount}
                                        onChange={(e) => setNewCost({ ...newCost, amount: e.target.value })}
                                        placeholder="0.00"
                                        className="w-full pl-7 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 focus:outline-none"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Category</label>
                                <select
                                    value={newCost.category}
                                    onChange={(e) => setNewCost({ ...newCost, category: e.target.value })}
                                    className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 focus:outline-none"
                                >
                                    <option value="software">Software</option>
                                    <option value="equipment">Equipment</option>
                                    <option value="advertising">Advertising</option>
                                    <option value="content_creation">Content Creation</option>
                                    <option value="labor">Labor</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Date</label>
                                <input
                                    type="date"
                                    value={newCost.date}
                                    onChange={(e) => setNewCost({ ...newCost, date: e.target.value })}
                                    className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Description (optional)</label>
                                <input
                                    type="text"
                                    value={newCost.description}
                                    onChange={(e) => setNewCost({ ...newCost, description: e.target.value })}
                                    placeholder="Adobe subscription, camera gear..."
                                    className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 focus:outline-none"
                                />
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setShowAddCost(false)}
                                className="flex-1 py-2.5 border border-gray-700 rounded-xl font-medium hover:bg-gray-800 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAddCost}
                                disabled={!newCost.amount || parseFloat(newCost.amount) <= 0}
                                className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-xl font-medium transition-colors"
                            >
                                Add Expense
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <BottomNav />
        </main>
    );
}

// Icons
function BackIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
    );
}

function PlusIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
    );
}

function TrashIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
    );
}
