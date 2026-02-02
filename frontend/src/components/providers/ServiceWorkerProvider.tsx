"use client";

import { useEffect } from "react";
import { OfflineBanner, UpdateBanner } from "@/hooks/useServiceWorker";

/**
 * Service Worker Provider Component
 *
 * Registers the service worker and provides offline/update banners.
 * Should be placed in the root layout to enable PWA features.
 */
export function ServiceWorkerProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    useEffect(() => {
        // Only register in production or when explicitly enabled
        if (
            typeof window !== "undefined" &&
            "serviceWorker" in navigator &&
            process.env.NODE_ENV === "production"
        ) {
            navigator.serviceWorker
                .register("/sw.js", { scope: "/" })
                .then((registration) => {
                    console.log("[SW] Registered:", registration.scope);
                })
                .catch((error) => {
                    console.error("[SW] Registration failed:", error);
                });
        }
    }, []);

    return (
        <>
            {children}
            <OfflineBanner />
            <UpdateBanner />
        </>
    );
}

export default ServiceWorkerProvider;
