'use client';

/**
 * GDPR Consent Banner
 * 
 * Cookie consent with granular options for GDPR compliance.
 */

import { useState, useEffect } from 'react';
import { Cookie, Shield, X } from 'lucide-react';

interface ConsentPreferences {
    essential: boolean; // Always true, required
    analytics: boolean;
    marketing: boolean;
    personalization: boolean;
}

const CONSENT_STORAGE_KEY = 'gdpr_consent';
const CONSENT_VERSION = '1.0';

function getStoredConsent(): ConsentPreferences | null {
    if (typeof localStorage === 'undefined') return null;
    try {
        const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed.version === CONSENT_VERSION) {
                return parsed.preferences;
            }
        }
    } catch {
        // Invalid stored data
    }
    return null;
}

function storeConsent(preferences: ConsentPreferences): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify({
        version: CONSENT_VERSION,
        preferences,
        timestamp: new Date().toISOString(),
    }));
}

export function ConsentBanner() {
    const [visible, setVisible] = useState(false);
    const [showCustomize, setShowCustomize] = useState(false);
    const [preferences, setPreferences] = useState<ConsentPreferences>({
        essential: true,
        analytics: false,
        marketing: false,
        personalization: false,
    });

    useEffect(() => {
        const stored = getStoredConsent();
        if (!stored) {
            setVisible(true);
        } else {
            setPreferences(stored);
        }
    }, []);

    const acceptAll = () => {
        const allAccepted: ConsentPreferences = {
            essential: true,
            analytics: true,
            marketing: true,
            personalization: true,
        };
        setPreferences(allAccepted);
        storeConsent(allAccepted);
        setVisible(false);
        // Would also send to backend here
    };

    const rejectAll = () => {
        const minimal: ConsentPreferences = {
            essential: true,
            analytics: false,
            marketing: false,
            personalization: false,
        };
        setPreferences(minimal);
        storeConsent(minimal);
        setVisible(false);
    };

    const savePreferences = () => {
        storeConsent(preferences);
        setVisible(false);
        setShowCustomize(false);
    };

    const togglePreference = (key: keyof ConsentPreferences) => {
        if (key === 'essential') return; // Can't toggle essential
        setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
    };

    if (!visible) return null;

    return (
        <div
            className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white dark:bg-gray-900 border-t dark:border-gray-800 shadow-lg"
            role="dialog"
            aria-label="Cookie consent"
        >
            <div className="max-w-4xl mx-auto">
                {!showCustomize ? (
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        <div className="flex items-start gap-3">
                            <Cookie className="h-6 w-6 text-amber-500 flex-shrink-0 mt-1" />
                            <div>
                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                    We value your privacy
                                </h3>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    We use cookies to enhance your experience, analyze site traffic, and personalize content.
                                    You can choose which cookies you accept.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                            <button
                                onClick={() => setShowCustomize(true)}
                                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                            >
                                Customize
                            </button>
                            <button
                                onClick={rejectAll}
                                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                            >
                                Reject All
                            </button>
                            <button
                                onClick={acceptAll}
                                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                            >
                                Accept All
                            </button>
                        </div>
                    </div>
                ) : (
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-indigo-500" />
                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                    Cookie Preferences
                                </h3>
                            </div>
                            <button
                                onClick={() => setShowCustomize(false)}
                                className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        <div className="space-y-3 mb-4">
                            {[
                                { key: 'essential', label: 'Essential', description: 'Required for the website to function', locked: true },
                                { key: 'analytics', label: 'Analytics', description: 'Help us understand how you use our site' },
                                { key: 'marketing', label: 'Marketing', description: 'Used to show relevant ads and measure campaigns' },
                                { key: 'personalization', label: 'Personalization', description: 'Remember your preferences and customize content' },
                            ].map(({ key, label, description, locked }) => (
                                <div key={key} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                    <div>
                                        <div className="font-medium text-gray-900 dark:text-white">{label}</div>
                                        <div className="text-sm text-gray-500">{description}</div>
                                    </div>
                                    <button
                                        onClick={() => togglePreference(key as keyof ConsentPreferences)}
                                        disabled={locked}
                                        className={`
                      relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                      ${preferences[key as keyof ConsentPreferences]
                                                ? 'bg-indigo-600'
                                                : 'bg-gray-300 dark:bg-gray-600'
                                            }
                      ${locked ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                                        aria-label={`Toggle ${label}`}
                                    >
                                        <span
                                            className={`
                        inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                        ${preferences[key as keyof ConsentPreferences] ? 'translate-x-6' : 'translate-x-1'}
                      `}
                                        />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <div className="flex justify-end gap-2">
                            <button
                                onClick={rejectAll}
                                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                            >
                                Reject All
                            </button>
                            <button
                                onClick={savePreferences}
                                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                            >
                                Save Preferences
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ConsentBanner;
