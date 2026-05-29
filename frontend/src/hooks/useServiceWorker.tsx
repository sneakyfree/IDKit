"use client";

import { useEffect, useState, useCallback } from "react";

interface ServiceWorkerState {
    isSupported: boolean;
    isRegistered: boolean;
    isOnline: boolean;
    waitingWorker: ServiceWorker | null;
    registration: ServiceWorkerRegistration | null;
}

interface UseServiceWorkerReturn extends ServiceWorkerState {
    update: () => Promise<void>;
    skipWaiting: () => void;
}

/**
 * Hook for service worker registration and management
 *
 * Features:
 * - Registers service worker on mount
 * - Tracks online/offline status
 * - Provides update mechanism for new versions
 * - Handles skipWaiting for immediate activation
 *
 * @example
 * const { isOnline, isRegistered, update } = useServiceWorker();
 */
export function useServiceWorker(): UseServiceWorkerReturn {
    // Optimistic default: assume online for the initial paint. navigator.onLine
    // is unreliable at load (it can report false while actually online on some
    // networks/browsers), which flashes a false "You're offline" banner. We
    // instead trust the more-reliable online/offline transition events below.
    const [state, setState] = useState<ServiceWorkerState>({
        isSupported: false,
        isRegistered: false,
        isOnline: true,
        waitingWorker: null,
        registration: null,
    });

    useEffect(() => {
        if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
            return;
        }

        setState((prev) => ({ ...prev, isSupported: true }));

        // Register service worker
        const registerSW = async () => {
            try {
                const registration = await navigator.serviceWorker.register("/sw.js", {
                    scope: "/",
                    updateViaCache: "none",
                });

                console.log("[SW] Service worker registered:", registration.scope);

                setState((prev) => ({
                    ...prev,
                    isRegistered: true,
                    registration,
                }));

                // Check for updates periodically
                registration.addEventListener("updatefound", () => {
                    const newWorker = registration.installing;
                    if (newWorker) {
                        newWorker.addEventListener("statechange", () => {
                            if (
                                newWorker.state === "installed" &&
                                navigator.serviceWorker.controller
                            ) {
                                // New version available
                                setState((prev) => ({ ...prev, waitingWorker: newWorker }));
                                console.log("[SW] New version available");
                            }
                        });
                    }
                });

                // Check for waiting worker on initial load
                if (registration.waiting) {
                    setState((prev) => ({ ...prev, waitingWorker: registration.waiting }));
                }
            } catch (error) {
                console.error("[SW] Registration failed:", error);
            }
        };

        registerSW();

        // Online/offline status
        const handleOnline = () => {
            setState((prev) => ({ ...prev, isOnline: true }));
            console.log("[SW] Back online");

            // Trigger background sync if available
            if ("sync" in ServiceWorkerRegistration.prototype) {
                navigator.serviceWorker.ready.then((registration) => {
                    (registration as any).sync.register("sync-drafts");
                    (registration as any).sync.register("sync-analytics");
                });
            }
        };

        const handleOffline = () => {
            setState((prev) => ({ ...prev, isOnline: false }));
            console.log("[SW] Went offline");
        };

        window.addEventListener("online", handleOnline);
        window.addEventListener("offline", handleOffline);

        // Controller change handler (new SW activated)
        const handleControllerChange = () => {
            console.log("[SW] Controller changed, reloading page");
            window.location.reload();
        };

        navigator.serviceWorker.addEventListener(
            "controllerchange",
            handleControllerChange
        );

        return () => {
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("offline", handleOffline);
            navigator.serviceWorker.removeEventListener(
                "controllerchange",
                handleControllerChange
            );
        };
    }, []);

    const update = useCallback(async () => {
        if (!state.registration) return;

        try {
            await state.registration.update();
            console.log("[SW] Update check triggered");
        } catch (error) {
            console.error("[SW] Update check failed:", error);
        }
    }, [state.registration]);

    const skipWaiting = useCallback(() => {
        if (!state.waitingWorker) return;

        state.waitingWorker.postMessage({ type: "SKIP_WAITING" });
        setState((prev) => ({ ...prev, waitingWorker: null }));
    }, [state.waitingWorker]);

    return {
        ...state,
        update,
        skipWaiting,
    };
}

/**
 * Component to show offline banner
 */
export function OfflineBanner() {
    const { isOnline } = useServiceWorker();

    if (isOnline) return null;

    return (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
            <div className="bg-yellow-500 text-black px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
                <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
                    />
                </svg>
                <span className="font-medium">You&apos;re offline</span>
                <span className="text-sm opacity-80">Changes will sync when online</span>
            </div>
        </div>
    );
}

/**
 * Component to show update available banner
 */
export function UpdateBanner() {
    const { waitingWorker, skipWaiting } = useServiceWorker();

    if (!waitingWorker) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50">
            <div className="bg-purple-600 text-white px-4 py-3 rounded-lg shadow-lg">
                <p className="font-medium mb-2">New version available!</p>
                <button
                    onClick={skipWaiting}
                    className="bg-white text-purple-600 px-4 py-1 rounded text-sm font-medium hover:bg-purple-100 transition-colors"
                >
                    Update Now
                </button>
            </div>
        </div>
    );
}

export default useServiceWorker;
