'use client';

interface Contradiction {
    contradiction_id: string;
    field_name: string;
    field_label: string;
    user_reported: any;
    api_verified: any;
    discrepancy_description: string;
    severity: string;
}

interface ContradictionBannerProps {
    contradictions: Contradiction[];
    onResolve: () => void;
}

export function ContradictionBanner({ contradictions, onResolve }: ContradictionBannerProps) {
    if (contradictions.length === 0) return null;

    const highSeverity = contradictions.filter(c => c.severity === 'high');
    const hasHighSeverity = highSeverity.length > 0;

    return (
        <div
            className={`mb-6 p-4 rounded-xl border ${hasHighSeverity
                    ? 'bg-red-50 border-red-200'
                    : 'bg-amber-50 border-amber-200'
                }`}
        >
            <div className="flex items-start space-x-3">
                <div
                    className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${hasHighSeverity ? 'bg-red-100' : 'bg-amber-100'
                        }`}
                >
                    <svg
                        className={`w-5 h-5 ${hasHighSeverity ? 'text-red-600' : 'text-amber-600'}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                    </svg>
                </div>

                <div className="flex-1">
                    <h3
                        className={`font-semibold ${hasHighSeverity ? 'text-red-900' : 'text-amber-900'
                            }`}
                    >
                        {contradictions.length === 1
                            ? 'We found a data mismatch'
                            : `We found ${contradictions.length} data mismatches`}
                    </h3>

                    <p
                        className={`text-sm mt-1 ${hasHighSeverity ? 'text-red-700' : 'text-amber-700'
                            }`}
                    >
                        Some of the information you provided doesn't match what we found from
                        your connected accounts. Please review and confirm.
                    </p>

                    <div className="mt-3 space-y-2">
                        {contradictions.slice(0, 3).map((c) => (
                            <div
                                key={c.contradiction_id}
                                className={`p-3 rounded-lg ${c.severity === 'high' ? 'bg-red-100' : 'bg-amber-100'
                                    }`}
                            >
                                <div className="flex justify-between items-start">
                                    <div>
                                        <span className="font-medium text-gray-900">
                                            {c.field_label}
                                        </span>
                                        <div className="text-sm text-gray-600 mt-1">
                                            <span>You said: </span>
                                            <span className="font-medium">{formatValue(c.user_reported)}</span>
                                            <span className="mx-2">→</span>
                                            <span>Connected account shows: </span>
                                            <span className="font-medium">{formatValue(c.api_verified)}</span>
                                        </div>
                                    </div>
                                    <span
                                        className={`text-xs px-2 py-1 rounded-full ${c.severity === 'high'
                                                ? 'bg-red-200 text-red-800'
                                                : 'bg-amber-200 text-amber-800'
                                            }`}
                                    >
                                        {c.discrepancy_description}
                                    </span>
                                </div>
                            </div>
                        ))}

                        {contradictions.length > 3 && (
                            <p className="text-sm text-gray-600">
                                + {contradictions.length - 3} more...
                            </p>
                        )}
                    </div>

                    <div className="mt-4 flex space-x-3">
                        <button
                            onClick={onResolve}
                            className={`px-4 py-2 text-sm font-medium rounded-lg ${hasHighSeverity
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'bg-amber-600 text-white hover:bg-amber-700'
                                } transition-colors`}
                        >
                            Review & Fix
                        </button>
                        <button
                            onClick={onResolve}
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                        >
                            Dismiss for now
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function formatValue(value: any): string {
    if (value === null || value === undefined) return 'Not set';
    if (typeof value === 'number') {
        return value.toLocaleString();
    }
    if (Array.isArray(value)) {
        return value.join(', ');
    }
    return String(value);
}
