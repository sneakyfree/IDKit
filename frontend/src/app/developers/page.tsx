"use client";

import { useState, useEffect } from "react";
import { Key, Plus, Copy, Eye, EyeOff, Trash2, Code, Book, Loader2, CheckCircle, AlertTriangle, AlertCircle } from "lucide-react";
import { developersApi } from "@/lib/api";

/**
 * Developer Portal UI
 * 
 * API documentation, key management, and SDK downloads
 */

interface ApiKey {
    id: string;
    name: string;
    prefix: string;
    createdAt: string;
    lastUsed?: string;
    scopes: string[];
    status: "active" | "revoked";
}

interface Endpoint {
    method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
    path: string;
    description: string;
    auth: boolean;
}

// Using real API instead of mock data

const API_ENDPOINTS: Endpoint[] = [
    { method: "GET", path: "/api/v1/content", description: "List all content", auth: true },
    { method: "POST", path: "/api/v1/content", description: "Create new content", auth: true },
    { method: "GET", path: "/api/v1/content/{id}", description: "Get content by ID", auth: true },
    { method: "PUT", path: "/api/v1/content/{id}", description: "Update content", auth: true },
    { method: "DELETE", path: "/api/v1/content/{id}", description: "Delete content", auth: true },
    { method: "GET", path: "/api/v1/analytics", description: "Get analytics data", auth: true },
    { method: "GET", path: "/api/v1/analytics/export", description: "Export analytics", auth: true },
    { method: "POST", path: "/api/v1/ai/generate", description: "Generate AI content", auth: true },
    { method: "GET", path: "/api/v1/twins", description: "List AI twins", auth: true },
    { method: "POST", path: "/api/v1/twins/{id}/generate", description: "Generate with twin", auth: true },
];

const SDKS = [
    { name: "JavaScript/TypeScript", version: "2.1.0", icon: "🟨" },
    { name: "Python", version: "2.0.5", icon: "🐍" },
    { name: "Go", version: "1.3.0", icon: "🔵" },
    { name: "Ruby", version: "1.1.2", icon: "💎" },
];

export default function DeveloperPortalPage() {
    const [keys, setKeys] = useState<ApiKey[]>([]);
    const [activeTab, setActiveTab] = useState<"keys" | "docs" | "sdks">("keys");
    const [showCreateKey, setShowCreateKey] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchKeys() {
            try {
                setLoading(true);
                setError(null);
                const response = await developersApi.listApiKeys();
                const apiKeys = Array.isArray(response) ? response : (response as any).keys || [];
                setKeys(apiKeys.map((k: any) => ({
                    id: k.id,
                    name: k.name,
                    prefix: k.prefix,
                    createdAt: k.created_at,
                    lastUsed: k.last_used_at,
                    scopes: k.scopes,
                    status: k.status,
                })));
            } catch (e) {
                setError(e instanceof Error ? e.message : 'Failed to load API keys');
            } finally {
                setLoading(false);
            }
        }
        fetchKeys();
    }, []);

    return (
        <main className="min-h-screen bg-black text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold">Developer Portal</h1>
                        <p className="text-gray-400">API keys, documentation, and SDKs</p>
                    </div>
                    <a
                        href="/docs"
                        target="_blank"
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-xl hover:bg-gray-700"
                    >
                        <Book className="w-5 h-5" />
                        Full Documentation
                    </a>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {(["keys", "docs", "sdks"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-lg capitalize ${activeTab === tab ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                }`}
                        >
                            {tab === "keys" ? "API Keys" : tab === "docs" ? "API Docs" : "SDKs"}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                    </div>
                ) : (
                    <>
                        {/* API Keys Tab */}
                        {activeTab === "keys" && (
                            <div className="space-y-4">
                                <div className="flex justify-end">
                                    <button
                                        onClick={() => setShowCreateKey(true)}
                                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 rounded-xl hover:bg-purple-700"
                                    >
                                        <Plus className="w-5 h-5" />
                                        Create API Key
                                    </button>
                                </div>

                                {keys.map((key) => (
                                    <ApiKeyCard
                                        key={key.id}
                                        apiKey={key}
                                        onRevoke={() => setKeys(prev => prev.map(k =>
                                            k.id === key.id ? { ...k, status: "revoked" as const } : k
                                        ))}
                                    />
                                ))}

                                <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
                                    <div className="flex gap-3">
                                        <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                                        <div className="text-sm">
                                            <p className="font-medium text-yellow-400">Keep your API keys secure</p>
                                            <p className="text-gray-400">Never share API keys in public repositories or client-side code.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* API Docs Tab */}
                        {activeTab === "docs" && (
                            <div className="bg-gray-900 rounded-xl overflow-hidden">
                                <div className="p-4 bg-gray-800 border-b border-gray-700">
                                    <p className="text-sm text-gray-400">Base URL: <code className="text-purple-400">https://api.idkit.io/v1</code></p>
                                </div>
                                <div className="divide-y divide-gray-800">
                                    {API_ENDPOINTS.map((endpoint, i) => (
                                        <div key={i} className="p-4 flex items-center justify-between hover:bg-gray-800/50">
                                            <div className="flex items-center gap-4">
                                                <span className={`px-2 py-1 text-xs font-mono rounded ${endpoint.method === "GET" ? "bg-green-500/20 text-green-400" :
                                                    endpoint.method === "POST" ? "bg-blue-500/20 text-blue-400" :
                                                        endpoint.method === "PUT" ? "bg-yellow-500/20 text-yellow-400" :
                                                            endpoint.method === "DELETE" ? "bg-red-500/20 text-red-400" :
                                                                "bg-purple-500/20 text-purple-400"
                                                    }`}>
                                                    {endpoint.method}
                                                </span>
                                                <code className="text-sm">{endpoint.path}</code>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <span className="text-sm text-gray-500">{endpoint.description}</span>
                                                {endpoint.auth && <Key className="w-4 h-4 text-gray-600" />}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* SDKs Tab */}
                        {activeTab === "sdks" && (
                            <div className="grid md:grid-cols-2 gap-4">
                                {SDKS.map((sdk) => (
                                    <div key={sdk.name} className="bg-gray-900 rounded-xl p-5">
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{sdk.icon}</span>
                                                <div>
                                                    <h3 className="font-medium">{sdk.name}</h3>
                                                    <p className="text-sm text-gray-500">v{sdk.version}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="bg-gray-800 rounded-lg p-3 font-mono text-sm mb-4">
                                            {sdk.name.includes("JavaScript") && "npm install @idkit/sdk"}
                                            {sdk.name === "Python" && "pip install idkit"}
                                            {sdk.name === "Go" && "go get github.com/idkit/go-sdk"}
                                            {sdk.name === "Ruby" && "gem install idkit"}
                                        </div>
                                        <div className="flex gap-2">
                                            <button className="flex-1 py-2 bg-purple-600 rounded-lg hover:bg-purple-700 text-sm">
                                                Documentation
                                            </button>
                                            <button className="flex-1 py-2 bg-gray-800 rounded-lg hover:bg-gray-700 text-sm">
                                                GitHub
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}

                {/* Create Key Modal */}
                {showCreateKey && (
                    <CreateKeyModal
                        onClose={() => setShowCreateKey(false)}
                        onCreate={(key) => {
                            setKeys(prev => [...prev, key]);
                            setShowCreateKey(false);
                        }}
                    />
                )}
            </div>
        </main>
    );
}

function ApiKeyCard({ apiKey, onRevoke }: { apiKey: ApiKey; onRevoke: () => void }) {
    const [showKey, setShowKey] = useState(false);

    return (
        <div className="bg-gray-900 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
                        <Key className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                        <h3 className="font-medium">{apiKey.name}</h3>
                        <div className="flex items-center gap-2">
                            <code className="text-sm text-gray-500">{showKey ? "pk_live_abc123xyz789" : apiKey.prefix}</code>
                            <button onClick={() => setShowKey(!showKey)} className="p-1 hover:bg-gray-800 rounded">
                                {showKey ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            </button>
                            <button className="p-1 hover:bg-gray-800 rounded">
                                <Copy className="w-3 h-3" />
                            </button>
                        </div>
                    </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${apiKey.status === "active" ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"
                    }`}>
                    {apiKey.status}
                </span>
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
                {apiKey.scopes.map((scope) => (
                    <span key={scope} className="text-xs bg-gray-800 px-2 py-1 rounded">
                        {scope}
                    </span>
                ))}
            </div>

            <div className="flex items-center justify-between text-sm text-gray-500">
                <span>Created {new Date(apiKey.createdAt).toLocaleDateString()}</span>
                {apiKey.status === "active" && (
                    <button onClick={onRevoke} className="text-red-400 hover:text-red-300 flex items-center gap-1">
                        <Trash2 className="w-3 h-3" />
                        Revoke
                    </button>
                )}
            </div>
        </div>
    );
}

function CreateKeyModal({ onClose, onCreate }: { onClose: () => void; onCreate: (key: ApiKey) => void }) {
    const [name, setName] = useState("");
    const [scopes, setScopes] = useState<string[]>(["read:content"]);

    const availableScopes = ["read:content", "write:content", "read:analytics", "write:analytics", "read:twins", "write:twins", "admin"];

    const toggleScope = (scope: string) => {
        setScopes(prev => prev.includes(scope) ? prev.filter(s => s !== scope) : [...prev, scope]);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onCreate({
            id: Date.now().toString(),
            name,
            prefix: `pk_live_${Math.random().toString(36).slice(2, 6)}****`,
            createdAt: new Date().toISOString(),
            scopes,
            status: "active",
        });
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
            <div className="bg-gray-900 rounded-2xl max-w-md w-full p-6">
                <h2 className="text-xl font-bold mb-6">Create API Key</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="api-key-name" className="block text-sm text-gray-400 mb-1">Key Name *</label>
                        <input
                            id="api-key-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            placeholder="My App"
                            className="w-full px-4 py-3 bg-gray-800 rounded-xl border border-gray-700"
                        />
                    </div>

                    <div>
                        <label id="scopes-label" className="block text-sm text-gray-400 mb-2">Scopes</label>
                        <div className="flex flex-wrap gap-2">
                            {availableScopes.map((scope) => (
                                <button
                                    key={scope}
                                    type="button"
                                    onClick={() => toggleScope(scope)}
                                    className={`px-3 py-1 text-sm rounded-lg ${scopes.includes(scope) ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"
                                        }`}
                                >
                                    {scope}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="flex gap-4 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 py-3 bg-gray-800 rounded-xl hover:bg-gray-700">
                            Cancel
                        </button>
                        <button type="submit" disabled={!name} className="flex-1 py-3 bg-purple-600 rounded-xl hover:bg-purple-700 disabled:opacity-50">
                            Create Key
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
