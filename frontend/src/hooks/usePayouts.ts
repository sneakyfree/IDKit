"use client";

import { useState, useCallback, useEffect } from "react";
import {
    payouts,
    ConnectAccountResponse,
    BalanceResponse,
    PayoutListResponse,
} from "@/lib/api";

interface PayoutsState {
    account: ConnectAccountResponse | null;
    balance: BalanceResponse | null;
    history: PayoutListResponse | null;
    isLoading: boolean;
    error: string | null;
}

interface UsePayoutsReturn extends PayoutsState {
    startOnboarding: () => Promise<string | null>;
    refreshAccount: () => Promise<void>;
    refreshBalance: () => Promise<void>;
    refreshHistory: () => Promise<void>;
    initiatePayout: (amountCents: number, currency?: string) => Promise<boolean>;
    openDashboard: () => Promise<void>;
}

export function usePayouts(): UsePayoutsReturn {
    const [state, setState] = useState<PayoutsState>({
        account: null,
        balance: null,
        history: null,
        isLoading: true,
        error: null,
    });

    const refreshAccount = useCallback(async () => {
        try {
            setState((prev) => ({ ...prev, isLoading: true, error: null }));
            const account = await payouts.getAccountStatus();
            setState((prev) => ({
                ...prev,
                account,
                isLoading: false,
            }));
        } catch (err) {
            // 404 means no account yet
            if ((err as { status?: number }).status === 404) {
                setState((prev) => ({
                    ...prev,
                    account: null,
                    isLoading: false,
                }));
            } else {
                setState((prev) => ({
                    ...prev,
                    error: (err as Error).message,
                    isLoading: false,
                }));
            }
        }
    }, []);

    const refreshBalance = useCallback(async () => {
        try {
            const balance = await payouts.getBalance();
            setState((prev) => ({ ...prev, balance }));
        } catch (err) {
            console.error("Failed to fetch balance:", err);
        }
    }, []);

    const refreshHistory = useCallback(async () => {
        try {
            const history = await payouts.getHistory();
            setState((prev) => ({ ...prev, history }));
        } catch (err) {
            console.error("Failed to fetch history:", err);
        }
    }, []);

    const startOnboarding = useCallback(async (): Promise<string | null> => {
        try {
            setState((prev) => ({ ...prev, isLoading: true, error: null }));
            const response = await payouts.startOnboarding();
            setState((prev) => ({ ...prev, isLoading: false }));
            return response.url;
        } catch (err) {
            setState((prev) => ({
                ...prev,
                error: (err as Error).message,
                isLoading: false,
            }));
            return null;
        }
    }, []);

    const initiatePayout = useCallback(
        async (amountCents: number, currency = "usd"): Promise<boolean> => {
            try {
                setState((prev) => ({ ...prev, isLoading: true, error: null }));
                await payouts.initiatePayout(amountCents, currency);
                setState((prev) => ({ ...prev, isLoading: false }));
                // Refresh balance and history after payout
                await refreshBalance();
                await refreshHistory();
                return true;
            } catch (err) {
                setState((prev) => ({
                    ...prev,
                    error: (err as Error).message,
                    isLoading: false,
                }));
                return false;
            }
        },
        [refreshBalance, refreshHistory]
    );

    const openDashboard = useCallback(async () => {
        try {
            const response = await payouts.getDashboardLink();
            window.open(response.url, "_blank");
        } catch (err) {
            console.error("Failed to get dashboard link:", err);
        }
    }, []);

    // Initial load
    useEffect(() => {
        const loadData = async () => {
            await refreshAccount();
        };
        loadData();
    }, [refreshAccount]);

    // Load balance and history when account is active
    useEffect(() => {
        if (state.account?.payouts_enabled) {
            refreshBalance();
            refreshHistory();
        }
    }, [state.account?.payouts_enabled, refreshBalance, refreshHistory]);

    return {
        ...state,
        startOnboarding,
        refreshAccount,
        refreshBalance,
        refreshHistory,
        initiatePayout,
        openDashboard,
    };
}
