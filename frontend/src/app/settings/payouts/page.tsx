"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { BottomNav } from "@/components/nav/BottomNav";
import { usePayouts } from "@/hooks/usePayouts";

export default function PayoutsSettingsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const {
        account,
        balance,
        history,
        isLoading,
        error,
        startOnboarding,
        refreshAccount,
        initiatePayout,
        openDashboard,
    } = usePayouts();

    const [payoutAmount, setPayoutAmount] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    // Handle onboarding return
    useEffect(() => {
        if (searchParams.get("onboarding") === "complete") {
            refreshAccount();
            // Clean up URL
            router.replace("/settings/payouts");
        }
        if (searchParams.get("refresh") === "true") {
            refreshAccount();
            router.replace("/settings/payouts");
        }
    }, [searchParams, refreshAccount, router]);

    const handleStartOnboarding = async () => {
        const url = await startOnboarding();
        if (url) {
            window.location.href = url;
        }
    };

    const handleInitiatePayout = async () => {
        const amountCents = Math.round(parseFloat(payoutAmount) * 100);
        if (isNaN(amountCents) || amountCents <= 0) {
            return;
        }

        setIsProcessing(true);
        const success = await initiatePayout(amountCents);
        setIsProcessing(false);

        if (success) {
            setPayoutAmount("");
            setSuccessMessage("Payout initiated successfully!");
            setTimeout(() => setSuccessMessage(null), 5000);
        }
    };

    const formatCurrency = (cents: number, currency = "usd") => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: currency.toUpperCase(),
        }).format(cents / 100);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const getStatusBadge = (status: string) => {
        const colors: Record<string, string> = {
            pending: "bg-yellow-500/20 text-yellow-400",
            in_transit: "bg-blue-500/20 text-blue-400",
            paid: "bg-green-500/20 text-green-400",
            completed: "bg-green-500/20 text-green-400",
            failed: "bg-red-500/20 text-red-400",
            active: "bg-green-500/20 text-green-400",
            restricted: "bg-yellow-500/20 text-yellow-400",
        };
        return colors[status] || "bg-gray-500/20 text-gray-200";
    };

    return (
        <main className="min-h-screen bg-black pb-20">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-black/90 backdrop-blur-sm border-b border-gray-800">
                <div className="flex items-center gap-3 px-4 py-3">
                    <Link href="/settings" className="text-gray-200 hover:text-white" aria-label="Back">
                        <BackIcon className="w-6 h-6" />
                    </Link>
                    <h1 className="text-xl font-bold text-white">Payouts</h1>
                </div>
            </header>

            <div className="p-4 space-y-6">
                {/* Error Message */}
                {error && (
                    <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-xl text-red-400">
                        {error}
                    </div>
                )}

                {/* Success Message */}
                {successMessage && (
                    <div className="p-4 bg-green-500/20 border border-green-500/50 rounded-xl text-green-400">
                        {successMessage}
                    </div>
                )}

                {/* Loading State */}
                {isLoading && !account && (
                    <div className="flex items-center justify-center py-12">
                        <div className="animate-spin w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full" />
                    </div>
                )}

                {/* No Account - Onboarding CTA */}
                {!isLoading && !account && (
                    <section className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 rounded-2xl p-6 border border-purple-500/30">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-14 h-14 bg-purple-500/20 rounded-xl flex items-center justify-center">
                                <BankIcon className="w-7 h-7 text-purple-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Start Getting Paid</h2>
                                <p className="text-gray-200 text-sm">
                                    Connect your bank account to receive payouts
                                </p>
                            </div>
                        </div>
                        <p className="text-gray-300 mb-6">
                            Set up your payout account to receive earnings from brand deals,
                            affiliate commissions, and royalties directly to your bank.
                        </p>
                        <button
                            onClick={handleStartOnboarding}
                            disabled={isLoading}
                            className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:opacity-80 rounded-xl font-medium transition-colors"
                        >
                            {isLoading ? "Setting up..." : "Set Up Payouts"}
                        </button>
                    </section>
                )}

                {/* Account Status */}
                {account && (
                    <>
                        {/* Account Card */}
                        <section className="bg-gray-900 rounded-2xl p-5">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold">Payout Account</h2>
                                <span
                                    className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(
                                        account.status
                                    )}`}
                                >
                                    {account.status.charAt(0).toUpperCase() +
                                        account.status.slice(1)}
                                </span>
                            </div>

                            {!account.payouts_enabled && (
                                <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl mb-4">
                                    <p className="text-yellow-400 text-sm">
                                        {account.details_submitted
                                            ? "Your account is being verified. This usually takes 1-2 business days."
                                            : "Please complete your account setup to enable payouts."}
                                    </p>
                                    {!account.details_submitted && (
                                        <button
                                            onClick={handleStartOnboarding}
                                            className="mt-3 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            Complete Setup
                                        </button>
                                    )}
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-gray-300 text-sm">Country</p>
                                    <p className="font-medium">{account.country}</p>
                                </div>
                                <div>
                                    <p className="text-gray-300 text-sm">Currency</p>
                                    <p className="font-medium uppercase">
                                        {account.default_currency}
                                    </p>
                                </div>
                            </div>

                            {account.payouts_enabled && (
                                <button
                                    onClick={openDashboard}
                                    className="mt-4 w-full py-2.5 border border-gray-700 hover:border-gray-600 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
                                >
                                    <ExternalLinkIcon className="w-4 h-4" />
                                    Open Stripe Dashboard
                                </button>
                            )}
                        </section>

                        {/* Balance Card */}
                        {account.payouts_enabled && balance && (
                            <section className="bg-gray-900 rounded-2xl p-5">
                                <h2 className="text-lg font-semibold mb-4">Balance</h2>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="bg-gray-800 rounded-xl p-4">
                                        <p className="text-gray-300 text-sm">Available</p>
                                        <p className="text-2xl font-bold text-green-400">
                                            {formatCurrency(balance.total_available_cents)}
                                        </p>
                                    </div>
                                    <div className="bg-gray-800 rounded-xl p-4">
                                        <p className="text-gray-300 text-sm">Pending</p>
                                        <p className="text-2xl font-bold text-yellow-400">
                                            {formatCurrency(balance.total_pending_cents)}
                                        </p>
                                    </div>
                                </div>

                                {/* Payout Form */}
                                {balance.total_available_cents > 0 && (
                                    <div className="border-t border-gray-800 pt-4">
                                        <h3 className="text-sm font-medium text-gray-200 mb-3">
                                            Request Payout
                                        </h3>
                                        <div className="flex gap-3">
                                            <div className="relative flex-1">
                                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-300">
                                                    $
                                                </span>
                                                <input
                                                    type="number"
                                                    value={payoutAmount}
                                                    onChange={(e) => setPayoutAmount(e.target.value)}
                                                    placeholder="0.00"
                                                    min="10"
                                                    max={balance.total_available_cents / 100}
                                                    step="0.01"
                                                    className="w-full pl-7 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl focus:border-purple-500 focus:outline-none"
                                                />
                                            </div>
                                            <button
                                                onClick={handleInitiatePayout}
                                                disabled={
                                                    isProcessing ||
                                                    !payoutAmount ||
                                                    parseFloat(payoutAmount) < 10
                                                }
                                                className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-80 disabled:cursor-not-allowed rounded-xl font-medium transition-colors"
                                            >
                                                {isProcessing ? "Processing..." : "Withdraw"}
                                            </button>
                                        </div>
                                        <p className="text-xs text-gray-300 mt-2">
                                            Minimum payout: $10.00. Usually arrives in 2-3 business
                                            days.
                                        </p>
                                    </div>
                                )}
                            </section>
                        )}

                        {/* Payout History */}
                        {account.payouts_enabled && history && (
                            <section className="bg-gray-900 rounded-2xl overflow-hidden">
                                <div className="p-5 border-b border-gray-800">
                                    <h2 className="text-lg font-semibold">History</h2>
                                </div>

                                {history.payouts.length === 0 &&
                                    history.transfers.length === 0 ? (
                                    <div className="p-8 text-center">
                                        <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                                            <HistoryIcon className="w-8 h-8 text-gray-200" />
                                        </div>
                                        <p className="text-gray-300">No transactions yet</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-800">
                                        {/* Show payouts first, then transfers */}
                                        {history.payouts.map((payout) => (
                                            <div
                                                key={payout.id}
                                                className="flex items-center justify-between p-4"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
                                                        <ArrowUpIcon className="w-5 h-5 text-purple-400" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium">Payout to Bank</p>
                                                        <p className="text-sm text-gray-300">
                                                            {formatDate(payout.created_at)}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <p className="font-medium">
                                                        -{formatCurrency(payout.amount_cents)}
                                                    </p>
                                                    <span
                                                        className={`text-xs px-2 py-0.5 rounded-full ${getStatusBadge(
                                                            payout.status
                                                        )}`}
                                                    >
                                                        {payout.status}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                        {history.transfers.map((transfer) => (
                                            <div
                                                key={transfer.id}
                                                className="flex items-center justify-between p-4"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                                                        <ArrowDownIcon className="w-5 h-5 text-green-400" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium">
                                                            {transfer.source_type || "Earnings"}
                                                        </p>
                                                        <p className="text-sm text-gray-300">
                                                            {formatDate(transfer.created_at)}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <p className="font-medium text-green-400">
                                                        +{formatCurrency(transfer.amount_cents)}
                                                    </p>
                                                    <span
                                                        className={`text-xs px-2 py-0.5 rounded-full ${getStatusBadge(
                                                            transfer.status
                                                        )}`}
                                                    >
                                                        {transfer.status}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        )}
                    </>
                )}
            </div>

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

function BankIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
    );
}

function ExternalLinkIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
    );
}

function HistoryIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function ArrowUpIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
    );
}

function ArrowDownIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
    );
}
