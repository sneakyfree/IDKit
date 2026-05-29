"use client";

import { WifiOff, RefreshCw } from "lucide-react";

/**
 * Offline Page
 * 
 * Shown when user is offline and page is not cached
 */

export default function OfflinePage() {
    const handleRetry = () => {
        window.location.reload();
    };

    return (
        <main className="min-h-screen bg-black text-white flex items-center justify-center p-6">
            <div className="text-center max-w-md">
                <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-6">
                    <WifiOff className="w-10 h-10 text-gray-300" />
                </div>

                <h1 className="text-2xl font-bold mb-2">You&apos;re Offline</h1>
                <p className="text-gray-200 mb-8">
                    It looks like you&apos;ve lost your internet connection. Some features may be unavailable until you&apos;re back online.
                </p>

                <div className="space-y-4">
                    <button
                        onClick={handleRetry}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 rounded-xl hover:bg-purple-700"
                    >
                        <RefreshCw className="w-5 h-5" />
                        Try Again
                    </button>

                    <div className="text-sm text-gray-300">
                        <p className="mb-2">While offline, you can still:</p>
                        <ul className="text-left space-y-1 pl-4">
                            <li>• View cached content</li>
                            <li>• Edit saved drafts</li>
                            <li>• Review analytics history</li>
                        </ul>
                    </div>
                </div>

                <p className="text-xs text-gray-200 mt-8">
                    Changes made offline will sync automatically when you reconnect.
                </p>
            </div>
        </main>
    );
}
